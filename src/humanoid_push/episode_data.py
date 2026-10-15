"""Benchmark 2: full episodes with phase targets, never ground-truth phase inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from .task_rules import box_inside_polygon

VERSION = 'full-episode-gru-v1'
PHASE_NAMES = ('approach', 'push', 'withdraw')
PHASE_MAP = {'approach':0, 'lower':0, 'settle':0, 'human_push':1,
             'goal_dwell':1, 'reference_hold':1, 'withdraw':2, 'final_settle':2}
FEATURE_NAMES = ['eef_minus_cube_x','eef_minus_cube_y','goal_minus_cube_x','goal_minus_cube_y',
    'eef_height_above_table','cube_height_above_table','cube_yaw_sin','cube_yaw_cos',
    *[f'eef_rotation_column_{col}_{row}' for col in range(2) for row in range(3)],'cube_inside_goal']
ACTION_LIMITS = np.array([.2,.2,.2,.3,.3,.3],np.float32)


def geometry(calibration):
    c=calibration
    origin=np.array([c['rectangle_width_m'],c['rectangle_height_m']])/2
    matrix=np.asarray(c['paper_to_robot_matrix'])
    polygon=(np.asarray(c['goal']['corners_table_xy_m'])-origin)@matrix.T
    return polygon,np.asarray(c['object_dimensions_m'])


def features(states,cube_wxyz,eef_xyzw,goal,polygon,size):
    states=np.atleast_2d(states)
    cube=np.atleast_2d(cube_wxyz)
    eef=np.atleast_2d(eef_xyzw)
    cr=Rotation.from_quat(cube[:,[1,2,3,0]]).as_matrix()
    er=Rotation.from_quat(eef).as_matrix()
    yaw=np.arctan2(cr[:,1,0],cr[:,0,0])
    inside=[box_inside_polygon(s[3:],r,size,polygon) for s,r in zip(states,cr)]
    x=np.column_stack([states[:,:2]-states[:,3:5],np.asarray(goal)-states[:,3:5],
        states[:,2]-.8,states[:,5]-.8,np.sin(yaw),np.cos(yaw),er[:,:,0],er[:,:,1],inside]).astype(np.float32)
    if x.shape[1]!=15 or not np.isfinite(x).all():
        raise ValueError('Invalid full-episode features')
    return x


def load_split(root,split):
    if split not in ('train','validation'):
        raise ValueError('Only training and validation may supply learning data')
    filename='training_rollout_index.json' if split=='train' else 'validation_rollout_index.json'
    index=json.loads((root/'data/manifests'/filename).read_text())
    episodes=[];sources=[];seen=set()
    for ep in index['episodes']:
        if ep['split']!=split or ep['episode'] in seen:
            raise ValueError('Split mismatch or duplicate source')
        seen.add(ep['episode'])
        eligible=ep.get('expert_eligible') if split=='train' else ep.get('validation_reference_eligible')
        if not eligible:continue
        m=json.loads((root/ep['metrics']).read_text())
        if not m['passed']:raise ValueError('Failed teacher is not an expert')
        path=root/ep['robot_rollout']
        c=json.loads((root/'data/calibration'/f"{ep['episode']}.json").read_text())
        polygon,size=geometry(c)
        with np.load(path,allow_pickle=False) as d:
            if str(d['push_controller'].item())!='human-object-feedback':
                raise ValueError('Unexpected teacher')
            x=features(d['observations_before'],d['cube_quat_wxyz_before'],
                       d['eef_quat_site_before'],d['target_xy_m'],polygon,size)
            y=d['actions'][:,:6].astype(np.float32)
            labels=np.array([PHASE_MAP[str(p)] for p in d['phases']],np.int64)
            if set(labels)!={0,1,2} or not np.all(np.diff(labels)>=0):
                raise ValueError('Teacher must have all three ordered phases')
            if not np.isfinite(y).all() or np.any(np.abs(y)>ACTION_LIMITS+1e-5):
                raise ValueError('Invalid controller labels')
        episodes.append((x,y,labels))
        sources.append({'episode':ep['episode'],'frames':len(x),'rollout':ep['robot_rollout'],
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'phase_frames':np.bincount(labels,minlength=3).tolist()})
    if not episodes:raise ValueError('No eligible full episodes')
    return episodes,sources


def pad(episodes):
    length=max(len(x) for x,_,_ in episodes);n=len(episodes)
    x=np.zeros((n,length,15),np.float32);y=np.zeros((n,length,6),np.float32)
    phase=np.zeros((n,length),np.int64);mask=np.zeros((n,length),bool)
    for i,(xx,yy,pp) in enumerate(episodes):
        k=len(xx);x[i,:k]=xx;y[i,:k]=yy;phase[i,:k]=pp;mask[i,:k]=True
    return x,y,phase,mask


def prepare(root,output):
    if output.exists() and any(output.iterdir()):raise ValueError('Choose a fresh dataset output folder')
    tr,ts=load_split(root,'train');va,vs=load_split(root,'validation')
    if ({r['episode'] for r in ts}&{r['episode'] for r in vs} or
        {r['sha256'] for r in ts}&{r['sha256'] for r in vs}):raise ValueError('Source leakage')
    all_x=np.concatenate([r[0] for r in tr]);mean=np.zeros(15,np.float32);std=np.ones(15,np.float32)
    mean[:6]=all_x[:,:6].mean(0);std[:6]=np.maximum(all_x[:,:6].std(0),1e-4)
    counts=sum((np.array(r['phase_frames']) for r in ts),np.zeros(3,int))
    weights=(counts.sum()/(3*counts)).astype(np.float32)
    arrays={}
    for split,eps in [('train',tr),('validation',va)]:
        for name,arr in zip(('x','y','phase','mask'),pad(eps)):arrays[f'{split}_{name}']=arr
    output.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(output/'dataset.npz',**arrays,mean=mean,std=std,phase_weights=weights)
    report={'feature_version':VERSION,'feature_names':FEATURE_NAMES,'phases':PHASE_NAMES,
        'phase_mapping':PHASE_MAP,'action_outputs':'world-frame OSC XYZ and rotation-vector commands; gripper fixed closed',
        'phase_input':False,'memory':'GRU hidden state, reset for each episode; no teacher-forced phase input',
        'train_sources':ts,'validation_sources':vs,'train_frames':int(counts.sum()),
        'validation_frames':sum(r['frames'] for r in vs),'train_phase_frames':counts.tolist(),
        'phase_weights_train_only':weights.tolist(),'test_used_for_learning':False,
        'source_provenance':'human-derived pushing; scripted teacher approach/lower/settle/withdrawal',
        'normalization':'first six position/height features, training statistics only',
        'initial_pose_coverage':'one fixed robot reset pose; no claim of arbitrary initial joint configurations'}
    (output/'provenance.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--output',type=Path,default=Path('outputs/benchmark2_dataset'))
    a=p.parse_args();r=prepare(a.root,a.output)
    print(json.dumps({k:r[k] for k in ['train_frames','validation_frames','train_phase_frames']},indent=2))


if __name__=='__main__':main()
