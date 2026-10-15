# Benchmark 2: 2,000 epochs improve label loss but reduce task success

The same-model 2,000-epoch experiment selects **epoch 1,958** by the lowest supervised validation joint loss, but achieves only **3/9 complete validation episodes**, versus **5/9** for the 1,000-epoch experiment. The better closed-loop controller remains the **epoch-877 checkpoint from the 1,000-epoch run**. All three runs are retained; no benchmark-2 test evaluation was performed.

## Why extend training?

The late 1,000-epoch curve showed small, noisy gains: mean validation action MSE decreased from 0.003762 over epochs 801–900 to 0.003706 over 901–1,000 (about 1.5%), while mean joint loss was roughly flat (0.004106 versus 0.004132). The final epoch's joint loss was 0.003580, near the prior best 0.003547. This justified a bounded duration-only experiment, not a claim of a steadily declining curve or guaranteed task improvement. Model complexity was deliberately held fixed.

## Controlled comparison

Training was rerun for 2,000 total epochs from the same seed-7 initialization because existing checkpoints omit optimizer state. **The first 1,000 epoch records exactly match the preceding run.** Data, architecture, optimizer, batch size, phase weights and all other settings were unchanged. Best-checkpoint selection remained the same supervised validation criterion. Simulation retained the 10-second push / 30-second episode limits and unchanged full-episode success rules.

| Epoch budget | Selected epoch | Validation joint loss | Validation action MSE | Complete validation episodes | Mean final distance, all nine (mm) |
|---|---:|---:|---:|---:|---:|
| 200 | 193 | 0.007057 | 0.006224 | 2/9 | 36.04 |
| 1,000 | 877 | 0.003547 | 0.003380 | 5/9 | 25.28 |
| 2,000 | 1958 | 0.002821 | 0.002769 | 3/9 | 57.70 |

The selected 2,000-epoch checkpoint reduces joint validation loss by **20.5%** and normalized action MSE by **18.1%** relative to the prior selected checkpoint. Phase accuracy on the six saved validation teacher trajectories remains 100%. These offline measurements do not imply robust execution from the policy's own states.

## Was loss still decreasing?

| Epoch window | Mean training joint loss | Mean validation joint loss | Mean validation action MSE |
|---|---:|---:|---:|
| 801–1000 | 0.003015 | 0.004119 | 0.003734 |
| 1001–1200 | 0.002846 | 0.003976 | 0.003574 |
| 1201–1400 | 0.002675 | 0.003882 | 0.003470 |
| 1401–1600 | 0.002332 | 0.003539 | 0.003318 |
| 1601–1800 | 0.002153 | 0.003402 | 0.003216 |
| 1801–2000 | 0.002224 | 0.003473 | 0.003163 |
| 1901–2000 | 0.001799 | 0.003071 | 0.003023 |

Fitting continued to improve overall, with fluctuations and occasional worse windows. The best supervised checkpoint occurred near the end, so the model had not completely exhausted its ability to fit this dataset. Nevertheless, longer training did not improve the actual task. Lower average errors on recorded teacher states can miss critical orientation/contact errors in closed-loop execution. The experiment does not isolate a single cause of the regression and does not establish that a larger model would fix it.

## All-nine validation outcomes

| Episode | 1,000-epoch result | 2,000-epoch result | New final distance (mm) | Tip/table contact steps |
|---|---|---|---:|---:|
| validation_001 | push_timeout | push_timeout | 78.13 | 31 |
| validation_002 | push_timeout | push_timeout | 87.83 | 3 |
| validation_003 | push_timeout | push_timeout | 99.20 | 23 |
| validation_004 | Success | push_timeout | 20.13 | 23 |
| validation_005 | Success | Success | 5.04 | 0 |
| validation_006 | Success | push_timeout | 94.73 | 0 |
| validation_007 | Success | Success | 7.21 | 0 |
| validation_008 | Success | Success | 5.19 | 0 |
| validation_009 | push_timeout | push_timeout | 121.85 | 0 |

Episodes **005, 007 and 008** remain successful. Episodes **004 and 006** regress from success to push timeout. The six failures all exhaust the push budget without achieving goal dwell. Episodes 001, 002, 003 and 004 additionally have paddle-tip/table contacts, which independently violate the unchanged validity rules. All simulator states/actions remain finite; no numerical training failure occurred.

The frozen model still controls the entire episode, including Cartesian XYZ, full rotation commands and phase selection. No scripted approach, height, orientation or withdrawal was introduced to improve the score.

## Retained evidence and next decision

[Right-start success 005](examples/benchmark2_epochs2000/validation_005/policy.mp4) · [Left-start success 007](examples/benchmark2_epochs2000/validation_007/policy.mp4)

Two successful direction-specific videos fully decode and match rollout frame counts; there was no successful above-side trial. Public artifacts include [selected minimum-loss checkpoint](examples/benchmark2_epochs2000/best.pt), [2,000-epoch history](examples/benchmark2_epochs2000/history.json), [configuration](examples/benchmark2_epochs2000/configuration.json), [summary](examples/benchmark2_epochs2000/summary.json), [audit](examples/benchmark2_epochs2000/audit.json), all nine numeric rollouts and metrics. Experiment settings/source hashes are in [the protocol](../data/manifests/benchmark2_epochs2000_protocol.json). Canonical local outputs are `outputs/benchmark2_training_2000/` and `outputs/benchmark2_validation_2000/`; the training log remains in `outputs/benchmark2_diagnostics/epochs2000_training.log`.

Keep the 1,000-epoch/epoch-877 policy as the current best controller. Do not extend training solely because supervised loss keeps falling. Future comparisons should use closed-loop validation to assess checkpoint/model quality, and investigate training-split approach/contact perturbations and corrective demonstrations. A larger-model trial can be isolated as a separate capacity comparison; this result provides no guarantee that reducing supervised loss further will increase task success. Do not tune on the test set.

Re-evaluate the 2,000-epoch experiment's selected checkpoint:

```bash
source .venv/bin/activate
MUJOCO_GL=egl python -m humanoid_push.episode_eval \
  --checkpoint docs/examples/benchmark2_epochs2000/best.pt \
  --output outputs/benchmark2_validation_2000_reproduction
```

Use a fresh output folder. The [1,000-epoch report](benchmark-2-epochs1000.md) provides the currently better controller and its reproduction command. Runtime/training source code did not change in this experiment; source/input hashes, checkpoint selection, finite losses and bounded actions were verified.
