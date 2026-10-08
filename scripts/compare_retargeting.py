"""Run a predefined paired geometric comparison; retain every failure."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--plan',type=Path,default=Path('data/manifests/retargeting_comparison.json'))
parser.add_argument('--output',type=Path,default=Path('outputs/retargeting_comparison'))
parser.add_argument('--video',action='store_true',help='Render every trial; default physics only')
args=parser.parse_args()
plan=json.loads(args.plan.read_text());args.output.mkdir(parents=True,exist_ok=True)
(args.output/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
demo=next(e for e in json.loads(Path(plan['demonstration_manifest']).read_text())['episodes'] if e['id']==plan['demonstration_id'])
rows=[]
for trial in plan['starts']:
    for mode in plan['methods']:
        folder=args.output/trial['id']/mode;folder.mkdir(parents=True,exist_ok=True)
        metrics_path=folder/'metrics.json'
        if metrics_path.exists():metrics_path.unlink()
        cmd=[sys.executable,'-m','humanoid_push.replay','--tracks',demo['tracks'],'--calibration',demo['calibration'],
             '--start-s',str(demo['start_s']),'--end-s',str(demo['end_s']),'--output',str(folder),
             '--retargeting',mode,'--start-offset-m',*[str(x) for x in trial['offset_m']],
             '--push-timeout-s',str(plan['push_timeout_s']),'--goal-dwell-s',str(plan['goal_dwell_s'])]
        cmd.extend(['--tool-yaw-offset-deg',str(demo.get('tool_yaw_offset_deg',0)),
                    '--detail-camera',demo.get('detail_camera','pushview')])
        if not args.video:cmd.append('--no-video')
        run=subprocess.run(cmd,capture_output=True,text=True)
        (folder/'run.log').write_text(run.stdout+'\n'+run.stderr)
        m=json.loads(metrics_path.read_text()) if metrics_path.exists() else {}
        row={'start_id':trial['id'],'role':trial['role'],'method':mode,'dx_m':trial['offset_m'][0],
             'dy_m':trial['offset_m'][1],'success':bool(m.get('passed',False)),
             'stop_reason':m.get('stop_reason','processing_error'),'push_elapsed_s':m.get('push_elapsed_s'),
             'final_distance_mm':1000*m['final_target_distance_m'] if m else None,
             'contact_steps':m.get('tool_object_contact_steps'),'pre_push_displacement_mm':1000*m['displacement_at_push_start_m'] if m else None,
             'whole_cube_inside':m.get('final_object_fully_inside_goal'),'returncode':run.returncode,
             'metrics':str(metrics_path)}
        rows.append(row);print(json.dumps(row),flush=True)
summary={'scope':'predefined new simulated starts; one demonstration, deterministic physics; no learned policy',
         'plan_sha256':hashlib.sha256(args.plan.read_bytes()).hexdigest(),'demonstration':demo,
         'methods':{},'trials':rows}
for mode in plan['methods']:
    measured=[r for r in rows if r['method']==mode and r['role']=='unseen_start']
    distances=[r['final_distance_mm'] for r in measured if r['final_distance_mm'] is not None]
    summary['methods'][mode]={'successes':sum(r['success'] for r in measured),'total':len(measured),
                             'median_final_distance_mm':float(np.median(distances)) if distances else None}
(args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
with (args.output/'summary.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
print(json.dumps(summary['methods'],indent=2),flush=True)
if any(r['stop_reason']=='processing_error' for r in rows):raise SystemExit('Processing error: inspect retained logs')
