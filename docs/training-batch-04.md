# Fourth training batch: calibration and tracking — 11 October 2026

**All ten videos, `train_033`–`train_042`, are calibrated and usable for tracking. This completes all 42 planned new training recordings. No rerecording is requested. Robot replay for this batch is still pending; these are not yet validated imitation expert rollouts.**

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
- `data/manifests/training_batch_04.json`: source provenance and reviewed contact segments; expert eligibility is null while replay is pending.
- `data/samples/train_033/`–`train_042/`: public numeric source tracks, with `data/manifests/public_training_batch_04.json` for clone-reproducible replay.
- `docs/examples/training_batch_04_tracking/`: durable quality summaries, review sheets and per-clip quality reports.

To regenerate one video's tracks with its saved calibration:

```bash
uv run --locked push-track --video data/raw/train_033.mp4 \
  --calibration data/calibration/train_033.json \
  --output data/processed/train_033 --no-overlay
```

All ten were processed with the existing tracker; no implementation/dependency change was needed. Tracking overlays were skipped to avoid duplicate generated videos; native static previews are retained.

## Next checkpoint

Run these ten through the existing recorded-object feedback teacher at the unchanged 10-second limit, validate contact/goal/physical checks, and retain successful rendered examples. No teacher parameters or success rules have been changed in this tracking checkpoint. The intended command is:

```bash
MUJOCO_GL=egl uv run --locked python scripts/run_batch.py \
  --manifest data/manifests/public_training_batch_04.json \
  --push-controller human-object-feedback --no-video \
  --examples-output docs/examples/training_batch_04/successful_examples \
  --output outputs/training_batch_04_teacher
```

Across the dataset, 42/42 new training sources are tracked. Existing teacher results remain **28/32**, with ten additional replays pending. No policy has been trained. Keep validation/test collection pending until retargeting and training-data generation are stable; all clips here and their descendants remain in the training split.
