import numpy as np
from scipy.spatial.transform import Rotation
from humanoid_push.task_rules import StopRule, box_inside_polygon


def test_pass_through_does_not_count_and_dwell_resets():
    rule=StopRule(8.,.2)
    assert rule.update(1.,True) is None
    assert rule.update(1.1,False) is None
    assert rule.update(1.2,True) is None
    assert rule.update(1.3,True) is None
    assert rule.update(1.4,True)=='goal_reached'


def test_timeout_wins_before_dwell_and_goal_wins_exact_tie():
    rule=StopRule(.3,.2)
    assert rule.update(.2,True) is None
    assert rule.update(.3,True)=='timeout'
    tied=StopRule(.3,.2)
    assert tied.update(.1,True) is None
    assert tied.update(.3,True)=='goal_reached'


def test_cube_orientation_unrestricted_but_whole_footprint_must_fit():
    square=np.array([[-.015,-.015],[-.015,.015],[.015,.015],[.015,-.015]])
    rotated=Rotation.from_euler('z',45,degrees=True).as_matrix()
    assert box_inside_polygon(np.array([0,0,.8085]),rotated,np.array([.017]*3),square)
    # Centre is inside, but cube crosses the square's right edge.
    assert not box_inside_polygon(np.array([.010,0,.8085]),np.eye(3),np.array([.017]*3),square)
