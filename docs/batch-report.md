# First goal-directed batch: individual replay results

**Orientation update:** active previews, calibrations and tracks now follow the native phone display and one fixed user convention. Original videos are unchanged. Use [the standardisation report](orientation-standardisation.md) for current validation and archive paths; earlier metrics below describe their original runs.

The user personally recorded and uploaded three new straight pushes and one diagonal. Together with `pilot_goal.mp4`, the collection contains five independent square-target episodes. This is a collection/tuning replay check, **not held-out evaluation or policy training**.

The task now uses goal-or-timeout stopping rather than completing every reference. See [current stopping results and commands](stopping.md). The table below preserves the earlier full-reference experiment.

## Reproduce

```bash
uv sync --locked --python 3.12
uv run --locked python scripts/run_batch.py --track --termination reference --output outputs/batch_replay
```

The reviewed episode manifest is [`data/manifests/goal_batch.json`](../data/manifests/goal_batch.json). It records source hashes, per-clip calibration and contact segments. `--track` regenerates tracks from original videos using saved calibration; omit it to replay existing tracks. `--no-video` runs physics checks without rendering. Failed replays remain in the summary; they are not dropped.

## Historical full-reference results

| Episode | Contact segment (s) | Target distance (mm) | Physical displacement (cm) | Cube fully in square | Pilot gate |
|---|---:|---:|---:|---|---|
| pilot_goal | 3.10–8.20 | 1.90 | 11.04 | Yes | Pass |
| goal_left1 | 2.63–6.00 | 1.88 | 4.84 | Yes | Pass |
| goal_left2 | 2.56–7.83 | 3.66 | 7.19 | Yes | Pass |
| goal_left3 | 2.20–9.80 | 2.51 | 15.10 | Yes | Pass |
| goal_diag1 | 2.10–8.93 | 3.97 | 11.69 | Yes | Pass |

All five passed the current pilot gate: centre inside calibrated square and within 10 mm of independent cross, finite state, on-table retention, limited lift, physical tool-object contact, negligible scripted pre-push movement and complete video decoding. Full object containment is reported separately and was true in all five.

## Diagonal result

`goal_diag1` succeeded with a **fixed paddle orientation during contact**, aligned before contact to the initial object-to-target direction (**17.05°**). The cube finished at approximately **17.19° yaw**, rotated through collision forces. There were no direct cube-pose updates after reset. The final target distance was **3.97 mm**.

This shows that one recorded diagonal transfers with initial paddle alignment. It does not show arbitrary curves, dynamic orientation adjustment, or success from unseen starts. The rotated flat face can physically turn the square die into alignment; success was not obtained by commanding its rotation.

## Tracking changes and failure retained

- All four new clips had object detections in every frame and no missing finger detections inside the visible interval. Red calibration marks remained available throughout.
- The die's red/pink side generated a fifth red component in `goal_left3`. Corner bootstrap now excludes thin red fragments; an independent synthetic regression test covers this case.
- Finger-marker detection originally stopped at the calibrated rectangle boundary. New batch calibrations allow a 90-pixel search margin around it and exclude the red corner windows. This permits approach outside the marked area without confusing orange and red markers. Old pilot JSON files retain their prior settings.
- The baseline `goal_left3` reached the target but moved the die **9.88 mm during scripted lowering**. That run is rejected, despite a good endpoint. Initial marker coordinates near the frame edge can be biased by partial visibility; the resulting tool pose must be checked for overlap.
- The corrected approach checks **initial cube/tool geometry only** and retreats the lowering position when necessary to leave 4 mm nominal clearance. It does not alter the recorded pushing XY references or apply online cube-position correction. Scripted retreat distance is saved in metrics. Pre-push displacement is measured from the observation immediately before the first human-push action.

Initial baseline: **4/5 pilot gates passed**. With the general approach-clearance fix: **5/5 passed**. The initial collection was used to discover and fix this failure, so the corrected count is a tuning result.

The failed baseline is reproducible with:

```bash
uv run --locked push-replay --tracks data/processed/goal_left3/tracks.npz \
  --calibration data/calibration/goal_left3.json --start-s 2.2 --end-s 9.8 \
  --approach recorded --termination reference --output outputs/batch_failure/goal_left3
```

This command is expected to return a nonzero exit code after saving metrics and video. Avoid treating its final yaw as a reliable orientation estimate: this rejected run produced an Euler-angle gimbal-lock warning. It is excluded from the validated training candidates.

## Inspectable artifacts

- Each accepted episode: `outputs/batch_replay/<episode>/replay.mp4`, `preview.png`, `metrics.json`, `rollout.npz`, `run.log`.
- Aggregate: `outputs/batch_replay/summary.json` and `summary.csv`.
- Rejected lowering-contact run: `outputs/batch_failure/goal_left3/metrics.json`; failed video/preview removed during requested cleanup.
- Tracking: tracks and quality JSON remain; overlays were removed and can be regenerated.
- Selected simulation examples/metrics: `docs/examples/batch_replay/`.

## Next step

The first [geometric comparison](retargeting-comparison.md) is complete using the goal pilot and eight predefined new simulated starts: absolute 2/8, relative 5/8 and relative-scaled 8/8. Next, build a small imitation policy with an episode-level split and its own predefined evaluation starts. No policy has been trained, and five successful replay episodes alone do not demonstrate generalisation.

For future recordings, leave enough image margin to see the complete orange marker before contact, particularly with starts near the left boundary. The existing near-edge episode remains documented as a data-quality caveat; the clearance fix addresses the robot approach rather than recovering unseen marker pixels.

## Media cleanup

At the user's request, failed replay videos/previews and regenerable tracking overlays were deleted. Original recordings, unique successful simulation videos, tracks, numerical rollouts, failure metrics and logs remain. Successful example videos are primarily under `docs/examples/`; identical video copies in `outputs/` were removed. Run commands regenerate outputs when needed. Historical paths to removed media are not available until regenerated. See [cleanup-report.json](cleanup-report.json) for the exact deletion list and verified original hashes.
