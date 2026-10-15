"""Retain requested failure videos by replaying and verifying saved policy actions."""
import argparse
import hashlib
import json
from pathlib import Path
import cv2
import imageio.v2 as imageio
import numpy as np
from robosuite.controllers import load_composite_controller_config
from humanoid_push.push_env import PlanarPush
from humanoid_push.episode_data import geometry,PHASE_NAMES


def render(root,episode,run):
    folder=run/episode['id'];video=folder/'failure.mp4'
    if video.exists():raise FileExistsError(f'Preserve existing video: {video}')
    metrics=json.loads((folder/'metrics.json').read_text())
    if metrics['passed']:raise ValueError('This renderer retains failed episodes only')
    c=json.loads((root/episode['calibration']).read_text())
    initial=json.loads((root/episode['metrics']).read_text())
    polygon,size=geometry(c)
    path=folder/'rollout.npz'
    with np.load(path,allow_pickle=False) as d:
        actions=d['actions'].copy();states=d['observations'].copy()
        before=d['observations_before'].copy();phases=d['predicted_phases'].copy()
    config=load_composite_controller_config(robot='Panda')
    config['body_parts']['right']['input_ref_frame']='world'
    env=PlanarPush(object_start=np.asarray(initial['initial_object_xyz_m'])[:2],
        target_xy=initial['target_xy_m'],object_size=size,target_polygon=polygon,
        paper_size=initial['paper_size_robot_xy_m'],robots='Panda',controller_configs=config,
        initialization_noise=None,has_renderer=False,has_offscreen_renderer=True,
        use_camera_obs=False,control_freq=20,horizon=1000,ignore_done=True,
        hard_reset=False,table_friction=(.3,.005,.0001),seed=7)
    writer=None;maximum=0.;completed=False
    try:
        obs=env.reset();writer=imageio.get_writer(video,fps=20,codec='libx264',quality=8)
        for i,action in enumerate(actions):
            observed=np.r_[obs['robot0_eef_pos'],obs['cube_pos']]
            maximum=max(maximum,float(np.max(np.abs(observed-before[i]))))
            obs,_,_,_=env.step(action)
            observed=np.r_[obs['robot0_eef_pos'],obs['cube_pos']]
            maximum=max(maximum,float(np.max(np.abs(observed-states[i]))))
            if maximum>1e-7:raise RuntimeError(f'{episode["id"]}: replay differs from recorded states by {maximum}')
            overview=env.sim.render(width=640,height=480,camera_name='pushview')[::-1]
            # Hide arm meshes only in the explanatory overhead panel.
            groups=env.sim.model.geom_group.copy()
            visibility=env.sim._render_context_offscreen.vopt.geomgroup.copy()
            try:
                for geom_id,name in enumerate(env.sim.model.geom_names):
                    if name and name.startswith(('robot0_','gripper0_')):env.sim.model.geom_group[geom_id]=5
                env.sim._render_context_offscreen.vopt.geomgroup[5]=0
                detail=env.sim.render(width=480,height=480,camera_name='robotview')[::-1]
            finally:
                env.sim.model.geom_group[:]=groups
                env.sim._render_context_offscreen.vopt.geomgroup[:]=visibility
            frame=np.ascontiguousarray(np.concatenate([overview,detail],axis=1))
            table=env.check_contact('pusher_tip','table_collision')
            cv2.rectangle(frame,(0,0),(1120,47),(20,20,20),-1)
            cv2.putText(frame,f'{episode["id"]} FAILED: {metrics["stop_reason"]} | {PHASE_NAMES[int(phases[i])]} | {(i+1)*.05:.2f}s',
                (8,19),cv2.FONT_HERSHEY_SIMPLEX,.46,(255,255,255),1)
            cv2.putText(frame,f'Tip/table contact: {"YES" if table else "no"}',(8,39),cv2.FONT_HERSHEY_SIMPLEX,.45,(0,0,255) if table else (220,220,220),1)
            cv2.putText(frame,'Robot overhead: arm hidden for inspection',(650,39),cv2.FONT_HERSHEY_SIMPLEX,.43,(220,220,220),1)
            writer.append_data(frame)
        writer.close();writer=None
        capture=cv2.VideoCapture(str(video));count=0
        while capture.read()[0]:count+=1
        capture.release()
        if count!=len(actions):raise RuntimeError('Saved video did not decode to the expected frame count')
        audit={'episode':episode['id'],'original_passed':False,'source':'saved learned-policy actions, not a new policy run',
            'original_stop_reason':metrics['stop_reason'],'frames':count,'fps':20,
            'rollout_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'max_abs_state_replay_error_m':maximum,'state_error_tolerance_m':1e-7,
            'video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),
            'original_metrics_and_score_unchanged':True,'retention':'user explicitly requested failure videos'}
        (folder/'failure_video.json').write_text(json.dumps(audit,indent=2)+'\n')
        completed=True;return audit
    finally:
        if writer is not None:writer.close()
        env.close()
        if not completed:video.unlink(missing_ok=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--manifest',type=Path,default=Path('data/manifests/public_validation_batch_01.json'))
    p.add_argument('--root',type=Path,default=Path('.'))
    a=p.parse_args();manifest=json.loads((a.root/a.manifest).read_text())
    episodes={e['id']:e for e in manifest['episodes']}
    summary=json.loads((a.run/'summary.json').read_text());audits=[]
    for result in summary['episodes']:
        if result['passed']:continue
        audit=render(a.root,episodes[result['episode']],a.run);audits.append(audit)
        print(f"{audit['episode']}: retained {audit['frames']} frames, maximum state error {audit['max_abs_state_replay_error_m']:.3g}",flush=True)
    (a.run/'failure_video_audit.json').write_text(json.dumps(audits,indent=2)+'\n')
    print(f'Retained {len(audits)} verified failure videos.',flush=True)


if __name__=='__main__':main()
