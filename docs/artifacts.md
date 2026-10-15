# Folder guide and final inventory

Benchmark 2 is closed. Read [its short final report](benchmark-2.md) first. The selected best model is `results/benchmark2/gru64_1000/best.pt` (5/9 validation). The following is the current layout, including local files. [Exact file-by-file inventory](file-inventory.txt) lists every project file by its containing folder; Git internals, installed environment contents and regenerable interpreter/tool caches are excluded explicitly.

| Folder | Files present / purpose |
|---|---|
| Project root | `README.md`, `AGENTS.md`, `pyproject.toml`, `uv.lock`, `.gitignore`, `.gitattributes` |
| `docs/` | `benchmark-1.md`, `benchmark-2.md`, `data.md`, `recording.md`, `recording-schedule.csv`, `failure-videos.md`, `artifacts.md`, `file-inventory.txt` |
| `src/humanoid_push/` | `__init__.py`; simulation: `push_env.py`, `smoke.py`, `task_rules.py`; human processing: `tracking.py`, `retargeting.py`, `teacher.py`, `replay.py`; benchmark 1: `bc_data.py`, `bc_model.py`, `bc_train.py`, `bc_eval.py`; benchmark 2: `episode_data.py`, `episode_model.py`, `episode_train.py`, `episode_eval.py`; larger model: `advanced_model.py`, `advanced_train.py`, `advanced_eval.py` |
| `scripts/` | `check_machine.py`, `calibrate_initial_scene.py`, `run_batch.py`, `render_policy_failures.py` |
| `tests/` | `test_tracking.py`, `test_retargeting.py`, `test_replay.py`, `test_teacher.py`, `test_task_rules.py`, `test_bc.py`, `test_episode_learning.py`, `test_advanced_episode.py` |
| `data/raw/` | Original recordings: `train_001.mp4`–`train_048.mp4`, `validation_001.mp4`–`validation_009.mp4`, `test_001.mp4`–`test_009.mp4`; earlier pilot/goal recordings and `pilot_notes.json`; all 75 videos are public and unchanged; `README.md` explains their splits |
| `data/calibration/` | `train_001.json`–`train_048.json`, `validation_001.json`–`validation_009.json`, `test_001.json`–`test_009.json`, `pilot.json` |
| `data/samples/` | `README.md`; training and validation episode folders with `tracks.csv`, `tracks.npz`; new 043–048 also retain reviewed tracking `preview.jpg` and `quality.json`; original pilot numeric tracks |
| `data/initial_scenes/` | `test_001.json`–`test_009.json`: opening-only held-out scene descriptions |
| `data/robot_rollouts/train/` | `train_001/`–`train_048/`, each containing `rollout.npz` and `metrics.json`; 37/42 baseline and 3/6 additional teachers successful; failures retained, not used as experts |
| `data/robot_rollouts/validation/` | `validation_001/`–`validation_009/`, each with `rollout.npz` and `metrics.json`; six eligible offline validation references |
| `data/manifests/` | `human_object_teacher.json`, `training_rollout_index.json`, `validation_rollout_index.json`, `public_validation_batch_01.json`, `public_test_initial_scenes.json`, `tracking_quality.json`; new `augmentation_pilot.json`, `benchmark2_augmented_training_index.json`; cleanup records `cleanup_audit.json`, `benchmark2_closure_cleanup.json` |
| `data/archive/` | `development-evidence.tar.gz`: earlier numerical diagnostics and full 32-episode finger-only baseline |
| `data/processed/pilot/` | Local original-pilot smoke-test tracks, quality report, preview and orientation-migration log; `.gitkeep` at parent |
| `data/viewing/` | `.gitkeep` only; no duplicate viewing videos |
| `results/` | `README.md`: experiment index |
| `results/benchmark1/validation/` | Best model, history/provenance, summaries, all nine numerical episode evaluations and representative successful videos |
| `results/benchmark1/test/` | Frozen protocol/audit, opening review image, summaries, all nine numerical evaluations and representative successful videos |
| `results/benchmark2/gru64_200/` | Selected model/history/configuration/protocol/provenance, all nine evaluations and success examples; `time_limit_diagnostic/` stores extended-limit evidence |
| `results/benchmark2/gru64_1000/` | **Best full-episode controller**, history/configuration/protocol, all nine numerical evaluations and success examples |
| `results/benchmark2/gru64_2000/` | Longer-run selected model/history/configuration/protocol, all nine evaluations and success examples |
| `results/benchmark2/gru128_gpu/` | Larger-model checkpoint/history/configuration, preflight/loss audits, all nine evaluations, one success video and **eight failure videos** with rendering audits |
| `results/benchmark2/gru64_augmented/` | `best.pt`, `history.json`, `configuration.json`, `summary.json`, `augmentation_comparison.json`, `failure_video_audit.json`; all nine episode folders with `metrics.json`, `rollout.npz`, plus success `policy.mp4` or **eight `failure.mp4` clips** and their `failure_video.json` audits |
| `results/teacher/` | Original teacher `summary.json`, representative successful `train_001.mp4`, `train_002.mp4`, `train_006.mp4` |
| `results/teacher/augmentation/` | `summary.json`, `summary.csv`, `augmentation_audit.json`, six replay videos `train_043.mp4`–`train_048.mp4` showing both useful and unsuccessful retargeting |
| `results/benchmark2/test/` | Frozen original-model test result (4/9): `summary.json`, `audit.json`, `protocol.json`, nine episode folders with `metrics.json` and `rollout.npz`, and all four success `policy.mp4` videos. |
| `outputs/bc_dataset/` | Local baseline benchmark-1 cache: `dataset.npz`, `provenance.json` |
| `outputs/benchmark2_dataset/` | Local original benchmark-2 cache: `dataset.npz`, `provenance.json` |
| `outputs/benchmark2_augmented_dataset/` | Local augmented 40-teacher cache: `dataset.npz`, `provenance.json` |
| `outputs/checkpoints/` | Saved `last.pt` under `benchmark1/`, `gru64_200/`, `gru64_1000/`, `gru64_2000/`, `gru128_gpu/`, `gru64_augmented/`; larger-model periodic epoch checkpoints remain under `gru128_gpu/` |
| `.venv/`, `.venv-gpu/` | Local working CPU/CUDA environments, preserved and ignored by Git |
| `.git/`, `.cache/`, `.pytest_cache/`, `__pycache__/` | Git metadata or automatically regenerated tool/interpreter caches; excluded from the file inventory |

## What was cleaned

Recent completed experiments moved from `outputs/experiments/` into the canonical `results/` and `data/robot_rollouts/` folders. The augmented cache and last checkpoint moved into the existing cache/checkpoint layout. The now-empty experiment folders were removed. Twenty redundant recent tracking/run/render logs, preview PNGs and the evaluation `progress.json` were retired. Complete numerical rollouts, selected/last checkpoints, histories, raw recordings and **all sixteen retained policy-failure videos** are preserved. The recent teacher videos are retained because they document where retargeting succeeds and fails.

The close-out audit records every move and a hash-verified recovery archive outside the project. No original was permanently deleted. The earlier broader cleanup is separately recorded in `cleanup_audit.json`. These backups do not clutter the repository, and Git history is unchanged.

Frozen experiment JSON/checkpoint provenance retains the original paths used at run time; these are historical records. Active manifests and current commands use the paths above. Selected model, rollout and video bytes were verified unchanged during relocation. Prepared datasets can be rebuilt using [the data guide](data.md). No training or test evaluation was launched during close-out.
