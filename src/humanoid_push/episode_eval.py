"""Benchmark 2 held-out evaluation: learned actions from reset through withdrawal."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
from scipy.spatial.transform import Rotation
from .episode_data import features,geometry,PHASE_NAMES
from .episode_model import load_policy

EPISODE_TIMEOUT_S=30.
PUSH_TIMEOUT_S=10.
WITHDRAWAL_HEIGHT_M=.948
DWELL_S=.2


def load_scene(root,episode,expected_split='validation'):
    if expected_split not in ('validation','test') or episode['split']!=expected_split:
        raise ValueError('Episode does not belong to the explicitly requested held-out split')
    c=json.loads((root/episode['calibration']).read_text())
    scene_key='initial_scene' if expected_split=='test' else 'metrics'
    m=json.loads((root/episode[scene_key]).read_text())
    if expected_split=='test' and m.get('opening_frames_used')!=30:
        raise ValueError('Test requires frozen opening-only initial scenes')
    return c,m


def evaluate_episode(model,root,episode,output,render=False,episode_timeout=EPISODE_TIMEOUT_S,expected_split='validation'):
    from robosuite.controllers import load_composite_controller_config
    from .push_env import PlanarPush
    import imageio.v2 as imageio
    c,m=load_scene(root,episode,expected_split)
    polygon,size=geometry(c);goal=np.asarray(m['target_xy_m']);start=np.asarray(m['initial_object_xyz_m'])[:2]
    config=load_composite_controller_config(robot='Panda')
    config['body_parts']['right']['input_ref_frame']='world'
    env=PlanarPush(object_start=start,target_xy=goal,object_size=size,target_polygon=polygon,
        paper_size=m['paper_size_robot_xy_m'],robots='Panda',controller_configs=config,
        initialization_noise=None,has_renderer=False,has_offscreen_renderer=render,
        use_camera_obs=False,control_freq=20,horizon=1000,ignore_done=True,
        hard_reset=False,table_friction=(.3,.005,.0001),seed=7)
    output.mkdir(parents=True,exist_ok=True)
    model.eval();hidden=None;writer=None;states=[];before=[];inputs=[];actions=[];phases=[];probabilities=[]
    contacts=[];table_contacts=[];cube_quats=[];site_quats=[]
    push_start=None;push_elapsed=0.;goal_since=None;goal_achieved=False;withdraw_since=None
    pre_push=None;reason='episode_timeout';passed=False
    try:
        obs=env.reset();initial=obs['cube_pos'].copy()
        if render:writer=imageio.get_writer(output/'policy.mp4',fps=20,codec='libx264')
        for step in range(round(episode_timeout/.05)):
            time=(step+1)*.05
            state=np.r_[obs['robot0_eef_pos'],obs['cube_pos']]
            site=Rotation.from_matrix(env.sim.data.site_xmat[env.robots[0].eef_site_id['right']].reshape(3,3)).as_quat()
            cube_q=env.sim.data.body_xquat[env.cube_body_id].copy()
            x=features(state,cube_q,site,goal,polygon,size)[0]
            with torch.no_grad():
                prediction,logits,hidden=model(torch.from_numpy(x).view(1,1,-1),hidden)
            action=np.r_[prediction[0,0].numpy(),1.]
            phase=int(logits[0,0].argmax())
            if not np.isfinite(action).all():
                reason='non_finite_action';break
            if phase==1 and push_start is None:
                push_start=time-.05;pre_push=float(np.linalg.norm(obs['cube_pos'][:2]-initial[:2]))
            before.append(state);inputs.append(x);actions.append(action);phases.append(phase)
            probabilities.append(logits[0,0].softmax(-1).numpy());cube_quats.append(cube_q);site_quats.append(site)
            obs,_,_,_=env.step(action)
            states.append(np.r_[obs['robot0_eef_pos'],obs['cube_pos']])
            contact=env.check_contact('pusher_tip',env.cube.contact_geoms)
            contacts.append(contact);table_contacts.append(env.check_contact('pusher_tip','table_collision'))
            if writer is not None:
                frame=env.sim.render(width=640,height=480,camera_name='pushview')[::-1]
                writer.append_data(np.ascontiguousarray(frame))
            if not np.isfinite(states[-1]).all() or not np.isfinite(env.sim.data.qpos).all():
                reason='non_finite_state';break
            inside=env._check_success()
            goal_since=(time if goal_since is None else goal_since) if inside else None
            if goal_since is not None and time-goal_since>=DWELL_S-1e-9:goal_achieved=True
            if push_start is not None and not goal_achieved:push_elapsed+=.05
            clear=phase==2 and goal_achieved and inside and obs['robot0_eef_pos'][2]>=WITHDRAWAL_HEIGHT_M and not contact
            withdraw_since=(time if withdraw_since is None else withdraw_since) if clear else None
            if withdraw_since is not None and time-withdraw_since>=DWELL_S-1e-9:
                reason='completed';break
            if push_elapsed>=PUSH_TIMEOUT_S-1e-9:
                reason='push_timeout';break
        if not states:raise RuntimeError('No finite simulator steps completed')
        states=np.asarray(states);cube=states[:,3:]
        finite=bool(np.isfinite(states).all() and np.isfinite(env.sim.data.qpos).all())
        lift=max(0.,float(cube[:,2].max()-(.8+size[2]/2)))
        on_table=bool(np.all(cube[:,2]>.8+size[2]/2-.005) and np.all(np.abs(cube[:,:2])<.39))
        valid=finite and lift<.005 and on_table and pre_push is not None and pre_push<.002 and not any(table_contacts)
        passed=bool(reason=='completed' and valid and env._check_success())
        result={'episode':episode['id'],'benchmark':2,'passed':passed,'stop_reason':reason,
            'episode_elapsed_s':len(states)*.05,'push_elapsed_s':push_elapsed,
            'push_started_s':push_start,'episode_timeout_s':episode_timeout,'push_timeout_s':PUSH_TIMEOUT_S,
            'goal_dwell_achieved':goal_achieved,'withdrawal_height_threshold_m':WITHDRAWAL_HEIGHT_M,
            'final_eef_height_m':float(states[-1,2]),'final_target_distance_m':float(np.linalg.norm(cube[-1,:2]-goal)),
            'final_cube_inside_goal':bool(env._check_success()),'finite_state':finite,
            'max_object_lift_m':lift,'stayed_on_table':on_table,'displacement_before_predicted_push_m':pre_push,
            'tool_object_contact_steps':int(sum(contacts)),'tool_table_contact_steps':int(sum(table_contacts)),
            'predicted_phase_steps':np.bincount(phases,minlength=3).tolist(),
            'phase_transitions':[[i*.05,PHASE_NAMES[p]] for i,p in enumerate(phases) if i==0 or p!=phases[i-1]],
            'scripted_movement':False,'ground_truth_phase_supplied':False,'recorded_future_path_accessed':False,
            'gripper':'fixed closed','seed':7,'initial_robot_pose':'same deterministic Panda reset as benchmark 1'}
        np.savez_compressed(output/'rollout.npz',observations_before=before,observations=states,features_before=inputs,
            actions=actions,predicted_phases=phases,phase_probabilities=probabilities,
            cube_quat_wxyz_before=cube_quats,eef_quat_site_before=site_quats,target_xy_m=goal,
            tool_object_contact=contacts,tool_table_contact=table_contacts)
        (output/'metrics.json').write_text(json.dumps(result,indent=2)+'\n')
        return result
    finally:
        if writer is not None:writer.close()
        env.close()
        if render and not passed:(output/'policy.mp4').unlink(missing_ok=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--manifest',type=Path,default=Path('data/manifests/public_validation_batch_01.json'))
    p.add_argument('--output',type=Path,default=Path('outputs/benchmark2_validation'))
    p.add_argument('--success-videos',type=int,default=3)
    p.add_argument('--split',choices=['validation','test'],default='validation')
    p.add_argument('--protocol',type=Path,help='Required frozen checkpoint, evaluator and scene hashes for test evaluation')
    a=p.parse_args()
    if a.output.exists() and any(a.output.iterdir()):p.error('Choose a fresh output folder')
    if a.success_videos<0:p.error('success-videos must be nonnegative')
    torch.set_num_threads(1);model,metadata=load_policy(a.checkpoint)
    episodes=json.loads((a.root/a.manifest).read_text())['episodes']
    if len(episodes)!=9 or len({e['id'] for e in episodes})!=9 or any(e['split']!=a.split for e in episodes):
        p.error('All nine distinct starts from the explicitly requested held-out split are required')
    if a.split=='test':
        if a.protocol is None:p.error('Test evaluation requires --protocol frozen before the run')
        protocol=json.loads((a.root/a.protocol).read_text())
        if protocol.get('benchmark')!=2 or protocol.get('split')!='test':p.error('Wrong frozen test protocol')
        if hashlib.sha256(a.checkpoint.read_bytes()).hexdigest()!=protocol['checkpoint_sha256']:
            p.error('Checkpoint differs from frozen protocol')
        required={str(a.manifest),'src/humanoid_push/episode_eval.py','src/humanoid_push/episode_data.py',
                  'src/humanoid_push/episode_model.py','src/humanoid_push/push_env.py','src/humanoid_push/task_rules.py'}
        required.update(e[k] for e in episodes for k in ['calibration','initial_scene'])
        if not required<=set(protocol['input_sha256']):p.error('Incomplete evaluator/scene hashes in protocol')
        for path,digest in protocol['input_sha256'].items():
            if hashlib.sha256((a.root/path).read_bytes()).hexdigest()!=digest:p.error(f'Frozen input changed: {path}')
    rows=[];sides=set()
    for ep in episodes:
        directory=a.output/ep['id'];r=evaluate_episode(model,a.root,ep,directory,expected_split=a.split)
        side=ep['recording_start_side']
        if r['passed'] and side not in sides and len(sides)<a.success_videos:
            repeat=evaluate_episode(model,a.root,ep,directory,render=True,expected_split=a.split)
            if not repeat['passed']:raise RuntimeError('Rendered replay disagreed with successful numerical evaluation')
            sides.add(side)
        rows.append(r)
        (a.output/'progress.json').write_text(json.dumps(rows,indent=2)+'\n')
        print(f"{ep['id']}: {r['passed']} ({r['stop_reason']}, {r['episode_elapsed_s']:.2f}s)",flush=True)
    summary={'benchmark':2,'split':a.split,'successes':sum(r['passed'] for r in rows),'total':len(rows),
        'mean_final_target_distance_m':float(np.mean([r['final_target_distance_m'] for r in rows])),
        'checkpoint_sha256':hashlib.sha256(a.checkpoint.read_bytes()).hexdigest(),
        'checkpoint_metadata':metadata,'episodes':rows,'test_used':a.split=='test',
        'frozen_protocol':str(a.protocol) if a.protocol else None,
        'comparison_note':'Benchmark 2 requires learned approach, orientation, height, phase and withdrawal; benchmark 1 scripts these.'}
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(f"Benchmark 2 {a.split}: {summary['successes']}/9",flush=True)


if __name__=='__main__':main()
