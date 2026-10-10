# Third training batch and 10-second push limit — 10 October 2026

**All ten originals, `train_023`–`train_032`, calibrated and tracked. The current push limit is 10 simulation seconds, excluding scripted approach and withdrawal. Continue with the final ten training slots, `train_033`–`train_042`; no rerecording of this batch is requested. Keep validation/test collection pending until retargeting is stable.**

The slow motions follow the recording guidance. Increasing the limit accommodates them without speeding up their recorded trajectories. Replays stop earlier when whole-cube containment lasts 0.2 seconds; the same physical-validity checks remain active. No policy is trained yet.

## Tracking and replay results

Original SHA-256 hashes were verified unchanged. Native phone display orientation and the shared direction convention are preserved. The object was detected in every decoded frame and there are no orange-marker gaps within the visible interval or selected contact segments. These detection checks establish continuity, not millimetre-level tracking accuracy.

| Clip | Recording side | Object detected | Corner fallback frames | Final centre distance (mm) | Push time (s) | Replay |
|---|---|---:|---:|---:|---:|---|
| train_023 | right | 299/299 | 0 | 8.68 | 10.00 | Timeout |
| train_024 | above | 299/299 | 0 | 6.12 | 10.00 | Timeout |
| train_025 | left | 308/308 | 0 | 7.21 | 10.00 | Timeout |
| train_026 | right | 320/320 | 0 | 2.81 | 4.90 | Success |
| train_027 | above | 320/320 | 39 | 6.74 | 10.00 | Timeout |
| train_028 | left | 268/268 | 0 | 4.35 | 5.40 | Success |
| train_029 | right | 283/283 | 0 | 7.14 | 10.00 | Timeout |
| train_030 | above | 276/276 | 0 | 5.06 | 10.00 | Timeout |
| train_031 | left | 414/414 | 2 | 4.41 | 8.10 | Success |
| train_032 | right | 409/409 | 0 | 6.60 | 8.45 | Goal reached; approach invalid |

**3/10 replays meet all success and physical-validity checks** at 10 seconds, versus **2/10** in the preserved 8-second batch. `train_031` now completes its dwell at 8.10 seconds. Six clips still finish with part of the footprint outside the square; extra endpoint holding does not correct their path. Their valid human tracks remain useful, but these robot rollouts are not imitation experts.

`train_032` reaches and remains inside the square at 8.45 seconds, but the scripted approach displaces the cube by 2.069 mm, exceeding the existing 2 mm validity limit. It is recorded as a goal-reaching but invalid replay and excluded from expert candidates. This is a retargeting/approach issue, not a reason to speed up or rerecord the human demonstration. The gate has not been relaxed. An independent repeat produced identical metrics, including the 2.069 mm approach displacement.

The five earlier failed clips (003, 006, 008, 009, 022) were also rerun with 10 seconds and remain outside the square. Earlier 17 successful replays finished before 8 seconds and remain the existing validated candidates; they were not rerun. Across the 32 new recordings, **32 track successfully and 20 currently have validated successful robot rollouts**. This is collection/tuning evidence, not held-out policy performance.

## Reviewed calibration and segments

- `train_026`: faint goal strokes did not form a closed outline under the default gray<90 detector. The independent opening-frame square was reviewed using gray<110 and 3×3 closing; the cross uses the unclosed mask. The saved calibration documents this review. The demonstrated endpoint does not define the goal.
- `train_027` and `train_031`: 39 and 2 frames respectively use the fixed opening-frame homography when corner detection is unreliable. Other clips have no corner fallback. The 15-pixel corner-shift guard remains active.
- `train_032`: an isolated pre-contact object-centroid wobble caused the automatic proposal to include human approach. Original frames were reviewed and contact onset corrected to 3.10 seconds; the segment ends at 11.133 seconds before withdrawal. Its duration is 8.033 seconds. The corrected segment is used in both the archived 8-second and current 10-second comparison.

All selected contact coordinates are finite; missing positions were not interpolated. The robot receives tracked finger references plus the existing constant marker/contact offset. Height, initial paddle orientation, approach and withdrawal remain scripted. Cube movement during pushing comes from MuJoCo contact physics.

## Reproduce and inspect

```bash
# Current 10-second limit is also the default:
MUJOCO_GL=egl uv run --locked python scripts/run_batch.py \
  --manifest data/manifests/public_training_batch_03.json \
  --push-timeout-s 10 --no-video --output outputs/training_batch_03

# Explicitly reproduce the historical limit, without overwriting current results:
MUJOCO_GL=egl uv run --locked python scripts/run_batch.py \
  --manifest data/manifests/public_training_batch_03.json \
  --push-timeout-s 8 --no-video --output outputs/training_batch_03_8s_repeat
```

Reviewed calibrations are in `data/calibration/`; numeric tracks in `data/samples/train_023/`–`train_032/`. Source provenance, contact times and expert eligibility are in `data/manifests/training_batch_03.json` and its public sample counterpart. Local original tracking outputs are in `data/processed/`; local simulation observations/actions are in `outputs/training_batch_03/`.

Committed evidence: `docs/examples/training_batch_03/`, historical `docs/examples/training_batch_03_8s/`, and `docs/examples/timeout_extension_checks_10s/`. Original recordings remain local and unchanged. No failed replay videos were generated. All descendants inherit their source training split.

## Next recording group

Follow the approximate die-centre offsets in [recording-schedule.csv](recording-schedule.csv) for `train_033`–`train_042`. Keep comfortable, smooth slow pushing; no need to rush. Show all corners and the independent square during the opening pause, keep both patches visible during contact, pause with the die fully inside, then withdraw. The simulation push clock excludes approach/withdrawal. No new below-side recording is required.
