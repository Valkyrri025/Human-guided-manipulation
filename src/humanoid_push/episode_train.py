"""Joint full-episode supervised learning, with training-derived phase balancing."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
from torch.nn import functional as F
from .episode_data import VERSION,ACTION_LIMITS
from .episode_model import EpisodePolicy,save_policy


def objective(action,logits,target,phase,mask,weights):
    scale=action.new_tensor(ACTION_LIMITS)
    w=weights[phase]*mask
    action_loss=(((action-target)/scale).square().mean(-1)*w).sum()/w.sum()
    ce=F.cross_entropy(logits.reshape(-1,3),phase.reshape(-1),reduction='none').reshape_as(phase)
    phase_loss=(ce*w).sum()/w.sum()
    return action_loss+.2*phase_loss,action_loss,phase_loss


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset',type=Path,default=Path('outputs/benchmark2_dataset'))
    p.add_argument('--output',type=Path,default=Path('outputs/benchmark2_training'))
    p.add_argument('--epochs',type=int,default=200)
    p.add_argument('--seed',type=int,default=7)
    a=p.parse_args()
    if a.epochs<1:p.error('epochs must be positive')
    if a.output.exists() and any(a.output.iterdir()):p.error('Choose a fresh output folder')
    torch.set_num_threads(1);torch.manual_seed(a.seed);torch.use_deterministic_algorithms(True)
    provenance=json.loads((a.dataset/'provenance.json').read_text())
    if provenance['feature_version']!=VERSION:raise ValueError('Dataset version mismatch')
    if {r['episode'] for r in provenance['train_sources']}&{r['episode'] for r in provenance['validation_sources']}:
        raise ValueError('Source leakage')
    with np.load(a.dataset/'dataset.npz',allow_pickle=False) as d:
        data={k:torch.from_numpy(d[k].copy()) for k in d.files}
    model=EpisodePolicy(data['mean'],data['std']);optimizer=torch.optim.Adam(model.parameters(),lr=.001)
    a.output.mkdir(parents=True,exist_ok=True)
    config={'status':'trained','benchmark':2,'feature_version':VERSION,'seed':a.seed,'epochs':a.epochs,
        'architecture':'15 -> Linear64/ReLU -> GRU64 -> joint phase3 + phase-mixture action6',
        'learning_rate':.001,'batch_size_episodes':8,'phase_loss_coefficient':.2,
        'selection':'minimum phase-balanced validation action MSE + 0.2 phase cross-entropy',
        'dataset_sha256':hashlib.sha256((a.dataset/'dataset.npz').read_bytes()).hexdigest(),
        'provenance':provenance,'ground_truth_phase_at_runtime':False,'scripted_movement_at_runtime':False}
    (a.output/'configuration.json').write_text(json.dumps(config,indent=2)+'\n')
    best=float('inf');history=[]
    for epoch in range(1,a.epochs+1):
        model.train();train_total=0.
        for ids in torch.randperm(len(data['train_x'])).split(8):
            action,logits,_=model(data['train_x'][ids])
            loss,_,_=objective(action,logits,data['train_y'][ids],data['train_phase'][ids],data['train_mask'][ids],data['phase_weights'])
            if not torch.isfinite(loss):raise RuntimeError('Non-finite training loss')
            optimizer.zero_grad();loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.,error_if_nonfinite=True)
            optimizer.step();train_total+=float(loss.detach())*len(ids)
        model.eval()
        with torch.no_grad():
            act,logits,_=model(data['validation_x'])
            val,action_loss,phase_loss=objective(act,logits,data['validation_y'],data['validation_phase'],data['validation_mask'],data['phase_weights'])
            correct=logits.argmax(-1)==data['validation_phase'];mask=data['validation_mask']
            accuracy=float(correct[mask].float().mean())
            per_phase=[float(correct[mask&(data['validation_phase']==i)].float().mean()) for i in range(3)]
        if not torch.isfinite(val):raise RuntimeError('Non-finite validation loss')
        row={'epoch':epoch,'train_joint_loss':train_total/len(data['train_x']),
            'validation_joint_loss':float(val),'validation_action_mse':float(action_loss),
            'validation_phase_ce':float(phase_loss),'validation_phase_accuracy':accuracy,
            'validation_phase_accuracy_by_phase':per_phase}
        history.append(row)
        if float(val)<best:
            best=float(val);save_policy(a.output/'best.pt',model,{**config,**row})
        (a.output/'history.json').write_text(json.dumps(history,indent=2)+'\n')
        if epoch==1 or epoch%10==0:print(json.dumps(row),flush=True)
    save_policy(a.output/'last.pt',model,{**config,**history[-1]})
    print('Training complete. best.pt selected by supervised validation loss; closed-loop success is not yet measured.',flush=True)


if __name__=='__main__':main()
