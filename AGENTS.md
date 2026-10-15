# Project working conventions

- Preserve all original recordings and provenance in `data/raw/`. Do not rotate, reencode or overwrite originals.
- Keep native phone orientation and the shared direction convention. All source descendants retain their source split.
- Keep complete current teacher rollouts and original training baseline rollouts. Preserve numerical failure evidence; do not label failures as imitation experts.
- Retain rendered successful examples for every future reviewed batch, preferably one per available recording side, up to three. `scripts/run_batch.py --no-video` now does this automatically. Use `--examples-output docs/examples/<batch>/successful_examples` when preparing public evidence. Do not retain failed example videos.
- Distinguish the finger-only baseline, recorded-object feedback teacher and learned policy. The teacher is scripted and uses simulator state. The first pushing-only BC policy achieves 7/9 validation successes; the frozen first test evaluation achieves 8/9 successes. Preserve this checkpoint and protocol; disclose any future development informed by test results.
- Put inspection/debug/repeated-run numerical diagnostics in a consolidated archive before deleting redundant generated artifacts. Keep unique successful example videos, calibration/tracks, dependency lockfile and the working `.venv`.
- Follow `docs/artifacts.md` for canonical artifact locations and update the workflow/report/schedule after each reviewed batch.

- Reviewing an uploaded training batch normally includes calibration, tracking, teacher replay, saved state/action rollouts, physical validation and retained successful example videos. Treat tracking-only results as an intermediate checkpoint unless the user explicitly limits scope. Name batch outputs `outputs/training_batch_XX/`; identify the controller method in metrics/manifests rather than adding a suffix. Preserve prior method outputs and distinguish their results.

- Benchmark 2 jointly learns all three phases and six Cartesian action components with a GRU; phase labels are training targets, not runtime inputs. The first 200-epoch run completes 2/9 full validation episodes. Preserve this initial checkpoint and failure evidence; benchmark-2 test evaluation has not run. Do not claim offline phase accuracy as task success or add scripted movement while labelling it fully learned. See `docs/benchmark-2.md` and `docs/benchmark-2-results.md`.
