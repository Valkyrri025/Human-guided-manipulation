"""Closed-loop held-out evaluation: policy sees current state, never a future human path."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
from scipy.spatial.transform import Rotation
from .bc_data import features
from .bc_model import load_policy
from .task_rules import StopRule


def evaluate_episode(model, root, episode, output, timeout=10., render=False):
    if not np.isfinite(timeout) or timeout < .05:
        raise ValueError('Timeout must allow at least one 20 Hz control step')
    model.eval()
    from robosuite.controllers import load_composite_controller_config
    from .push_env import PlanarPush
    import imageio.v2 as imageio
    if episode['split'] not in ('validation', 'test'):
        raise ValueError('Evaluation requires held-out scenes')
    geometry_path = episode['initial_scene'] if episode['split']=='test' else episode['metrics']
    m = json.loads((root / geometry_path).read_text())
    c = json.loads((root / episode['calibration']).read_text())
    origin = np.array([c['rectangle_width_m'], c['rectangle_height_m']])/2
    matrix = np.asarray(c['paper_to_robot_matrix'])
    polygon = (np.asarray(c['goal']['corners_table_xy_m'])-origin) @ matrix.T
    start = np.asarray(m['initial_object_xyz_m'])[:2]
    goal = np.asarray(m['target_xy_m']); size = np.asarray(m['object_dimensions_m'])
    direction = goal-start; direction /= np.linalg.norm(direction)
    yaw = np.arctan2(direction[1], direction[0]) + np.deg2rad(episode.get('tool_yaw_offset_deg',0))
    orientation = Rotation.from_euler('z', yaw)*Rotation.from_matrix(np.diag([1.,-1.,-1.]))
    config = load_composite_controller_config(robot='Panda')
    config['body_parts']['right']['input_ref_frame'] = 'world'
    env = PlanarPush(object_start=start, target_xy=goal, object_size=size, target_polygon=polygon,
        paper_size=m['paper_size_robot_xy_m'], robots='Panda', controller_configs=config,
        initialization_noise=None, has_renderer=False, has_offscreen_renderer=render,
        use_camera_obs=False, control_freq=20, horizon=1000, ignore_done=True,
        hard_reset=False, table_friction=(.3,.005,.0001), seed=7)
    output.mkdir(parents=True,exist_ok=True)
    states, before, actions, phases, inputs, contacts = [], [], [], [], [], []
    writer = None
    try:
        obs = env.reset(); initial = obs['cube_pos'].copy()
        if render:
            writer = imageio.get_writer(output/'policy.mp4',fps=20,codec='libx264')
        def step(target, phase, learned=False):
            nonlocal obs
            site = Rotation.from_matrix(env.sim.data.site_xmat[env.robots[0].eef_site_id['right']].reshape(3,3))
            state = np.r_[obs['robot0_eef_pos'], obs['cube_pos']]
            x = features(state, env.sim.data.body_xquat[env.cube_body_id].copy(), site.as_quat(), goal)[0]
            action = np.zeros(env.action_dim)
            action[:3] = np.clip((target-obs['robot0_eef_pos'])/.05,-.2,.2)
            if learned:
                with torch.no_grad():
                    action[:2] = model(torch.from_numpy(x).unsqueeze(0)).numpy()[0]
            action[3:6] = np.clip((orientation*site.inv()).as_rotvec()/.5,-.3,.3)
            action[-1] = 1
            if not np.isfinite(action).all():
                raise RuntimeError('Non-finite policy action')
            before.append(state); inputs.append(x); actions.append(action.copy()); phases.append(phase)
            obs,_,_,_ = env.step(action)
            states.append(np.r_[obs['robot0_eef_pos'],obs['cube_pos']])
            contacts.append(env.check_contact('pusher_tip',env.cube.contact_geoms))
            if writer is not None:
                writer.append_data(env.sim.render(width=640,height=480,camera_name='pushview')[::-1])
        def move(target, count, phase):
            begin = obs['robot0_eef_pos'].copy()
            for alpha in np.linspace(0,1,count):
                step(begin+(target-begin)*(alpha*alpha*(3-2*alpha)),phase)
        support = np.dot(np.abs(direction),size[:2]/2)
        lower = np.r_[start-direction*(support+.004+.012),.868]
        move(lower+[0,0,.1],100,'approach'); move(lower,60,'lower')
        for _ in range(20):
            step(lower,'settle')
        pre_push = float(np.linalg.norm(obs['cube_pos'][:2]-initial[:2]))
        monitor = StopRule(timeout,.2); hold = None; reason = 'timeout'
        for i in range(round(timeout/.05)):
            target = np.r_[obs['robot0_eef_pos'][:2],.868] if hold is None else hold
            step(target,'policy_push' if hold is None else 'goal_dwell',learned=hold is None)
            inside = env._check_success()
            result = monitor.update((i+1)*.05,inside)
            hold = obs['robot0_eef_pos'].copy() if inside else None
            if result is not None:
                reason = result; break
        last = obs['robot0_eef_pos'].copy()+[0,0,.1]
        move(last,60,'withdraw')
        for _ in range(20):
            step(last,'final_settle')
        states = np.asarray(states); cube = states[:,3:]
        finite = bool(np.isfinite(states).all() and np.isfinite(env.sim.data.qpos).all())
        lift = max(0.,float(cube[:,2].max()-(.8+size[2]/2)))
        on_table = bool(np.all(cube[:,2]>.8+size[2]/2-.005) and np.all(np.abs(cube[:,:2])<.39))
        valid = finite and lift<.005 and on_table and pre_push<.002
        passed = bool(valid and reason=='goal_reached' and env._check_success())
        metrics = {'episode':episode['id'],'controller':'learned-BC-pushing; scripted approach/height/yaw/dwell/withdrawal',
            'passed':passed,'stop_reason':reason,'push_elapsed_s':(i+1)*.05,'push_timeout_s':timeout,
            'goal_dwell_s':.2,'final_target_distance_m':float(np.linalg.norm(cube[-1,:2]-goal)),
            'finite_state':finite,'max_object_lift_m':lift,'stayed_on_table':on_table,
            'displacement_at_push_start_m':pre_push,'tool_object_contact_steps':int(sum(contacts)),
            'recorded_future_path_accessed':False,'seed':7,'final_object_xyz_m':cube[-1].tolist()}
        np.savez_compressed(output/'rollout.npz',observations_before=before,observations=states,
            features_before=inputs,actions=actions,phases=phases,target_xy_m=goal)
        (output/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
        return metrics
    finally:
        if writer is not None:
            writer.close()
        env.close()
        if render and not locals().get('passed',False):
            (output/'policy.mp4').unlink(missing_ok=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--manifest',type=Path,default=Path('data/manifests/public_validation_batch_01.json'))
    p.add_argument('--output',type=Path,default=Path('outputs/bc_validation'))
    p.add_argument('--success-videos',type=int,default=3)
    p.add_argument('--split',choices=['validation','test'],default='validation')
    p.add_argument('--protocol',type=Path,help='Required frozen protocol for test evaluation')
    a = p.parse_args()
    if a.success_videos < 0:
        p.error('success-videos must be nonnegative')
    if a.output.exists() and any(a.output.iterdir()):
        p.error('Output directory is not empty; choose a new --output to preserve evaluation evidence')
    torch.set_num_threads(1)
    model, metadata = load_policy(a.checkpoint)
    if metadata.get('status') != 'trained':
        p.error('Official evaluation requires a trained checkpoint')
    episodes = json.loads((a.root/a.manifest).read_text())['episodes']
    if (len(episodes)!=9 or any(ep['split']!=a.split for ep in episodes) or
            len({ep['id'] for ep in episodes})!=9):
        p.error('Evaluate all nine distinct starts from the requested held-out split')
    if a.split=='test':
        if a.protocol is None:
            p.error('Test evaluation requires --protocol with the frozen checkpoint and code hashes')
        protocol=json.loads((a.root/a.protocol).read_text())
        if hashlib.sha256(a.checkpoint.read_bytes()).hexdigest()!=protocol['checkpoint_sha256']:
            p.error('Checkpoint differs from the frozen test protocol')
        for filename,digest in protocol['evaluation_code_sha256'].items():
            if hashlib.sha256((a.root/filename).read_bytes()).hexdigest()!=digest:
                p.error(f'Evaluation code differs from frozen protocol: {filename}')
    rows = []; retained = 0; rendered_sides = set()
    for ep in episodes:
        directory = a.output/ep['id']
        row = evaluate_episode(model,a.root,ep,directory)
        side=ep.get('recording_start_side',ep['id'])
        if row['passed'] and retained<a.success_videos and side not in rendered_sides:
            rerun = evaluate_episode(model,a.root,ep,directory,render=True)
            if rerun['passed']:
                retained += 1; rendered_sides.add(side)
            else:
                raise RuntimeError('Rendered rerun disagrees with successful numerical evaluation')
        rows.append(row)
        (a.output/'progress.json').write_text(json.dumps({'split':a.split,'completed':len(rows),'episodes':rows},indent=2)+'\n')
        print(f"{ep['id']}: {row['passed']} ({row['stop_reason']})",flush=True)
    summary = {'split':a.split,'total':len(rows),'successes':sum(r['passed'] for r in rows),
        'mean_final_target_distance_m':float(np.mean([r['final_target_distance_m'] for r in rows])),
        'checkpoint_sha256':hashlib.sha256(a.checkpoint.read_bytes()).hexdigest(),
        'checkpoint_metadata':metadata,'episodes':rows,'test_accessed':a.split=='test',
        'protocol':str(a.protocol) if a.protocol else None}
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(f"{a.split.title()}: {summary['successes']}/{summary['total']} successes")
