"""One recurrent policy jointly predicts phase and six Cartesian control actions."""
import torch
from torch import nn
from .episode_data import VERSION,ACTION_LIMITS


class EpisodePolicy(nn.Module):
    def __init__(self,mean,std):
        super().__init__()
        self.register_buffer('mean',torch.as_tensor(mean,dtype=torch.float32).clone())
        self.register_buffer('std',torch.as_tensor(std,dtype=torch.float32).clone())
        self.register_buffer('limits',torch.as_tensor(ACTION_LIMITS).clone())
        self.encoder=nn.Sequential(nn.Linear(15,64),nn.ReLU())
        self.memory=nn.GRU(64,64,batch_first=True)
        self.phase_head=nn.Linear(64,3)
        self.action_heads=nn.Linear(64,18)

    def forward(self,x,hidden=None):
        h,hidden=self.memory(self.encoder((x-self.mean)/self.std),hidden)
        logits=self.phase_head(h)
        candidates=torch.tanh(self.action_heads(h).reshape(*h.shape[:-1],3,6))*self.limits
        action=(candidates*logits.softmax(-1).unsqueeze(-1)).sum(-2)
        return action,logits,hidden


def save_policy(path,model,metadata):
    torch.save({'version':VERSION,'state_dict':model.state_dict(),'metadata':metadata},path)


def load_policy(path):
    d=torch.load(path,map_location='cpu',weights_only=True)
    if d['version']!=VERSION:raise ValueError('Not a benchmark-2 checkpoint')
    state=d['state_dict'];model=EpisodePolicy(state['mean'],state['std'])
    model.load_state_dict(state);model.eval()
    return model,d['metadata']
