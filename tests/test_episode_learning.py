import numpy as np
import pytest
torch=pytest.importorskip('torch')
from scipy.spatial.transform import Rotation
from humanoid_push.episode_data import features,pad,load_split,PHASE_MAP
from humanoid_push.episode_model import EpisodePolicy,save_policy,load_policy
from humanoid_push.episode_train import objective


def test_test_scene_requires_explicit_split_and_uses_opening_only(tmp_path):
    import json
    from humanoid_push.episode_eval import load_scene
    (tmp_path/'calibration.json').write_text('{}')
    (tmp_path/'opening.json').write_text(json.dumps({'opening_frames_used':30,'target_xy_m':[.01,.02]}))
    ep={'split':'test','calibration':'calibration.json','initial_scene':'opening.json',
        'metrics':'must_not_read_future_teacher_metrics.json'}
    with pytest.raises(ValueError,match='explicitly requested'):
        load_scene(tmp_path,ep)
    _,scene=load_scene(tmp_path,ep,expected_split='test')
    assert scene['target_xy_m']==[.01,.02]
    (tmp_path/'opening.json').write_text(json.dumps({'opening_frames_used':300}))
    with pytest.raises(ValueError,match='opening-only'):
        load_scene(tmp_path,ep,expected_split='test')


def test_features_include_actual_height_orientation_and_goal_not_phase():
    state=np.array([.02,.01,.968,0,0,.8085])
    q=Rotation.from_euler('z',90,degrees=True).as_quat()
    x=features(state,[1,0,0,0],q,[0,0],[[-.02,-.02],[.02,-.02],[.02,.02],[-.02,.02]],[.017]*3)
    assert x.shape==(1,15)
    np.testing.assert_allclose(x[0,:8],[.02,.01,0,0,.168,.0085,0,1],atol=1e-6)
    np.testing.assert_allclose(x[0,8:14],[0,1,0,-1,0,0],atol=1e-6)
    assert x[0,-1]==1
    state[3]=.04
    assert features(state,[1,0,0,0],q,[0,0],[[-.02,-.02],[.02,-.02],[.02,.02],[-.02,.02]],[.017]*3)[0,-1]==0


def test_sequence_and_streamed_policy_are_identical_and_bounded(tmp_path):
    torch.manual_seed(7);model=EpisodePolicy(np.zeros(15),np.ones(15)).eval()
    x=torch.randn(2,12,15)
    with torch.no_grad():
        all_actions,all_phases,_=model(x)
        hidden=None;actions=[];phases=[]
        for step in range(12):
            a,p,hidden=model(x[:,step:step+1],hidden);actions.append(a);phases.append(p)
    torch.testing.assert_close(all_actions,torch.cat(actions,1),atol=1e-6,rtol=1e-5)
    torch.testing.assert_close(all_phases,torch.cat(phases,1),atol=1e-6,rtol=1e-5)
    assert torch.all(all_actions.abs()<=model.limits)
    save_policy(tmp_path/'model.pt',model,{'status':'unit-test'})
    restored,_=load_policy(tmp_path/'model.pt')
    torch.testing.assert_close(restored(x)[0],all_actions)


def test_joint_loss_masks_padding_and_trains_both_outputs():
    torch.manual_seed(7);model=EpisodePolicy(np.zeros(15),np.ones(15))
    x=torch.randn(1,6,15);target=torch.zeros(1,6,6);phase=torch.tensor([[0,0,1,1,2,2]])
    mask=torch.tensor([[True,True,True,True,False,False]])
    a,p,_=model(x);loss,*_=objective(a,p,target,phase,mask,torch.ones(3))
    modified=target.clone();modified[:,4:]=100
    identical,*_=objective(a,p,modified,phase,mask,torch.ones(3))
    torch.testing.assert_close(loss,identical)
    loss.backward()
    for module in [model.phase_head,model.action_heads,model.memory]:
        assert all(v.grad is not None and torch.isfinite(v.grad).all() for v in module.parameters())


def test_three_phase_mapping_and_no_test_learning(tmp_path):
    assert [PHASE_MAP[s] for s in ['approach','lower','settle','human_push','goal_dwell','withdraw','final_settle']]==[0,0,0,1,1,2,2]
    with pytest.raises(ValueError,match='Only training'):
        load_split(tmp_path,'test')
    episodes=[(np.ones((2,15)),np.ones((2,6)),np.array([0,1])),
              (np.ones((3,15)),np.ones((3,6)),np.array([0,1,2]))]
    x,y,p,m=pad(episodes)
    assert x.shape==(2,3,15) and m.sum()==5 and not m[0,-1]
