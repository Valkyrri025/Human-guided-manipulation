# Project conventions

- Scope is the robot-learning project. Preserve every original recording and measurement in `data/raw/`; never rotate or overwrite them. Keep `.venv`, `.venv-gpu` and the dependency lockfile.
- Phone rectangle is 30 cm horizontal × 29.7 cm vertical; native display orientation stays unchanged. Phone left/right/above/below map to robot below/above/left/right. See `docs/data.md`.
- Keep source splits and provenance. Only eligible successful training teachers supply imitation labels. Validation never supplies gradients; no test tuning. Benchmark 1 test has been seen, benchmark 2 has no test score.
- Distinguish scripted human-object teacher labels from direct robot demonstrations, and scripted components from learned policy actions. Never substitute scripts while claiming full-episode learned control.
- Canonical benchmark evidence is under `results/`; current teacher rollouts are under `data/robot_rollouts/`. Consult `docs/artifacts.md`. Keep complete numerical current rollouts and archived finger-only baseline evidence.
- Preserve all eight explicitly requested larger-model failure videos. Keep meaningful successful examples, normally one per available recorded side, up to three. Remove duplicate media rather than keeping multiple canonical copies.
- Best full-episode controller: GRU64, 1,000-epoch run, selected epoch 877, 5/9 validation. Other preserved comparisons: 200 epochs 2/9; 2,000 epochs 3/9; residual GRU128 GPU epoch 857 1/9 (three motion completions, two invalidated by table contact). Lower offline loss is not improved task success.
- Benchmark 1 achieves 7/9 validation and 8/9 frozen test. Preserve checkpoints, protocols and controller/model source hashes. Historical records retain their original path strings; use current active manifests and the folder guide for relocated files.
- Keep documentation consolidated: README plus data, recording, benchmark-1, benchmark-2, failure-video and artifact guides. Add experiment evidence to existing guides/results rather than another overlapping progress report.
- New runs go under `outputs/experiments/` or `outputs/reproductions/` with explicit output paths. Preserve the user's trained snapshots in `outputs/checkpoints/`. Inspecting results or rendering videos does not authorize new training.
- The full verified pre-cleanup backup is recorded in `data/manifests/cleanup_audit.json`. Do not delete requested evidence or unique numerical records during future cleanup without preserving it.
