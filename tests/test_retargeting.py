import numpy as np
import pytest
from humanoid_push.retargeting import adapt_reference


def reference():
    return {'object_start':np.array([0.,0.]),'target':np.array([.1,0.]),
            'reference_xy':np.array([[-.014,0.],[.03,.005],[.086,0.]]),
            'endpoint':np.array([.1,0.]),'object_size':np.array([.017]*3),
            'push_yaw_rad':0.,'time_s':np.array([0.,1.,2.])}


def test_absolute_keeps_path_and_all_modes_share_orientation():
    ref=reference();start=np.array([0.,-.02])
    absolute=adapt_reference(ref,start,'absolute')
    np.testing.assert_array_equal(absolute['reference_xy'],ref['reference_xy'])
    assert absolute['push_yaw_rad']==adapt_reference(ref,start,'relative')['push_yaw_rad']
    np.testing.assert_array_equal(ref['object_start'],[0,0])


def test_scaled_path_preserves_curve_and_times_without_stretching_contact_offset():
    ref=reference();start=np.array([-.1,0.])
    scaled=adapt_reference(ref,start,'relative-scaled')
    rigid=adapt_reference(ref,start,'relative')
    np.testing.assert_allclose(scaled['reference_xy'][0]-start,ref['reference_xy'][0])
    np.testing.assert_allclose(np.diff(scaled['reference_xy'],axis=0),2*np.diff(ref['reference_xy'],axis=0))
    np.testing.assert_allclose(np.diff(rigid['reference_xy'],axis=0),np.diff(ref['reference_xy'],axis=0))
    np.testing.assert_array_equal(scaled['time_s'],ref['time_s'])
    np.testing.assert_allclose(scaled['endpoint'],ref['target'])


def test_rotation_uses_new_goal_direction_and_changes_cube_support():
    ref=reference();new=adapt_reference(ref,np.array([.1,-.1]),'relative-scaled')
    np.testing.assert_allclose(new['reference_xy'][0],[.1,-.114],atol=1e-12)
    np.testing.assert_allclose(new['reference_xy'][1]-new['reference_xy'][0],[-.005,.044],atol=1e-12)
    assert new['push_yaw_rad']==pytest.approx(np.pi/2)


def test_diagonal_contact_offset_adjusts_support_without_scaling_geometry():
    ref=reference();start=np.array([-.1,-.2])
    new=adapt_reference(ref,start,'relative-scaled')
    normal=np.array([1.,1.])/np.sqrt(2)
    extra_support=.0085*(np.sqrt(2)-1)
    np.testing.assert_allclose(new['reference_xy'][0]-start,-normal*(.014+extra_support))
    np.testing.assert_allclose(new['endpoint'],ref['target'],atol=1e-12)


def test_zero_offset_is_identity_in_every_mode():
    ref=reference()
    for mode in ['absolute','relative','relative-scaled']:
        result=adapt_reference(ref,ref['object_start'],mode)
        np.testing.assert_allclose(result['reference_xy'],ref['reference_xy'])
