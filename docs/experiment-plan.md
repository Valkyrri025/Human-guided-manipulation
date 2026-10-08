Current implementation and evidence: [workflow](workflow.md). The initial comparison uses the predefined [trial manifest](../data/manifests/retargeting_comparison.json); see [implementation and results](retargeting-comparison.md).

# Human-data replay comparison

## Data and provenance

Assign each personally collected clip a stable ID. Preserve original video, collector, recording time, object dimensions, rectangle measurements and calibration clicks. Keep raw, tracked and retargeted files separate. Store invalid or occluded frames explicitly; do not silently replace long gaps with invented motion. Review an annotated pilot video before collecting the remaining clips.

## Tracks and mapping

Track coloured object-top centre and finger marker in pixels with OpenCV. Map to table metres with a four-corner homography. Inspect parallax from elevated markers. Store timestamp, pixel coordinates, table coordinates, detection status and calibration metadata. Object and finger dimensions determine the contact offset; a marker centre is not automatically the physical contact point.

## Baselines

Use the same demonstration and controller for both methods in each comparison.

- Absolute replay: map calibrated finger XY to the simulation workspace with a single fixed transform; replay unchanged for every held-out start.
- Relative retargeting: translate and rotate recorded motion into the new start-to-goal frame, without scaling.
- Relative-scaled retargeting: the same adaptation, with recorded displacements scaled by new/old start-to-goal distance. Initial contact offsets and physical cube/tool sizes remain in metres. Both preserve recorded sample timing.

Both use a scripted approach/withdrawal and fixed pushing height. Any initial orientation alignment must be shared and disclosed: current goal replay aligns the paddle to the initial object-to-target direction, then holds that orientation during contact. Record exactly how the robot contact geometry differs from a finger. Physics moves the object; never teleport it along the human object track during execution.

## Observations and action labels

The low-level controller receives simulated end-effector pose. Relative initial alignment receives simulated initial object position and specified target position. Any online object correction adds simulator-state feedback and must be disclosed separately. Human footage provides planar trajectory references, not robot joint states or action labels. Save references, simulated observations and derived controller actions for inspection.

## Evaluation

Predefine held-out initial XY positions, target locations, demonstration selection and seed(s) before final evaluation. Use paired trials with identical starts and physics for both methods. The current square-target rule requires the whole projected cube to remain inside the calibrated square for 0.2 s before an 8 s push timeout, and remain inside after withdrawal. Orientation is unrestricted; cross distance is diagnostic. Approach/withdrawal are excluded from the push clock. Use the same rule for both methods, as detailed in [stopping.md](stopping.md). Freeze the evaluation settings before reporting. Do not reuse the old 2 cm endpoint-only diagnostic as the square-target success rule. Also check that the object remains on the table and is not lifted. Log final target distance, push displacement, end-effector tracking error, completion, and failure reason. Distinguish simulation states from camera-derived quantities.

Show per-trial outcomes and success counts `n/N`, with median final distance, plus representative success and failure videos. Do not claim statistical certainty from a small hand-collected dataset. Use tuning starts separately from held-out starts. A learned policy is optional and must use a demonstration-level split rather than random frames from the same clip.
