# Public human-derived tracks

`train_001`–`train_042` and `validation_001`–`validation_009` contain planar object/finger coordinates extracted from personally collected videos. These are human tracks, not robot action labels. Original videos are publicly included in `data/raw/`; calibration and source hashes/contact intervals remain in `data/calibration/` and `data/manifests/human_object_teacher.json` / `public_validation_batch_01.json`.

Robot labels are in `data/robot_rollouts/`. Full workflow: [data guide](../../docs/data.md). Test uses opening-only scenes under `data/initial_scenes/`, not future motion tracks. The small original pilot is retained as a local smoke reference; earlier development numeric evidence is compressed in `data/archive/`.
