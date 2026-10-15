"""Evaluate residual GRU128 using exactly the existing benchmark-2 task loop."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
from .advanced_model import load_policy
from .episode_eval import evaluate_episode


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--manifest',type=Path,default=Path('data/manifests/public_validation_batch_01.json'))
    p.add_argument('--output',type=Path,default=Path('outputs/benchmark2_validation_advanced'))
    p.add_argument('--success-videos',type=int,default=3)
    a=p.parse_args()
    if a.output.exists() and any(a.output.iterdir()):p.error('Choose a fresh output folder')
    if a.success_videos<0:p.error('success-videos must be nonnegative')
    torch.set_num_threads(1);model,metadata=load_policy(a.checkpoint)
    if metadata.get('status')!='trained':p.error('Evaluation requires a trained checkpoint')
    episodes=json.loads((a.root/a.manifest).read_text())['episodes']
    if len(episodes)!=9 or len({e['id'] for e in episodes})!=9 or any(e['split']!='validation' for e in episodes):
        p.error('All nine distinct validation episodes required; no test evaluation during development')
    rows=[];sides=set()
    for ep in episodes:
        directory=a.output/ep['id'];result=evaluate_episode(model,a.root,ep,directory)
        side=ep['recording_start_side']
        if result['passed'] and side not in sides and len(sides)<a.success_videos:
            repeat=evaluate_episode(model,a.root,ep,directory,render=True)
            if not repeat['passed']:raise RuntimeError('Rendered replay disagreed with numerical success')
            sides.add(side)
        rows.append(result)
        (a.output/'progress.json').write_text(json.dumps(rows,indent=2)+'\n')
        print(f"{ep['id']}: {result['passed']} ({result['stop_reason']})",flush=True)
    summary={'benchmark':2,'architecture':metadata['architecture'],'split':'validation',
        'successes':sum(r['passed'] for r in rows),'total':len(rows),
        'mean_final_target_distance_m':float(np.mean([r['final_target_distance_m'] for r in rows])),
        'checkpoint_sha256':hashlib.sha256(a.checkpoint.read_bytes()).hexdigest(),
        'checkpoint_metadata':metadata,'episodes':rows,'test_used':False,
        'evaluation_loop':'unchanged humanoid_push.episode_eval.evaluate_episode'}
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(f"Advanced model validation: {summary['successes']}/9",flush=True)


if __name__=='__main__':main()
