# Native orientation standardisation — 8 October 2026

All nine raw video files are unchanged; their SHA-256 hashes were verified before and after processing, and again after replay validation. No original has been rotated, re-encoded or replaced. The decoder honours embedded display-rotation metadata in memory, so every active preview and track follows the phone's original displayed view. The earlier discrepancy in `goal_above1` was a decoder/calibration inconsistency, not an intentional change to the recording.

## One fixed convention

| Recording start side | Robot-table start side |
|---|---|
| Left | Below |
| Right | Above |
| Above | Left |
| Below | Right |

Recording dimensions remain **30 cm horizontal × 29.7 cm vertical** in every clip. Robot-table display dimensions are **29.7 cm horizontal × 30 cm vertical**. Centred native paper coordinates convert to robot world coordinates through X = u, Y = −v. All active calibrations use the same matrix and `user_convention_v1` frame. See [coordinate-convention.md](coordinate-convention.md).

The calibrated cube/finger trajectories and goal polygon are all transformed together. Tool/contact offsets are derived in robot metres after that conversion. Approach, height, paddle orientation and withdrawal remain scripted; pushing references still come from the tracked human finger. The existing 180° paddle-face choice for `goal_above1` remains an arm configuration choice, independent of the image convention.

## Current validation

All nine videos tracked the object in every decoded frame. The selected contact segments contain valid finger detections. All eight independently drawn-goal episodes reached the square under physical simulation, before the 8-second push timeout, using the whole-footprint test and 0.2-second dwell. The first pilot has no independently drawn square and passes only its endpoint diagnostic. These are tuning/replay results, not held-out policy performance.

| Episode | Push time (s) | Final centre-to-target distance (mm) | Result |
|---|---:|---:|---|
| pilot_goal | 4.80 | 6.01 | Whole cube inside square |
| goal_left1 | 3.15 | 5.73 | Whole cube inside square |
| goal_left2 | 4.95 | 7.00 | Whole cube inside square |
| goal_left3 | 7.05 | 6.91 | Whole cube inside square |
| goal_diag1 | 6.80 | 4.79 | Whole cube inside square |
| goal_right1 | 3.35 | 4.34 | Whole cube inside square |
| goal_above1 | 4.00 | 5.04 | Whole cube inside square |
| goal_below1 | 2.80 | 3.62 | Whole cube inside square |
| pilot | 4.25 | 18.28 | Endpoint diagnostic |

Validation also checked the initial positions for all four direction correspondences. The project tests pass: **21/21**. New tracks carry their calibration hash and display-orientation label; replay rejects mismatching labels/hashes. Fresh simulated rollouts carry the robot frame and conversion matrix.

## Active data and historical archives

- Active calibration: `data/calibration/<episode>.json`.
- Native previews/tracks: `data/processed/<episode>/preview.jpg`, `tracks.csv`, `tracks.npz`, `quality.json`.
- Current simulation labels/results: `outputs/native_replay_validation/<episode>/rollout.npz` and `metrics.json`; aggregate `summary.csv` and `summary.json`.
- Original hashes and migration record: `data/manifests/orientation_migration.json`.
- Previous calibration/tracking/manifest versions: `data/calibration/legacy/`, `data/processed/legacy/`, `data/manifests/legacy/`.

Earlier examples and reports retain their original numerical results. Their reproduction manifests in the legacy directory point to archived inputs. Use the fresh validation rollouts for subsequent dataset work; do not silently mix old and new labels. The old 2/8, 5/8, 8/8 geometric comparison has not been rerun in the new frame. No imitation policy or world model has been trained.

Tracking overlays and duplicate replay videos were not regenerated. The upright JPG previews are sufficient to inspect this correction; retained older successful replay videos remain historical examples.

## Reproduce and process new recordings

From the project directory, replay the standardised nine clips:

```bash
MUJOCO_GL=egl uv run --locked python scripts/run_batch.py \
  --manifest data/manifests/native_replay_validation.json \
  --no-video --output outputs/native_replay_validation
uv run --locked python -m pytest -q
```

To regenerate a current track, use its reviewed calibration:

```bash
uv run --locked push-track --video data/raw/goal_above1.mp4 \
  --calibration data/calibration/goal_above1.json \
  --output data/processed/goal_above1 --no-overlay
```

For a new square-target recording, save the untouched file and create a separate calibration. Display orientation and the common matrix are now the defaults:

```bash
uv run --locked push-track --video data/raw/new_goal.mp4 \
  --calibration data/calibration/new_goal.json \
  --output data/processed/new_goal --initialise-calibration \
  --detect-goal-square --width-m 0.30 --height-m 0.297 --no-overlay
```

Inspect the preview and contact detections before adding a segment to a replay manifest. Any changed calibration requires regenerated tracks. The one-time migration implementation is `scripts/standardise_orientation.py`; normal recording work uses the commands above rather than rerunning the whole migration.
