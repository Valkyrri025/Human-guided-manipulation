# Benchmark 1: learned pushing, scripted approach and withdrawal

The 8→64→64→2 MLP succeeds on **7/9 validation** and **8/9 frozen test** starts. The checkpoint at epoch **143** was selected by offline validation action loss. The test checkpoint and rules were frozen before decoding test videos; only opening scenes were used, never their pushing trajectories.

Inputs are end-effector minus cube XY, goal minus cube XY, and cube/grip-site heading sine/cosine. Outputs are two normalized world-frame OSC XY commands bounded to ±0.2, not absolute coordinates or joint angles. Robosuite's OSC converts Cartesian commands into joint torques. Height, paddle orientation, approach, containment holding and withdrawal are scripted.

Training uses 3,318 state-before-action pairs from 37 successful training teachers. Six successful validation references provide 423 pairs for validation loss. All nine validation starts count in simulator evaluation, including teacher failures. Phase selection is limited to `human_push`, `goal_dwell`, `reference_hold`.

## Results and evidence

| Split | Successes | Mean final centre distance | Failures |
|---|---:|---:|---|
| Validation | 7/9 | 6.68 mm | 003, 009: timeout |
| Frozen test | 8/9 | 5.44 mm | 003: timeout |

Success requires whole-cube containment for 0.2 s, completion within 10 s of pushing, containment after scripted withdrawal, finite state and physical-validity checks. Cube orientation is unrestricted. Centre distance alone is not success.

- [Selected checkpoint](../results/benchmark1/validation/best.pt), [history](../results/benchmark1/validation/training_history.json), [validation summary](../results/benchmark1/validation/summary.json).
- [Test summary](../results/benchmark1/test/summary.json) and [frozen protocol](../results/benchmark1/test/protocol.json).
- Test videos: [001](../results/benchmark1/test/test_001/policy.mp4), [002](../results/benchmark1/test/test_002/policy.mp4), [006](../results/benchmark1/test/test_006/policy.mp4).

All per-episode rollouts and metrics remain beside these videos. This is a simulator-state policy; no image or language model is involved.

## Commands

Prepare data as described in [the data guide](data.md). On this PC it is already prepared.

```bash
push-bc-train --help
push-bc-train --epochs 200 --output outputs/experiments/benchmark1_train
MUJOCO_GL=egl push-bc-evaluate \
  --checkpoint results/benchmark1/validation/best.pt \
  --output outputs/reproductions/benchmark1_validation
MUJOCO_GL=egl push-bc-evaluate \
  --checkpoint results/benchmark1/validation/best.pt \
  --split test --manifest data/manifests/public_test_initial_scenes.json \
  --protocol results/benchmark1/test/protocol.json \
  --output outputs/reproductions/benchmark1_test
```

Use fresh output folders. The evaluator retains up to three successful videos. Test results are already known and must not be used to tune later methods while claiming a blind test.
