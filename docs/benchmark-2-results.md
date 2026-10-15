# Benchmark 2: first training run and validation

The first joint full-episode policy completes **2/9 validation episodes**. It predicts approach/lowering, pushing and withdrawal together with all six Cartesian controller commands. No scripted Cartesian movement or ground-truth phase is supplied during evaluation. Benchmark 1 remains unchanged: 7/9 validation and 8/9 frozen test, with scripted approach/orientation/height/withdrawal.

## Training result

One recurrent policy was trained for 200 epochs on CPU using 37 successful full training episodes (12,938 steps). Six successful validation teacher episodes supply 1,983 reference steps for supervised checkpoint selection. The three phases are trained jointly using phase-balanced action loss and phase cross-entropy. The model's own phase predictions mix its action heads during both training and evaluation. Hidden memory resets at episode boundaries. No benchmark-2 test data were used.

Epoch **193** was selected by the predefined minimum joint validation loss: **0.007057**. Normalized action MSE is 0.006224. Phase prediction accuracy is **99.85% on saved teacher states**; per-phase accuracies are 99.72% approach, 100% pushing and 100% withdrawal. These offline measurements do not measure autonomous execution accuracy. The 27,349-parameter policy sees different states after its own errors accumulate in simulation.

## Closed-loop validation

The same nine validation starts were evaluated with full-episode criteria fixed before evaluation. [Protocol](../data/manifests/benchmark2_protocol.json) and [model/data details](benchmark-2.md).

| Episode | Complete-task outcome | Total time (s) | Final target distance (mm) | Goal dwell achieved | Tip/table contact steps |
|---|---|---:|---:|---|---:|
| validation_001 | push_timeout | 19.45 | 41.45 | No | 0 |
| validation_002 | push_timeout | 19.25 | 36.91 | No | 9 |
| validation_003 | push_timeout | 18.70 | 82.88 | No | 0 |
| validation_004 | Success | 16.90 | 7.08 | Yes | 0 |
| validation_005 | Success | 15.45 | 4.02 | Yes | 0 |
| validation_006 | push_timeout | 18.90 | 22.55 | No | 0 |
| validation_007 | push_timeout | 18.95 | 32.45 | No | 0 |
| validation_008 | episode_timeout | 30.00 | 11.66 | Yes | 0 |
| validation_009 | push_timeout | 20.05 | 85.40 | No | 19 |

Episodes **004 and 005** achieved the goal, kept the cube contained and completed learned withdrawal above the 0.948 m clearance threshold. Their approach, height, full orientation, push and withdrawal actions all came from the model. Two successful videos were retained and decoded completely: [004](examples/benchmark2/validation_004/policy.mp4), [005](examples/benchmark2/validation_005/policy.mp4). No successful above-side example exists in this run.

Episode **008** achieved goal dwell but failed complete-task success: it exhausted the 30-second episode cap, ending at only 0.918 m end-effector height, below the withdrawal threshold. Its final cube also did not satisfy the complete success condition. The other six failures exhausted the 10-second push budget without goal dwell. Episodes **002 and 009** additionally had tip/table contacts, which violate the predefined physical criteria. All nine runs remained numerically finite; this is a learned-control failure, not a numerical training failure.

## What needs improvement

At the first predicted push, pose differences from the corresponding teacher are substantial in some episodes. For example, 003 and 009 have grip-site orientation errors of approximately 75.5 and 66.2 degrees, respectively. Episode 008 illustrates that predicting withdrawal is insufficient unless the resulting physical motion actually clears the cube. These measurements support investigating orientation/contact consistency and recovery data; they do not isolate a single cause of every failure.

The existing approach/withdrawal demonstrations are scripted successful paths from one robot reset pose. They contain little coverage of the states produced by an imperfect learned approach. High phase accuracy on teacher states therefore does not establish recovery capability. Retain this initial run as an honest baseline. A next iteration should use **training-split** perturbations and validated recovery demonstrations, preserve the learned full-episode scope, and select improvements on validation. Do not relax thresholds or use the previously seen benchmark-1 test results to tune this run.

## Artifacts and commands

Local data: `outputs/benchmark2_dataset/`; training: `outputs/benchmark2_training/`; validation: `outputs/benchmark2_validation/`.

Public evidence: [selected checkpoint](examples/benchmark2/best.pt), [training history](examples/benchmark2/history.json), [configuration](examples/benchmark2/configuration.json), [summary](examples/benchmark2/summary.json), [audit](examples/benchmark2/audit.json), all nine numeric rollouts/metrics and the two successful videos. [Dataset provenance](../data/manifests/benchmark2_dataset_provenance.json) records source hashes and phase counts. All 34 regression tests pass, including streamed/batched recurrent equivalence, masked losses and independent source splits. Benchmark-1 checkpoint and frozen code hashes are unchanged.

Re-evaluate this exact policy without rerunning training:

```bash
source .venv/bin/activate
MUJOCO_GL=egl python -m humanoid_push.episode_eval \
  --checkpoint docs/examples/benchmark2/best.pt \
  --output outputs/benchmark2_validation_reproduction
```

Choose a fresh output directory. This first run establishes benchmark-2 training and an initial evaluation; it does **not** conclude benchmark 2 as solved.

## Time-limit diagnostic (15 October 2026)

The seven failed episodes were replayed with the **same checkpoint and learned controller**, increasing only the push budget from 10 to **20 s** and total cap from 30 to **60 s**. No model was retrained and no official criterion/result was overwritten. Every replay's observations/actions match the original trajectory up to its original stopping point (checked numerically to 1e-7).

**None of the seven failures was rescued.** The two original successful episodes had already finished before the original limits and were not rerun. The six original push failures again exhausted the longer push budget. Their final distances were 41.44, 36.91, 82.88, 22.55, 56.99 and 85.40 mm for episodes 001, 002, 003, 006, 007 and 009. Episode 008 again exhausted the total cap; after 60 s its end-effector height was 0.892 m, below the 0.948 m withdrawal criterion, and final distance was 15.38 mm.

Original phase/progress logs further distinguish these from merely slow successful pushes: 002 predicted withdrawal at 13.80 s without first achieving goal dwell; 003, 006 and 009 had nearly stationary cube positions near timeout; 001 and 007 moved farther from the goal over their final two seconds. 008 first achieved goal dwell, but did not maintain placement and complete clearance during withdrawal. Longer time therefore did not address the observed failure modes. This does not prove that no future time budget could ever change an outcome; it supports prioritizing alignment, contact and recovery learning over increasing limits.

The scripts supplied **teacher labels**, not runtime motion. At runtime the network must reproduce those actions from its own imperfect state trajectory. High supervised accuracy on teacher trajectories does not guarantee that capability. The retained first benchmark-2 score stays **2/9**.

[Diagnostic summary and exact settings](examples/benchmark2/time_limit_diagnostic/summary.json). All seven longer-run metrics are published beside it; full numerical rollouts remain in `outputs/benchmark2_diagnostics/time_limits_20_60/`. No failed video was rendered or retained.
