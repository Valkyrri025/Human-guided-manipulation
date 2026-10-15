# Larger-model failure videos

All eight failed episodes are explicitly retained at the user's request, alongside the one physical success. Each failure clip replays the original saved actions, with zero position difference from the original trajectory in the recorded audit. Clips include arm and overhead views, predicted phase, time and table contact. The overhead panel hides arm meshes for inspection only; physics is unchanged.

| Episode | What to inspect | Video |
|---|---|---|
| 001 | Push timeout; table contact | [Failure](../results/benchmark2/gru128_gpu/validation_001/failure.mp4) |
| 002 | Only fully valid success | [Success](../results/benchmark2/gru128_gpu/validation_002/policy.mp4) |
| 003 | No cube contact; delayed push | [Failure](../results/benchmark2/gru128_gpu/validation_003/failure.mp4) |
| 004 | Push timeout; table contact | [Failure](../results/benchmark2/gru128_gpu/validation_004/failure.mp4) |
| 005 | Goal and withdrawal completed; table contact invalidates | [Failure](../results/benchmark2/gru128_gpu/validation_005/failure.mp4) |
| 006 | Push timeout | [Failure](../results/benchmark2/gru128_gpu/validation_006/failure.mp4) |
| 007 | Withdrawal before pushing, return to approach, sustained table contact | [Failure](../results/benchmark2/gru128_gpu/validation_007/failure.mp4) |
| 008 | Goal and withdrawal completed; table contact invalidates | [Failure](../results/benchmark2/gru128_gpu/validation_008/failure.mp4) |
| 009 | Push timeout | [Failure](../results/benchmark2/gru128_gpu/validation_009/failure.mp4) |

The title “FAILED: completed” in 005/008 records motion completion with failed physical validity. The outcome is still failure; no criterion was relaxed. [Video audit](../results/benchmark2/gru128_gpu/failure_video_audit.json) and per-episode metrics/rollouts are beside the clips.

For a future run, render requested failures from its saved actions:

```bash
MUJOCO_GL=egl python scripts/render_policy_failures.py \
  --run outputs/experiments/YOUR_VALIDATION_RUN
```

The renderer refuses to overwrite an existing `failure.mp4`. Current reference clips are already complete and must be kept in future cleanups.
