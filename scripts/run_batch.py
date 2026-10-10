"""Replay reviewed episode segments, retaining failed episodes in the summary."""
import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--manifest',type=Path,default=Path('data/manifests/goal_batch.json'))
parser.add_argument('--output',type=Path,default=Path('outputs/batch_baseline'))
parser.add_argument('--track',action='store_true',help='Regenerate tracks from originals using reviewed calibrations before replay')
parser.add_argument('--approach',choices=['clearance','recorded'],default='clearance')
parser.add_argument('--termination',choices=['goal-or-timeout','reference'],default='goal-or-timeout')
parser.add_argument('--push-timeout-s',type=float,default=10.)
parser.add_argument('--goal-dwell-s',type=float,default=.2)
parser.add_argument('--no-video',action='store_true')
parser.add_argument('--push-controller',choices=['finger-replay','human-object-feedback'],default='finger-replay')
args=parser.parse_args()
manifest=json.loads(args.manifest.read_text());args.output.mkdir(parents=True,exist_ok=True)
rows=[]
for item in manifest['episodes']:
    name=item['id'];folder=args.output/name;folder.mkdir(parents=True,exist_ok=True)
    cmd=[sys.executable,'-m','humanoid_push.replay','--tracks',item['tracks'],
         '--calibration',item['calibration'],'--start-s',str(item['start_s']),
         '--end-s',str(item['end_s']),'--output',str(folder),'--approach',args.approach,'--termination',args.termination,
         '--push-timeout-s',str(args.push_timeout_s),'--goal-dwell-s',str(args.goal_dwell_s)]
    cmd.extend(['--push-controller',args.push_controller])
    cmd.extend(['--tool-yaw-offset-deg',str(item.get('tool_yaw_offset_deg',0)),
                '--detail-camera',item.get('detail_camera','pushview')])
    if args.no_video:cmd.append('--no-video')
    if args.track:
        track_cmd=[sys.executable,'-m','humanoid_push.tracking','--video',item['video'],
                   '--calibration',item['calibration'],'--output',str(Path(item['tracks']).parent)]
        tracking=subprocess.run(track_cmd,capture_output=True,text=True)
        (folder/'tracking.log').write_text(tracking.stdout+'\n'+tracking.stderr)
        if tracking.returncode!=0:
            rows.append({'episode':name,'returncode':tracking.returncode,'passed':False,
                         'error':'Tracking failed; see tracking.log'})
            print(f'{name}: tracking failed',flush=True)
            continue
    # Generated metrics must belong to this run, not an older failed invocation.
    metrics_path=folder/'metrics.json'
    if metrics_path.exists():metrics_path.unlink()
    result=subprocess.run(cmd,capture_output=True,text=True)
    (folder/'run.log').write_text(result.stdout+'\n'+result.stderr)
    metrics=json.loads(metrics_path.read_text()) if metrics_path.exists() else {}
    row={'episode':name,'returncode':result.returncode,'passed':bool(metrics.get('passed',False)),
         'target_distance_mm':None if 'final_target_distance_m' not in metrics else 1000*metrics['final_target_distance_m'],
         'physical_displacement_cm':None if 'object_displacement_m' not in metrics else 100*metrics['object_displacement_m'],
         'fully_inside_goal':metrics.get('final_object_fully_inside_goal'),
         'yaw_degrees':metrics.get('push_yaw_degrees'),
         'pre_push_displacement_mm':None if 'displacement_at_push_start_m' not in metrics else 1000*metrics['displacement_at_push_start_m'],
         'final_cube_yaw_degrees':metrics.get('final_cube_yaw_degrees'),
         'stop_reason':metrics.get('stop_reason'),'push_elapsed_s':metrics.get('push_elapsed_s'),
         'metrics':str(metrics_path),'video':None if args.no_video else str(folder/'replay.mp4')}
    if not metrics:row['error']='Replay did not produce metrics; see run.log'
    rows.append(row)
    print(json.dumps(row),flush=True)
summary={'scope':'collection/tuning episode replay; not held-out policy evaluation','approach_mode':args.approach,
         'push_controller':args.push_controller,'push_timeout_s':args.push_timeout_s,
         'manifest':str(args.manifest),'passed':sum(r['passed'] for r in rows),'total':len(rows),
         'episodes':rows}
(args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
columns=['episode','passed','target_distance_mm','physical_displacement_cm','fully_inside_goal',
         'yaw_degrees','pre_push_displacement_mm','final_cube_yaw_degrees','stop_reason','push_elapsed_s','returncode']
with (args.output/'summary.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');w.writeheader();w.writerows(rows)
print(f"Batch: {summary['passed']}/{summary['total']} pilot gates passed",flush=True)
# A physical failure is a measured result; only a processing error fails the batch driver.
if any('error' in r for r in rows):raise SystemExit(1)
