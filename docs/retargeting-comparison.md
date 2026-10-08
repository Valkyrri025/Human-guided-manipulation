# Geometric retargeting comparison

**Orientation update:** active previews, calibrations and tracks now follow the native phone display and one fixed user convention. Original videos are unchanged. Use [the standardisation report](orientation-standardisation.md) for current validation and archive paths; earlier metrics below describe their original runs.

This is a non-learning baseline: personally recorded finger motion is adapted using initial geometry, then replayed through physical Panda contact. The cube is placed once at reset and subsequently moved only by physics. No policy or learned world model is involved.

## Fixed experiment

The [plan](../data/manifests/retargeting_comparison.json) was written before running trials. We always use `pilot_goal`, chosen before evaluation, for all three methods. The target is its independently calibrated square. Eight new simulated starts form a 3 × 3 grid with offsets −2, 0, +2 cm in each axis, excluding the centre. The recorded start is a separate control, excluded from the new-start counts. All methods get identical starts and physics, seed 7, fixed contact height, initial-state clearance approach, 8-second push timeout, and 0.2-second containment dwell.

+X is right and +Y is down in the calibrated overhead image. These are simulated offsets, not new human recordings. This first comparison covers nearby starts only and one deterministic seed; it is not held-out human-episode evaluation.

## Three methods

- **Absolute:** keep recorded table XY references unchanged.
- **Relative:** translate the contact path to the new start and rotate it by the change in start-to-target direction. Preserve recorded displacement lengths.
- **Relative-scaled:** additionally multiply recorded displacements by the ratio of new to recorded start-to-target distance. Sample timing is unchanged, so scaling also changes commanded speed.

Every method, including absolute replay, aligns the paddle to the **new** initial start-to-target direction before contact and holds it fixed while pushing. Thus absolute is an unchanged-position-path baseline with shared orientation assistance. The same scripted lowering-clearance rule uses initial cube/tool geometry in all methods; it can retreat the lowering position but does not rewrite the pushing references.

For the relative methods, let `p0` be the first recorded tool reference and `p(t)` the remaining references. The adapted path is:

```text
new_start + rotated_contact_offset + scale × rotation × (p(t) − p0)
```

The initial contact offset is rotated without scaling; it includes a correction for the square cube's support width along the new direction. Cube size, paddle size, contact height and target-square size are never scaled. The time sequence and path variations still come from the recording. This method assumes transformed motion remains effective; it does not solve contact dynamics or correct the path online. Simulator cube pose/orientation supplies termination and diagnostics, not push steering.

`retargeting.py` implements the transform; `replay.py` saves original and executed references separately in the rollout. Metrics save method, rotation, displacement scale, start offset, final containment, distance, contacts and stop reason.

## Reproduce

With processed `pilot_goal` tracks available:

```bash
uv sync --locked --python 3.12
uv run --locked python scripts/compare_retargeting.py \
  --plan data/manifests/retargeting_comparison.json \
  --output outputs/retargeting_comparison
uv run --locked python -m pytest -q tests
```

The comparison defaults to physics only. Add `--video` to render all 27 trials. The driver retains failed physical trials and exits nonzero only for processing errors. Each trial has metrics, rollout and log; aggregate CSV/JSON contain every outcome and a copy/hash of the plan. Each rollout also identifies its input tracks by SHA-256.

A single adapted trial:

```bash
uv run --locked push-replay \
  --tracks data/processed/pilot_goal/tracks.npz \
  --calibration data/calibration/pilot_goal.json --start-s 3.1 --end-s 8.2 \
  --retargeting relative-scaled --start-offset-m -0.02 -0.02 \
  --output outputs/relative_example
```

## Results

| Method | Success on new starts | Median final cross distance, all 8 trials (mm) |
|---|---:|---:|
| absolute | 2/8 | 99.63 |
| relative | 5/8 | 5.60 |
| relative-scaled | 8/8 | 5.29 |

All three recorded-start controls passed, with identical 6.19 mm final distances. They are excluded from these counts. All unsuccessful trials timed out; no processing errors occurred. Rigid adaptation fell short on the three starts 2 cm farther left. Unchanged replay succeeded on the two same-row starts but failed on all six vertical-offset starts. Scaled adaptation succeeded on all eight.

| Start | ΔX (cm) | ΔY (cm) | Absolute | Relative | Relative-scaled |
|---|---:|---:|---|---|---|
| start_01 | -2 | -2 | Timeout | Timeout | Success |
| start_02 | -2 | 0 | Success | Timeout | Success |
| start_03 | -2 | 2 | Timeout | Timeout | Success |
| start_04 | 0 | -2 | Timeout | Success | Success |
| start_05 | 0 | 2 | Timeout | Success | Success |
| start_06 | 2 | -2 | Timeout | Success | Success |
| start_07 | 2 | 0 | Success | Success | Success |
| start_08 | 2 | 2 | Timeout | Success | Success |

Results are preliminary: one personally collected demonstration, eight nearby unseen simulated starts, fixed target and one seed. No result-driven parameter tuning was performed after these trials. The full test suite passed 16 tests, including identity, motion-shape/timing preservation, unscaled contact geometry and diagonal cube support.

The successful representative video uses `start_01` (2 cm farther left and 2 cm above the recorded start), showing scaled adaptation. Its failed unchanged-path/rigid-transform videos were removed at the user's request; their metrics remain. The verified video reruns were illustrations, not extra evaluation trials. See `docs/examples/retargeting_comparison/videos/relative-scaled/`.

## Interpretation and next step

This is a useful baseline for the future imitation policy: matching these results on nearby starts is a modest test, while handling slips, perturbations or broader starts would demonstrate additional value. A successful geometric transformation does not prove that a learned policy will generalise. Do not count these transformed trials as new personally collected episodes or create an episode split by randomly dividing frames from the original pilot.

Next, build an episode-based imitation dataset from validated human-derived replay rollouts, with explicit scripted phase labels and simulator observations. Define a separate policy evaluation set before training, and retain this first comparison as a baseline result rather than repeatedly tuning on its starts. With more time, expand real demonstrations and investigate a small learned dynamics model; see [model directions](model-directions.md).

## Media cleanup

At the user's request, failed replay videos/previews and regenerable tracking overlays were deleted. Original recordings, unique successful simulation videos, tracks, numerical rollouts, failure metrics and logs remain. Successful example videos are primarily under `docs/examples/`; identical video copies in `outputs/` were removed. Run commands regenerate outputs when needed. Historical paths to removed media are not available until regenerated. See [cleanup-report.json](cleanup-report.json) for the exact deletion list and verified original hashes.
