# Dataset recording plan — 8 October 2026

**Latest batch:** clips 023–032 are processed (10/10 tracked, 3/10 validated replay successes at the new 10-second push limit). Total: 32 tracked sources, 20 validated robot rollouts. Next record `train_033`–`train_042`. See [the third batch review](training-batch-03.md); earlier updates below are historical.

**10 October update:** the first 12 clips are calibrated/tracked; 8/12 robot replays pass. Continue with `train_013`–`train_042`, preferably uploading groups of 10. Keep validation/test slots for after the training pipeline is stable. See [the batch review](training-batch-01.md); no first-batch rerecording is requested.

We are ready to collect the next batch: all four approach sides have physically replayed successfully using your fixed direction convention. This validates the current setup, not arbitrary curved trajectories or a learned policy. **The first 32 are processed. Record the final ten training clips, `train_033`–`train_042`, then upload them for review. Keep validation/test for after the training pipeline is stable.**

## Direction and placement

Every direction and offset below refers to **your original phone recording view**. Keep original files unchanged.

| Recording start side | Robot-table start side | New real clips planned |
|---|---|---:|
| Left | Below | 20 |
| Right | Above | 20 |
| Above | Left | 20 |
| Below | Right | 0: wall restriction |

The existing `goal_below1` supplies development/training data for the constrained direction. We may generate additional geometrically retargeted robot rollouts from it, validate each physically, and label them synthetic. They do not count as additional personally recorded episodes or independent held-out evidence. We can still test the policy on separately predefined simulated starts from that side.

Keep the same target cross, 3 cm square, approximately 1.7 cm die, green top, orange nail marker and **30 cm horizontal × 29.7 cm vertical** red-mark rectangle. Keep the phone stable during each clip, preferably throughout the batch. The program calibrates each clip separately; note any setup change. There is no need to measure camera height or reproduce an exact finger trajectory.

Distances describe the approximate **die centre relative to the target cross**, not your hand's entry location. Your hand may enter from whichever side is convenient, provided the orange marker is visible before contact and throughout pushing. Try not to obscure the green top. All four red marks and the goal must be unobstructed for the opening pause; brief later corner occlusion is allowed with the fixed-camera fallback, but marker loss during contact can invalidate the segment.

## First batch: 12 training clips

| Filename | Put die centre here, relative to cross |
|---|---|
| `train_001.mp4` | 6 cm left, 2 cm above |
| `train_002.mp4` | 6 cm right, 2 cm above |
| `train_003.mp4` | 6 cm above, 2 cm left |
| `train_004.mp4` | 6 cm left, 2 cm below |
| `train_005.mp4` | 6 cm right, 2 cm below |
| `train_006.mp4` | 6 cm above, 2 cm right |
| `train_007.mp4` | 9 cm left, 2 cm above |
| `train_008.mp4` | 9 cm right, 2 cm above |
| `train_009.mp4` | 9 cm above, 2 cm left |
| `train_010.mp4` | 9 cm left, 2 cm below |
| `train_011.mp4` | 9 cm right, 2 cm below |
| `train_012.mp4` | 9 cm above, 2 cm right |

Approximate placement is enough; tracking measures the actual start. Push towards the centre cross with one finger, aiming to leave the **whole die inside the square**. Straight or shallow diagonal pushes are fine. Allow natural small deviations, sliding rotation and speed differences. No clamping, lifting, rolling or deliberately elaborate curves are needed.

For each file:

1. Leave the die still for about 1 second with all red corners and the goal visible, hand clear.
2. Approach with the orange marker visible before contact.
3. Push slowly and smoothly towards the cross, roughly 2–5 seconds if comfortable. Speed guidance is flexible, not a recording deadline.
4. Briefly pause, withdraw, and leave the final die visible for about 1 second.
5. Save the original untrimmed file under the prescribed name in `data/raw/`. Do not rotate, crop or recompress it.

Keep successful and failed attempts. If you need another attempt, use `train_001_retry1.mp4`, for example, and note why. All retries inherit the source slot's split; retain the original. Tell me about slipping, loss of marker visibility or camera changes. We will distinguish capture problems, tracking problems and robot replay failures.

The first 12 have now been calibrated, tracked and physically replayed. See [the batch review](training-batch-01.md) for eight successes, four near-goal timeouts, and the decision to continue training-data collection.

## Full target: 60 new real clips

| Split | Left | Right | Above | Total | Purpose |
|---|---:|---:|---:|---:|---|
| Training | 14 | 14 | 14 | 42 | Fit the policy; refine tracking/retargeting |
| Validation | 3 | 3 | 3 | 9 | Choose model/settings |
| Test | 3 | 3 | 3 | 9 | Final held-out evaluation |

The first 12 are included in the 42 training clips. After their review, the remaining training slots add 6, 9 and 12 cm starts, side offsets up to 4 cm, a little repetition, and slow/comfortable pushes. Keep the die and finger contact comfortably inside the marked workspace, preferably at least 1.5 cm from a border. If a prescribed position does not fit your actual target placement or reach, leave it pending and tell me; keep the target fixed.

The complete, ordered schedule is [recording-schedule.csv](recording-schedule.csv). Its machine-readable version is [recording_plan.json](../data/manifests/recording_plan.json). Columns `start_dx_cm_positive_right` and `start_dy_cm_positive_down` give signed offsets in your recording view: positive dx means right; positive dy means below. The side columns also explicitly show the robot-view equivalent.

Record validation and test slots only after the training batch has established stable tracking/retargeting rules. Their approximate positions are preassigned. They are new episodes within the accessible workspace, not a test of an unseen approach direction. No manual below-side test footage is available, so we will report that coverage limitation explicitly.

Keep validation for tuning and reserve test episodes for the final frozen evaluation. Related frames, retries and all synthetic descendants stay in their source episode's split. The existing nine pilots are development data and may later supplement training; none belong to the new validation/test pool. A test processing/replay failure remains a reported failure, rather than being silently replaced.

Sixty is a practical collection target, not a guarantee of sufficient usable experts. We will decide whether more data is useful after the batch reports and first policy evaluation.

## What we will train from this

1. **Pushing-only imitation:** learn Cartesian pushing actions from physically validated human-derived robot rollouts. Approach, contact height/orientation and withdrawal remain scripted.
2. **Full-episode imitation:** include validated scripted robot approach/withdrawal as explicitly synthetic action labels. Do not describe them as motions demonstrated directly by you.
3. **Dynamics/world-model extension:** log additional state/velocity information if needed, learn action-conditioned object motion, and evaluate prediction separately from control performance.

The human videos supply motion references. Simulator/controller execution produces the robot observations and action labels. We have not trained any policy yet. See [learning-roadmap.md](learning-roadmap.md) for the benchmark boundaries and [orientation-standardisation.md](orientation-standardisation.md) for the current replay checks.
