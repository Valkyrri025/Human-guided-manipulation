# Where project files belong

As of **11 October 2026**, all 42 training videos are calibrated and tracked. All 42 have teacher replays (37 validated successes); nine validation sources are now processed separately; test remains reserved for final frozen evaluation.

## Files to keep

| Location | Purpose |
|---|---|
| `data/raw/` | Original personally recorded videos and measurements; unchanged, local, excluded from Git |
| `data/calibration/` | Reviewed per-video calibration and independent goals |
| `data/processed/` | Local extracted CSV/NPZ tracks, quality reports and useful native previews |
| `data/processed/legacy/` | Historical coordinate-frame tracks supporting archived experiments |
| `data/samples/` | Public numeric copies needed to reproduce robot replay without original videos |
| `data/viewing/` | Compatible playback copies for originals that need them; these are not replacements for the source files |
| `data/manifests/` | Provenance, selected contact segments, split assignments and expert eligibility |
| `outputs/human_object_teacher/` | All 32 current teacher state/action rollouts, including four recorded failures |
| `outputs/training_batch_01/`–`training_batch_03/` | Original finger-only training baseline rollouts and metrics |
| `outputs/training_batch_04/` | Clips 033–042 with the recorded-object teacher; rollouts, metrics and summary |
| `outputs/validation_batch_01/` | Nine validation-only teacher rollouts, metrics and summary |
| `outputs/native_replay_validation/` | Native-direction pilot validation rollouts |
| `outputs/retargeting_comparison/` | Historical geometric comparison rollouts; legacy inputs, not current policy results |
| `outputs/smoke/`, `outputs/machine.json` | Setup check and machine information |
| `docs/examples/` | Canonical published successful videos, previews and numerical evidence |
| `.venv/`, `uv.lock`, `pyproject.toml` | Working environment and reproducible dependency specification |

The public numeric copies and local processed tracks have different roles, so both remain. Most of the Python environment's size is dependencies; removing it would require reinstalling the simulator.

## Successful videos in future batches

Batch replay with `--no-video` skips rendering every episode, then automatically renders **up to three successful examples**, preferring different recording sides. Each rendered example must pass the same physical checks and video-decode check. Its full state/action rollout stays in the primary episode folder; the example folder retains only video, preview, metrics and log. Failures remain numerical diagnostics.

```bash
MUJOCO_GL=egl uv run --locked python scripts/run_batch.py \
  --manifest data/manifests/human_object_teacher.json \
  --push-controller human-object-feedback --no-video \
  --examples-output docs/examples/human_object_teacher/successful_examples \
  --output outputs/human_object_teacher
```

Set `--success-videos 0` for an explicitly physics-only check. Omit `--no-video` to render every episode. Future reviewed batches should retain their successful examples in a dedicated `docs/examples/<batch>/successful_examples/` folder for GitHub.

Current examples: [recording left](examples/human_object_teacher/successful_examples/train_001/replay.mp4), [right](examples/human_object_teacher/successful_examples/train_002/replay.mp4), [above](examples/human_object_teacher/successful_examples/train_006/replay.mp4), and [slow clip 032](examples/human_object_teacher/train_032_video/replay.mp4).

## Cleanup on 10 October

Obsolete debug folders, inspection contact sheets, duplicate development/repeat runs, identical preview copies and regenerable caches were removed. Small historical numerical diagnostics were consolidated into [one archive](archive/generated-run-evidence.json); their path keys describe the old locations. Historical report commands can regenerate deleted experiment outputs. Existing published reports and distinct successful videos remain.

The [cleanup audit](cleanup-2026-10-10.json) records removed files, sizes, retained experiment directories and hashes confirming every original source/provenance file stayed unchanged. No files in neighbouring projects were touched.

## Learned-policy benchmark 1

Validation: `outputs/bc_validation_run02/` (7/9); test: `outputs/bc_test/` (8/9). Public metrics, all nine numeric rollouts per split and three successful videos per split are retained in `docs/examples/bc_validation/` and `docs/examples/bc_test/`. The frozen checkpoint is `docs/examples/bc_validation/best.pt`. Initial test geometry and its frozen hashes are in `data/initial_scenes/` and `data/manifests/bc_test_protocol.json`. The original videos are preserved; only opening frames were decoded for test setup.
