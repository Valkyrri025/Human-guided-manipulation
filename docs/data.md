# Data and reproducible workflow

The user personally collected the original phone recordings. Four red L marks calibrate a 30 cm horizontal × 29.7 cm vertical rectangle. A green marker tracks a roughly 17 mm die and an orange marker tracks the pushing finger. The independent drawn target is approximately 3 × 3 cm.

Original recordings are never rotated, trimmed or overwritten. Tracking uses native phone display orientation. In the robot overhead view, recording left → below, right → above, above → left, below → right. Robot coordinates use paper-centred `(u, v)` mapped to `(X, Y)=(u, -v)`; the robot base is on the -X side. Table calibration is planar: lens distortion and marker-height parallax are not corrected.

## Splits and labels

- **42 training sources:** all tracked and replayed; 37 successful teacher rollouts supply imitation labels.
- **9 validation sources:** 6 successful teacher references supply offline validation loss; all 9 initial scenes supply closed-loop validation.
- **9 test sources:** benchmark 1 used only the opening 30 frames to define initial scenes. No test future trajectory supplies policy input, training or checkpoint selection.
- Earlier pilots are development material, not additional independent held-out trials.

`data/raw/` publishes all 75 original personally collected videos and the measurement notes, without rotating, trimming or overwriting the originals. `data/calibration/` holds reviewed calibration; `data/samples/` holds public time-stamped object/finger tracks. `data/robot_rollouts/train/` and `validation/` contain all 51 baseline teacher state/action rollouts, including failures. Manifests identify source hashes, contact intervals and eligibility; failures are not silently relabelled as experts.

The recorded-object feedback teacher follows the human object's recorded path with bounded simulator-state correction and a rigid mounted paddle. Initial approach, fixed tool yaw/height and withdrawal are scripted. The human recordings therefore influence the training labels meaningfully, but these labels are **generated robot actions**, not direct robot demonstrations. The historical finger-only baseline achieved 20/32; the current teacher achieves 37/42 training successes. Historical numerical evidence remains in `data/archive/development-evidence.tar.gz`.

## Recreate robot labels

Raw videos are unnecessary for replay from public numeric tracks:

```bash
MUJOCO_GL=egl python scripts/run_batch.py \
  --manifest data/manifests/human_object_teacher.json \
  --push-controller human-object-feedback --no-video \
  --output outputs/reproductions/teacher_train
MUJOCO_GL=egl python scripts/run_batch.py \
  --manifest data/manifests/public_validation_batch_01.json \
  --push-controller human-object-feedback --no-video \
  --output outputs/reproductions/teacher_validation
```

These new output paths preserve the canonical teacher data. Use `--success-videos 0` for a numerical-only run. Tracking new/original video requires the source recording and its reviewed calibration:

```bash
push-track --video data/raw/train_001.mp4 \
  --calibration data/calibration/train_001.json \
  --output data/processed/train_001 --no-overlay
```

`tracking.py` keeps missing detections as missing rather than inventing positions. `data/manifests/tracking_quality.json` consolidates the 51 reviewed tracking-quality reports. Test scene extraction is opening-only via `scripts/calibrate_initial_scene.py`; current test initial scenes are already saved and must not be overwritten for tuning.

## What goes into learning

Teacher NPZ files save observations **before** each action, issued 7D OSC actions, grip-site XYZW and cube WXYZ quaternions, phases, timestamps and diagnostic human references. Training features never contain future human motion. Benchmark 1 selects push/dwell/hold steps; benchmark 2 uses full successful episodes. Training-only statistics normalize positions; validation never supplies optimizer gradients. A source and all synthetic descendants retain their split.

On a fresh checkout, prepare the small learning caches:

```bash
push-bc-prepare
python -m humanoid_push.episode_data
```

The caches already exist on this PC under `outputs/bc_dataset/` and `outputs/benchmark2_dataset/`. The full-episode preparer refuses to overwrite an existing dataset; use a new `--output` for an intentional regeneration. Current teacher manifests/indexes point to the relocated canonical data. Frozen experiment provenance retains the paths used at the time; [the folder guide](artifacts.md) explains migration/history.

## Closed augmentation comparison

Six additional training-only recordings, `train_043`–`train_048`, are calibrated and tracked. All six teacher rollouts and metrics are preserved in `data/robot_rollouts/train/`; only successful 045, 046 and 048 extend the separate augmented index to 40 experts. Baseline indexes and splits remain unchanged. The augmented policy scored 1/9 validation, so the original 5/9 benchmark-2 policy is retained. No more recording or training is planned for benchmark 2. See [final report](benchmark-2.md).

The augmented cache is local at `outputs/benchmark2_augmented_dataset/`. To regenerate it into a fresh folder from canonical public teacher data: `python -m humanoid_push.episode_data --training-index data/manifests/benchmark2_augmented_training_index.json --output outputs/reproductions/augmented_dataset`. Do not overwrite the original baseline cache.
