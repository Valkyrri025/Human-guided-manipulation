"""Small bounded pushing policy. Input normalization travels with checkpoint."""
import torch
from torch import nn
from .bc_data import FEATURE_VERSION


class PushPolicy(nn.Module):
    def __init__(self, mean, std):
        super().__init__()
        self.register_buffer('mean', torch.as_tensor(mean, dtype=torch.float32).clone())
        self.register_buffer('std', torch.as_tensor(std, dtype=torch.float32).clone())
        self.net = nn.Sequential(nn.Linear(8, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU(), nn.Linear(64, 2))

    def forward(self, x):
        return .2 * torch.tanh(self.net((x - self.mean) / self.std))


def save_policy(path, model, metadata):
    torch.save({'feature_version': FEATURE_VERSION, 'state_dict': model.state_dict(), 'metadata': metadata}, path)


def load_policy(path):
    checkpoint = torch.load(path, map_location='cpu', weights_only=True)
    if checkpoint['feature_version'] != FEATURE_VERSION:
        raise ValueError('Checkpoint feature contract mismatch')
    state = checkpoint['state_dict']
    model = PushPolicy(state['mean'], state['std'])
    model.load_state_dict(state); model.eval()
    return model, checkpoint['metadata']
