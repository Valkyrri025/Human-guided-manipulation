import numpy as np
import pytest
torch = pytest.importorskip("torch", reason="Install the learning extra for BC tests")
from scipy.spatial.transform import Rotation
from humanoid_push.bc_data import features, load_split, prepare
from humanoid_push.bc_model import PushPolicy, save_policy, load_policy


def test_feature_frames_quaternion_orders_and_translation_invariance():
    states=np.array([[.1,.2,.868,.03,.04,.8085]])
    cube=Rotation.from_euler('z',90,degrees=True).as_quat()[[3,0,1,2]]
    eef=(Rotation.from_euler('z',-30,degrees=True)*Rotation.from_euler('x',180,degrees=True)).as_quat()
    x=features(states,cube,eef,[.05,.06])
    np.testing.assert_allclose(x,[[.07,.16,.02,.02,1,0,-.5,np.sqrt(3)/2]],atol=1e-6)
    shifted=states.copy();shifted[:,:2]+=[2,3];shifted[:,3:5]+=[2,3]
    np.testing.assert_allclose(features(shifted,cube,eef,[2.05,3.06]),x,atol=1e-6)


def test_policy_bounds_gradient_and_checkpoint(tmp_path):
    torch.manual_seed(7)
    model=PushPolicy(np.zeros(8),np.ones(8))
    x=torch.randn(24,8)*10
    y=model(x)
    assert y.shape==(24,2) and torch.isfinite(y).all() and y.abs().max()<=.2
    y.square().mean().backward()
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())
    save_policy(tmp_path/'model.pt',model,{'status':'unit-test-only'})
    loaded,meta=load_policy(tmp_path/'model.pt')
    torch.testing.assert_close(loaded(x),y)
    assert meta['status']=='unit-test-only'


def test_reject_test_split_without_accessing_files(tmp_path):
    with pytest.raises(ValueError,match='reserved'):
        load_split(tmp_path,tmp_path/'does-not-exist.json','test')


def test_dataset_causality_and_training_only_statistics(tmp_path):
    import json
    (tmp_path/'data/manifests').mkdir(parents=True)
    for split,prefix,shift in [('train','train',0.),('validation','validation',10.)]:
        states=np.array([[.1+shift,.2,.868,.03,.04,.8085],[.2+shift,.2,.868,.03,.04,.8085]])
        np.savez(tmp_path/f'{prefix}.npz',observations_before=states,observations=states+100,
            cube_quat_wxyz_before=np.tile([1,0,0,0],(2,1)),eef_quat_site_before=np.tile([1,0,0,0],(2,1)),
            target_xy_m=[.05,.06],actions=np.tile([.1,-.1,0,0,0,0,1],(2,1)),
            phases=['human_push','approach'],push_controller='human-object-feedback')
        (tmp_path/f'{prefix}.json').write_text(json.dumps({'passed':True}))
        ep={'episode':prefix,'split':split,'expert_eligible':True,'validation_reference_eligible':True,
            'robot_rollout':f'{prefix}.npz','metrics':f'{prefix}.json'}
        filename='training_rollout_index.json' if split=='train' else 'validation_rollout_index.json'
        (tmp_path/'data/manifests'/filename).write_text(json.dumps({'episodes':[ep]}))
    report=prepare(tmp_path,tmp_path/'prepared')
    with np.load(tmp_path/'prepared/dataset.npz') as d:
        assert len(d['train_x'])==1 and len(d['validation_x'])==1
        np.testing.assert_allclose(d['mean'][:2],[.07,.16],atol=1e-6)
        np.testing.assert_allclose(d['train_y'],[[.1,-.1]])
        assert d['validation_x'][0,0]>10
    assert not report['test_accessed']


def test_test_evaluation_requires_frozen_protocol(tmp_path, monkeypatch):
    import json,sys
    from humanoid_push import bc_eval
    manifest=tmp_path/'manifest.json'
    manifest.write_text(json.dumps({'episodes':[{'id':f'test_{i:03d}','split':'test'} for i in range(1,10)]}))
    monkeypatch.setattr(bc_eval,'load_policy',lambda path:(None,{'status':'trained'}))
    monkeypatch.setattr(sys,'argv',['push-bc-evaluate','--checkpoint','unused.pt','--split','test',
        '--manifest',str(manifest),'--output',str(tmp_path/'output')])
    with pytest.raises(SystemExit) as error:
        bc_eval.main()
    assert error.value.code==2
    assert not (tmp_path/'output').exists()


def test_test_evaluation_rejects_changed_checkpoint(tmp_path, monkeypatch):
    import json,sys
    from humanoid_push import bc_eval
    manifest=tmp_path/'manifest.json';protocol=tmp_path/'protocol.json';checkpoint=tmp_path/'checkpoint.pt'
    manifest.write_text(json.dumps({'episodes':[{'id':f'test_{i:03d}','split':'test'} for i in range(1,10)]}))
    protocol.write_text(json.dumps({'checkpoint_sha256':'incorrect-digest'}));checkpoint.write_bytes(b'changed')
    monkeypatch.setattr(bc_eval,'load_policy',lambda path:(None,{'status':'trained'}))
    monkeypatch.setattr(sys,'argv',['push-bc-evaluate','--checkpoint',str(checkpoint),'--split','test',
        '--manifest',str(manifest),'--protocol',str(protocol),'--output',str(tmp_path/'output')])
    with pytest.raises(SystemExit) as error:
        bc_eval.main()
    assert error.value.code==2
    assert not (tmp_path/'output').exists()
