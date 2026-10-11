"""Calibrate a held-out scene using only its opening 30 frames, never its push."""
import argparse
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np
from humanoid_push.tracking import create_config, detect_goal_square, open_video, homography, detect_marker, map_point


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--video',type=Path,required=True)
    p.add_argument('--calibration',type=Path,required=True)
    p.add_argument('--scene',type=Path,required=True)
    a=p.parse_args()
    if a.calibration.exists() or a.scene.exists():
        p.error('Choose fresh output paths; preserve reviewed/frozen initial scenes')
    c=create_config(a.video,a.calibration,.30,.297)
    c['goal']=detect_goal_square(a.video,c)
    matrix=homography(c['corners_px'],.30,.297)
    positions=[];cap=open_video(a.video)
    try:
        for _ in range(30):
            ok,frame=cap.read()
            if not ok:
                raise ValueError('Opening sample requires 30 frames')
            workspace=np.zeros(frame.shape[:2],np.uint8)
            cv2.fillConvexPoly(workspace,np.rint(c['corners_px']).astype(np.int32),255)
            point,_=detect_marker(frame,c['object_hsv_ranges'],workspace,*c['object_area_px'])
            if point is None:
                raise ValueError('Missing opening green marker; inspect source')
            positions.append(map_point(point,matrix))
    finally:
        cap.release()
    positions=np.asarray(positions);median=np.median(positions,axis=0)
    spread=float(np.max(np.linalg.norm(positions-median,axis=1)))
    if spread>.002:
        raise ValueError('Cube moved more than 2 mm during opening sample; inspect source')
    origin=np.array([.15,.1485]);registration=np.asarray(c['paper_to_robot_matrix'])
    scene={'initial_object_xyz_m':[*((median-origin)@registration.T),.809],
        'target_xy_m':((np.asarray(c['goal']['center_table_xy_m'])-origin)@registration.T).tolist(),
        'object_dimensions_m':c['object_dimensions_m'],'paper_size_robot_xy_m':[.30,.297],
        'opening_frames_used':30,'max_opening_deviation_m':spread,
        'video_sha256':hashlib.sha256(a.video.read_bytes()).hexdigest(),
        'source':'median green marker centroid from opening 30 frames; no pushing trajectory read',
        'initial_cube_orientation':'identity, same as validation; human object yaw not retargeted'}
    c['calibration_review']='pending visual review; do not evaluate until reviewed'
    a.calibration.write_text(json.dumps(c,indent=2)+'\n')
    a.scene.parent.mkdir(parents=True,exist_ok=True)
    a.scene.write_text(json.dumps(scene,indent=2)+'\n')
    print(f'Opening scene prepared; maximum marker deviation {spread*1000:.2f} mm. Inspect corners, goal and cube before use.')


if __name__=='__main__':
    main()
