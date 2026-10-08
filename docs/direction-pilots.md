# Direction pilots: expanding beyond left-side starts

**Orientation update:** active previews, calibrations and tracks now follow the native phone display and one fixed user convention. Original videos are unchanged. Use [the standardisation report](orientation-standardisation.md) for current validation and archive paths; earlier metrics below describe their original runs.

**Coordinate correction:** `goal_right1` now uses a +90° paper-to-robot registration. Its cube starts above the goal in the robot-aligned table view, away from the base, and pushes toward the base. The corrected replay succeeds after 3.35 s, with 4.14 mm final cross distance. See [corrected video](examples/direction_pilots/goal_right1_registered/replay.mp4). The unregistered results below are historical and are not the training-frame mapping.

The user requested coverage around the target, rather than only starts to its left. The earlier 60-slot recording schedule is **paused**. Check a few real direction pilots and robot reachability before publishing a replacement schedule.

## Personally collected `goal_right1`

The original remains at `data/raw/goal_right1.mp4`, SHA-256 `4bd71145bef99d7f3eb41fed24493553c97de2e0c335bc2e1f25cea685027bd2`. It has 543 frames at approximately 59.945 fps, duration 9.058 s, decoded size 1920 × 1080. Its own opening-frame calibration and independent target detection are saved under `data/calibration/goal_right1.json`. The user confirmed **30 cm horizontal × 29.7 cm vertical** in this video's displayed view; the die remains approximately 17 mm per side.

The filename is the user's direction label. In the decoded image, the die starts above the target and moves downwards. The earlier replay directly copied image-plane axes into simulation axes and therefore used approximately +Y pushing at 88.55°. That registration did not match the user's intended robot-table orientation. The corrected per-session rotation maps centred image coordinates `(u,v)` to robot coordinates `(-v,u)`, rotating the object, tool path, independent goal polygon and paddle yaw together. Older recordings retain their zero-degree registration: their left-side starts are toward the robot base (below in the robot-aligned table view).

### Tracking

- Green object detected in **543/543 frames**.
- Finger marker visible from 2.219 to 7.023 s, with **no missing detections inside that interval**.
- **10/543 frames** used the opening homography because all corners were not recovered.
- Maximum recovered corner shift approximately 5.15 pixels. This is a detection/movement diagnostic, not proof of exact camera stability.
- Observed object displacement approximately **8.49 cm**.
- Source samples and the contact overlay were visually inspected. Both marker centroids and the independent target were correctly located in the inspected frames.

Temporary calibration fallback was sufficient for this pilot. A fixed phone/paper remains necessary when corners are obscured. The overlay is encoded at 1920 × 1088 by imageio for codec alignment; tracking uses the original 1920 × 1080 frames, so this encoding resize does not alter measured coordinates.

### Historical unregistered physical replay

Selected contact-motion segment: **3.1–6.4 s**, chosen from source samples and tracks. The pushing trajectory uses the existing constant marker-to-tool offset and recorded finger references. No policy, online goal steering or cube-pose copying was added.

- Task success: **yes**, whole cube inside the calibrated square after withdrawal.
- Goal stop at **3.35 simulated push seconds**, including the 0.2 s containment dwell.
- Final cross distance: **4.36 mm**; physical cube displacement **8.02 cm**.
- Scripted approach retreated **2.71 mm** for initial clearance; pre-push object displacement was negligible.
- Tool-object contact: **60 control steps**; tool-table contact: **0**.
- All **327 rendered frames** decoded successfully.

This is a direction-pilot/tuning result, not held-out evaluation. Success demonstrates this recorded motion under assumed simulator physics, not arbitrary-direction robustness.

```bash
uv run --locked push-track --video data/raw/goal_right1.mp4 \
  --calibration data/calibration/goal_right1.json --output data/processed/goal_right1
uv run --locked push-replay --tracks data/processed/goal_right1/tracks.npz \
  --calibration data/calibration/goal_right1.json --start-s 3.1 --end-s 6.4 \
  --detail-camera robotview --output outputs/direction_pilots/goal_right1_registered
```

Use the saved reviewed calibration on reruns. The [direction-pilot manifest](../data/manifests/direction_pilots.json) preserves input paths, source hash and segment selection. Examples are under `docs/examples/direction_pilots/goal_right1/`.

## Historical synthetic cardinal-direction checks

These stored checks used the old unregistered calibration. To reproduce their old world-coordinate offsets, use the saved `direction_checks_legacy.json` plan, which points to the archived `docs/examples/direction_pilots/goal_right1/legacy_calibration.json`. The current calibration has the corrected +90° registration; old offsets must not silently be reused as if their frame were unchanged.

The [diagnostic plan](../data/manifests/direction_checks.json) rotates/scales this same recording to start 8 cm right, left and below the fixed target in **simulation coordinates**. These are reachability/contact checks using synthetic augmentation, not additional personally collected demonstrations or a new unbiased benchmark. They were specified before these trials. The recorded pilot supplies the approximately above-target case.

```bash
uv run --locked python scripts/compare_retargeting.py \
  --plan data/manifests/direction_checks_legacy.json --output outputs/direction_checks
```

| Start relative to target in simulation | Tool yaw | Outcome | Push time (s) | Final cross distance (mm) |
|---|---:|---|---:|---:|
| from_right | 180° | Success | 3.30 | 5.05 |
| from_left | 0° | Success | 3.35 | 4.27 |
| from_below | -90° | Timeout | 8.00 | 80.00 |
| from_below, equivalent face | 90° | Success | 3.30 | 5.24 |

The initial below-target trial had **zero contact steps** and **102.55 mm pushing tracking RMSE**. At push onset the grip was approximately 160 mm away in X from its reference, despite approximately correct orientation. This establishes an orientation-dependent tracking failure; a particular joint limit or singularity has not been isolated. The failed metrics and rollout remain in `outputs/direction_checks/from_below/relative-scaled/`.

The paddle is symmetric under a 180° yaw change. Choosing its equivalent face changes the arm configuration without changing the pushing trajectory, contact plane or cube geometry. The below-target tuning retry used `--tool-yaw-offset-deg 180`; pushing direction stayed −90° while the wrist/tool yaw became +90°. It succeeded, with 57 contact steps, 4.78 mm tracking RMSE, negligible pre-push displacement, no tool-table contact, and all 326 video frames decoded. This is an explicit per-run choice, **not automatic posture selection**, and was chosen after inspecting the failed check. All 16 existing tests pass after adding the option.

Thus all four cardinal directions have at least one successful diagnostic configuration, including the recorded above-target direction. This small tuning exercise is not evidence of success throughout the surrounding workspace.

Reproduce the below-target retry:

```bash
uv run --locked push-replay --tracks data/processed/goal_right1/tracks.npz \
  --calibration docs/examples/direction_pilots/goal_right1/legacy_calibration.json --start-s 3.1 --end-s 6.4 \
  --retargeting relative-scaled --start-offset-m 0.00211956352 0.16390606195 \
  --tool-yaw-offset-deg 180 --output outputs/direction_checks/from_below_equivalent_face
```

## Earlier collection checkpoint (completed)

The following pilot request has been completed; see the new-pilot results below. Originally: record the remaining requested human pilots from above and below relative to your table, keeping the phone/paper framing fixed within each recording and both patches visible during contact. Save distinct original files (for example `goal_above1.mp4`, `goal_below1.mp4`) and a note if the camera/table orientation differs from the original pilots. This allows explicit direction mapping instead of trusting filenames.

Do not start the old left-only 60-slot schedule. After reviewing these pilots and robot checks, replace it with a balanced schedule around the target at several distances, with predefined episode splits. Keep synthetic robot phases and transformed trajectories clearly separated from personally collected data.

## Robot-table display convention

The `robotview` overhead camera places the robot base below the table: away from the base is up (+X), and towards the base is down (−X). Arm meshes are hidden only in that labelled table panel to avoid occluding the cube and paddle. The overview still renders the full arm. This is a visibility setting, not a physics change. The +90° registration is the actual trajectory/goal transformation; rotating the camera alone would not fix the user-requested correspondence.

**Direction convention:** recording left → robot below; right → above; above → left; below → right. See [coordinate-convention.md](coordinate-convention.md). Apply this convention when registering each session.

## New real pilots: `goal_above1` and `goal_below1`

Both uploaded originals were processed. No extra demonstrations or scaled rollouts were generated in this step.

| Recording | Robot-table start side | Contact segment in source (s) | Push time (s) | Final cross distance (mm) | Whole cube inside after withdrawal |
|---|---|---:|---:|---:|---|
| goal_above1 | Left | 3.0–7.0 | 4.00 | 4.98 | Yes |
| goal_below1 | Right | 4.7–7.6 | 2.80 | 3.40 | Yes |

Each uses its own red-corner calibration and independently detected square. Recording calibration remains 30 cm horizontal × 29.7 cm vertical. The robot rectangle is X 30 cm × Y 29.7 cm, which displays as horizontal 29.7 cm × vertical 30 cm in the robot-table view. Registration saves its complete 2 × 2 matrix in metrics. For the landscape decoded `goal_above1` frame, the −90° registration also normalises the rectangle axes (factors 0.99 and 1.010101); this is coordinate registration to the declared fixed rectangle, not additional demonstration augmentation. Contact offsets are derived after registration with the unchanged physical 17 mm cube and 4 mm paddle half-thickness. `goal_below1` uses 180° registration.

### Tracking and occlusion

`goal_above1`: 567 frames, approximately 59.947 fps, 9.458 s; green object detected in every frame, no internal finger gap, and 9 opening-calibration fallback frames.

`goal_below1`: 304 frames at 30 fps, 10.133 s; green object detected in every frame. Initial tracking falsely detected a stationary red spot beside the paper as the orange finger and accepted a false corner shift of 62.59 pixels near the hand. Rejected quality/tracks/calibration are retained under `outputs/new_direction_pilots/goal_below1_rejected_tracking/`.

The reviewed calibration now excludes that stationary spot's small image window and rejects corner displacements greater than 15 pixels from the opening frame. Rejected/missing corners use the opening homography; missing markers are not interpolated. Corrected output has no gaps between the finger's first/last visible detections (1.533–9.433 s) and 119/304 calibration fallback frames. Maximum accepted corner shift is 14.32 pixels. The largest object frame step fell from 10.72 mm to 2.30 mm. Source samples and contact overlays were visually inspected. This substantial fallback count is a data-quality caveat, not evidence of recovered hidden corners; validity assumes a stationary camera and paper.

### Robot execution failure retained

`goal_above1` first used a tool yaw near −89.35°. The arm tracked poorly, had zero tool-object contacts and 98 tool-table contact steps, and timed out with the cube unmoved. That episode is rejected and retained at `outputs/direction_pilots/goal_above1_rejected_orientation/` and `docs/examples/direction_pilots/goal_above1_rejected_orientation/`.

Using the symmetric paddle's equivalent face (`--tool-yaw-offset-deg 180`) kept the trajectory unchanged, changed tool yaw to +90.65°, and succeeded. The chosen offset is saved in the episode manifest. Accepted above/below runs have 66/47 tool-object contact steps respectively, zero tool-table contacts, negligible pre-push displacement, and fully decoded videos (340/316 frames). This is a tuning configuration choice, not automatic orientation planning.

### Reproduce and inspect

```bash
uv run --locked push-track --video data/raw/goal_above1.mp4 \
  --calibration data/calibration/goal_above1.json --output data/processed/goal_above1
uv run --locked push-track --video data/raw/goal_below1.mp4 \
  --calibration data/calibration/goal_below1.json --output data/processed/goal_below1
uv run --locked push-replay --tracks data/processed/goal_above1/tracks.npz \
  --calibration data/calibration/goal_above1.json --start-s 3 --end-s 7 \
  --tool-yaw-offset-deg 180 --detail-camera robotview --output outputs/direction_pilots/goal_above1
uv run --locked push-replay --tracks data/processed/goal_below1/tracks.npz \
  --calibration data/calibration/goal_below1.json --start-s 4.7 --end-s 7.6 \
  --detail-camera robotview --output outputs/direction_pilots/goal_below1
```

Simulation videos, metrics and tracking-quality JSON are included under `docs/examples/direction_pilots/goal_above1/` and `goal_below1/`. Combined CSV/JSON are in `outputs/new_direction_pilots/` and `docs/examples/direction_pilots/`. Source hashes and validated tool settings are saved in `data/manifests/direction_pilots.json`. The existing test suite now passes 19 tests, including the false-corner rejection and fixed rectangle dimensions.

### Wall constraint and subsequent augmentation

The user cannot collect further real below-side starts because a wall obstructs access. In `goal_below1`, the hand enters from the left before pushing from below in the user's recording; the robot push correctly starts from the right. Human approach motion is excluded by the selected contact interval and replaced with the declared scripted robot approach.

Keep this limitation in the dataset provenance. Future translations/rotations/scaling of this one recording can provide synthetic robot rollouts for this direction, each checked for physical success. They do not count as additional human episodes, cannot establish real demonstration diversity, and must inherit the source recording's split. Do not place augmentations of this pilot into independent validation/test pools. Evaluate unseen simulator starts separately and disclose the lack of multiple real recordings for this direction. No more real below-side recordings are requested.

Batch reproduction of the two new accepted pilots:

```bash
uv run --locked python scripts/run_batch.py --manifest data/manifests/direction_pair.json \
  --no-video --output outputs/new_direction_pilots/reproduction_check
```

Omit `--no-video` to render. The manifest preserves the above pilot's 180° symmetric-face selection.

## Media cleanup

At the user's request, failed replay videos/previews and regenerable tracking overlays were deleted. Original recordings, unique successful simulation videos, tracks, numerical rollouts, failure metrics and logs remain. Successful example videos are primarily under `docs/examples/`; identical video copies in `outputs/` were removed. Run commands regenerate outputs when needed. Historical paths to removed media are not available until regenerated. See [cleanup-report.json](cleanup-report.json) for the exact deletion list and verified original hashes.
