# Fourth training batch: tracking and robot replay — 11 October 2026

**All ten videos, `train_033`–`train_042`, are calibrated and usable for tracking. This completes all 42 planned new training recordings. No rerecording is requested. Robot replay is now complete: **9/10** pass every success/physical-validity check and are imitation-training candidates.**

Original untrimmed files are unchanged, verified by SHA-256. Each opening frame supplies four red L intersections and its own independent drawn goal square/cross. The automatic goal detector worked for all ten without manual goal-mask changes. Native phone display orientation and the fixed recording-to-robot convention are unchanged: recording left/right/above/below map to robot below/above/left/right. The paper remains 30 cm horizontally × 29.7 cm vertically in the recording view.

## Results and source review

The green object was detected in every decoded frame in all ten videos. There were zero orange-marker gaps within the first-to-last visible interval and all proposed contact coordinates are finite. Missing detections outside that interval remain missing; no interpolation was used. All clips decode as 720×1280 at 30 fps.

| Clip | Recording start side | Object detected | Finger gaps | Corner fallback frames | Reviewed contact interval (s) | Human endpoint-to-cross distance (mm) |
|---|---|---:|---:|---:|---:|---:|
| train_033 | above | 253/253 | 0 | 0 | 2.07–6.00 | 1.71 |
| train_034 | left | 268/268 | 0 | 50 | 1.30–7.10 | 2.90 |
| train_035 | right | 291/291 | 0 | 0 | 2.23–7.67 | 2.07 |
| train_036 | above | 253/253 | 0 | 0 | 2.27–6.70 | 1.27 |
| train_037 | left | 265/265 | 0 | 0 | 1.63–6.30 | 2.32 |
| train_038 | right | 286/286 | 0 | 0 | 2.47–7.17 | 1.15 |
| train_039 | above | 273/273 | 0 | 74 | 1.90–7.00 | 2.84 |
| train_040 | left | 208/208 | 0 | 0 | 1.73–4.33 | 4.52 |
| train_041 | right | 208/208 | 0 | 0 | 2.80–5.13 | 2.21 |
| train_042 | above | 189/189 | 0 | 0 | 1.90–4.03 | 2.19 |

Opening calibration frames and start/middle/end contact frames were inspected. The independently detected goal is aligned with the drawn square. The final tracked object centres are 1.15–4.52 mm from the cross; this is a planar source diagnostic, not a robot success measurement or a recovered 3D footprint/orientation guarantee.

`train_034` and `train_039` use the fixed opening-frame homography for 50 and 74 frames respectively when red-corner detection is unreliable. The 15-pixel corner-shift guard remains active; this fallback requires the camera and paper to stay fixed. These events are explicit quality flags, rather than silently discarded frames. The remaining clips have no fallback.

`train_034` has the largest per-frame contact movements: approximately 3.68 mm for the object and 4.38 mm for the finger. Both tracks stay detected, so no missing data was filled. Larger finger jumps reported over whole clips occur outside the selected pushing intervals; contact-only maxima are included in the saved summary. No smoothing or fabricated robot actions were added.

Contact intervals use the existing >2 mm object-motion proposal with a four-frame lead, ending at the first sustained 0.3-second final pause with a five-frame tail, bounded to visible finger detections. Source frames were reviewed to keep approach/withdrawal out. The object has moved less than 0.41 mm from its opening median at every selected onset, so the intervals include the beginning of the push. Durations are approximately 2.13–5.80 seconds. Segments and source hashes are recorded in the manifest.

[Opening-frame calibration review](examples/training_batch_04_tracking/calibration_review.jpg) · [Contact-frame review](examples/training_batch_04_tracking/contact_review.jpg)

## Saved files and reproduction

- `data/calibration/train_033.json`–`train_042.json`: reviewed corners, goal and shared coordinate mapping.
- `data/processed/train_033/`–`train_042/`: local `tracks.csv`, `tracks.npz`, native `preview.jpg`, `quality.json` and processing log.
- `data/manifests/training_batch_04.json`: source provenance, reviewed contact segments and measured teacher expert eligibility.
- `data/samples/train_033/`–`train_042/`: public numeric source tracks, with `data/manifests/public_training_batch_04.json` for clone-reproducible replay.
- `docs/examples/training_batch_04_tracking/`: durable quality summaries, review sheets and per-clip quality reports.

To regenerate one video's tracks with its saved calibration:

```bash
uv run --locked push-track --video data/raw/train_033.mp4 \
  --calibration data/calibration/train_033.json \
  --output data/processed/train_033 --no-overlay
```

All ten were processed with the existing tracker; no implementation/dependency change was needed. Tracking overlays were skipped to avoid duplicate generated videos; native static previews are retained.

## Robot replay results

These ten were replayed with the existing recorded-object feedback teacher, unchanged 10-second limit and 0.2-second whole-cube containment dwell. No teacher parameter, calibration, contact segment or success-rule change was made. The following command reproduces the completed run:

```bash
MUJOCO_GL=egl uv run --locked python scripts/run_batch.py \
  --manifest data/manifests/public_training_batch_04.json \
  --push-controller human-object-feedback --no-video \
  --examples-output docs/examples/training_batch_04/successful_examples \
  --output outputs/training_batch_04
```

| Clip | Robot outcome | Push time (s) | Final cross distance (mm) | Whole cube inside after withdrawal |
|---|---|---:|---:|---|
| train_033 | Success | 4.00 | 3.10 | Yes |
| train_034 | Success | 5.85 | 3.45 | Yes |
| train_035 | Success | 5.25 | 3.13 | Yes |
| train_036 | Success | 4.70 | 3.44 | Yes |
| train_037 | Success | 4.80 | 4.67 | Yes |
| train_038 | Success | 4.75 | 3.99 | Yes |
| train_039 | Timeout | 10.00 | 5.17 | No |
| train_040 | Success | 2.60 | 5.73 | Yes |
| train_041 | Success | 2.30 | 3.48 | Yes |
| train_042 | Success | 2.15 | 2.59 | Yes |

**9/10 validated successes**. `train_039` reaches the 10-second limit with its centre 5.17 mm from the cross; part of the rotated cube footprint remains outside. Its state/actions remain saved as a diagnostic, but it is excluded from successful imitation experts. All ten runs are finite, stay on the table, and meet lift/pre-push-motion limits. A failed replay does not invalidate its human recording.

The full numerical outputs are under **`outputs/training_batch_04/`**, matching the naming of batches 01–03. Each episode contains `rollout.npz`, `metrics.json` and `run.log`; the root contains `summary.json` and `summary.csv`. The method is identified by `push_controller` in metrics and rollouts, rather than a folder suffix. Earlier batches 01–03 are retained finger-baseline outputs; their newer teacher versions remain under `outputs/human_object_teacher/`.

Successful videos and previews are retained for [above: 033](examples/training_batch_04/successful_examples/train_033/replay.mp4), [left: 034](examples/training_batch_04/successful_examples/train_034/replay.mp4), and [right: 035](examples/training_batch_04/successful_examples/train_035/replay.mp4). Rendered repeats also pass physics and full video-decode checks. Metrics and batch summaries are committed under `docs/examples/training_batch_04/`; full state/action arrays remain local and can be regenerated from public numeric samples.

## Training-data readiness

All 42 new training sources are tracked and robot-replayed. The fixed teacher yields **37/42 validated successes (88.1%)**: 28/32 earlier plus 9/10 here. These successful rollouts are candidate imitation data. The five failed sources (003, 009, 022, 027, 039) remain explicit diagnostics and are not successful expert labels. The original finger-only baseline remains 20/32; this batch did not add finger-only runs.

`data/manifests/human_object_teacher.json` now indexes all 42 source episodes and their measured expert eligibility. `data/manifests/training_rollout_index.json` directly lists the local rollout/metrics paths and training split. A future trainer must select `expert_eligible: true` and documented contact/dwell phases for the pushing-only benchmark. Rollouts save simulator observations before actions, cube and end-effector orientations, derived OSC action labels, executed targets, phases and human trajectories. Approach/withdrawal are scripted and belong to the separately planned full-episode benchmark. These are robot examples generated from human video by a scripted feedback teacher, not direct robot demonstrations or learned-policy results.

Next is packaging the pushing-only imitation inputs and defining/fixing the training/evaluation protocol; validation/test collection remains pending until that pipeline is stable. No policy has been trained. All 42 sources and their descendants retain the training split.
