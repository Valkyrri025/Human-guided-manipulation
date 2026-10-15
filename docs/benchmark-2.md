# Benchmark 2: learn approach, push and withdrawal together

One recurrent policy predicts **all movement and phase selection** from robot reset through withdrawal. The three supervised phase targets are approach (including lower/settle), push (including goal dwell), and withdraw. Ground-truth phase is never a runtime input. All XYZ and rotation commands are learned; only the closed gripper, low-level OSC, reset and task monitors remain external.

The same 37 successful full teacher episodes provide **12,938 training steps**; six successful validation references provide **1,983 offline validation steps**. Evaluation always uses all nine validation starts. Human recordings guide pushing; approach/orientation/withdrawal labels come from the scripted simulation teacher. No benchmark-2 test score exists.

## Models and measured results

| Model / epoch budget | Selected epoch | Validation joint loss | Full validation successes | Evidence |
|---|---:|---:|---:|---|
| GRU64 / 200 | 193 | 0.007057 | 2/9 | [Result](../results/benchmark2/gru64_200/summary.json) |
| **GRU64 / 1,000** | **877** | 0.003547 | **5/9** | [Best controller](../results/benchmark2/gru64_1000/best.pt) · [result](../results/benchmark2/gru64_1000/summary.json) |
| GRU64 / 2,000 | 1,958 | 0.002821 | 3/9 | [Result](../results/benchmark2/gru64_2000/summary.json) |
| Residual GRU128 / GPU / 2,000 | 857 | **0.002620** | 1/9 | [Checkpoint](../results/benchmark2/gru128_gpu/best.pt) · [result](../results/benchmark2/gru128_gpu/summary.json) |

The current best controller remains **GRU64 epoch 877**. Longer original-model runs exactly reproduce their earlier optimization-history prefixes. Data, optimizer and limits were unchanged. The larger model also changes regularization/state paths and backend, so it is not a width-only ablation. Lowest demonstration loss did not reliably select the best physical controller.

## Architecture and training

Both variants use 15 causal features: relative end-effector/cube/goal XY, end-effector/cube heights, cube heading sine/cosine, grip-site rotation represented by two matrix columns, and known-goal containment. Training statistics normalize position/height only. No future trajectory, true phase, episode identifier or reference target enters the network.

- **Original:** Linear64/ReLU → one GRU64 → phase head and three action heads, 27,349 parameters.
- **Larger:** residual encoder128 with normalization/SiLU → two GRU128 layers with 10% inter-layer dropout → current-state residual fusion → deeper heads, 268,373 parameters.

Each network's own phase probabilities mix its three six-action heads during both training and evaluation. Outputs are bounded world-frame XYZ (±0.2) and rotation-vector commands (±0.3). Hidden state resets each episode. Adam uses learning rate 0.001, batch size eight episodes, seed 7, phase-balanced normalized action MSE plus 0.2 phase cross-entropy. `best.pt` means minimum supervised validation loss, not best simulator score.

## Evaluation rules

- 30-second full-episode cap.
- 10-second push budget from first predicted push until goal dwell; predicting withdrawal early does not stop the clock.
- Whole cube inside the square for 0.2 s; no requested cube orientation.
- After goal dwell: predicted withdrawal, end-effector at least 0.948 m high, no cube contact, cube still inside, for 0.2 s.
- Finite state, cube on table, lift below 5 mm, displacement before predicted push below 2 mm, and no paddle-tip/table contact.

These criteria are stricter than benchmark 1 because approach, orientation, height and withdrawal are learned. More time did not rescue the seven initial failures when tested with 20-second pushing / 60-second total caps; [diagnostic evidence](../results/benchmark2/gru64_200/time_limit_diagnostic/summary.json).

## Larger-model diagnosis

The GPU run correctly evaluated epoch 857. Recomputed CPU/GPU losses agree (0.0026197515 / 0.0026197508); saved action sequences reproduce from saved inputs. [Audit](../results/benchmark2/gru128_gpu/loss_audit.json). This found no obvious loading or inference-mode error.

Three episodes complete placement/withdrawal (002, 005, 008), but 005 and 008 have table contact and fail physical validity. Episode 007 predicts withdrawal before pushing, returns to approach and never touches the cube. Episode 003 also makes no cube contact. Other failures time out. [All eight requested failure videos](failure-videos.md) are retained.

The model reaches 100% phase accuracy on saved teacher states while failing on its own trajectories. Successful demonstrations provide little recovery-state coverage; small height/orientation errors can alter contact. Training beyond the selected epoch further reduces training loss but worsens validation loss. Next comparisons should assess saved checkpoints by **closed-loop validation**, and investigate training-split perturbation/corrective examples. More capacity or epochs alone is not an established fix.

## Commands

See [environment setup](../README.md#environment) and [data preparation](data.md). Existing caches are ready on this PC. No training runs automatically.

Original architecture:

```bash
source .venv/bin/activate
python -m humanoid_push.episode_train --epochs 2000 \
  --output outputs/experiments/gru64_2000
MUJOCO_GL=egl python -m humanoid_push.episode_eval \
  --checkpoint results/benchmark2/gru64_1000/best.pt \
  --output outputs/reproductions/gru64_best
```

Larger architecture on the TITAN V:

```bash
source .venv-gpu/bin/activate
python -u -m humanoid_push.advanced_train --device cuda --epochs 2000 \
  --output outputs/experiments/gru128_gpu
MUJOCO_GL=egl python -m humanoid_push.advanced_eval \
  --checkpoint results/benchmark2/gru128_gpu/best.pt \
  --output outputs/reproductions/gru128_gpu
```

`advanced_train` retains snapshots every 100 epochs in addition to `best.pt` and `last.pt`; existing larger-model snapshots are in `outputs/checkpoints/gru128_gpu/`. CPU and GPU environments are separate; the CUDA wheel supports the TITAN V without changing system CUDA. See [GPU preflight](../results/benchmark2/gru128_gpu/preflight.json). The tests verify streamed and batched recurrent equivalence, causal features, bounds, gradients and checkpoint compatibility.

Use new output directories. Do not supply test data for learning/selection. Preserve historical baselines and the requested failure videos.
