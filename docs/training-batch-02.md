# Second training batch review — 10 October 2026

**Proceed with `train_023.mp4` through `train_032.mp4`, then upload that group for review. No rerecording of clips 013–022 is requested. Keep validation/test collection for after the training-data pipeline is stable.**

All ten new personally recorded videos calibrated and tracked successfully, with native phone display orientation and the same shared direction convention. The original videos are unchanged; their SHA-256 hashes were rechecked after processing. All remain in the training split.

## Results

The object was detected in every decoded frame across all ten clips, and there were no finger-marker detection gaps between first and last visibility. Selected contact segments have continuous finite tracks. Opening/middle/end source frames were reviewed to exclude approach and withdrawal.

| Clip | Recording side | Object detected | Calibration fallback frames | Robot target distance (mm) | Push time (s) | Replay |
|---|---|---:|---:|---:|---:|---|
| train_013 | left | 603/603 | 14 | 6.89 | 4.75 | Success |
| train_014 | right | 329/329 | 0 | 5.82 | 4.35 | Success |
| train_015 | above | 270/270 | 0 | 5.02 | 4.65 | Success |
| train_016 | left | 263/263 | 0 | 5.27 | 3.40 | Success |
| train_017 | right | 297/297 | 0 | 5.43 | 4.10 | Success |
| train_018 | above | 258/258 | 0 | 4.86 | 3.70 | Success |
| train_019 | left | 341/341 | 0 | 5.51 | 6.15 | Success |
| train_020 | right | 285/285 | 0 | 2.86 | 4.10 | Success |
| train_021 | above | 270/270 | 0 | 5.18 | 4.35 | Success |
| train_022 | left | 347/347 | 140 | 8.36 | 8.00 | Timeout |

**9/10 physical replays succeed** under the unchanged whole-cube containment criterion, 0.2-second dwell, and 8-second push limit. `train_022` times out 8.36 mm from the target centre because part of the cube footprint remains outside. Its human tracks are still usable; the failed robot rollout is not an imitation expert. All runs remain finite and on the table, within lift/pre-push-motion validity limits.

The steeper diagonal in 022 starts approximately 9.4 cm left and 6.0 cm above the target in the recording view (the scheduled secondary offset was 4 cm). Preserve this measured start rather than changing its labels or dropping it to improve the replay score. Its approximately 32° fixed paddle direction and source trajectory add useful coverage, but this run does not establish reliable steep-diagonal retargeting.

Across the two training batches, **22/22 source clips are tracked and 17/22 robot replays succeed**. These are training-data collection checks, not held-out policy scores. Five failed replay outcomes remain explicit. No policy has been trained.

## Calibration review and recording notes

`train_020`: the default gray<90 goal-outline detector found no closed square. Source inspection showed that the drawn square was clear but some strokes were lighter than that threshold. Its independent opening-frame target was calibrated from a reviewed gray<110 mask with 3×3 closing. The cross centroid uses the unclosed mask. This is saved in the calibration's goal review note. The demonstrated endpoint was not used as the target. No global tracker or success-rule change was made.

`train_013`: 1080×1920 at approximately 59.94 fps; the other clips are 720×1280 at 30 fps. Native display orientation and recorded timestamps were preserved. Different frame rates are handled before replay resamples to the existing robot control rate.

`train_013` and `train_022` use the fixed opening-frame homography for 14 and 140 frames respectively when red corners are not reliably detected. The source review showed hand occlusion with a fixed camera. All other clips retain detected calibration throughout. The 15-pixel corner-displacement guard remains active.

Contact proposals start around observed object motion (>2 mm from the opening median, four-frame lead), and end at the first sustained final-position pause (within 2 mm of final median for 0.3 seconds, five-frame tail), bounded to visible finger frames. This avoids including withdrawal because of a later isolated centroid wobble. Contact times and source review are recorded in the manifest; no missing positions are interpolated. Robot approach/height/orientation/withdrawal remain scripted; pushing references come from the selected human finger trajectory with the existing constant contact offset.

## Data and reproduction

- Reviewed calibration: `data/calibration/train_013.json` through `train_022.json`.
- Native previews, CSV/NPZ tracks, quality and logs: `data/processed/train_013/` through `train_022/`.
- Source hashes, contact times, training splits and expert eligibility: `data/manifests/training_batch_02.json`.
- Local simulation state/action rollouts and metrics: `outputs/training_batch_02/`.
- Persistent metric/quality snapshots: `docs/examples/training_batch_02/`.
- Numeric samples and clone-reproducible replay manifest: `data/samples/train_013/` through `train_022/`, `data/manifests/public_training_batch_02.json`.

```bash
# Regenerate one original's tracking with its reviewed calibration:
uv run --locked push-track --video data/raw/train_020.mp4 \
  --calibration data/calibration/train_020.json \
  --output data/processed/train_020 --no-overlay

# Reproduce all ten robot outcomes from the numeric samples:
MUJOCO_GL=egl uv run --locked python scripts/run_batch.py \
  --manifest data/manifests/public_training_batch_02.json \
  --push-timeout-s 8 --no-video --output outputs/training_batch_02
```

No tracking overlays or failed replay videos were generated, following the earlier cleanup request. Original phone files remain local and unchanged. All synthetic descendants of these episodes inherit the training split.

## Next collection

Use the next ten rows in [recording-schedule.csv](recording-schedule.csv): `train_023`–`train_032`. Keep the camera fixed during each clip and ideally across the group; show all corners and the goal during the opening pause. Keep both patches visible through pushing. The offsets are approximate **die-centre** positions in your original recording view. Natural variation is welcome; staying roughly near the listed offsets keeps the intended coverage balanced. No new below-side recording is required.
