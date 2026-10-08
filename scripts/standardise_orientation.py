"""Migrate derived calibration/tracks to phone display axes; never write raw data."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import cv2
from humanoid_push.tracking import create_config, detect_goal_square, open_video

cv2.setNumThreads(1)
calibration_dir=Path('data/calibration');legacy=calibration_dir/'legacy';legacy.mkdir(exist_ok=True)
processed_legacy=Path('data/processed/legacy');processed_legacy.mkdir(exist_ok=True)
manifest_dir=Path('data/manifests');manifest_legacy=manifest_dir/'legacy';manifest_legacy.mkdir(exist_ok=True)
configs=list(calibration_dir.glob('*.json'));manifest_files=list(manifest_dir.glob('*.json'))

def old_paths(value):
    if isinstance(value,dict):return {k:old_paths(v) for k,v in value.items()}
    if isinstance(value,list):return [old_paths(v) for v in value]
    if isinstance(value,str):
        for prefix in ['data/calibration/','data/processed/','data/manifests/']:
            if value.startswith(prefix) and not value.startswith(prefix+'legacy/'):
                return prefix+'legacy/'+value[len(prefix):]
    return value

for p in manifest_files:
    archive=manifest_legacy/p.name
    if not archive.exists():archive.write_text(json.dumps(old_paths(json.loads(p.read_text())),indent=2)+'\n')
report={'originals_before':{},'episodes':[]}
for p in configs:
    cfg=json.loads(p.read_text());video=Path(cfg['video']);name=p.stem
    report['originals_before'][str(video)]=hashlib.sha256(video.read_bytes()).hexdigest()
    archive=legacy/p.name
    if not archive.exists():shutil.copy2(p,archive)
    old=json.loads(archive.read_text())
    output=Path('data/processed')/name;archive_out=processed_legacy/name;archive_out.mkdir(exist_ok=True)
    for file in output.glob('*'):
        if file.is_file() and file.suffix!='.mp4' and not (archive_out/file.name).exists():shutil.copy2(file,archive_out/file.name)
    new=create_config(video,p,.30,.297)
    for key in ['object_hsv_ranges','finger_hsv_ranges','red_hsv_ranges','object_area_px','finger_area_px',
                'object_dimensions_m','object_dimensions_source','finger_workspace_margin_px','max_corner_shift_px','collection_constraint']:
        if key in old:new[key]=old[key]
    if old.get('finger_exclusion_windows_px'):
        # Rotate exclusion regions with the same display transform as the pixels.
        cap=open_video(video,'stored');width=int(cap.get(3));height=int(cap.get(4));angle=round(cap.get(cv2.CAP_PROP_ORIENTATION_META))%360;cap.release()
        import numpy as np
        mask=np.zeros((height,width),np.uint8)
        for x0,y0,x1,y1 in old['finger_exclusion_windows_px']:mask[y0:y1,x0:x1]=255
        if angle in (90,180,270):mask=cv2.rotate(mask,{90:cv2.ROTATE_90_CLOCKWISE,180:cv2.ROTATE_180,270:cv2.ROTATE_90_COUNTERCLOCKWISE}[angle])
        n,_,stats,_=cv2.connectedComponentsWithStats(mask)
        new['finger_exclusion_windows_px']=[[int(x),int(y),int(x+w),int(y+h)] for x,y,w,h,a in stats[1:]]
    if 'goal' in old:new['goal']=detect_goal_square(video,new)
    new['registration_source']='Shared user convention applied to native display axes; original files unchanged'
    p.write_text(json.dumps(new,indent=2)+'\n')
    report['episodes'].append({'id':name,'video':str(video),'calibration':str(p),'legacy_calibration':str(archive),'output':str(output)})

def process(item):
    cmd=[sys.executable,'-c','import cv2; cv2.setNumThreads(1); from humanoid_push.tracking import main; main()',
         '--video',item['video'],'--calibration',item['calibration'],'--output',item['output'],'--no-overlay']
    run=subprocess.run(cmd,capture_output=True,text=True)
    log=Path(item['output'])/'orientation_migration.log';log.write_text(run.stdout+'\n'+run.stderr)
    if run.returncode:raise RuntimeError(f"Tracking failed: {item['id']}; see {log}")
    q=json.loads((Path(item['output'])/'quality.json').read_text());print(item['id'],q['frame_size_px'],q['object_detected_frames'],'/',q['frames'],flush=True)

with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(process,report['episodes']))
for path,sha in report['originals_before'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha
report['originals_unchanged']=True
report['frame']='native display axes; user left->robot below, right->above, above->left, below->right'
Path('data/manifests/orientation_migration.json').write_text(json.dumps(report,indent=2)+'\n')
print('All source hashes unchanged; no overlay videos generated.',flush=True)
