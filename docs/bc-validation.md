# Pushing-only behavior-cloning validation

The first learned pushing policy succeeds on **7/9 validation starts (77.8%)**, with mean final target-centre distance **6.68 mm** across all nine runs. This is validation performance; the test recordings remain unopened.

The user trained for 200 epochs on CPU. The 8–64–64–2 bounded MLP uses 3,318 state-before-action pairs from 37 successful training teachers. Normalization uses training data only. The checkpoint at epoch **143** was selected by the lowest validation action loss, 0.028495 normalized MSE, using 423 pairs from six successful validation teacher references. Final epoch 200 had higher validation loss, 0.031052. All nine validation starts were included in closed-loop evaluation, including three teacher failures.

| Episode | Learned result | Push time (s) | Final target distance (mm) |
|---|---|---:|---:|
| validation_001 | Success | 3.85 | 3.26 |
| validation_002 | Success | 4.05 | 3.36 |
| validation_003 | Timeout | 10.00 | 18.71 |
| validation_004 | Success | 4.50 | 5.96 |
| validation_005 | Success | 4.10 | 5.31 |
| validation_006 | Success | 3.95 | 4.92 |
| validation_007 | Success | 5.00 | 3.79 |
| validation_008 | Success | 4.00 | 5.00 |
| validation_009 | Timeout | 10.00 | 9.83 |

All nine rollouts have finite states/actions, stay on the table, remain below the 5 mm lift limit, and have pre-push disturbance below 2 mm. Success requires the whole cube inside the drawn square for 0.2 seconds, completion within 10 seconds of pushing, and containment after withdrawal. Orientation is unrestricted. Centre distance alone is not the success criterion.

Episodes 003 and 009 exhausted the 10-second limit without meeting the containment dwell. Their final distances are 18.71 mm and 9.83 mm; numerical metrics alone do not establish the precise contact failure cause. Their full state/action evidence remains available. Episode 007 succeeds with the policy although its teacher reference failed. On the same nine starts, the scripted recorded-object teacher achieved **6/9**, while the policy achieved **7/9**. This nine-episode comparison is descriptive; it does not establish a general improvement.

Only pushing X/Y is learned. Approach, lowering, grip height, initial goal-facing paddle orientation, dwell holding and withdrawal remain scripted. The policy receives simulator cube/end-effector state and an explicit goal, with no recorded future trajectory. Robot labels come from retargeted human recordings and a scripted simulation teacher, not direct robot demonstrations. No VLA or world model is used here.

## Inspect and reproduce

[Left-start example 001](examples/bc_validation/validation_001/policy.mp4) · [Right-start example 002](examples/bc_validation/validation_002/policy.mp4) · [Example 004](examples/bc_validation/validation_004/policy.mp4)

The public evidence folder contains [the summary and checkpoint provenance](examples/bc_validation/summary.json), [training losses](examples/bc_validation/training_history.json), the selected [checkpoint](examples/bc_validation/best.pt), all nine numeric policy rollouts/metrics and three fully decoded successful videos. Canonical local results remain in `outputs/bc_validation_run02/`; the earlier interrupted run remains preserved separately.

```bash
cd /home/zhangzhiy/git/humanoid-push
source .venv/bin/activate
MUJOCO_GL=egl push-bc-evaluate \
  --checkpoint docs/examples/bc_validation/best.pt \
  --output outputs/bc_validation_reproduction
```

Use a fresh output folder. The evaluation runs all nine episodes and automatically retains up to three successful videos. See [the learning workflow](behavior-cloning.md) for installation and training commands.

Next: freeze this benchmark's checkpoint and evaluation rules before preparing final test episodes. Any further model selection uses validation only and must be documented. The test set remains reserved; no test score is reported.
