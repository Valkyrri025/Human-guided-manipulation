"""Explicit supervised training command; validation never supplies gradients."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
from .bc_model import PushPolicy, save_policy
from .bc_data import FEATURE_VERSION


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset', type=Path, default=Path('outputs/bc_dataset'))
    p.add_argument('--output', type=Path, default=Path('outputs/bc_training'))
    p.add_argument('--epochs', type=int, default=200)
    p.add_argument('--seed', type=int, default=7)
    a = p.parse_args()
    if a.epochs < 1:
        p.error('epochs must be positive')
    if a.output.exists() and any(a.output.iterdir()):
        p.error('Output directory is not empty; choose a new --output to preserve checkpoints')
    torch.set_num_threads(1); torch.manual_seed(a.seed)
    with np.load(a.dataset / 'dataset.npz', allow_pickle=False) as d:
        if set(d['train_episode']) & set(d['validation_episode']):
            raise ValueError('Source split leakage')
        tx, ty, vx, vy = [torch.from_numpy(d[k].copy()) for k in ('train_x','train_y','validation_x','validation_y')]
        model = PushPolicy(d['mean'], d['std'])
    provenance = json.loads((a.dataset/'provenance.json').read_text())
    if provenance['feature_version'] != FEATURE_VERSION:
        raise ValueError('Dataset feature contract mismatch; prepare again')
    optimizer = torch.optim.Adam(model.parameters(), lr=.001)
    a.output.mkdir(parents=True, exist_ok=True)
    best = float('inf'); history = []
    metadata = {'seed': a.seed, 'architecture': [8,64,64,2], 'batch_size':128,
        'learning_rate':.001, 'selection':'lowest validation action MSE; assess task success separately',
        'dataset_sha256':hashlib.sha256((a.dataset/'dataset.npz').read_bytes()).hexdigest(),
        'provenance':provenance, 'status':'trained'}
    for epoch in range(1, a.epochs + 1):
        model.train(); total = 0.
        for indices in torch.randperm(len(tx)).split(128):
            loss = ((model(tx[indices]) - ty[indices]) / .2).square().mean()
            if not torch.isfinite(loss):
                raise RuntimeError('Non-finite loss; training stopped without replacing best checkpoint')
            optimizer.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1., error_if_nonfinite=True)
            optimizer.step(); total += loss.item()*len(indices)
        model.eval()
        with torch.no_grad():
            validation = ((model(vx)-vy)/.2).square().mean().item()
        if not np.isfinite(validation):
            raise RuntimeError('Non-finite validation loss')
        row = {'epoch':epoch,'train_normalized_mse':total/len(tx),'validation_normalized_mse':validation}
        history.append(row)
        if validation < best:
            best = validation
            save_policy(a.output/'best.pt', model, {**metadata, **row})
        (a.output/'history.json').write_text(json.dumps(history, indent=2)+'\n')
        if epoch == 1 or epoch % 10 == 0:
            print(row, flush=True)
    save_policy(a.output/'last.pt', model, {**metadata, **history[-1]})
    print('Saved best.pt by validation loss. Run push-bc-evaluate to measure closed-loop success.')
