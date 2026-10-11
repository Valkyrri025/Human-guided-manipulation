"""Causal state/action pairs, separated by source episode and split."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

FEATURE_VERSION = 'relative-planar-v1'
PHASES = ('human_push', 'goal_dwell', 'reference_hold')
FEATURE_NAMES = ['eef_minus_cube_x', 'eef_minus_cube_y', 'goal_minus_cube_x',
                 'goal_minus_cube_y', 'cube_yaw_sin', 'cube_yaw_cos', 'eef_yaw_sin', 'eef_yaw_cos']


def features(states, cube_wxyz, eef_xyzw, goal):
    states = np.atleast_2d(states)
    cube = np.atleast_2d(cube_wxyz)
    eef = np.atleast_2d(eef_xyzw)
    headings = []
    for q in (cube[:, [1, 2, 3, 0]], eef):
        r = Rotation.from_quat(q).as_matrix()
        yaw = np.arctan2(r[:, 1, 0], r[:, 0, 0])
        headings.extend([np.sin(yaw), np.cos(yaw)])
    x = np.column_stack([states[:, :2] - states[:, 3:5],
                         np.asarray(goal) - states[:, 3:5], *headings]).astype(np.float32)
    if not np.isfinite(x).all():
        raise ValueError('Non-finite policy inputs')
    return x


def load_split(root, index_path, split):
    if split not in ('train', 'validation'):
        raise ValueError('Test data are reserved for frozen final evaluation')
    index = json.loads((root / index_path).read_text())
    rows, labels, ids, steps, sources = [], [], [], [], []
    seen = set()
    for ep in index['episodes']:
        if ep['split'] != split or ep['episode'] in seen:
            raise ValueError('Wrong split or duplicate episode')
        seen.add(ep['episode'])
        eligible = ep.get('expert_eligible') if split == 'train' else ep.get('validation_reference_eligible')
        if not eligible:
            continue
        metrics = json.loads((root / ep['metrics']).read_text())
        if not metrics['passed']:
            raise ValueError('Failed replay marked eligible')
        path = root / ep['robot_rollout']
        with np.load(path, allow_pickle=False) as d:
            if str(d['push_controller'].item()) != 'human-object-feedback':
                raise ValueError('Expected recorded-object feedback teacher')
            mask = np.isin(d['phases'], PHASES)
            x = features(d['observations_before'], d['cube_quat_wxyz_before'],
                         d['eef_quat_site_before'], d['target_xy_m'])[mask]
            y = d['actions'][mask, :2].astype(np.float32)
            if not len(x) or not np.isfinite(y).all() or np.max(np.abs(y)) > .20001:
                raise ValueError('Invalid pushing action labels')
            rows.append(x); labels.append(y)
            ids.extend([ep['episode']] * len(x)); steps.extend(np.flatnonzero(mask).tolist())
        sources.append({'episode': ep['episode'], 'samples': len(x), 'rollout': ep['robot_rollout'],
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    if not rows:
        raise ValueError('No eligible data')
    return np.concatenate(rows), np.concatenate(labels), np.asarray(ids), np.asarray(steps), sources


def prepare(root, output):
    train = load_split(root, Path('data/manifests/training_rollout_index.json'), 'train')
    val = load_split(root, Path('data/manifests/validation_rollout_index.json'), 'validation')
    if (set(train[2]) & set(val[2]) or
            {s['sha256'] for s in train[4]} & {s['sha256'] for s in val[4]}):
        raise ValueError('Source episode leakage')
    mean = np.zeros(8, np.float32); std = np.ones(8, np.float32)
    mean[:4] = train[0][:, :4].mean(0)
    std[:4] = np.maximum(train[0][:, :4].std(0), 1e-4)
    output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output / 'dataset.npz', train_x=train[0], train_y=train[1],
        train_episode=train[2], train_step=train[3], validation_x=val[0], validation_y=val[1],
        validation_episode=val[2], validation_step=val[3], mean=mean, std=std)
    report = {'status': 'prepared; no policy trained', 'feature_version': FEATURE_VERSION,
        'features': FEATURE_NAMES, 'phases': PHASES, 'labels': 'normalized world-frame OSC X/Y actions, bounded +/-0.2',
        'normalization': 'first four position features, statistics from training only',
        'train_samples': len(train[0]), 'validation_samples': len(val[0]),
        'train_sources': train[4], 'validation_sources': val[4],
        'test_accessed': False, 'architecture': [8, 64, 64, 2]}
    (output / 'provenance.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path('.'))
    p.add_argument('--output', type=Path, default=Path('outputs/bc_dataset'))
    a = p.parse_args(); r = prepare(a.root, a.output)
    print(f"Prepared {r['train_samples']} training / {r['validation_samples']} validation pairs; no training run.")
