# Recording and tracking

The benchmark collection contains 42 training, 9 validation and 9 test episodes. Six additional training-only augmentation pilots, `train_043`–`train_048`, have also been tracked and replayed; three produce successful robot teachers. See [their results and limitations](benchmark-2.md). The [schedule](recording-schedule.csv) preserves the original collection plan. Benchmark 2 is now closed; no further recording batch is requested.

For additional sources, preserve originals, label the split before processing and keep all descendants in that split. Use a fixed overhead phone with all four red L corners visible in the opening frame. The measured rectangle is **30 cm horizontally × 29.7 cm vertically in native phone display orientation**. Keep the phone fixed; a moderate angle is handled by planar homography, but lens distortion and height parallax remain approximations.

Use the small rigid die (approximately 17 mm per side) with a green top and a contrasting orange fingernail marker. Keep markers visible; the rest of the arm need not remain visible. Tape markers firmly without changing the contact surface. Push the object along the paper rather than grasping or lifting it. Secure the paper so it cannot shift. A white background is fine when the colour markers remain distinct.

The independent target is a roughly 3 × 3 cm drawn square. Record a brief stationary opening (at least 30 frames), approach, a controlled push into the square, withdrawal and a short final pause. Preserve the full untrimmed video. Corner occlusion later in a fixed-camera clip can use the reviewed opening calibration; opening corner visibility matters. Missing finger detections during the selected pushing interval require review rather than invented interpolation.

For new tracks, create/review calibration with `push-track --help`; inspect marker/goal alignment before robot replay. The reviewed current calibrations are under `data/calibration/`. Finger-replay requires continuous finger detections. The recorded-object teacher permits missing finger detections when object tracks remain continuous, but does not reproduce finger disengagement during a pause. [Data workflow and commands](data.md).

The robot overhead convention is fixed: phone left → robot below, right → above, above → left, below → right. Never rotate originals to make these names agree. The wall-constrained recording-below direction is not part of the new 60-source dataset; do not label synthetic rotations as independently recorded held-out data.
