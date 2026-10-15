"""Larger benchmark-2 policy, isolated from the frozen GRU64 implementation."""
import torch
from torch import nn
from .episode_data import VERSION as FEATURE_VERSION,ACTION_LIMITS

MODEL_VERSION='full-episode-residual-gru128-v1'
ARCHITECTURE='15 -> residual encoder128 -> GRU128 x2 -> residual state fusion -> deep phase3/action6 heads'


class AdvancedEpisodePolicy(nn.Module):
    def __init__(self,mean,std):
        super().__init__()
        self.register_buffer('mean',torch.as_tensor(mean,dtype=torch.float32).clone())
        self.register_buffer('std',torch.as_tensor(std,dtype=torch.float32).clone())
        self.register_buffer('limits',torch.as_tensor(ACTION_LIMITS).clone())
        self.encoder=nn.Sequential(nn.Linear(15,128),nn.LayerNorm(128),nn.SiLU())
        self.state_residual=nn.Sequential(nn.LayerNorm(128),nn.Linear(128,128),nn.SiLU(),nn.Linear(128,128))
        self.memory=nn.GRU(128,128,num_layers=2,dropout=.1,batch_first=True)
        self.context_norm=nn.LayerNorm(128)
        self.phase_head=nn.Sequential(nn.Linear(128,64),nn.SiLU(),nn.Linear(64,3))
        self.action_heads=nn.ModuleList([nn.Sequential(nn.Linear(128,64),nn.SiLU(),nn.Linear(64,6)) for _ in range(3)])

    def forward(self,x,hidden=None):
        encoded=self.encoder((x-self.mean)/self.std)
        encoded=encoded+self.state_residual(encoded)
        history,hidden=self.memory(encoded,hidden)
        context=self.context_norm(history+encoded)
        logits=self.phase_head(context)
        candidates=torch.stack([torch.tanh(head(context))*self.limits for head in self.action_heads],dim=-2)
        actions=(candidates*logits.softmax(-1).unsqueeze(-1)).sum(-2)
        return actions,logits,hidden


def save_policy(path,model,metadata):
    torch.save({'version':MODEL_VERSION,'feature_version':FEATURE_VERSION,
                'state_dict':model.state_dict(),'metadata':metadata},path)


def load_policy(path):
    d=torch.load(path,map_location='cpu',weights_only=True)
    if d.get('version')!=MODEL_VERSION or d.get('feature_version')!=FEATURE_VERSION:
        raise ValueError('Not a residual GRU128 benchmark-2 checkpoint')
    state=d['state_dict'];model=AdvancedEpisodePolicy(state['mean'],state['std'])
    model.load_state_dict(state);model.eval()
    return model,d['metadata']
