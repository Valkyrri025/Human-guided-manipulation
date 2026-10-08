"""Colour-marker tracking and table-plane calibration; no robot action labels.

Coordinates: origin at top-left calibration mark, +x right, +y down in image.
Missing detections remain NaN/blank. Four-corner calibration does not correct
lens distortion or the parallax of markers above the paper.
"""
import argparse
from contextlib import nullcontext
import csv
import hashlib
import json
from pathlib import Path

import cv2
import imageio.v2 as imageio
import numpy as np



def open_video(video, orientation='display'):
    """Read the original; honour display metadata without rewriting the file."""
    capture=cv2.VideoCapture(str(video))
    if orientation not in ('display','stored'):
        capture.release()
        raise ValueError('Unknown image orientation')
    metadata=capture.get(cv2.CAP_PROP_ORIENTATION_META)
    supported=capture.set(cv2.CAP_PROP_ORIENTATION_AUTO,1. if orientation=='display' else 0.)
    if orientation=='display' and abs(metadata)>1e-6 and not supported:
        capture.release()
        raise ValueError('Decoder cannot apply video display metadata')
    return capture


def colour_mask(frame, ranges):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    for lower, upper in ranges:
        mask |= cv2.inRange(hsv, np.array(lower, np.uint8), np.array(upper, np.uint8))
    return mask


def components(mask, minimum=80, maximum=10000):
    n, labels, stats, centres = cv2.connectedComponentsWithStats(mask)
    return [(i, s, c) for i, s, c in zip(range(1, n), stats[1:], centres[1:])
            if minimum <= s[cv2.CC_STAT_AREA] <= maximum], labels


def corner_intersection(mask):
    """Intersection of the thick vertical/horizontal strokes of an L mark."""
    rows, cols = (mask > 0).sum(axis=1), (mask > 0).sum(axis=0)
    if rows.max() == 0 or cols.max() == 0:
        raise ValueError('Empty corner mask')
    x = float(np.median(np.flatnonzero(cols >= 0.75 * cols.max())))
    y = float(np.median(np.flatnonzero(rows >= 0.75 * rows.max())))
    return [x, y]


def homography(corners, width, height):
    corners = np.asarray(corners, np.float32)
    if corners.shape != (4, 2) or not np.isfinite(corners).all():
        raise ValueError('Four finite corners required: TL, TR, BR, BL')
    if not cv2.isContourConvex(corners) or cv2.contourArea(corners) < 100:
        raise ValueError('Calibration quadrilateral is too small or not convex')
    if width <= 0 or height <= 0:
        raise ValueError('Measured rectangle dimensions must be positive')
    return cv2.getPerspectiveTransform(corners, np.float32([[0, 0], [width, 0],
                                                          [width, height], [0, height]]))


def map_point(point, matrix):
    if point is None:
        return np.full(2, np.nan)
    return cv2.perspectiveTransform(np.float32(point).reshape(1, 1, 2), matrix)[0, 0].astype(float)


def detect_marker(frame, ranges, workspace, minimum, maximum):
    mask = colour_mask(frame, ranges) & workspace
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    candidates, labels = components(mask, minimum, maximum)
    if not candidates:
        return None, 0
    i, stats, centre = max(candidates, key=lambda item: item[1][cv2.CC_STAT_AREA])
    return centre, int(stats[cv2.CC_STAT_AREA])


def create_config(video, output, width, height):
    capture = open_video(video)
    ok, frame = capture.read()
    capture.release()
    if not ok:
        raise ValueError('Cannot decode first video frame')
    red = [[[0, 100, 60], [10, 255, 255]], [[170, 100, 60], [179, 255, 255]]]
    candidates, labels = components(colour_mask(frame, red), 100, 5000)
    # Ignore thin red object-side fragments: L marks have substantial
    # horizontal and vertical extent at this recording resolution.
    candidates=[item for item in candidates if item[1][2]>=12 and item[1][3]>=12 and .5<=item[1][2]/item[1][3]<=2.]
    # Bootstrap from an unobstructed opening frame. Human-review the preview.
    if len(candidates) != 4:
        raise ValueError(f'Expected exactly four red marks, found {len(candidates)}; supply a reviewed calibration JSON')
    candidates.sort(key=lambda item: item[2][1])
    top = sorted(candidates[:2], key=lambda item: item[2][0])
    bottom = sorted(candidates[2:], key=lambda item: item[2][0])
    ordered = top + bottom[::-1]
    corners = [corner_intersection((labels == i).astype(np.uint8)) for i, _, _ in ordered]
    windows = []
    for _, s, _ in ordered:
        x, y, w, h = map(int, s[:4])
        windows.append([max(0, x-15), max(0, y-15), min(frame.shape[1], x+w+15), min(frame.shape[0], y+h+15)])
    homography(corners, width, height)
    config = {
        'schema_version': 2, 'video': str(video),
        'image_orientation':'display',
        'paper_to_robot_frame':'user_convention_v1',
        'paper_to_robot_matrix':[[1.,0.],[0.,-1.]],
        'robot_rectangle_dimensions_xy_m':[.30,.297],
        'rectangle_width_m': width, 'rectangle_height_m': height,
        'coordinate_convention': 'origin top-left L intersection; x right, y down; metres',
        'corners_order': ['top_left', 'top_right', 'bottom_right', 'bottom_left'],
        'corners_px': corners, 'corner_search_windows_px': windows,
        'calibration_source': 'red L stroke intersections detected in opening frame; inspect preview',
        'marker_height_correction': 'none; planar approximation',
        'lens_distortion_correction': 'none',
        'red_hsv_ranges': red,
        'object_hsv_ranges': [[[35, 70, 50], [90, 255, 255]]],
        'finger_hsv_ranges': [[[0, 160, 140], [22, 255, 255]]],
        'object_area_px': [80, 5000], 'finger_area_px': [80, 7000],
        'object_dimensions_m': [0.017, 0.017, 0.017],
        'object_dimensions_source': 'user approximate measurement',
        'finger_workspace_margin_px': 90,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(config, indent=2) + '\n')
    return config


def detect_goal_square(video, config):
    """Detect one dark square and its cross in an unobstructed opening frame."""
    capture=open_video(video,config.get('image_orientation','stored')); ok,frame=capture.read(); capture.release()
    if not ok: raise ValueError('Cannot decode goal calibration frame')
    workspace=np.zeros(frame.shape[:2],np.uint8)
    cv2.fillConvexPoly(workspace,np.rint(config['corners_px']).astype(np.int32),255)
    workspace=cv2.erode(workspace,np.ones((31,31),np.uint8))
    mask=(cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)<90).astype(np.uint8)*255 & workspace
    contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    candidates=[]
    for contour in contours:
        polygon=cv2.approxPolyDP(contour,.02*cv2.arcLength(contour,True),True)
        x,y,w,h=cv2.boundingRect(contour)
        if 500<cv2.contourArea(contour)<10000 and len(polygon)==4 and .6<w/h<1.6:
            candidates.append(polygon.reshape(4,2))
    if len(candidates)!=1:
        raise ValueError(f'Expected one goal square, found {len(candidates)}; inspect opening frame')
    corners=candidates[0].astype(float)
    centre=corners.mean(axis=0)
    # Start just inside the outline; use the cross centroid when detectable.
    x0,y0=np.ceil(corners.min(axis=0)+7).astype(int)
    x1,y1=np.floor(corners.max(axis=0)-7).astype(int)
    ys,xs=np.nonzero(mask[y0:y1,x0:x1])
    source='square-corner mean'
    if 5<=len(xs)<=300:
        centre=np.array([xs.mean()+x0,ys.mean()+y0]); source='black centre-cross centroid'
    matrix=homography(config['corners_px'],config['rectangle_width_m'],config['rectangle_height_m'])
    return {'source':'independent drawn square in opening frame',
            'center_source':source,'center_px':centre.tolist(),
            'center_table_xy_m':map_point(centre,matrix).tolist(),
            'corners_px':corners.tolist(),
            'corners_table_xy_m':[map_point(c,matrix).tolist() for c in corners],
            'success_center_tolerance_m':.010}


def frame_corners(frame, config):
    red_mask = colour_mask(frame, config['red_hsv_ranges'])
    corners = []
    for window in config['corner_search_windows_px']:
        x0, y0, x1, y1 = window
        crop = red_mask[y0:y1, x0:x1]
        candidates, labels = components(crop, 70, 5000)
        if not candidates:
            return None
        i, _, _ = max(candidates, key=lambda item: item[1][cv2.CC_STAT_AREA])
        x, y = corner_intersection((labels == i).astype(np.uint8))
        corners.append([x+x0, y+y0])
    corners=np.asarray(corners)
    limit=config.get('max_corner_shift_px')
    if limit is not None and np.max(np.linalg.norm(corners-np.asarray(config['corners_px']),axis=1))>float(limit):
        return None
    return corners


def track(video, config, output, write_overlay=True):
    output.mkdir(parents=True, exist_ok=True)
    capture = open_video(video,config.get('image_orientation','stored'))
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    if not capture.isOpened() or fps <= 0:
        raise ValueError('Cannot open video or invalid FPS')
    width, height = int(capture.get(3)), int(capture.get(4))
    initial_corners = np.asarray(config['corners_px'])
    initial_h = homography(initial_corners, config['rectangle_width_m'], config['rectangle_height_m'])
    records, calibration_shifts = [], []
    preview = None
    index = 0
    try:
        writer_context=imageio.get_writer(output / 'tracking_overlay.mp4',fps=fps,codec='libx264',quality=8,macro_block_size=16) if write_overlay else nullcontext(None)
        with writer_context as writer:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                corners = frame_corners(frame, config)
                valid_calibration = corners is not None
                if valid_calibration:
                    matrix = homography(corners, config['rectangle_width_m'], config['rectangle_height_m'])
                    calibration_shifts.append(float(np.max(np.linalg.norm(corners-initial_corners, axis=1))))
                else:
                    corners, matrix = initial_corners, initial_h
                workspace = np.zeros((height, width), np.uint8)
                cv2.fillConvexPoly(workspace, np.rint(corners).astype(np.int32), 255)
                # Exclude the red border from orange detection.
                workspace = cv2.erode(workspace, np.ones((21, 21), np.uint8))
                obj, obj_area = detect_marker(frame, config['object_hsv_ranges'], workspace, *config['object_area_px'])
                margin=int(config.get('finger_workspace_margin_px',0))
                finger_workspace=workspace.copy()
                if margin>0:
                    finger_workspace=cv2.dilate(workspace,np.ones((2*margin+1,2*margin+1),np.uint8))
                    # Orange HSV overlaps red: exclude known calibration marks.
                    for x0,y0,x1,y1 in config['corner_search_windows_px']:
                        finger_workspace[y0:y1,x0:x1]=0
                for x0,y0,x1,y1 in config.get('finger_exclusion_windows_px',[]):
                    finger_workspace[y0:y1,x0:x1]=0
                finger, finger_area = detect_marker(frame, config['finger_hsv_ranges'], finger_workspace, *config['finger_area_px'])
                obj_xy, finger_xy = map_point(obj, matrix), map_point(finger, matrix)
                records.append([index, index/fps, *(obj if obj is not None else [np.nan]*2), *obj_xy,
                                *(finger if finger is not None else [np.nan]*2), *finger_xy,
                                int(obj is not None), int(finger is not None), obj_area, finger_area,
                                int(valid_calibration)])
                cv2.polylines(frame, [np.rint(corners).astype(np.int32)], True, (255, 120, 0), 2)
                if 'goal' in config:
                    goal=config['goal']
                    target_pixels=cv2.perspectiveTransform(np.float32(goal['corners_table_xy_m']).reshape(-1,1,2),np.linalg.inv(matrix))
                    cv2.polylines(frame,[np.rint(target_pixels).astype(np.int32)],True,(255,0,255),2)
                    centre=map_point(goal['center_table_xy_m'],np.linalg.inv(matrix))
                    cv2.drawMarker(frame,tuple(np.rint(centre).astype(int)),(255,0,255),cv2.MARKER_CROSS,14,2)
                for label, point, xy, colour in [('object', obj, obj_xy, (0, 220, 0)),
                                                 ('finger', finger, finger_xy, (0, 170, 255))]:
                    if point is not None:
                        pixel = tuple(np.rint(point).astype(int))
                        cv2.circle(frame, pixel, 5, colour, 2)
                        cv2.putText(frame, f'{label} {xy[0]:.3f},{xy[1]:.3f} m',
                                    (max(5, pixel[0]-80), pixel[1]-18), cv2.FONT_HERSHEY_SIMPLEX, .42, colour, 1)
                cv2.putText(frame, f'{index/fps:.2f}s | calibration: {"detected" if valid_calibration else "opening-frame fallback"}',
                            (15, 35), cv2.FONT_HERSHEY_SIMPLEX, .5, (30, 30, 30), 1)
                cv2.putText(frame, 'Finger marker centre is NOT the contact point', (15, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, .45, (30, 30, 30), 1)
                if writer is not None:
                    writer.append_data(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                if obj is not None and finger is not None and (preview is None or index == int(capture.get(cv2.CAP_PROP_FRAME_COUNT)) // 2):
                    preview = frame.copy()
                index += 1
    finally:
        capture.release()
    if not records:
        raise ValueError('Video decoded zero frames')
    data = np.asarray(records)
    header = ['frame', 'time_s', 'object_u_px', 'object_v_px', 'object_x_m', 'object_y_m',
              'finger_u_px', 'finger_v_px', 'finger_x_m', 'finger_y_m', 'object_detected',
              'finger_detected', 'object_area_px', 'finger_area_px', 'calibration_detected']
    with (output / 'tracks.csv').open('w', newline='') as f:
        writer = csv.writer(f); writer.writerow(header)
        for row in records:
            writer.writerow(['' if isinstance(v, (float, np.floating)) and np.isnan(v) else v for v in row])
    np.savez_compressed(output / 'tracks.npz', time_s=data[:, 1], object_xy_m=data[:, 4:6],
                        finger_xy_m=data[:, 8:10], detected=data[:, 10:12].astype(bool),
                        calibration_detected=data[:, 14].astype(bool),
                        image_orientation=np.asarray(config.get('image_orientation','stored')),
                        calibration_sha256=np.asarray(hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()))
    if preview is not None:
        cv2.imwrite(str(output / 'preview.jpg'), preview)
    valid_object = data[:, 10].astype(bool)
    object_xy = data[valid_object, 4:6]
    if not len(object_xy):
        raise SystemExit('No object detections; inspect the colour ranges and opening frame')
    # Paused endpoint medians suppress pixel jitter. Not a chosen task target.
    start = np.median(object_xy[:min(30, len(object_xy))], axis=0) if len(object_xy) else np.full(2, np.nan)
    end = np.median(object_xy[-min(15, len(object_xy)):], axis=0) if len(object_xy) else np.full(2, np.nan)
    active = data[:, 11].astype(bool)
    deltas = np.linalg.norm(np.diff(data[:, 4:6], axis=0), axis=1)
    finger_deltas = np.linalg.norm(np.diff(data[:, 8:10], axis=0), axis=1)
    def max_finite(values):
        return float(np.nanmax(values)) if np.isfinite(values).any() else None
    decoded=None
    if write_overlay:
        with imageio.get_reader(output / 'tracking_overlay.mp4') as reader:
            decoded=sum(1 for _ in reader)
    result = {
        'video': str(video), 'video_sha256': hashlib.sha256(video.read_bytes()).hexdigest(),
        'frames': len(records), 'fps': fps, 'duration_s': len(records)/fps,
        'frame_size_px': [width, height], 'decoded_overlay_frames': decoded,
        'image_orientation':config.get('image_orientation','stored'),'overlay_generated':write_overlay,
        'object_detected_frames': int(valid_object.sum()),
        'finger_detected_frames': int(active.sum()),
        'finger_first_visible_s': float(data[active, 1][0]) if active.any() else None,
        'finger_last_visible_s': float(data[active, 1][-1]) if active.any() else None,
        'finger_missing_inside_visible_interval': int((~active[np.flatnonzero(active)[0]:np.flatnonzero(active)[-1]+1]).sum()) if active.any() else None,
        'calibration_fallback_frames': int((data[:, 14] == 0).sum()),
        'max_corner_shift_px': max(calibration_shifts) if calibration_shifts else None,
        'object_start_xy_m': start.tolist(), 'object_end_xy_m': end.tolist(),
        'observed_object_displacement_m': float(np.linalg.norm(end-start)) if len(object_xy) else None,
        'largest_object_frame_step_m': max_finite(deltas),
        'largest_finger_frame_step_m': max_finite(finger_deltas),
        'independent_goal': config.get('goal'),
        'limitations': ['No lens distortion or marker-height correction',
                       'Tracks marker centres, not physical finger contact point',
                       'No interpolation of missing detections',
                       'Object endpoint is observed outcome; independent target saved separately when present',
                       'No robot actions or pushing success evaluation generated at this checkpoint'],
    }
    (output / 'quality.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, allow_nan=False))
    if (write_overlay and decoded != len(records)) or not len(object_xy):
        raise SystemExit('Tracking output validation failed')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video', type=Path, default=Path('data/raw/pilot_push.mp4'))
    parser.add_argument('--calibration', type=Path, default=Path('data/calibration/pilot.json'))
    parser.add_argument('--output', type=Path, default=Path('data/processed/pilot'))
    parser.add_argument('--no-overlay',action='store_true',help='Save tracks and upright preview without a regenerable overlay video')
    parser.add_argument('--detect-goal-square', action='store_true')
    parser.add_argument('--initialise-calibration', action='store_true')
    parser.add_argument('--width-m', type=float, default=0.30)
    parser.add_argument('--height-m', type=float, default=0.297)
    args = parser.parse_args()
    if args.initialise_calibration:
        if args.calibration.exists():
            parser.error('Calibration already exists; use a new path to avoid overwriting reviewed calibration')
        config = create_config(args.video, args.calibration, args.width_m, args.height_m)
    else:
        config = json.loads(args.calibration.read_text())
    if args.detect_goal_square:
        config['goal']=detect_goal_square(args.video,config)
        args.calibration.write_text(json.dumps(config,indent=2)+'\n')
    track(args.video, config, args.output,write_overlay=not args.no_overlay)


if __name__ == '__main__':
    main()
