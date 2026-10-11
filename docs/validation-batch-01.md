# Validation batch 01 — 11 October 2026

**All nine sources (`validation_001`–`validation_009`) calibrated and tracked. The unchanged recorded-object teacher succeeds on 6/9 physical replays. All nine state/action rollouts are saved separately from training, and successful rendered examples are retained.** No rerecording or teacher tuning was performed. These are validation reference-generation results, not learned-policy scores.

## Frozen protocol and source quality

The teacher uses the existing gain 0.75, 6 mm correction cap, 12 mm approach clearance, fixed initial paddle yaw, 10-second push limit and 0.2-second whole-cube containment dwell. Tracking retains its existing colour ranges, 15-pixel corner-shift guard, native phone display orientation and recording-to-robot mapping. Per-clip four-corner/goal calibration uses the independent opening frame, not the demonstrated endpoint. All nine goal squares were detected without manual mask changes.

The protocol was recorded before replay at commit `2d046e9`; code SHA-256 hashes are in the manifest and verified unchanged after evaluation. Human contact segments were reviewed before robot replay using the same motion-onset/final-pause method as training. No source segment was changed to rescue a failed validation replay. Original untrimmed video SHA-256 hashes are verified unchanged.

| Clip | Recording side | Object detected | Finger gaps | Corner fallback frames | Contact interval (s) |
|---|---|---:|---:|---:|---:|
| validation_001 | left | 268/268 | 0 | 78 | 2.50–6.63 |
| validation_002 | right | 229/229 | 0 | 0 | 2.20–5.73 |
| validation_003 | above | 233/233 | 0 | 0 | 2.47–5.90 |
| validation_004 | left | 214/214 | 0 | 0 | 1.87–5.03 |
| validation_005 | right | 251/251 | 0 | 0 | 2.57–6.27 |
| validation_006 | above | 216/216 | 0 | 0 | 2.00–5.17 |
| validation_007 | left | 256/256 | 0 | 0 | 1.93–6.00 |
| validation_008 | right | 247/247 | 0 | 0 | 2.20–5.67 |
| validation_009 | above | 229/229 | 0 | 25 | 1.77–5.33 |

The green object is detected in every decoded frame, and there are no orange-marker gaps within the visible interval or selected contact segments. All clips are 720×1280 at 30 fps. `validation_001` and `validation_009` use the fixed opening-frame homography for 78 and 25 frames when corner detection is unreliable. These are explicit quality flags; the camera/paper must remain fixed for this fallback. Missing positions outside contact remain missing; nothing was interpolated.

The selected starts are less than 0.9 mm from their opening object medians. Source start/middle/end frames and opening calibration frames were inspected. Measured starts differ naturally from scheduled approximate offsets; the actual source positions are preserved. This is a split of independent recordings within the accessible directions, not a claim that every validation position or direction is unseen in training.

[Calibration review](examples/validation_batch_01/calibration_review.jpg) · [Contact review](examples/validation_batch_01/contact_review.jpg)

## Physical teacher results

| Clip | Outcome | Push time (s) | Final cross distance (mm) | Whole cube inside after withdrawal |
|---|---|---:|---:|---|
| validation_001 | Success | 4.20 | 3.77 | Yes |
| validation_002 | Success | 3.70 | 3.04 | Yes |
| validation_003 | Timeout | 10.00 | 4.42 | No |
| validation_004 | Success | 3.15 | 3.30 | Yes |
| validation_005 | Success | 3.65 | 4.32 | Yes |
| validation_006 | Success | 3.15 | 3.57 | Yes |
| validation_007 | Timeout | 10.00 | 6.09 | No |
| validation_008 | Success | 3.30 | 3.30 | Yes |
| validation_009 | Timeout | 10.00 | 4.78 | No |

**6/9 successful teacher references**. Failures: validation_003, validation_007, validation_009. They hit the 10-second limit with part of the cube footprint outside the square. The centre alone fitting is insufficient, especially after a diagonal push rotates the cube. Failed state/action rollouts and all source tracks remain saved; failures were not silently replaced, relabelled as successes or used to tune the teacher.

All nine runs meet finite-state, table/lift and pre-push-motion validity checks. Final footprint containment was independently recomputed from saved final cube position/orientation and the calibrated polygon. This tests data/teacher transfer; no learned imitation policy exists yet.

## Files, examples and reproduction

- `data/raw/validation_001.mp4`–`validation_009.mp4`: local unchanged originals.
- `data/calibration/validation_001.json`–`validation_009.json`: reviewed per-clip calibration/goal.
- `data/processed/validation_001/`–`validation_009/`: local CSV/NPZ tracks, quality, native preview and log.
- `outputs/validation_batch_01/`: all nine `rollout.npz`, `metrics.json`, `run.log`, plus batch summaries.
- `data/manifests/validation_batch_01.json`, `public_validation_batch_01.json`: source hashes, contact segments, frozen protocol and reference outcomes.
- `data/manifests/validation_rollout_index.json`: validation-only local rollout paths.
- `data/samples/validation_001/`–`validation_009/`: committed numeric source trajectories.
- `docs/examples/validation_batch_01/`: persistent tracking/replay evidence and rendered examples.

Successful videos: [left: 001](examples/validation_batch_01/successful_examples/validation_001/replay.mp4), [right: 002](examples/validation_batch_01/successful_examples/validation_002/replay.mp4), [above: 006](examples/validation_batch_01/successful_examples/validation_006/replay.mp4). Each rendered repeat passes the physical checks and full video decoding. No failed example video is retained.

```bash
# Recreate one video's tracking from its original with reviewed calibration:
uv run --locked push-track --video data/raw/validation_001.mp4 \
  --calibration data/calibration/validation_001.json \
  --output data/processed/validation_001 --no-overlay

# Recreate validation robot rollouts from public numeric samples:
MUJOCO_GL=egl uv run --locked python scripts/run_batch.py \
  --manifest data/manifests/public_validation_batch_01.json \
  --push-controller human-object-feedback --no-video \
  --examples-output docs/examples/validation_batch_01/successful_examples \
  --output outputs/validation_batch_01
```

## How these will be used

Training remains **37 successful candidates from 42 training sources**. Its rollout index and teacher manifest are unchanged. Validation remains **nine separate sources**, including 6 successful teacher reference rollouts. Every source and descendant keeps `split: validation` and `training_eligible: false`; none is added to training gradients or training augmentation.

Successful validation references can support imitation validation loss/model selection. Any loss using only successful teacher references must disclose the resulting subset. Later closed-loop validation should include all nine predefined source starts/targets, without providing the learned policy with their recorded future trajectories. Retain all nine for validation accounting rather than silently excluding teacher failures. World-model validation can also use valid failure trajectories while respecting the source split.

No policy has been trained. Next is preparing and training the pushing-only imitation benchmark using training episodes, with validation for model selection. Reserve the final nine test recordings/evaluation for after the policy and evaluation protocol are frozen.
