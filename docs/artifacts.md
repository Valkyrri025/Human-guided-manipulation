# Folder guide

| Folder | Important contents |
|---|---|
| `src/humanoid_push/` | Simulator, tracking/retargeting and the three learning pipelines (`bc_*`, `episode_*`, `advanced_*`) |
| `data/raw/` | Original user recordings/measurements; local, ignored by Git, never modified |
| `data/calibration/`, `data/samples/` | Reviewed geometry and public numeric human tracks |
| `data/initial_scenes/` | Opening-only test setups |
| `data/robot_rollouts/train/`, `validation/` | All 51 current teacher rollouts and metrics, including failures |
| `data/manifests/` | Active source/index/split/quality metadata and cleanup audit |
| `results/benchmark1/validation/`, `test/` | Benchmark-1 checkpoint, history, all evaluation rollouts, scores and videos |
| `results/benchmark2/gru64_200/`, `gru64_1000/`, `gru64_2000/` | Original-model comparisons; 1,000-epoch checkpoint is the best controller |
| `results/benchmark2/gru128_gpu/` | Larger model, history, audits, all nine rollouts, success and eight requested failure videos |
| `results/teacher/` | Teacher summary and three direction-specific successful replay videos |
| `outputs/bc_dataset/`, `benchmark2_dataset/` | Small prepared learning caches, local and regenerable |
| `outputs/checkpoints/` | Unpublished last/periodic checkpoints retained for future selection |
| `outputs/experiments/`, `outputs/reproductions/` | Recommended locations for new runs; created when needed |
| `data/archive/development-evidence.tar.gz` | Compressed historical numerical diagnostics and complete 32-episode finger-only baseline |
| `.venv/`, `.venv-gpu/` | Working CPU/GPU environments; excluded from Git and preserved |

The repository keeps one canonical copy of published benchmark evidence. New guides replace overlapping pilot/batch/progress reports. Obsolete migration scripts, old previews and duplicate generated media are removed. Tests, current training/evaluation code, teacher data, source calibration, dependency files and benchmark records remain.

The cleanup audit records file relocations and the location of a full hash-verified pre-cleanup snapshot outside this project. Original recordings and requested failure videos must retain their hashes. Git history also preserves removed tracked documents; the cleanup does not rewrite repository history.

Frozen experiment JSON/checkpoint provenance retains original paths used at the time. Those historical path strings are not rewritten inside scientific records. Current commands and active source/index manifests use the canonical paths above. For exact historical layout use the pre-cleanup commit recorded in the cleanup audit; controller/model source and checkpoint bytes are unchanged.
