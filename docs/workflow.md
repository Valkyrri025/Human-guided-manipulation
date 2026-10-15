# Workflow: personally recorded pushes → simulated goal task

**Orientation update:** active previews, calibrations and tracks now follow the native phone display and one fixed user convention. Original videos are unchanged. Use [the standardisation report](orientation-standardisation.md) for current validation and archive paths; earlier metrics below describe their original runs.

This is the main workflow document. Detailed evidence lives in the linked reports. Update this document when the implementation or experiment scope changes; distinguish completed results from planned work.

## 1. Task and current scope

Push a 17 mm die on a flat surface into a roughly 30 × 30 mm square; final orientation is unrestricted. Human video supplies planar motion; a simulated Panda with a rigid mounted paddle performs the push.

**Current collection scope:** all four direction pilots have replayed successfully with the shared native-display convention. New training data cover recording left, right and above. The wall-constrained below side uses the existing pilot plus explicitly labelled synthetic augmentation. All 42 planned new training clips are tracked; teacher results are 37/42 validated successes in [recording-plan.md](recording-plan.md). Validation is processed separately; reserve test for final frozen evaluation. Deliberate curved pushing and changing tool yaw during contact remain extensions.

## 2. What is done and what remains

| Stage | Status | Evidence |
|---|---|---|
| Isolated simulator, Panda motion, GPU video | Done | [README smoke commands](../README.md#run-checkpoint-1) |
| Track first human pilot | Done | [Tracking report](pilot-report.md) |
| Retarget first pilot into physical contact | Done | [Replay report](pilot-replay.md) |
| Calibrate independent square goal and replay goal pilot | Done | [Goal pilot report](goal-pilot.md) |
| Collect and validate first additional batch | Done: 3 straight + 1 diagonal, plus goal pilot | [Batch report](batch-report.md) |
| Stop on sustained square containment or push timeout | Done: 10 s limit, 0.2 s dwell | [Stopping report](stopping.md) |
| Structured new dataset | 51/60 sources tracked: training teacher 37/42; validation teacher 6/9 | [Learning roadmap](learning-roadmap.md) |
| Compare absolute/relative replay on new starts | Done: absolute 2/8, relative 5/8, scaled 8/8 | [Comparison report](retargeting-comparison.md) |
| Pushing-only imitation policy | Planned Benchmark 1; no training yet | [Learning roadmap](learning-roadmap.md) |
| Full-episode imitation including synthetic scripted labels | Planned Benchmark 2 | [Learning roadmap](learning-roadmap.md) |
| Learned dynamics predictor and optional model-based control | Planned Benchmark 3 | [Learning roadmap](learning-roadmap.md) |
| Publish public GitHub submission | Published | [GitHub](https://github.com/Valkyrri025/Human-guided-manipulation) |

Nine recordings are personally collected by the user: the initial trajectory pilot, five original goal episodes, and three new direction pilots (`goal_right1`, `goal_above1`, `goal_below1`). Collection replay numbers are tuning results. The geometric baseline additionally tests eight predefined unseen simulated starts using one recorded demonstration; this is not held-out human-episode evaluation.

## 3. Record and preserve data

Current setup: fixed overhead phone at reported 0.5×, four red L marks **30 cm horizontally × 29.7 cm vertically**, flat paper surface, green top patch on an approximately **17 mm die**, orange finger marker, black target square and centre cross.

Keep the camera, paper, marks, target and colours fixed during the next batch. Leave all calibration marks and the independent target unobstructed during the opening pause. Approach from outside the frame is allowed, but the finger marker must become visible before contact and stay visible during pushing. Use one finger; do not grip, lift or roll the die.

Save original, untrimmed videos under `data/raw/`; never overwrite an earlier episode. Save available measurements and provenance alongside them. Unknown recording times/measurements remain unknown rather than invented. Raw recordings are currently ignored by Git; public sample inclusion will be deliberate.

Existing originals:

- `pilot_push.mp4`: initial trajectory pilot; no independent drawn target.
- `pilot_goal.mp4`: independent square-target pilot.

The completed first batch is named `goal_left1.mp4`, `goal_left2.mp4`, `goal_left3.mp4`, and `goal_diag1.mp4`; it is combined with `pilot_goal.mp4`. The later right/above/below pilots validate the remaining sides. New collection follows [the active recording plan](recording-plan.md), with all 42 training sources tracked and teacher replay of `train_033.mp4` through `train_042.mp4` complete. See [the latest batch review](training-batch-04.md).

## 4. Calibrate and track

`src/humanoid_push/tracking.py` detects the red L-stroke intersections, green top centroid and orange marker centroid. A four-point homography maps pixels to paper-plane metres. Coordinates have origin at the top-left L intersection, +x right and +y down as viewed by the camera.

Red marks are re-detected per frame to account for small image movement. If unavailable, opening-frame calibration is used and flagged. Missing marker detections stay blank/NaN. No motion is invented to fill contact gaps.

The black square and centre cross are detected in the opening frame; their mapped coordinates define the independent target. It remains fixed in table coordinates when later covered by the die or hand. Inspect the magenta goal overlay and marker detections before accepting the calibration.

New-episode example:

```bash
uv run --locked push-track --video data/raw/goal_01.mp4 \
  --calibration data/calibration/goal_01.json --initialise-calibration \
  --width-m 0.30 --height-m 0.297 --detect-goal-square \
  --output data/processed/goal_01
```

For reruns, omit `--initialise-calibration` and `--detect-goal-square` to reuse the saved reviewed calibration. Every episode has its own JSON and output folder. Do not overwrite a reviewed calibration with one from another camera framing.

Outputs: `tracking_overlay.mp4`, `tracks.csv`, `tracks.npz`, `quality.json`, `preview.jpg`. Check continuous detections during contact, target location, corner fallback counts and visibly misplaced centroids. Four-corner calibration does not correct lens distortion or height-related parallax.

## 5. Retarget the human path

`src/humanoid_push/replay.py`:

1. Select a valid contact-motion segment for that episode. Do not reuse the pilot timestamps automatically.
2. Map paper coordinates to the centred simulation workspace at measured scale.
3. Estimate one constant marker-to-tool offset from human object/finger separation and contact geometry. Marker centroid is not the fingertip contact point.
4. Resample recorded finger XY at 20 Hz.
5. For a calibrated goal, rotate the paddle before contact to face the initial object-to-target direction. Keep that orientation fixed during the push.
6. Use scripted approach, lowering, contact height and withdrawal. The grip site is at 0.868 m above a table at 0.800 m; the paddle centre is 60 mm below the grip site.
7. Convert the reference and simulated grip pose into normalised Cartesian controller commands. Robosuite's OSC controller computes joint torques; MuJoCo advances contact physics.

The cube is set at reset only; its trajectory is **not** copied into the simulation or imposed frame by frame. The human object track supplies initial placement, constant offset calibration and comparison outcome. An independent goal, when available, supplies the actual target. Runtime cube pose/orientation monitors square containment and decides when to stop; it also supplies diagnostics. It does not steer the replay XY trajectory. On containment, advancing through the recorded path pauses for the success dwell; the robot then withdraws. See [the stopping rule](stopping.md).

The Panda model, gripper, controller and table come from robosuite. Our `push_env.py` creates the die, mounted paddle and task. Block density/friction are assumptions, not measurements from footage. The tool is rigidly fixed to the gripper body, not maintained by a friction grasp.

## 6. Reproduce the validated goal pilot

From the project directory:

```bash
uv sync --locked --python 3.12
uv run --locked push-track --video data/raw/pilot_goal.mp4 \
  --calibration data/calibration/pilot_goal.json --output data/processed/pilot_goal
uv run --locked push-replay --tracks data/processed/pilot_goal/tracks.npz \
  --calibration data/calibration/pilot_goal.json \
  --start-s 3.1 --end-s 8.2 --output outputs/goal_replay
uv run --locked python -m pytest -q tests
```

For another episode, substitute its paths and select its own `--start-s` / `--end-s` after inspecting tracks/video. Contact segment selection remains manual. The reviewed five-episode manifest is replayed by `scripts/run_batch.py`; use `--track` to regenerate tracking with saved calibrations. Automatic general contact detection is not implemented.

With the current stopping rule, the goal pilot stops after **4.80 s of pushing**, moves **10.56 cm**, and finishes **6.19 mm from the cross**, fully inside the square. The earlier full-reference replay moved 11.04 cm and finished 1.90 mm from the cross; it is archived in the goal-pilot report. The current test suite has 19 passing tests. Use `--termination reference` to replay the full selected segment as before.

Development failures are documented: rounded tip missed the initial endpoint; a gripper-body versus grip-site quaternion mismatch caused early contact. A flat paddle and correct site-orientation feedback resolved the pilot issues. See [replay report](pilot-replay.md).

## 7. What the replay saves

`outputs/<episode>/rollout.npz` stores aligned pre-action and post-action observations, derived normalised Cartesian actions, grip-site quaternions, timestamps, reference positions (original human-derived and executed adapted paths), phase labels, contact flags, initial cube XY and target XY. It currently does not save robot joint angles, velocities or torques.

This is a **retargeted human episode with simulator-derived robot labels**. A timestep becomes a potential observation/action training pair. The recording is not a direct robot demonstration. Scripted approach/withdrawal phases are labelled and can be excluded from planar-pushing training.

## 8. Evaluation and optional training

The first geometric comparison is complete: absolute replay 2/8, relative translation/rotation 5/8, and relative plus displacement scaling 8/8 on eight predefined new simulated starts. See [the comparison report](retargeting-comparison.md) for scope and limitations. Future policy evaluation needs its own predefined starts and episode split. Log per-trial final target distance, success, contact failures and videos. The current task rule is full projected cube containment for 0.2 s before a 10 s push timeout, plus physical validity and containment after withdrawal. Distance to the cross is diagnostic; no desired cube angle or minimum travel distance is imposed. Keep this rule identical across methods. Approach and withdrawal are outside the push clock. The historical >4 cm pilot movement requirement is only a legacy setup check.

If time permits, train a small behaviour-cloning policy from validated replay episodes. Planned inputs: robot/object/target-relative planar state; output: next planar robot command. Height, orientation selection, low-level joint control and approach/withdrawal can remain scripted. Disclose all use of simulator state.

Split by entire demonstration/episode, not random frames from the same episode. Evaluate the policy in actual closed-loop simulation on new starts, not only by prediction loss. A policy is not already present, and successful replay does not guarantee successful imitation learning. Retargeting plus honest evaluation remains a valid submission if learning adds little.

## 9. Submission

Public repository should include exact versions/commands, an intentionally packaged personally recorded sample with provenance, simulation examples, final per-trial results, assumptions, scripted components, failures, and robosuite/MuJoCo attribution. Ensure someone can reproduce the documented sample without access to private local data.

Deadline: the user reports an extension; the new date has not been supplied. The original deadline was 9 October 2026, 23:59 BST / 10 October 2026, 00:59 Europe/Zurich. The challenge PDF has not been inspected on this machine.

## First-batch update

See [the batch report](batch-report.md) for individual results, diagonal contact behaviour, a rejected lowering-contact run, and the initial-geometry clearance fix. Five goal episodes pass both the historical full-reference check and the new goal-or-timeout rule; this is not held-out evaluation. See [the updated stopping results](stopping.md). The [geometric comparison](retargeting-comparison.md) is now complete. The next checkpoint is an episode-based imitation dataset and a compact policy with separate closed-loop evaluation.

## Relation to VLA and world models

The current baseline is hand-coded retargeting, not a VLA or learned world model. See [model directions](model-directions.md) for practical policy, visual/language and dynamics-model extensions. The user reports a deadline extension, so these extensions can be considered after the baseline and imitation pipeline.

## Agreed staged expansion

See [learning-roadmap.md](learning-roadmap.md) for pushing-only imitation, full-episode imitation and dynamics-model benchmarks. The active [recording plan](recording-plan.md) covers the three accessible sides with 42 training, 9 validation and 9 test clips. The old left-only schedule is archived. Scripted approach/withdrawal labels are synthetic experts requiring validation, not directly recorded human robot demonstrations.

## Native orientation and current direction evidence

Every active calibration decodes the phone's display orientation in memory; raw files remain untouched. Paper coordinates map to robot X = centred recording-right coordinate, robot Y = negative centred recording-down coordinate. The matrix `[[1, 0], [0, -1]]` implements recording left → robot below, right → above, above → left, below → right. See [coordinate-convention.md](coordinate-convention.md).

All eight drawn-goal episodes pass physical replay with this convention. [Current metric snapshots](examples/native_validation/summary.csv) and [current four-direction videos](examples/native_directions/summary.csv) retain evidence. Earlier per-session yaw corrections and numerical results are historical; archived manifests point to legacy inputs. Use current tracks or [the prepared numeric samples](../data/samples/README.md) for subsequent dataset work.

## Repository publication

The public repository is [Human-guided-manipulation](https://github.com/Valkyrri025/Human-guided-manipulation). Code, documentation, compact trajectory samples and successful replay examples are included. Original phone recordings remain local under `data/raw/`. Future project changes can be committed locally and pushed to `origin/main`.

## Recorded-object feedback teacher update

See [the teacher report](object-trajectory-teacher.md) for the new scripted simulator-feedback method and full comparison. It follows the recorded object trajectory, while the original finger-only replay stays available. It is not a learned policy; cube feedback now steers this optional teacher. Only validated successes are expert candidates. The original source files and split assignments are unchanged.

## Artifact retention

The [folder guide](artifacts.md) lists canonical rollouts and media. Batch runs now automatically retain up to three successful rendered examples even with `--no-video`; explicitly use `--success-videos 0` only for physics-only checks. Obsolete diagnostics were consolidated before cleanup. All 42 training sources are tracked as of 11 October; next is pushing-only imitation dataset preparation.

## Validation reference checkpoint

All nine validation recordings are calibrated, tracked and teacher-replayed with unchanged settings. See [the validation review](validation-batch-01.md). Training remains 37/42; validation teacher references are 6/9 and never enter training gradients. These are reference-generation outcomes, not learned-policy performance. Test remains reserved for final frozen evaluation.

## Pushing-only learning implementation (11 October 2026)

The [behavior-cloning workflow](behavior-cloning.md) now specifies and implements causal feature extraction, train-only normalization, the bounded small MLP, explicit supervised training and closed-loop validation. Prepared data contain 3,318 training pairs from 37 successful teacher episodes and 423 validation reference pairs from six successes. Closed-loop evaluation includes all nine validation starts, without future human paths. The test files are uploaded and remain unopened. Training has not started; next run the documented training command, then assess all-nine validation task success separately from action loss.

## First learned-policy result

The user completed 200 training epochs and all-nine closed-loop validation. The epoch-143 checkpoint selected by validation action loss achieved **7/9 successes**, compared with 6/9 for the recorded-object teacher on the same starts. Mean final target distance is 6.68 mm. Episodes 003 and 009 timed out; numerical evidence and three successful rendered videos are retained. See [the complete result](bc-validation.md). Test recordings remain unopened.

## Frozen test benchmark completed

The epoch-143 pushing-only policy achieved **8/9 successes** on opening scenes extracted from the nine test recordings, with 5.44 mm mean final target distance. Only the opening 30 frames supplied starting cube positions and independent drawn-goal calibration; no test pushing trajectory was loaded. The checkpoint/task rules were frozen before test access, and code/geometry were committed before evaluation. All nine numeric rollouts plus three successful videos are retained. See [the final test report](bc-test.md). Benchmark 1 is complete; keep this frozen baseline for subsequent methods.

## Benchmark 2: joint recurrent training

The complete successful robot episodes now supply 12,938 training steps and 1,983 validation reference steps. A single GRU policy learns approach/lowering, push and withdrawal together, predicting both phase and six Cartesian controller actions. Scripted teacher phase labels supervise training but are never provided as runtime inputs. No scripted Cartesian approach, orientation, height or withdrawal command remains. The first 200-epoch run selects epoch 193 by joint supervised validation loss (99.85% validation phase accuracy on teacher states). Actual closed-loop completion is assessed separately. See [the full benchmark-2 procedure and criteria](benchmark-2.md).

The initial benchmark-2 closed-loop run completes 2/9 episodes (004, 005). Episode 008 reaches the goal but fails withdrawal; six others time out during pushing. All numerical evidence and two successful videos are retained. See [the initial result](benchmark-2-results.md). No benchmark-2 test evaluation was performed.

## Benchmark 2: longer training, unchanged model

A same-seed 1,000-epoch run exactly reproduces the original first 200 epochs, then trains 800 more. Only the epoch budget changed. Epoch 877 was selected by the same supervised validation loss and achieved **5/9 full validation successes**, up from 2/9 under unchanged rules. Newly successful episodes are 006, 007 and 008; all nine outcomes, three successful videos and both checkpoints are retained. See [the duration comparison](benchmark-2-epochs1000.md). No benchmark-2 test data were evaluated.

## Benchmark 2: 2,000-epoch extension

A further same-model duration experiment exactly reproduces the prior first 1,000 epoch records, then continues to 2,000. Epoch 1,958 has the lowest supervised validation loss (0.002821), but completes only 3/9 full validation episodes, down from 5/9 at the selected epoch-877 checkpoint. Keep that 1,000-epoch controller as the current best. No code/data/optimizer/timeout changes or test evaluation occurred. The [report](benchmark-2-epochs2000.md) records late-loss windows, all-nine outcomes, all rollouts and two successful videos.

## Larger architecture and GPU preparation

The user requested to start the next training run themselves. A separate `advanced_model` / `advanced_train` / `advanced_eval` path implements a residual two-layer GRU128 (268,373 parameters), with unchanged observation/action contracts and task loop. PyTorch 2.5.1+cu118 is installed in the isolated `.venv-gpu`, and actual-sized GPU forward/backward plus both environment test suites pass. No real training run was launched. Commands and model rationale are in [the advanced-model workflow](benchmark-2-advanced.md). `best.pt` remains minimum supervised validation loss; periodic snapshots every 100 epochs allow later documented task-based selection.

## Larger-model user run and failure retention

The user completed 2,000 GPU epochs and evaluated the selected epoch-857 checkpoint: 1/9 physically valid successes. Three episodes complete placement/withdrawal, but two have table contact. A CPU/GPU loss and saved-action reproduction audit found no obvious checkpoint or inference-mode error. The user explicitly requested failure videos; all eight are rendered from saved actions with exact position replay, decoded and retained with the successful video. See [the result and all clips](benchmark-2-advanced-results.md). No additional training/test evaluation was launched.
