# Pilot tracking: checkpoint 2

**Orientation update:** active previews, calibrations and tracks now follow the native phone display and one fixed user convention. Original videos are unchanged. Use [the standardisation report](orientation-standardisation.md) for current validation and archive paths; earlier metrics below describe their original runs.

The user personally collected and uploaded `data/raw/pilot_push.mp4`. Original preserved; SHA-256: `59a50d549196d2d457eb7f38038052146bbb209603a794a77ef0bf990197d94c`.

## Measurements and assumptions

- Red L-mark rectangle: **0.30 m horizontally × 0.297 m vertically**, confirmed by the user.
- Die: approximately **0.017 m on each side**, user-reported; green top patch.
- Orange finger marker; tracked point is the patch centroid, not the nail tip/contact point.
- Origin at the top-left red L intersection, +x right and +y down as viewed by the camera.
- Lens distortion and marker elevation remain uncorrected. Distances are planar estimates, not precision measurements.

Calibration and colour thresholds: [`data/calibration/pilot.json`](../data/calibration/pilot.json). Initial red L intersections were auto-detected and inspected in the overlay; the four corners are re-detected within local windows each frame. If marks disappear, the tracker falls back to the opening calibration and explicitly flags that frame.

## Full-video checks

| Check | Result |
|---|---:|
| Resolution | 720 × 1280 |
| Frame rate | 30 fps |
| Decoded input/output frames | 326 / 326 |
| Duration | 10.87 s |
| Green object detections | 326 / 326 |
| Orange finger detections | 244 / 326 |
| Finger-visible interval | 1.63–9.73 s |
| Missing finger detections inside that interval | 0 |
| Calibration fallback frames | 0 |
| Maximum corner displacement from opening frame | 5.59 pixels |
| Observed planar object displacement | 0.0816 m |
| Largest object step between adjacent frames | 0.00152 m |

Missing finger frames occur before entry and after withdrawal. Sampled overlays show detections on the correct patches, including during pushing. Detection continuity alone does not prove position accuracy. Corner shifts may include both image motion and detector jitter; per-frame calibration accounts for the observed shifts.

## Files and reproduction

```bash
uv sync --locked --python 3.12
uv run --locked push-track
uv run --locked python -m pytest -q tests/test_tracking.py
```

Outputs at `data/processed/pilot/`:

- `tracking_overlay.mp4`: full annotated recording and calibration outline.
- `tracks.csv`: timestamps, raw pixel centroids, calibrated XY, areas, detection flags.
- `tracks.npz`: array companion, retaining NaN for missing marker detections.
- `quality.json`: source hash and full-video checks.
- `preview.jpg`: representative tracked contact frame.

An independent synthetic projective transform validates metre conversion; additional checks cover missing detections, orange-border exclusion, and rejection of crossed calibration corners.

## Next checkpoint

Use this pilot to build a physical simulated push before collecting the full dataset. Define a constant marker-to-contact offset, suitable Panda contact geometry, fixed contact height and orientation, and a contact-motion segment. Robot approach and withdrawal are scripted. Human finger XY supplies the pushing reference. Physics must move the die; no per-frame object teleporting is allowed.

Checkpoint 3 is now implemented: see [the physical replay report](pilot-replay.md).

The observed final object location is a demonstrated endpoint, not an independently marked target. A replay match to this endpoint is a pilot diagnostic, not held-out task success. Subsequent evaluation needs specified targets and new starts. No robot labels, learned policy, or simulated push result are claimed at checkpoint 2.

## Media cleanup

At the user's request, failed replay videos/previews and regenerable tracking overlays were deleted. Original recordings, unique successful simulation videos, tracks, numerical rollouts, failure metrics and logs remain. Successful example videos are primarily under `docs/examples/`; identical video copies in `outputs/` were removed. Run commands regenerate outputs when needed. Historical paths to removed media are not available until regenerated. See [cleanup-report.json](cleanup-report.json) for the exact deletion list and verified original hashes.
