"""Replay personally collected finger XY through physical Panda contact.

No policy training. The optional human-object teacher uses cube-state feedback;
the original finger replay uses cube state only for termination.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault('MUJOCO_GL', 'egl')
os.environ.setdefault('PYOPENGL_PLATFORM', os.environ['MUJOCO_GL'])
os.environ.setdefault('NUMBA_CACHE_DIR', str(Path.cwd()/'.cache'/'numba'))

import cv2
import imageio.v2 as imageio
import numpy as np
from scipy.spatial.transform import Rotation
from robosuite.controllers import load_composite_controller_config
from .push_env import PlanarPush
from .task_rules import StopRule, box_inside_polygon
from .retargeting import adapt_reference
from .teacher import object_tracking_target


def prepare_reference(tracks_path, calibration_path, start_s, end_s, radius):
    tracks = np.load(tracks_path)
    calibration = json.loads(calibration_path.read_text())
    if 'image_orientation' in tracks.files and tracks['image_orientation'].item()!=calibration.get('image_orientation','stored'):
        raise ValueError('Tracks and calibration image orientations differ; regenerate tracks')
    if 'calibration_sha256' in tracks.files and tracks['calibration_sha256'].item()!=hashlib.sha256(json.dumps(calibration,sort_keys=True).encode()).hexdigest():
        raise ValueError('Tracks do not match this calibration; regenerate tracks')
    time, obj, finger = tracks['time_s'], tracks['object_xy_m'], tracks['finger_xy_m']
    selected = (time >= start_s) & (time <= end_s)
    if selected.sum() < 5 or not np.isfinite(finger[selected]).all():
        raise ValueError('Contact segment must contain at least five valid finger detections with no gaps')
    obj_start = np.median(obj[:30], axis=0)
    obj_end = np.median(obj[-15:], axis=0)
    direction = obj_end-obj_start
    if np.linalg.norm(direction) < .01:
        raise ValueError('Pilot object displacement is too small to define a push direction')
    direction /= np.linalg.norm(direction)
    size = np.asarray(calibration['object_dimensions_m'])
    # One constant alignment from the middle of the contact segment, not
    # following the observed object at each frame. Box support along direction.
    middle = selected & (time >= start_s+.5) & (time <= end_s-.5)
    valid = middle & np.isfinite(obj).all(axis=1) & np.isfinite(finger).all(axis=1)
    if valid.sum() < 3:
        raise ValueError('Insufficient valid contact frames for constant marker offset')
    support = float(np.dot(np.abs(direction), size[:2]/2))
    offset = np.median(obj[valid]-finger[valid], axis=0)-direction*(support+radius+.0005)
    origin = np.array([calibration['rectangle_width_m']/2, calibration['rectangle_height_m']/2])
    goal=calibration.get('goal')
    target=np.asarray(goal['center_table_xy_m']) if goal else obj_end
    target_direction=target-obj_start
    yaw=float(np.arctan2(target_direction[1],target_direction[0])) if goal else 0.
    result={'time_s': time[selected]-time[selected][0],
            'reference_xy': finger[selected]+offset-origin,
            'object_start': obj_start-origin, 'endpoint': obj_end-origin,
            'target':target-origin, 'goal_source':goal['source'] if goal else 'observed demonstration endpoint',
            'target_polygon':np.asarray(goal['corners_table_xy_m'])-origin if goal else None,
            'goal_tolerance_m':goal.get('success_center_tolerance_m',.01) if goal else .02,
            'push_yaw_rad':yaw,
            'marker_to_tool_offset_m': offset, 'object_size': size}
    # Register the decoded paper axes to the user's fixed robot rectangle.
    angle=float(calibration.get('paper_to_robot_yaw_degrees',0.))
    theta=np.deg2rad(angle)
    rotation=np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
    paper_dimensions=np.array([calibration['rectangle_width_m'],calibration['rectangle_height_m']])
    rotated_dimensions=np.abs(rotation)@paper_dimensions
    robot_dimensions=np.asarray(calibration.get('robot_rectangle_dimensions_xy_m',rotated_dimensions))
    if robot_dimensions.shape!=(2,) or not np.isfinite(robot_dimensions).all() or np.any(robot_dimensions<=0):
        raise ValueError('Robot rectangle must have two positive finite dimensions')
    matrix=np.diag(robot_dimensions/rotated_dimensions)@rotation
    if 'paper_to_robot_matrix' in calibration:
        matrix=np.asarray(calibration['paper_to_robot_matrix'],float)
        if matrix.shape!=(2,2) or not np.isfinite(matrix).all() or abs(np.linalg.det(matrix))<1e-8:
            raise ValueError('Paper-to-robot matrix must be finite and invertible')
        robot_dimensions=np.abs(matrix)@paper_dimensions
    # Derive the physical contact offset in robot metres after registration;
    # never stretch cube/tool dimensions with the paper-axis conversion.
    robot_obj=(obj-origin)@matrix.T
    robot_finger=(finger-origin)@matrix.T
    robot_start=(obj_start-origin)@matrix.T
    robot_end=(obj_end-origin)@matrix.T
    robot_direction=robot_end-robot_start
    robot_direction/=np.linalg.norm(robot_direction)
    robot_support=float(np.dot(np.abs(robot_direction),size[:2]/2))
    robot_offset=np.median(robot_obj[valid]-robot_finger[valid],axis=0)-robot_direction*(robot_support+radius+.0005)
    result['reference_xy']=robot_finger[selected]+robot_offset
    result['object_reference_xy']=robot_obj[selected]
    result['object_start']=robot_start
    result['endpoint']=robot_end
    result['target']=(target-origin)@matrix.T
    result['marker_to_tool_offset_m']=robot_offset
    if result['target_polygon'] is not None:
        result['target_polygon']=result['target_polygon']@matrix.T
    target_robot_direction=result['target']-robot_start
    result['push_yaw_rad']=float(np.arctan2(target_robot_direction[1],target_robot_direction[0])) if goal else yaw+theta
    result['paper_to_robot_yaw_degrees']=angle
    result['paper_to_robot_frame']=calibration.get('paper_to_robot_frame','legacy')
    result['paper_to_robot_matrix']=matrix
    result['paper_size_robot_xy']=robot_dimensions
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tracks', type=Path, default=Path('data/processed/pilot/tracks.npz'))
    parser.add_argument('--calibration', type=Path, default=Path('data/calibration/pilot.json'))
    parser.add_argument('--output', type=Path, default=Path('outputs/pilot_replay'))
    parser.add_argument('--start-s', type=float, default=3.6)
    parser.add_argument('--end-s', type=float, default=8.7)
    parser.add_argument('--eef-height-m', type=float, default=.868)
    parser.add_argument('--tool', choices=['paddle','capsule'], default='paddle')
    parser.add_argument('--tool-yaw-offset-deg',type=int,choices=[0,180],default=0,help='Choose equivalent symmetric tool face without changing push direction')
    parser.add_argument('--approach',choices=['clearance','recorded'],default='clearance',help='Clearance checks initial geometry before lowering; recorded reproduces development baseline')
    parser.add_argument('--termination',choices=['goal-or-timeout','reference'],default='goal-or-timeout')
    parser.add_argument('--push-timeout-s',type=float,default=10.,help='Simulation seconds from start of pushing, excluding approach/withdrawal')
    parser.add_argument('--goal-dwell-s',type=float,default=.2)
    parser.add_argument('--retargeting',choices=['absolute','relative','relative-scaled'],default='absolute')
    parser.add_argument('--start-offset-m',type=float,nargs=2,default=[0.,0.],metavar=('DX','DY'),help='Shift simulated cube start in table metres; target stays fixed')
    parser.add_argument('--detail-camera',choices=['pushview','robotview'],default='pushview')
    parser.add_argument('--no-video', action='store_true')
    parser.add_argument('--push-controller',choices=['finger-replay','human-object-feedback'],default='finger-replay',help='Optional scripted teacher tracks the human object path using simulated cube feedback')
    args = parser.parse_args()
    if args.end_s <= args.start_s:
        parser.error('end must follow start')
    if args.push_timeout_s<.05 or abs(args.push_timeout_s/.05-round(args.push_timeout_s/.05))>1e-7:
        parser.error('--push-timeout-s must be a positive multiple of 0.05 s')
    if args.goal_dwell_s<0:
        parser.error('--goal-dwell-s cannot be negative')
    args.output.mkdir(parents=True, exist_ok=True)
    tool_radius=.004
    reference = prepare_reference(args.tracks, args.calibration, args.start_s, args.end_s, tool_radius)
    if args.push_controller=='human-object-feedback' and not np.isfinite(reference['object_reference_xy']).all():
        parser.error('Human-object teacher requires continuous finite object tracks throughout contact')
    if args.push_controller=='human-object-feedback' and (args.retargeting!='absolute' or np.any(np.asarray(args.start_offset_m)!=0)):
        parser.error('Human-object teacher currently supports original starting positions only')
    if args.retargeting!='absolute' or np.any(np.asarray(args.start_offset_m)!=0):
        reference=adapt_reference(reference,reference['object_start']+np.asarray(args.start_offset_m),args.retargeting,tool_radius)
    config = load_composite_controller_config(robot='Panda')
    config['body_parts']['right']['input_ref_frame']='world'
    env = PlanarPush(paper_size=reference['paper_size_robot_xy'],object_start=reference['object_start'], target_xy=reference['target'], target_polygon=reference['target_polygon'],
        goal_tolerance=reference['goal_tolerance_m'],
        object_size=reference['object_size'], tool_radius=tool_radius, tool_kind=args.tool, robots='Panda',
        controller_configs=config, initialization_noise=None, has_renderer=False,
        has_offscreen_renderer=not args.no_video, use_camera_obs=False,
        control_freq=20, horizon=1000, ignore_done=True, hard_reset=False,
        table_friction=(.3,.005,.0001), seed=7)
    observations, actions, desired, phases, contacts, table_contacts = [], [], [], [], [], []
    writer = None
    before_states, before_quats, after_quats = [], [], []
    cube_quats_before, cube_quats_after = [], []
    tool_yaw=reference['push_yaw_rad']+np.deg2rad(args.tool_yaw_offset_deg)
    orientation=Rotation.from_euler('z',tool_yaw)*Rotation.from_matrix(np.diag([1.,-1.,-1.]))
    try:
        obs=env.reset()
        initial_cube=obs['cube_pos'].copy()
        if not args.no_video:
            writer=imageio.get_writer(args.output/'replay.mp4',fps=20,codec='libx264',quality=8)
        def command(target, phase):
            nonlocal obs
            action=np.zeros(env.action_dim)
            action[:3]=np.clip((target-obs['robot0_eef_pos'])/.05,-.2,.2)
            # Legacy eef_quat is an upstream body quaternion; OSC controls the
            # grip SITE, whose frame includes a fixed gripper rotation.
            site_rotation=Rotation.from_matrix(env.sim.data.site_xmat[env.robots[0].eef_site_id['right']].reshape(3,3))
            error=(orientation*site_rotation.inv()).as_rotvec()
            action[3:6]=np.clip(error/.5,-.3,.3)
            action[-1]=1
            before_states.append(np.r_[obs['robot0_eef_pos'],obs['cube_pos']])
            before_quats.append(site_rotation.as_quat())
            cube_quats_before.append(env.sim.data.body_xquat[env.cube_body_id].copy())
            obs,_,_,_=env.step(action)
            cube_quats_after.append(env.sim.data.body_xquat[env.cube_body_id].copy())
            after_quats.append(Rotation.from_matrix(env.sim.data.site_xmat[env.robots[0].eef_site_id['right']].reshape(3,3)).as_quat())
            observations.append(np.r_[obs['robot0_eef_pos'],obs['cube_pos']])
            actions.append(action.copy()); desired.append(target.copy()); phases.append(phase)
            contacts.append(env.check_contact('pusher_tip',env.cube.contact_geoms))
            table_contacts.append(env.check_contact('pusher_tip','table_collision'))
            if writer is not None:
                if args.detail_camera=='robotview':
                    # Hide arm meshes only in the explanatory overhead panel.
                    # Physics and the full-arm overview remain unchanged.
                    groups=env.sim.model.geom_group.copy()
                    visible=env.sim._render_context_offscreen.vopt.geomgroup.copy()
                    try:
                        for geom_id,name in enumerate(env.sim.model.geom_names):
                            if name and name.startswith(('robot0_','gripper0_')):
                                env.sim.model.geom_group[geom_id]=5
                        env.sim._render_context_offscreen.vopt.geomgroup[5]=0
                        frame=env.sim.render(width=480,height=480,camera_name=args.detail_camera)[::-1]
                    finally:
                        env.sim.model.geom_group[:]=groups
                        env.sim._render_context_offscreen.vopt.geomgroup[:]=visible
                else:
                    frame=env.sim.render(width=480,height=480,camera_name=args.detail_camera)[::-1]
                # Side-by-side overview and close-up improve contact inspection.
                overview=env.sim.render(width=480,height=480,camera_name='frontview')[::-1]
                combined=np.ascontiguousarray(np.concatenate([overview,frame],axis=1))
                cv2.rectangle(combined,(0,0),(960,30),(25,25,25),-1)
                cv2.putText(combined,'Panda overview',(12,21),cv2.FONT_HERSHEY_SIMPLEX,.5,(255,255,255),1)
                cv2.putText(combined,f'{"Table: base below; arm hidden" if args.detail_camera=="robotview" else "Physical contact"} | {phase} | {len(phases)/20:.2f}s',(490,21),cv2.FONT_HERSHEY_SIMPLEX,.45,(255,255,255),1)
                writer.append_data(combined)
        def move(target, steps, phase):
            begin=obs['robot0_eef_pos'].copy()
            for alpha in np.linspace(0,1,steps):
                smooth=alpha*alpha*(3-2*alpha)
                command(begin+(target-begin)*smooth,phase)
        first=np.r_[reference['reference_xy'][0],args.eef_height_m]
        direction=np.array([np.cos(reference['push_yaw_rad']),np.sin(reference['push_yaw_rad'])])
        if args.push_controller=='human-object-feedback':
            support=float(np.dot(np.abs(direction),reference['object_size'][:2]/2))
            first[:2]=reference['object_start']-direction*(support+tool_radius+.0005)
        lower=first.copy()
        approach_retreat=0.
        if args.approach=='clearance':
            direction=np.array([np.cos(reference['push_yaw_rad']),np.sin(reference['push_yaw_rad'])])
            support=float(np.dot(np.abs(direction),reference['object_size'][:2]/2))
            # Initial-state-only geometric clearance. The recorded marker
            # centroid can be biased near image boundaries. Do not lower an
            # overlapping paddle onto the die; keep the human XY reference intact.
            gap=float(np.dot(reference['object_start']-first[:2],direction))
            clearance=.012 if args.push_controller=='human-object-feedback' else .004
            approach_retreat=max(0.,support+tool_radius+clearance-gap)
            lower[:2]-=direction*approach_retreat
        above=lower+np.array([0,0,.10])
        move(above,100,'approach')
        move(lower,60,'lower')
        for _ in range(20):command(lower,'settle')
        monitor=StopRule(args.push_timeout_s,args.goal_dwell_s)
        stop_reason='reference_complete'
        push_steps=0
        hold_position=None
        if args.termination=='reference':
            steps=len(np.arange(0,reference['time_s'][-1]+.001,.05))
        else:
            steps=round(args.push_timeout_s/.05)
        for step in range(steps):
            t=step*.05
            if hold_position is None:
                # Once footage ends, hold the final reference until goal/timeout.
                xy=np.array([np.interp(t,reference['time_s'],reference['reference_xy'][:,i]) for i in range(2)])
                if args.push_controller=='human-object-feedback':
                    object_goal=np.array([np.interp(t,reference['time_s'],reference['object_reference_xy'][:,i]) for i in range(2)])
                    # Box support changes as contact rotates the cube. Follow
                    # the recorded object path with bounded state correction.
                    rotation=env.sim.data.body_xmat[env.cube_body_id].reshape(3,3)
                    xy=object_tracking_target(object_goal,obs['cube_pos'][:2],rotation,reference['object_size'],direction,tool_radius)
                target=np.r_[xy,args.eef_height_m]
                phase='human_push' if t<=reference['time_s'][-1] else 'reference_hold'
            else:
                target=hold_position
                phase='goal_dwell'
            command(target,phase)
            push_steps+=1
            if args.termination=='goal-or-timeout':
                inside=env._check_success()
                reason=monitor.update(push_steps*.05,inside)
                # Stop advancing the recorded trajectory upon containment.
                # Freeze the achieved grip XYZ during the success dwell.
                hold_position=obs['robot0_eef_pos'].copy() if inside else None
                if reason is not None:
                    stop_reason=reason
                    break
        last=obs['robot0_eef_pos'].copy()
        if args.termination=='reference':
            last=np.r_[reference['reference_xy'][-1],args.eef_height_m]
            for _ in range(10):command(last,'hold')
        move(last+np.array([0,0,.10]),60,'withdraw')
        for _ in range(20):command(last+np.array([0,0,.10]),'final_settle')
        states=np.asarray(observations); goals=np.asarray(desired); phases=np.asarray(phases)
        push=phases=='human_push'; cube=states[:,3:]; final=cube[-1]
        endpoint_distance=float(np.linalg.norm(final[:2]-reference['endpoint']))
        target_distance=float(np.linalg.norm(final[:2]-reference['target']))
        polygon=reference['target_polygon']
        center_inside=None if polygon is None else bool(cv2.pointPolygonTest(np.float32(polygon),tuple(final[:2]),False)>=0)
        body_rotation=env.sim.data.body_xmat[env.cube_body_id].reshape(3,3)
        local_corners=np.array([[sx*reference['object_size'][0]/2,sy*reference['object_size'][1]/2,sz*reference['object_size'][2]/2] for sx in [-1,1] for sy in [-1,1] for sz in [-1,1]])
        world_corners=local_corners@body_rotation.T+final
        fully_inside=None if polygon is None else box_inside_polygon(final,body_rotation,reference['object_size'],polygon)
        displacement=float(np.linalg.norm(final[:2]-initial_cube[:2]))
        lift=max(0.,float(np.max(cube[:,2])-(.8+reference['object_size'][2]/2)))
        stayed_on_table=bool(np.all(cube[:,2] > .8+reference['object_size'][2]/2-.005) and np.all(np.abs(cube[:,:2]) < .39))
        pre_push_displacement=float(np.linalg.norm(np.asarray(before_states)[np.flatnonzero(push)[0],3:5]-initial_cube[:2]))
        finite=bool(np.isfinite(states).all() and np.isfinite(env.sim.data.qpos).all())
        final_goal=bool(fully_inside) if polygon is not None else target_distance<reference['goal_tolerance_m']
        valid=finite and lift<.005 and stayed_on_table and pre_push_displacement<.002
        passed=bool(valid and final_goal and (stop_reason=='goal_reached' if args.termination=='goal-or-timeout' else displacement>.04 and any(contacts)))
        result={'checkpoint':'physical replay of personally recorded finger motion; pilot diagnostic',
            'passed':passed,'task_success':bool(stop_reason=='goal_reached' and final_goal and valid),
            'termination_mode':args.termination,'stop_reason':stop_reason,
            'push_elapsed_s':push_steps*.05,'push_timeout_s':args.push_timeout_s,'goal_dwell_s':args.goal_dwell_s,
            'success_rule':'whole projected cube inside square; orientation unrestricted' if polygon is not None else 'legacy endpoint-distance diagnostic',
            'frames':len(states),'seed':7,'control_hz':20,
            'retargeting':reference.get('retargeting',{'mode':'absolute','displacement_scale':1.,'rotation_degrees':0.}),
            'start_offset_m':args.start_offset_m,
            'paper_to_robot_yaw_degrees':reference['paper_to_robot_yaw_degrees'],'detail_camera':args.detail_camera,
            'robot_coordinate_frame':reference['paper_to_robot_frame'],
            'paper_to_robot_matrix':reference['paper_to_robot_matrix'].tolist(),'paper_size_robot_xy_m':reference['paper_size_robot_xy'].tolist(),
            'contact_segment_s':[args.start_s,args.end_s],'approach_mode':args.approach,
            'scripted_approach_retreat_m':approach_retreat, 'eef_height_m':args.eef_height_m,
            'tool':args.tool, 'tool_description':('rigid 8 x 24 x 12 mm paddle at local z=60 mm with stem' if args.tool=='paddle' else 'rigid capsule radius 4 mm; local z endpoints 25 and 60 mm'),
            'marker_to_tool_offset_m':reference['marker_to_tool_offset_m'].tolist(),
            'object_dimensions_m':reference['object_size'].tolist(),
            'initial_object_xyz_m':initial_cube.tolist(),'final_object_xyz_m':final.tolist(),
            'demonstrated_endpoint_xy_m':reference['endpoint'].tolist(),
            'target_xy_m':reference['target'].tolist(),'goal_source':reference['goal_source'],
            'goal_tolerance_m':reference['goal_tolerance_m'],'final_target_distance_m':target_distance,
            'final_center_inside_goal':center_inside,'final_object_fully_inside_goal':fully_inside,
            'push_yaw_degrees':float(np.degrees(reference['push_yaw_rad'])),
            'tool_yaw_offset_degrees':args.tool_yaw_offset_deg,'tool_yaw_degrees':float(np.degrees(tool_yaw)),
            'final_cube_yaw_degrees':float(Rotation.from_matrix(body_rotation).as_euler('xyz',degrees=True)[2]),
            'object_displacement_m':displacement,'displacement_at_push_start_m':pre_push_displacement,'final_endpoint_distance_m':endpoint_distance,
            'max_object_lift_m':lift,'stayed_on_table':stayed_on_table,'tool_object_contact_steps':int(np.sum(contacts)),
            'tool_table_contact_steps':int(np.sum(table_contacts)),
            'push_tracking_rmse_m':float(np.sqrt(np.mean(np.sum((states[push,:3]-goals[push])**2,axis=1)))),
            'finite_state':finite, 'tracks_sha256':hashlib.sha256(args.tracks.read_bytes()).hexdigest(),
            'push_controller':args.push_controller,
            'observations':('simulator eef pose for control; cube pose/orientation for termination, logging and diagnostics; no XY steering from cube state' if args.push_controller=='finger-replay' else 'scripted teacher: simulator cube position/orientation steers XY to the recorded human object trajectory; fixed initial tool yaw; feedback gain 0.75 capped at 6 mm'),
            'limitations':['Pilot tuning result, not held-out success','Target source is recorded explicitly; independent drawn goal used when calibrated',
                          'Assumed table/object friction; marker parallax uncorrected','Scripted height, orientation, approach and withdrawal',
                          'Tool attachment differs from human fingertip; no policy trained']}
        np.savez_compressed(args.output/'rollout.npz',observations=states,actions=np.asarray(actions),
                            observations_before=np.asarray(before_states),eef_quat_site_before=np.asarray(before_quats),
                            eef_quat_site_after=np.asarray(after_quats),action_time_s=np.arange(len(states))/20,
                            cube_quat_wxyz_before=np.asarray(cube_quats_before),cube_quat_wxyz_after=np.asarray(cube_quats_after),
                            observation_time_s=(np.arange(len(states))+1)/20,
                            target_xyz=goals,phases=phases,tool_object_contact=contacts,
                            human_reference_xy=reference.get('original_reference_xy',reference['reference_xy']),
                            executed_reference_xy=(reference['reference_xy'] if args.push_controller=='finger-replay' else goals[np.isin(phases,['human_push','goal_dwell','reference_hold']),:2]),
                            executed_reference_time_s=(reference['time_s'] if args.push_controller=='finger-replay' else np.arange(push_steps)*.05),
                            nominal_finger_reference_xy=reference['reference_xy'],human_time_s=reference['time_s'],
                            human_object_reference_xy=reference['object_reference_xy'],push_controller=np.asarray(args.push_controller),
                            target_xy_m=reference['target'],object_start_xy_m=reference['object_start'],
                            robot_coordinate_frame=np.asarray(reference['paper_to_robot_frame']),
                            paper_to_robot_matrix=reference['paper_to_robot_matrix'])
        if writer is not None:
            writer.close();writer=None
            with imageio.get_reader(args.output/'replay.mp4') as reader:
                result['decoded_video_frames']=sum(1 for _ in reader)
            if result['decoded_video_frames']!=len(states):result['passed']=False
            with imageio.get_reader(args.output/'replay.mp4') as reader:
                imageio.imwrite(args.output/'preview.png',reader.get_data(int(np.flatnonzero(push)[len(np.flatnonzero(push))//2])))
        (args.output/'metrics.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2),flush=True)
        if not result['passed']:raise SystemExit('Pilot replay failed; inspect metrics and contact video')
    finally:
        if writer is not None:writer.close()
        env.close()


if __name__=='__main__':main()
