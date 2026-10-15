# Benchmark 2: full-episode imitation — final report

**Closed on 15 October 2026.** Retain GRU64 epoch **877**, with **5/9 validation successes**. No further training or recordings are planned for this benchmark. No benchmark-2 test evaluation was performed.

## Experiments

The policy learns end-effector XYZ, orientation and approach/push/withdrawal phase together, using simulator state and a known goal. True phase and future human trajectories are not runtime inputs. Low-level OSC, reset, closed gripper and task/safety monitors remain external.

| Experiment | Selected epoch | Validation loss | Autonomous validation |
|---|---:|---:|---:|
| GRU64, 200 epochs | 193 | 0.007057 | 2/9 |
| **GRU64, 1,000 epochs** | **877** | **0.003547** | **5/9** |
| GRU64, 2,000 epochs | 1,958 | 0.002821 | 3/9 |
| Residual stacked GRU128, GPU, 2,000 epochs | 857 | 0.002620 | 1/9 |
| GRU64, 1,000 epochs, three additional teachers | 938 | 0.003348 | 1/9 |

Increasing 200 to 1,000 epochs helped. Further training, the larger model and additional data did **not** improve on 5/9. The larger model also changes regularization/backend, so this is not a width-only comparison. Augmentation changes loss weights; [recomputing with identical weights](../results/benchmark2/gru64_augmented/augmentation_comparison.json) still shows lower offline error but worse autonomous control.

Original training used **37 successful teachers / 12,938 steps**. Six new recordings—close starts, pause/resume and curves—yielded three successful robot replays: **train_045, 046 and 048**. Augmented training therefore used **40 teachers / 14,074 steps**, with validation unchanged. The other three replays failed containment or lost contact and were excluded from expert labels. Pauses transfer as waiting near the cube, not finger retreat/reapproach.

## Failures and interpretation

The augmented policy succeeds only on validation_004. Episodes 005 and 008 complete placement/withdrawal but each touches the table once; six others time out, including two with no cube contact. Checkpoint and dataset hashes were verified. An earlier extended-time diagnostic did not rescue the initial model's failures, so insufficient time is not a complete explanation.

The objective—put the cube fully inside the square—is clear, but our transfer assumptions are restrictive. A human finger changes contact patch and direction easily; our teacher uses a rigid paddle with fixed yaw and height. The 2D video does not measure force, finger deformation, height or full orientation. Some human curves consequently do not transfer faithfully to robot contact.

Human object paths guide pushing; **approach, height, orientation and withdrawal labels are scripted in simulation**. Learning these components increases control difficulty without corresponding measured human supervision. Successful teacher trajectories also contain little recovery behavior. Small execution errors change contact and move the policy away from demonstrated states. Both original and augmented models classify phases perfectly on teacher validation states, yet fail on their own trajectories.

These are plausible limitations, not an isolated causal proof. Optimization, normalization and state coverage also matter. Retargeting and full-episode learning are not inherently unsuitable, but this teacher and representation are a limited fit within our data/time budget. Lower imitation loss alone did not fix the mismatch.

## Conclusion and retained evidence

Close benchmark 2 as an exploratory comparison, preserving **5/9** as its best validation result without claiming robust generalization. Benchmark 1 remains the clearer demonstration of human-derived learned pushing: **7/9 validation, 8/9 frozen test**, with scripted supporting motion. Its simpler control task differs, and its seen test set must not guide later tuning.

[Experiment index](../results/README.md) · [additional teacher audit](../results/teacher/augmentation/augmentation_audit.json) · [failure videos](failure-videos.md) · [folder inventory](artifacts.md). All selected checkpoints, histories and nine-episode numerical evaluations are retained under `results/benchmark2/`. Exact model/optimizer settings remain in run configurations. The original model is a 27,349-parameter GRU64; the larger model has 268,373 parameters. Checkpoints were selected by supervised validation loss.

Evaluation requires whole-cube containment, safe withdrawal and no table contact, with a 10-second push cap and 30-second episode cap. Reproduce the best controller without training:

```bash
source .venv/bin/activate
MUJOCO_GL=egl python -m humanoid_push.episode_eval \
  --checkpoint results/benchmark2/gru64_1000/best.pt \
  --output outputs/reproductions/benchmark2_best
```
