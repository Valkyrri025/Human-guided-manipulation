# Goal-or-timeout stopping

The task is to push the whole cube into the independently drawn square. There is no desired final cube orientation and no requirement to reach the centre cross. Current defaults are an **8-second simulated pushing limit** and **0.2 seconds of continuous containment**. Approach, lowering, withdrawal and final settling are outside this push clock.

## What the script does

1. Approach and lower with the existing scripted clearance check.
2. Follow the retargeted human finger XY references at 20 Hz, with fixed contact height and initial paddle orientation.
3. After each action, check all eight projected cube vertices against the calibrated goal polygon, and check the cube is at table height. This uses simulator cube pose/orientation.
4. On containment, pause advancement of the reference and hold the achieved grip position while checking the dwell. If the cube leaves, reset the dwell and resume the reference at the elapsed reference time.
5. Stop when containment lasts 0.2 seconds or pushing reaches 8 seconds. If both happen on the same control step, completed containment wins. If the recorded segment ends first, hold its final reference until goal or timeout.
6. Withdraw vertically from the achieved position and settle. Count success only if the goal stop occurred, the cube remains fully inside after withdrawal, state is finite, the cube stayed on the table with less than 5 mm lift, and scripted pre-push displacement was less than 2 mm.

Cube feedback decides termination and pausing; it does not adjust the pushing XY path towards the goal. This remains retargeting, with no trained policy. The target cross is used for initial paddle alignment and distance diagnostics. The historical `goal_tolerance_m` field is retained for the old pilot without a square; it is not a success threshold for square goals.

## Reproduce

From `humanoid-push`, with existing processed tracks:

```bash
uv sync --locked --python 3.12
uv run --locked python scripts/run_batch.py --output outputs/batch_stopping \
  --push-timeout-s 8 --goal-dwell-s 0.2
uv run --locked python -m pytest -q tests
```

Add `--track` to regenerate tracks from the original videos and reviewed calibrations. Add `--no-video` for physics only. `--termination reference` preserves full-segment replay for historical comparisons. Timeout values must be positive multiples of the 0.05-second control period.

## Measured collection results

| Episode | Stop reason | Push time (s) | Final cross distance (mm) | Whole cube in square after withdrawal |
|---|---|---:|---:|---|
| pilot_goal | goal_reached | 4.80 | 6.19 | Yes |
| goal_left1 | goal_reached | 3.15 | 5.81 | Yes |
| goal_left2 | goal_reached | 4.95 | 7.32 | Yes |
| goal_left3 | goal_reached | 7.05 | 7.36 | Yes |
| goal_diag1 | goal_reached | 6.85 | 4.88 | Yes |

**5/5 successful collection/tuning replays**, with no meaningful pre-push displacement and no tool-table contact. Stopping at containment naturally leaves the cube farther from the cross than completing the full recorded path. These results do not measure unseen-start performance.

Outputs: `outputs/batch_stopping/summary.csv`, `summary.json`, and each episode's `metrics.json`, `rollout.npz`, `replay.mp4`, `preview.png`, and log. Phases distinguish `human_push`, `goal_dwell`, `reference_hold`, and scripted motion. Metrics record stop reason, elapsed push time, timeout and dwell configuration. Selected videos and metrics are preserved under `docs/examples/stopping/`.

## Timeout and tests

```bash
uv run --locked push-replay \
  --tracks data/processed/pilot_goal/tracks.npz \
  --calibration data/calibration/pilot_goal.json --start-s 3.1 --end-s 8.2 \
  --push-timeout-s 1 --no-video --output outputs/timeout_check
```

This intentionally unfinished trial saves `stop_reason: timeout`, `push_elapsed_s: 1.0`, and `task_success: false`, then returns a nonzero exit code. Withdrawal still completes. The whole test suite passes **11 tests**, including dwell reset after a brief pass-through, timeout before dwell, simultaneous goal/timeout precedence, rotated-cube containment and rejection when only the centre fits.

## Next checkpoint

The first comparison has now completed: unchanged replay 2/8, translation/rotation 5/8, and adding scaling 8/8 on eight new nearby simulated starts. See [the comparison report](retargeting-comparison.md). Next, build an episode-based imitation dataset and evaluate a compact policy on a separate predefined set.

## Media cleanup

At the user's request, failed replay videos/previews and regenerable tracking overlays were deleted. Original recordings, unique successful simulation videos, tracks, numerical rollouts, failure metrics and logs remain. Successful example videos are primarily under `docs/examples/`; identical video copies in `outputs/` were removed. Run commands regenerate outputs when needed. Historical paths to removed media are not available until regenerated. See [cleanup-report.json](cleanup-report.json) for the exact deletion list and verified original hashes.
