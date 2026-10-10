# Human-object trajectory teacher — 10 October 2026

The recorded human pushes and their robot replays are different episodes. A human success can become a robot failure because the mounted paddle, simulated friction, controller tracking error and cube rotation change the contact. The last batch's tracked human endpoint centres were 1.1–5.3 mm from the independently drawn target cross, whereas several finger-only robot endpoints missed whole-cube containment. Tracking continuity alone does not prove exact contact or footprint accuracy.

**The new scripted teacher succeeds on 28/32 recordings (87.5%), compared with 20/32 (62.5%) validated finger-only replays. On clips 023–032 it improves from 3/10 to 9/10.** This is a development/training-data check on recordings used to improve retargeting, not held-out policy performance. One deterministic simulation seed is used. No imitation policy has been trained.

## What changed

The original `finger-replay` remains the default baseline and its metrics are preserved. Select the new `human-object-feedback` teacher explicitly:

1. Use the tracked human **object XY trajectory and original timestamps** as the desired object motion. The recorded finger path remains saved for comparison; it does not steer this teacher.
2. Position the paddle behind that desired object point along the initial pushing direction. Recompute the cube's support distance from its current simulated orientation, rather than assuming the initial axis-aligned cube shape throughout contact.
3. Add 0.75 times the desired-minus-simulated object position error, limited to 6 mm in magnitude. This is disclosed simulator-state feedback, not learning. It helps compensate for contact/controller error; it never writes the cube's position or joints.
4. Use 12 mm initial approach clearance, compared with 4 mm in the finger baseline. This fixes `train_032`'s incidental pre-push movement. Pushing height, initial paddle yaw and withdrawal remain scripted. Initial yaw is still chosen from the independent target; it is fixed during contact.
5. Keep the same 10-second push limit, 0.2-second whole-cube dwell, final containment, finite-state, lift/table and <2 mm pre-push-motion checks. When the recording ends, hold its desired endpoint; do not replace it with the target cross.

These changes are evaluated as one teacher method, not separate ablations. All 32 recordings use the same settings, with no episode-specific action edits, enlarged square or relaxed success rule. Source videos, tracks, calibrations and contact segments are unchanged. The teacher currently supports the recorded starts only; new-start augmentation needs an explicitly implemented transformation of the object trajectory.

## Per-recording comparison

| Source | Finger baseline valid success | Object teacher valid success | Teacher final centre distance (mm) | Push time (s) |
|---|---|---|---:|---:|
| train_001 | Yes | Yes | 3.77 | 3.65 |
| train_002 | Yes | Yes | 3.41 | 2.90 |
| train_003 | No | No | 5.02 | 10.00 |
| train_004 | Yes | Yes | 4.65 | 4.40 |
| train_005 | Yes | Yes | 2.87 | 3.35 |
| train_006 | No | Yes | 2.48 | 4.00 |
| train_007 | Yes | Yes | 4.54 | 5.15 |
| train_008 | No | Yes | 3.59 | 4.00 |
| train_009 | No | No | 3.56 | 10.00 |
| train_010 | Yes | Yes | 5.31 | 4.95 |
| train_011 | Yes | Yes | 3.36 | 3.90 |
| train_012 | Yes | Yes | 4.79 | 4.95 |
| train_013 | Yes | Yes | 6.87 | 4.55 |
| train_014 | Yes | Yes | 5.51 | 4.15 |
| train_015 | Yes | Yes | 5.11 | 4.50 |
| train_016 | Yes | Yes | 5.81 | 3.25 |
| train_017 | Yes | Yes | 5.12 | 3.95 |
| train_018 | Yes | Yes | 4.15 | 3.60 |
| train_019 | Yes | Yes | 5.74 | 6.05 |
| train_020 | Yes | Yes | 3.13 | 3.95 |
| train_021 | Yes | Yes | 4.50 | 4.15 |
| train_022 | No | No | 18.99 | 10.00 |
| train_023 | No | Yes | 2.24 | 4.50 |
| train_024 | No | Yes | 3.00 | 4.70 |
| train_025 | No | Yes | 4.62 | 5.20 |
| train_026 | Yes | Yes | 2.44 | 4.50 |
| train_027 | No | No | 6.88 | 10.00 |
| train_028 | Yes | Yes | 3.14 | 5.15 |
| train_029 | No | Yes | 3.23 | 4.45 |
| train_030 | No | Yes | 3.28 | 5.75 |
| train_031 | Yes | Yes | 3.89 | 7.90 |
| train_032 | No | Yes | 4.18 | 7.95 |

Remaining failures: train_003, train_009, train_022, train_027. These remain diagnostics, excluded from successful expert candidates. In particular, a cube centre inside the square is insufficient when a rotated corner remains outside. The new method improves aggregate performance but does not guarantee every physical transfer will succeed.

## What this means for imitation training

Use the **successful physically validated teacher rollouts**, not failed replays relabelled as successes. Failed human sources remain usable for investigating retargeting. Each source and its descendants keep their original training split; none of these 32 clips becomes validation/test data.

For pushing-only imitation, simulated observations before each action and controller action labels are in `rollout.npz`. Observations include end-effector/cube XYZ; separate arrays save end-effector site orientation (XYZW quaternion) and cube orientation (WXYZ quaternion), before/after actions. The independent goal, recorded human object/finger references, timestamps, executed position targets, phases and controller identity are also saved. Filter to documented pushing/dwell phases; scripted approach/withdrawal labels belong to the planned full-episode benchmark. These are derived robot demonstrations generated by a scripted teacher, not direct human robot-control recordings. The desired human time-varying trajectory is teacher guidance; a later goal-conditioned policy must be evaluated without access to an unseen demonstration trajectory.

Better expert generation gives imitation learning useful examples; it does not establish learned-policy generalisation. We still need training, validation and held-out simulated rollouts. Teacher mistakes, limited starts and mismatched human contact remain limitations.

## Reproduce

```bash
MUJOCO_GL=egl uv run --locked python scripts/run_batch.py \
  --manifest data/manifests/human_object_teacher.json \
  --push-controller human-object-feedback --push-timeout-s 10 \
  --no-video --output outputs/human_object_teacher

uv run --locked python -m pytest -q
```

The manifest points to committed numeric human samples, so raw phone videos are not needed to reproduce robot rollouts. Metrics/summary are committed under `docs/examples/human_object_teacher/`; full state/action rollouts are generated locally. The initial development pass and final pass with complete cube-orientation labels are preserved separately. [Successful slow clip 032 video](examples/human_object_teacher/train_032_video/replay.mp4) is rendered from the same teacher settings; the 419-frame video decodes successfully. The full arm is visible in the left panel; the right panel hides arm meshes for contact inspection.

## Recording guidance and next step

For `train_033`–`train_042`, keep comfortable smooth pushes, preferably contacting near the centre of a cube face. A roughly perpendicular push can reduce twisting, but precise finger angle is neither measured nor required. Keep natural variation rather than forcing identical motions; avoid excessive sideways slip or twisting, keep both patches visible, and finish with the whole die inside. Do not rerecord the existing episodes because their finger angle differs from the paddle. Hold validation/test collection until the training-data pipeline is stable.

## Retained examples and cleanup

Successful examples from [left](examples/human_object_teacher/successful_examples/train_001/replay.mp4), [right](examples/human_object_teacher/successful_examples/train_002/replay.mp4) and [above](examples/human_object_teacher/successful_examples/train_006/replay.mp4) are now retained alongside slow clip 032. Current rollouts remain in `outputs/human_object_teacher/`; redundant development-run rollouts were removed after numerical evidence was archived. See [the folder guide](artifacts.md).
