"""Check limits and geometric behavior of the separate scripted teacher."""
import numpy as np
from scipy.spatial.transform import Rotation
from humanoid_push.teacher import object_tracking_target


def target(goal, position, angle=0):
    return object_tracking_target(np.array(goal),np.array(position),Rotation.from_euler('z',angle).as_matrix(),np.array([.017]*3),np.array([1.,0.]),.004)


def test_large_tracking_error_is_bounded_and_does_not_teleport_to_goal():
    no_error=target([.1,.2],[.1,.2])
    distant_cube=target([.1,.2],[-10,-10])
    assert np.isclose(np.linalg.norm(distant_cube-no_error),.006)
    assert distant_cube[0]>no_error[0] and distant_cube[1]>no_error[1]


def test_contact_offset_tracks_rotated_box_support():
    aligned=target([0,0],[0,0])
    diagonal=target([0,0],[0,0],np.pi/4)
    assert diagonal[0]<aligned[0]
    assert np.isclose(diagonal[1],0)


def test_recorded_trajectory_changes_teacher_reference():
    origin=target([0,0],[0,0])
    shifted=target([.02,.01],[.02,.01])
    np.testing.assert_allclose(shifted-origin,[.02,.01])
