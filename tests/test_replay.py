"""Check that human references survive retargeting and gaps are rejected."""
import json
import numpy as np
import pytest
from humanoid_push.replay import prepare_reference


def example(tmp_path, gap=False):
    times=np.arange(180)/30
    obj=np.column_stack([.1+.015*times, .15+.002*np.sin(times)])
    finger=obj-np.array([.03,.004])
    if gap:finger[80]=np.nan
    tracks=tmp_path/'tracks.npz'
    np.savez(tracks,time_s=times,object_xy_m=obj,finger_xy_m=finger)
    calibration=tmp_path/'calibration.json'
    calibration.write_text(json.dumps({'rectangle_width_m':.3,'rectangle_height_m':.297,
                                       'object_dimensions_m':[.017]*3}))
    return tracks,calibration,times,finger


def test_retargeting_preserves_recorded_motion_not_just_endpoints(tmp_path):
    tracks,calibration,times,finger=example(tmp_path)
    reference=prepare_reference(tracks,calibration,1.,5.,.004)
    selected=(times>=1.)&(times<=5.)
    np.testing.assert_allclose(np.diff(reference['reference_xy'],axis=0),
                               np.diff(finger[selected],axis=0),atol=1e-12)
    assert np.ptp(reference['reference_xy'][:,1])>.003
    assert reference['time_s'][0]==0


def test_replay_rejects_missing_contact_marker_instead_of_inventing_motion(tmp_path):
    tracks,calibration,_,_=example(tmp_path,gap=True)
    with pytest.raises(ValueError,match='no gaps'):
        prepare_reference(tracks,calibration,1.,5.,.004)


def test_independent_target_does_not_come_from_recorded_endpoint(tmp_path):
    tracks,calibration,_,_=example(tmp_path)
    cfg=json.loads(calibration.read_text())
    cfg['goal']={'center_table_xy_m':[.25,.23],
                 'corners_table_xy_m':[[.235,.215],[.235,.245],[.265,.245],[.265,.215]],
                 'source':'independent drawn square in opening frame','success_center_tolerance_m':.01}
    calibration.write_text(json.dumps(cfg))
    result=prepare_reference(tracks,calibration,1.,5.,.004)
    np.testing.assert_allclose(result['target'],[.10,.0815])
    assert np.linalg.norm(result['target']-result['endpoint'])>.02
    assert result['goal_tolerance_m']==.01


def test_session_registration_rotates_all_geometry_into_robot_frame(tmp_path):
    tracks,calibration,_,_=example(tmp_path)
    cfg=json.loads(calibration.read_text())
    cfg['goal']={'center_table_xy_m':[.25,.23],
                 'corners_table_xy_m':[[.235,.215],[.235,.245],[.265,.245],[.265,.215]],
                 'source':'independent drawn square'}
    calibration.write_text(json.dumps(cfg))
    original=prepare_reference(tracks,calibration,1.,5.,.004)
    cfg['paper_to_robot_yaw_degrees']=90.
    calibration.write_text(json.dumps(cfg))
    registered=prepare_reference(tracks,calibration,1.,5.,.004)
    rotation=np.array([[0.,-1.],[1.,0.]])
    for key in ['reference_xy','object_start','endpoint','target','target_polygon','marker_to_tool_offset_m']:
        np.testing.assert_allclose(registered[key],original[key]@rotation.T,atol=1e-12)
    np.testing.assert_allclose(registered['paper_size_robot_xy'],[.297,.30])
    assert registered['push_yaw_rad']==pytest.approx(original['push_yaw_rad']+np.pi/2)
    # A decoded start above its goal maps farther from the robot base (+X).
    relative=rotation@np.array([0.,-.08])
    np.testing.assert_allclose(relative,[.08,0.])


def test_registered_rectangle_matches_user_dimensions_without_stretching_cube(tmp_path):
    tracks,calibration,_,_=example(tmp_path)
    cfg=json.loads(calibration.read_text())
    cfg['paper_to_robot_yaw_degrees']=-90.
    cfg['robot_rectangle_dimensions_xy_m']=[.30,.297]
    calibration.write_text(json.dumps(cfg))
    result=prepare_reference(tracks,calibration,1.,5.,.004)
    matrix=result['paper_to_robot_matrix']
    corners=np.array([[-.15,-.1485],[.15,-.1485],[.15,.1485],[-.15,.1485]])@matrix.T
    np.testing.assert_allclose(np.ptp(corners,axis=0),[.30,.297])
    np.testing.assert_allclose(result['object_size'],[.017]*3)
    assert np.linalg.norm(matrix@np.array([0,1]))==pytest.approx(.30/.297)


def test_native_recording_sides_follow_user_robot_convention(tmp_path):
    tracks,calibration,_,_=example(tmp_path)
    cfg=json.loads(calibration.read_text());cfg['paper_to_robot_matrix']=[[1,0],[0,-1]]
    calibration.write_text(json.dumps(cfg))
    result=prepare_reference(tracks,calibration,1.,5.,.004)
    matrix=result['paper_to_robot_matrix']
    # Robot base is -X; overhead screen left is +Y.
    for recording,expected in [([-1,0],[-1,0]),([1,0],[1,0]),([0,-1],[0,1]),([0,1],[0,-1])]:
        np.testing.assert_allclose(matrix@recording,expected)
    np.testing.assert_allclose(result['paper_size_robot_xy'],[.30,.297])


def test_mixing_old_tracks_and_new_orientation_is_rejected(tmp_path):
    tracks,calibration,_,_=example(tmp_path)
    data=dict(np.load(tracks));data['image_orientation']=np.asarray('stored')
    np.savez(tracks,**data)
    cfg=json.loads(calibration.read_text());cfg['image_orientation']='display';calibration.write_text(json.dumps(cfg))
    with pytest.raises(ValueError,match='orientations differ'):
        prepare_reference(tracks,calibration,1.,5.,.004)
