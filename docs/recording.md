# Recording checklist: current square-target task

**Collection update:** `train_033.mp4` through `train_042.mp4` are now tracked and replayed; next is pushing-only imitation dataset preparation. Successful rendered examples will be retained for each reviewed batch; see [the artifact guide](artifacts.md).

**Latest status (11 October):** all 42 training and nine validation sources are tracked and teacher-replayed. Training: 37/42 successful candidates. Validation teacher references: 6/9, kept separate from training. See [the validation review](validation-batch-01.md). No more recordings are requested now; reserve test for final frozen evaluation. Earlier updates are historical.

**10 October update:** the first 12 clips are calibrated/tracked; 8/12 robot replays pass. Continue with `train_013`–`train_042`, preferably uploading groups of 10. Keep validation/test slots for after the training pipeline is stable. See [the batch review](training-batch-01.md); no first-batch rerecording is requested.

**Orientation update:** active previews, calibrations and tracks now follow the native phone display and one fixed user convention. Original videos are unchanged. Use [the standardisation report](orientation-standardisation.md) for current validation and archive paths; earlier metrics below describe their original runs.

**Record the next ten training slots, `train_023`–`train_032`, in [the dataset plan](recording-plan.md).** All four direction pilots have passed replay. The new schedule covers recording left, right and above; the wall-constrained below side uses the existing pilot and separately labelled synthetic augmentation. The old left-only schedule is archived.

Use [the dataset plan](recording-plan.md) for exact filenames, positions, split assignments and the stop-after-12 checkpoint. Read [the workflow](workflow.md) for recording → tracking → retargeting → evaluation.

## Keep this setup

- Fixed overhead phone; current reported 0.5× setup is usable. Keep framing and zoom fixed during the batch.
- Four visible red L marks: **30 cm horizontal × 29.7 cm vertical**, measured between their stroke intersections.
- Paper taped flat; avoid wrinkles/seams in the sliding path.
- Approximately **1.7 cm die**, with securely attached green top patch.
- Orange nail marker, leaving the contact edge unobstructed.
- Thin black square approximately **3 × 3 cm**, with a cross marking the target centre. Keep it fixed.
- Steady lighting; object and finger colours must stay distinguishable under the hand's shadow.

## Where to start

Use training rows 023–032 in [recording-schedule.csv](recording-schedule.csv). The first 22 rows are processed; [the latest batch report](training-batch-02.md) records their outcomes. All directions refer to your original recording view. Positions are approximate die-centre offsets from the target cross. Keep the target fixed and push towards its centre; do not repeat an exact trajectory. Upload groups of 10 so each new set is checked promptly.

## One clip

1. Pause with the die, all red marks and the target cross visible. Keep the hand clear so calibration and target detection can use the opening frame.
2. Enter the frame with the orange marker visible before contact.
3. Approach and push slowly with one finger towards the cross. Do not clamp, lift or roll the die.
4. Pause briefly at the target, withdraw, and leave the final die position visible.
5. Keep both coloured markers visible throughout contact. The entire arm need not be visible.
6. Save each original untrimmed clip under its scheduled name, next `data/raw/train_023.mp4` through `train_032.mp4`. Preserve `pilot_push.mp4` and `pilot_goal.mp4`.

Current 720 × 1280 / 30 fps clips tracked successfully. Preserve the original file you have; avoid further messaging-app compression. For new captures, 1080p / 30 fps is suitable if practical.

## Measurements and provenance

Save actual available metadata beside each video; leave unknown values null. Example for this setup:

```json
{
  "collector": "YOUR NAME",
  "recorded_at": null,
  "rectangle_width_m": 0.30,
  "rectangle_height_m": 0.297,
  "object_dimensions_m": [0.017, 0.017, 0.017],
  "object_dimensions_precision": "approximate",
  "object_colour": "green top patch",
  "finger_marker_colour": "orange",
  "goal": "black square with centre cross, fixed throughout session",
  "camera_mode": "0.5x",
  "notes": "Any camera movement, occlusion, tipping or setup changes"
}
```

The pipeline tracks patch centroids on an assumed table plane. Height-related parallax and lens distortion remain limitations. Calibration is saved separately per episode; a moved phone or paper requires recalibration. The robot's height/orientation and approach are scripted. Derived robot commands must be described as retargeted human demonstrations, not directly recorded robot actions.

**Direction convention:** recording left → robot below; right → above; above → left; below → right. See [coordinate-convention.md](coordinate-convention.md). Apply this convention when registering each session.

**Fixed dimensions for all recordings:** 30 cm horizontally and 29.7 cm vertically in the recording; 29.7 cm horizontally and 30 cm vertically in the robot-arm table view.

**Collection constraint:** `goal_below1` is processed and usable. The wall prevents further real recordings from below; no more are requested for that direction. Planned augmentation must be labelled synthetic and kept in the same split as its source clip. The old left-only schedule is archived; the active accessible-workspace plan is [recording-plan.md](recording-plan.md).

**Playback:** HEVC/HDR originals may fail in the IDE preview while still decoding correctly for processing. Compatible H.264 viewing copies of `goal_right1` and `goal_above1` are under `data/viewing/`; see [video-playback.md](video-playback.md). Keep using original files for tracking.

Push near the centre of a face when convenient, without forcing a precise finger angle. Smooth contact and visible markers matter more than reproducing the paddle orientation. Natural variation is welcome; avoid excessive twisting or sideways slipping.
