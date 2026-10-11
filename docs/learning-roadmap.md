# Staged learning roadmap and next recording batch

**Latest status (11 October):** all 42 training sources are tracked and teacher-replayed; 37/42 are validated successful training candidates. Batch 04 passes 9/10. No more training recordings are requested now. See [the fourth batch review](training-batch-04.md). Validation/test collection remains pending; earlier updates are historical.

**10 October update:** the first 12 clips are calibrated/tracked; 8/12 robot replays pass. Continue with `train_013`–`train_042`, preferably uploading groups of 10. Keep validation/test slots for after the training pipeline is stable. See [the batch review](training-batch-01.md); no first-batch rerecording is requested.

**Active collection plan:** [recording-plan.md](recording-plan.md), 60 new clips across recording left/right/above, split 42 train / 9 validation / 9 test. All 42 training sources are tracked and teacher-replayed; next is imitation input preparation. The below side uses the existing pilot and explicitly synthetic augmentation due to the wall. The old left-only roadmap/schedule are retained in `docs/archive/`.

Agreed direction: collect a broader personally recorded dataset, train a pushing-only imitation policy, extend imitation to the whole robot episode, then investigate a compact learned dynamics model. These are planned benchmarks; no learned model has been trained yet. The geometric baseline is complete and remains an independent non-learning reference.

## What the geometric baseline used

Every trial used `pilot_goal` (contact segment 3.1–8.2 s). The other four square-goal recordings were not used in that comparison. Each of three methods ran the same recorded-start control and eight new simulated starts. New-start results were absolute 2/8, relative 5/8, relative-scaled 8/8. These nearby deterministic starts were evaluated already; do not call them fresh policy test starts. See [the full report](retargeting-comparison.md).

## Benchmark 1: learn pushing only

- Source: validated robot rollouts retargeted from personally collected pushes, now including the separately disclosed [recorded-object feedback teacher](object-trajectory-teacher.md). Its simulated cube feedback generates labels; a trained goal-conditioned policy must run without a recorded future trajectory.
- Learn: planar Cartesian actions during contact/pushing, including appropriate settling near the goal. Phase selection and any dwell labels must be documented.
- Script: initial approach, lowering, contact height, initial paddle yaw, withdrawal, low-level OSC/joint control and task termination.
- Observe: simulator end-effector and cube state, plus target-relative geometry; no raw-image or language input initially.
- Evaluate: closed-loop simulated task success, final target distance, time and physical validity on predefined starts, compared with geometric replay. Report tracking/replay failures separately from policy failures.

## Benchmark 2: learn approach, push and withdrawal

- Source: the same human-derived episodes, with scripted robot approach/lowering/withdrawal retained as synthetic expert labels.
- Learn: Cartesian XYZ motion across all phases; orientation may remain scripted initially and must be disclosed. Use phase/progress information or policy memory to resolve phase ambiguity, especially when the cube is already in the square but withdrawal is unfinished.
- Script: low-level controller, reset, fixed tool definition and task success/timeout monitor. If phase transitions remain scripted, label this as phase-conditioned imitation, rather than claiming autonomous learned sequencing.
- Expand robot initial poses/approach offsets in simulation, with checked expert labels, if the original identical scripted approach offers insufficient variety. These are synthetic augmentations, not new human demonstrations.
- Evaluate: target success plus a defined withdrawal-clearance endpoint, full-episode completion time, and approach/tool-table contacts. Preserve the 10-second pushing benchmark for comparison; define a separate full-episode cap before this benchmark. The current approach alone takes about 9 simulated seconds, so a 10-second total cap would be inappropriate.

The scripts are useful teachers, not perfect guidance. Validate finite state, reachability, tool clearance, unintended pre-push cube movement and successful withdrawal. For learned approaches, movement of the cube before an externally designated push phase needs a new phase-aware validity definition; do not silently reuse the legacy scripted pre-push gate.

## Benchmark 3: learned dynamics/world-model extension

Begin with a small state-based model predicting cube motion from current cube/robot state and applied action. Log cube rotation/velocity and robot velocities if required; current rollouts save positions and end-effector quaternions but are not a complete dynamics dataset yet. Friction/mass variation is a separate controlled experiment.

Evaluate held-out one-step and multi-step prediction errors against simple baselines (no movement and constant velocity). Retain misses, slips and varying speeds as dynamics examples when observations are valid; imitation experts may exclude unsuccessful execution. A predictor alone is not a stronger control policy. If using predictions to select/correct actions, compare control success against Benchmark 1/2 and disclose the changed action-selection method. Train and test the dynamics model without mixing transitions from related episodes across splits.

A world model is a better fit for our present state/action setup than adding language to a single fixed-goal task. This is a project choice, not a requirement from the uninspected challenge PDF. A simulation-trained model learns simulation dynamics; do not claim real-world dynamics prediction without testing it on real observations.

## Recording and data split

Follow [the current dataset plan](recording-plan.md) and [the CSV schedule](recording-schedule.csv). The first 12 cover three accessible approach sides and shallow diagonal offsets. Track and physically replay every clip before proceeding. Later clips extend distance/offset/speed coverage. Keep originals and failure evidence; retries and synthetic descendants inherit their source split.

The existing nine source videos are development/tuning data and may supplement training. New validation/test clips must remain separate. Freeze tracking/retargeting settings on training data first. Predefine simulated evaluation starts before policy tuning, covering all four sides, including the constrained below side. Report real held-out episode coverage and synthetic-start performance separately.

## Documentation and evidence

Update [workflow](workflow.md) and this roadmap at each completed benchmark. Save source hashes, split assignments, contact segments, expert-validity decisions, training configurations, model checkpoints, frozen evaluation plans and per-trial failures. Robot action labels are generated by simulator execution of human-derived references, with scripted phases labelled explicitly. The user reported a deadline extension; the new deadline is unspecified.
