"""Train the residual GRU128 policy; user-started capacity comparison."""
import argparse
import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG",":4096:8")
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
from .episode_data import VERSION
from .advanced_model import AdvancedEpisodePolicy,save_policy,ARCHITECTURE,MODEL_VERSION
from .episode_train import objective



def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset',type=Path,default=Path('outputs/benchmark2_dataset'))
    p.add_argument('--output',type=Path,default=Path('outputs/benchmark2_training_advanced'))
    p.add_argument('--epochs',type=int,default=2000)
    p.add_argument('--seed',type=int,default=7)
    p.add_argument('--device',choices=['auto','cpu','cuda'],default='auto')
    p.add_argument('--save-every',type=int,default=100,help='Retain periodic checkpoints for later closed-loop selection; 0 disables')
    a=p.parse_args()
    if a.epochs<1:p.error('epochs must be positive')
    if a.save_every<0:p.error('save-every must be nonnegative')
    if a.output.exists() and any(a.output.iterdir()):p.error('Choose a fresh output folder')
    device=torch.device('cuda' if (a.device=='cuda' or a.device=='auto' and torch.cuda.is_available()) else 'cpu')
    if device.type=='cuda' and not torch.cuda.is_available():
        p.error('CUDA requested but unavailable. Activate .venv-gpu; the original .venv has CPU-only PyTorch.')
    torch.set_num_threads(1);torch.manual_seed(a.seed);torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark=False
    torch.backends.cudnn.deterministic=True
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    provenance=json.loads((a.dataset/'provenance.json').read_text())
    if provenance['feature_version']!=VERSION:raise ValueError('Dataset version mismatch')
    if {r['episode'] for r in provenance['train_sources']}&{r['episode'] for r in provenance['validation_sources']}:
        raise ValueError('Source leakage')
    with np.load(a.dataset/'dataset.npz',allow_pickle=False) as d:
        data={k:torch.from_numpy(d[k].copy()).to(device) for k in d.files}
    model=AdvancedEpisodePolicy(data['mean'],data['std']).to(device);optimizer=torch.optim.Adam(model.parameters(),lr=.001)
    a.output.mkdir(parents=True,exist_ok=True)
    config={'status':'trained','benchmark':2,'feature_version':VERSION,'seed':a.seed,'epochs':a.epochs,
        'architecture':ARCHITECTURE,'model_version':MODEL_VERSION,
        'parameters':sum(p.numel() for p in model.parameters()),'recurrent_layers':2,
        'device':str(device),'torch_version':str(torch.__version__),'cuda_runtime':torch.version.cuda,
        'gpu_name':torch.cuda.get_device_name(0) if device.type=='cuda' else None,
        'hidden_size':128,'inter_layer_dropout':.1,
        'learning_rate':.001,'batch_size_episodes':8,'phase_loss_coefficient':.2,
        'selection':'minimum phase-balanced validation action MSE + 0.2 phase cross-entropy',
        'save_every_epochs':a.save_every,
        'dataset_sha256':hashlib.sha256((a.dataset/'dataset.npz').read_bytes()).hexdigest(),
        'provenance':provenance,'ground_truth_phase_at_runtime':False,'scripted_movement_at_runtime':False}
    (a.output/'configuration.json').write_text(json.dumps(config,indent=2)+'\n')
    print(json.dumps({'model':ARCHITECTURE,'parameters':config['parameters'],'epochs':a.epochs,'device':str(device),'gpu':config['gpu_name']}),flush=True)
    best=float('inf');history=[]
    for epoch in range(1,a.epochs+1):
        model.train();train_total=0.
        for ids in torch.randperm(len(data['train_x']),device=device).split(8):
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
        if a.save_every and epoch%a.save_every==0:
            save_policy(a.output/f'epoch_{epoch:04d}.pt',model,{**config,**row})
        (a.output/'history.json').write_text(json.dumps(history,indent=2)+'\n')
        if epoch==1 or epoch%10==0:print(json.dumps(row),flush=True)
    save_policy(a.output/'last.pt',model,{**config,**history[-1]})
    print('Training complete. best.pt selected by supervised validation loss; closed-loop success is not yet measured.',flush=True)


if __name__=='__main__':main()
