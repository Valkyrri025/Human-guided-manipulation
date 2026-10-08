"""Geometry and detection checks independent of the pilot's measured output."""
import cv2
import numpy as np
import pytest
from humanoid_push.tracking import homography, map_point, detect_marker


def test_projective_calibration_recovers_known_table_points():
    # Known table-to-image projective camera transform, independent of fitter.
    world_to_image = np.array([[1300, 120, 80], [30, 1500, 60], [.3, .2, 1.]])
    table = np.float32([[0, 0], [.3, 0], [.3, .297], [0, .297]])
    image = cv2.perspectiveTransform(table.reshape(-1, 1, 2), world_to_image).reshape(-1, 2)
    calibration = homography(image, .3, .297)
    expected = np.float32([.12, .19])
    pixel = cv2.perspectiveTransform(expected.reshape(1, 1, 2), world_to_image)[0, 0]
    np.testing.assert_allclose(map_point(pixel, calibration), expected, atol=1e-6)


def test_missing_marker_stays_missing_and_border_is_excluded():
    ranges = [[[0, 160, 140], [22, 255, 255]]]
    frame = np.zeros((120, 120, 3), np.uint8)
    hsv_colour = np.uint8([[[6, 220, 210]]])
    colour = tuple(int(x) for x in cv2.cvtColor(hsv_colour, cv2.COLOR_HSV2BGR)[0, 0])
    cv2.rectangle(frame, (0, 0), (19, 19), colour, -1)
    workspace = np.zeros((120, 120), np.uint8)
    workspace[25:110, 25:110] = 255
    marker, area = detect_marker(frame, ranges, workspace, 80, 5000)
    assert marker is None and area == 0
    assert np.isnan(map_point(marker, np.eye(3))).all()
    cv2.rectangle(frame, (60, 60), (79, 79), colour, -1)
    marker, area = detect_marker(frame, ranges, workspace, 80, 5000)
    np.testing.assert_allclose(marker, [69.5, 69.5])
    assert area == 400


def test_invalid_corner_order_is_rejected():
    with pytest.raises(ValueError):
        homography([[0, 0], [100, 100], [100, 0], [0, 100]], .3, .297)


def test_goal_cross_is_calibrated_from_opening_frame(tmp_path):
    from humanoid_push.tracking import detect_goal_square
    frame=np.full((300,300,3),255,np.uint8)
    cv2.rectangle(frame,(120,120),(180,180),(0,0,0),2)
    cv2.line(frame,(145,145),(155,155),(0,0,0),1)
    cv2.line(frame,(145,155),(155,145),(0,0,0),1)
    source=tmp_path/'opening.png';cv2.imwrite(str(source),frame)
    cfg={'corners_px':[[10,10],[290,10],[290,290],[10,290]],
         'rectangle_width_m':.3,'rectangle_height_m':.3}
    goal=detect_goal_square(source,cfg)
    np.testing.assert_allclose(goal['center_table_xy_m'],[.15,.15],atol=1e-6)
    assert goal['center_source']=='black centre-cross centroid'


def test_corner_calibration_ignores_thin_red_object_side(tmp_path):
    from humanoid_push.tracking import create_config
    frame=np.full((400,400,3),255,np.uint8)
    red=(0,0,220)
    for x,y,sx,sy in [(30,30,1,1),(370,30,-1,1),(370,370,-1,-1),(30,370,1,-1)]:
        cv2.line(frame,(x,y),(x+25*sx,y),red,3)
        cv2.line(frame,(x,y),(x,y+25*sy),red,3)
    cv2.rectangle(frame,(90,180),(96,207),red,-1)
    source=tmp_path/'opening.png';cv2.imwrite(str(source),frame)
    cfg=create_config(source,tmp_path/'calibration.json',.3,.297)
    np.testing.assert_allclose(cfg['corners_px'],[[30,30],[370,30],[370,370],[30,370]],atol=2)


def test_occluded_corner_replaced_by_red_finger_is_rejected(tmp_path):
    from humanoid_push.tracking import create_config,frame_corners
    frame=np.full((400,400,3),255,np.uint8)
    for x,y,sx,sy in [(30,30,1,1),(370,30,-1,1),(370,370,-1,-1),(30,370,1,-1)]:
        cv2.line(frame,(x,y),(x+25*sx,y),(0,0,220),3)
        cv2.line(frame,(x,y),(x,y+25*sy),(0,0,220),3)
    source=tmp_path/'opening.png';cv2.imwrite(str(source),frame)
    cfg=create_config(source,tmp_path/'calibration.json',.3,.297)
    cfg['max_corner_shift_px']=15.
    assert frame_corners(frame,cfg) is not None
    frame[12:72,12:72]=255
    cv2.rectangle(frame,(52,52),(68,68),(0,0,220),-1)
    assert frame_corners(frame,cfg) is None
