# Staged learning roadmap and next recording batch

**Collection update: the left-only 60-slot schedule below is paused.** The user requested starts around the target; see [direction pilots](direction-pilots.md). It is retained as historical planning, not instructions to collect now.
Agreed direction: collect a broader personally recorded dataset, train a pushing-only imitation policy, extend imitation to the whole robot episode, then investigate a compact learned dynamics model. These are planned benchmarks; no learned model has been trained yet. The geometric baseline is complete and remains an independent non-learning reference.

## What the geometric baseline used

Every trial used `pilot_goal` (contact segment 3.1–8.2 s). The other four square-goal recordings were not used in that comparison. Each of three methods ran the same recorded-start control and eight new simulated starts. New-start results were absolute 2/8, relative 5/8, relative-scaled 8/8. These nearby deterministic starts were evaluated already; do not call them fresh policy test starts. See [the full report](retargeting-comparison.md).

## Benchmark 1: learn pushing only

- Source: validated robot rollouts retargeted from personally collected pushes.
- Learn: planar Cartesian actions during contact/pushing, including appropriate settling near the goal. Phase selection and any dwell labels must be documented.
- Script: initial approach, lowering, contact height, initial paddle yaw, withdrawal, low-level OSC/joint control and task termination.
- Observe: simulator end-effector and cube state, plus target-relative geometry; no raw-image or language input initially.
- Evaluate: closed-loop simulated task success, final target distance, time and physical validity on predefined starts, compared with geometric replay. Report tracking/replay failures separately from policy failures.

## Benchmark 2: learn approach, push and withdrawal

- Source: the same human-derived episodes, with scripted robot approach/lowering/withdrawal retained as synthetic expert labels.
- Learn: Cartesian XYZ motion across all phases; orientation may remain scripted initially and must be disclosed. Use phase/progress information or policy memory to resolve phase ambiguity, especially when the cube is already in the square but withdrawal is unfinished.
- Script: low-level controller, reset, fixed tool definition and task success/timeout monitor. If phase transitions remain scripted, label this as phase-conditioned imitation, rather than claiming autonomous learned sequencing.
- Expand robot initial poses/approach offsets in simulation, with checked expert labels, if the original identical scripted approach offers insufficient variety. These are synthetic augmentations, not new human demonstrations.
- Evaluate: target success plus a defined withdrawal-clearance endpoint, full-episode completion time, and approach/tool-table contacts. Preserve the 8-second pushing benchmark for comparison; define a separate full-episode cap before this benchmark. The current approach alone takes about 9 simulated seconds, so an 8-second total cap would be inappropriate.

The scripts are useful teachers, not perfect guidance. Validate finite state, reachability, tool clearance, unintended pre-push cube movement and successful withdrawal. For learned approaches, movement of the cube before an externally designated push phase needs a new phase-aware validity definition; do not silently reuse the legacy scripted pre-push gate.

## Benchmark 3: learned dynamics/world-model extension

Begin with a small state-based model predicting cube motion from current cube/robot state and applied action. Log cube rotation/velocity and robot velocities if required; current rollouts save positions and end-effector quaternions but are not a complete dynamics dataset yet. Friction/mass variation is a separate controlled experiment.

Evaluate held-out one-step and multi-step prediction errors against simple baselines (no movement and constant velocity). Retain misses, slips and varying speeds as dynamics examples when observations are valid; imitation experts may exclude unsuccessful execution. A predictor alone is not a stronger control policy. If using predictions to select/correct actions, compare control success against Benchmark 1/2 and disclose the changed action-selection method. Train and test the dynamics model without mixing transitions from related episodes across splits.

A world model is a better fit for our present state/action setup than adding language to a single fixed-goal task. This is a project choice, not a requirement from the uninspected challenge PDF. A simulation-trained model learns simulation dynamics; do not claim real-world dynamics prediction without testing it on real observations.

## Recording target: 60 new goal episodes, in batches

This is a practical starting budget, not a guarantee of sufficient data. The existing five goal recordings remain development/tuning examples. Keep them outside the new validation/test pool. Start with **12 new clips** for tracking and physical replay checks, then continue to the planned 60 once that batch is usable. Record one approach–push–withdrawal episode per file; preserve failures and originals.

Use 15 approximate starting regions, four repetitions per region:

| Horizontal distance left of cross | Vertical offsets relative to cross in overhead image |
|---|---|
| 6 cm | 4 cm above, 2 cm above, same row, 2 cm below, 4 cm below |
| 9 cm | 4 cm above, 2 cm above, same row, 2 cm below, 4 cm below |
| 12 cm | 4 cm above, 2 cm above, same row, 2 cm below, 4 cm below |

Keep target, camera, die and paper fixed. Approximate placement is sufficient: tracking measures actual starts. Add small natural differences within each region; do not repeat an exact trajectory. Push gently towards the cross with the cube sliding; no gripping, lifting or deliberate rolling. Mix slow and moderate speeds across repetitions. Preserve complete visibility of both markers during contact. A 4 cm offset is an expansion of the earlier shallow-diagonal data; inspect its replay before collecting many more.

The ready-made [capture schedule](recording-schedule.csv) and [machine-readable manifest](../data/manifests/recording_plan.json) specify filenames and split assignments before collection:

- 40 new training episodes, including the first 12 inspection clips.
- 10 validation episodes for tuning and model selection.
- 10 test episodes held out from parameter tuning and model selection.

Approximate-region stratification tests new episodes from the same general workspace; it does not by itself prove generalisation to entirely new approach directions. Also predefine a separate simulated-start evaluation set before training. Freeze tracking/retargeting rules using training clips first. Apply them unchanged to validation/test originals; keep failed test processing/execution visible in reporting, rather than replacing failures because the system struggled.

All transformed descendants of one recording inherit that recording's split. No random frame split. Synthetic augmentations never multiply the count of personally collected episodes. If a clip is unusable due to missing/occluded markers, record its reason; use an additional filename for any replacement and retain the original. The numbers are recording slots, not a promise of 60 successful robot experts.

## First 12 clips to record now

Use the first 12 rows of [recording-schedule.csv](recording-schedule.csv), named `train_001.mp4` through `train_012.mp4`. They cover all five vertical offsets and all three distances, with all assigned to training. Upload originals to `data/raw/`. Include a brief opening pause showing all corners and the square, approach with the marker visible, push to the cross, pause, withdraw, and leave the cube visible. Keep notes on any setup changes. We will inspect tracking and replay before requesting the remaining clips.

## Documentation and evidence

Update [workflow](workflow.md) and this roadmap at each completed benchmark. Save capture provenance, split manifests, original/processed hashes, selected contact segments, expert-validity decisions, training commands/configuration, model checkpoints, frozen evaluation plans, per-trial outcomes and failure videos. Distinguish measured results from plans and human motion from scripted robot labels. The new deadline is unspecified; the user has reported an extension.

## Direction pilots and constrained collection update

`goal_above1` and `goal_below1` are now tracked and replayed successfully, mapping to robot left/right respectively. The wall prevents additional personally recorded below-side demonstrations. Keep the old schedule paused; the replacement should collect variation in the accessible directions and explicitly separate any scaled synthetic descendants of `goal_below1`. Those descendants remain in the source split and do not count as new real recordings. See [direction-pilots.md](direction-pilots.md).
