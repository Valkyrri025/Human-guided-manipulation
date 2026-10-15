import numpy as np
import pytest
torch=pytest.importorskip('torch')
from humanoid_push.advanced_model import AdvancedEpisodePolicy,save_policy,load_policy
from humanoid_push.episode_train import objective
from humanoid_push.episode_model import load_policy as load_baseline


def test_advanced_streaming_matches_sequence_and_stays_causal():
    torch.manual_seed(7);torch.set_num_threads(1)
    model=AdvancedEpisodePolicy(np.zeros(15),np.ones(15)).eval()
    x=torch.randn(2,10,15)
    with torch.no_grad():
        full,phase,_=model(x)
        hidden=None;actions=[];phases=[]
        for i in range(10):
            a,p,hidden=model(x[:,i:i+1],hidden);actions.append(a);phases.append(p)
        changed=x.clone();changed[:,6:]+=20
        altered=model(changed)[0]
    assert hidden.shape==(2,2,128)
    torch.testing.assert_close(full,torch.cat(actions,1),atol=1e-6,rtol=1e-5)
    torch.testing.assert_close(phase,torch.cat(phases,1),atol=1e-6,rtol=1e-5)
    torch.testing.assert_close(full[:,:6],altered[:,:6])
    assert torch.all(full.abs()<=model.limits+1e-6)


def test_advanced_joint_gradient_and_checkpoint_contract(tmp_path):
    torch.manual_seed(7)
    model=AdvancedEpisodePolicy(np.zeros(15),np.ones(15))
    x=torch.randn(2,8,15);target=torch.zeros(2,8,6)
    phase=torch.tensor([[0,0,0,1,1,1,2,2]]*2);mask=torch.ones(2,8,dtype=torch.bool)
    a,p,_=model(x);loss,*_=objective(a,p,target,phase,mask,torch.ones(3));loss.backward()
    assert all(v.grad is not None and torch.isfinite(v.grad).all() for v in model.parameters())
    model.eval();save_policy(tmp_path/'model.pt',model,{'status':'unit-test-only'})
    loaded,metadata=load_policy(tmp_path/'model.pt')
    with torch.no_grad():torch.testing.assert_close(loaded(x)[0],model(x)[0])
    assert metadata['status']=='unit-test-only'
    with pytest.raises(ValueError,match='Not a benchmark-2'):
        load_baseline(tmp_path/'model.pt')
