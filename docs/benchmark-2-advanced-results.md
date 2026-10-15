# Larger-model result: lower loss, 1/9 physically valid validation successes

The user completed 2,000 GPU training epochs and all-nine validation. The residual stacked-GRU128 policy's minimum supervised validation loss occurs at **epoch 857**: joint loss **0.00261975**, normalized action MSE **0.00260147**, and 100% phase accuracy on the six saved validation teacher references. It achieves **1/9 physically valid complete episodes**. Three episodes meet placement/withdrawal completion, but two are invalidated by paddle/table contact. All nine starts remain in the denominator.

The 1,000-epoch original GRU64 policy remains the best known controller (5/9). More model capacity did not improve this measured task result. This variant also changes normalization, residual paths, dropout and compute backend, so the result is not an isolated test of hidden width alone.

## Checkpoint and inference audit

Evaluation used the correct `best.pt`, not the final epoch. Its SHA-256 matches the evaluation summary and its epoch matches the history's minimum joint validation loss. Dropout is disabled through evaluation mode. Recomputed GPU loss is 0.0026197508; CPU loss is 0.0026197515. The maximum CPU/GPU action difference on saved validation references is approximately 2.4e-7 controller units.

All nine saved action sequences were reproduced from the saved feature sequences, with maximum errors below 1e-5. This found no obvious checkpoint-selection, evaluation-mode or recurrent-inference wiring error. It does not prove that every architectural choice is suitable. See [the numerical audit](examples/benchmark2_advanced_run/loss_audit.json).

Later training shows overfitting of the demonstration distribution: training joint loss decreases from 0.001484 at the selected epoch to 0.000278 at epoch 2,000, while validation joint loss rises to 0.003203. However, the evaluation already used the earlier best checkpoint, so accidentally evaluating the last epoch does not explain the low success count.

## What failed

| Episode | Complete-task outcome | Goal dwell achieved | Tip/table contact steps | Final target distance (mm) |
|---|---|---|---:|---:|
| validation_001 | push_timeout | No | 2 | 72.25 |
| validation_002 | Success | Yes | 0 | 3.05 |
| validation_003 | push_timeout | No | 0 | 102.86 |
| validation_004 | push_timeout | No | 13 | 30.89 |
| validation_005 | Table contact | Yes | 6 | 5.38 |
| validation_006 | push_timeout | No | 0 | 13.46 |
| validation_007 | episode_timeout | No | 422 | 125.43 |
| validation_008 | Table contact | Yes | 2 | 4.39 |
| validation_009 | push_timeout | No | 0 | 29.12 |

- **002** succeeds with no table contact.
- **005 and 008** achieve placement and withdrawal, but have 6 and 2 paddle-tip/table contact steps. The physical-validity rule therefore rejects them. No threshold was relaxed to count these as successes.
- **007** predicts approach → withdrawal at 8.65 s, then returns to approach at 9.20 s and never predicts pushing. It never contacts the cube and spends 422 steps in table contact before the 30-second cap.
- **003** makes no cube contact at all and begins its predicted pushing phase only at 14.05 s.
- **001, 004, 006 and 009**, plus 003, exhaust the push budget without goal dwell. Episodes 001 and 004 also have table contact.

The supervised loss is measured on successful teacher-state sequences, including only six validation teacher references; task success is measured on all nine independently executed starting scenes. Small height/orientation errors can change contact and take the robot into states absent from these successful demonstrations. Average action MSE and teacher-state phase accuracy do not measure recovery from those deviations. Larger models can fit demonstrations more accurately without improving this robustness.

Recommended next experiment: assess the saved periodic checkpoints using closed-loop validation success, distance and physical validity, rather than assuming minimum action loss selects the best controller. Then investigate validated **training-split** perturbation/recovery examples. Avoid more capacity or epochs based only on label loss. Keep all test data out of model selection. No new training or extra test evaluation was performed during this inspection.

## Retained videos, including failures requested by the user

The user explicitly requested failure videos. All eight failed episodes are now retained, alongside the original success. Each failure video has an arm view and a robot-overhead panel (arm meshes hidden only in that panel), predicted phase, elapsed time and paddle/table-contact annotation. The original recorded actions were replayed; there was no new policy decision or parameter change. Every rendered position sample exactly matches the saved rollout, with maximum absolute error zero in this run. Every video fully decoded to the expected frame count. The title shows the original stop reason; “FAILED: completed” on 005/008 means motion completion was reached but physical validity failed because of table contact. [Replay audit](examples/benchmark2_advanced_run/failure_video_audit.json).

- [validation_001: push_timeout](examples/benchmark2_advanced_run/validation_001/failure.mp4)
- [validation_002: Success](examples/benchmark2_advanced_run/validation_002/policy.mp4)
- [validation_003: push_timeout](examples/benchmark2_advanced_run/validation_003/failure.mp4)
- [validation_004: push_timeout](examples/benchmark2_advanced_run/validation_004/failure.mp4)
- [validation_005: Table contact](examples/benchmark2_advanced_run/validation_005/failure.mp4)
- [validation_006: push_timeout](examples/benchmark2_advanced_run/validation_006/failure.mp4)
- [validation_007: episode_timeout](examples/benchmark2_advanced_run/validation_007/failure.mp4)
- [validation_008: Table contact](examples/benchmark2_advanced_run/validation_008/failure.mp4)
- [validation_009: push_timeout](examples/benchmark2_advanced_run/validation_009/failure.mp4)

Canonical local failure paths are `outputs/benchmark2_validation_advanced_gpu/validation_XXX/failure.mp4`. Public copies, metrics and all numeric rollouts are under `docs/examples/benchmark2_advanced_run/`. Training history, configuration and the selected checkpoint are retained there too. Original recordings and previous benchmark models remain unchanged.

For future requested failure rendering, use the corresponding run folder:

```bash
MUJOCO_GL=egl python scripts/render_policy_failures.py \
  --run outputs/benchmark2_validation_advanced_gpu
```

This command refuses to overwrite existing failure videos; the eight above are already rendered. It uses the reviewed validation initial scenes and verifies the saved state trajectory. No failure video should be removed in cleanup without respecting the user's retention request.
