# Independent square-target pilot

**Orientation update:** active previews, calibrations and tracks now follow the native phone display and one fixed user convention. Original videos are unchanged. Use [the standardisation report](orientation-standardisation.md) for current validation and archive paths; earlier metrics below describe their original runs.

This report preserves the historical full-reference experiment. Use `--termination reference` for its replay commands; see [current goal-or-timeout behavior](stopping.md).
`data/raw/pilot_goal.mp4` is the second personally collected user recording. The goal is defined by the black square and cross visible before contact, not by the observed final die position. Original preserved; SHA-256 `f3823f9ed23d57ddb643d7615a5730fa00f28441968d49e0a66aec2f34e046e8`.

## Reproduce

```bash
uv sync --locked --python 3.12
uv run --locked push-track --video data/raw/pilot_goal.mp4 \
  --calibration data/calibration/pilot_goal.json --output data/processed/pilot_goal
uv run --locked push-replay --tracks data/processed/pilot_goal/tracks.npz \
  --calibration data/calibration/pilot_goal.json \
  --start-s 3.1 --end-s 8.2 --output outputs/goal_replay
```

The saved calibration includes the goal. `--detect-goal-square` can initialise goal metadata from an opening frame containing exactly one unobstructed dark square inside the red-marked area. Review the overlay before accepting detection. The centre-cross centroid is used when detectable; otherwise the square-corner mean is used. Calibration geometry is retained separately for each recording because camera framing changed.

## Independent target

- Working rectangle: 30 cm horizontally × 29.7 cm vertically, using the existing user-confirmed dimensions and unchanged die size (approximately 17 mm).
- Cross centroid in opening frame: pixel **[357.884, 544.465]**.
- Goal in calibrated table coordinates: **[0.17070, 0.14020] m**.
- Goal in centred simulation coordinates: **[0.02070, −0.00830] m**.
- The four mapped square corners define the displayed simulation outline and containment diagnostics.
- Goal check: final object centre inside the square and less than **10 mm** from its cross, plus the existing physical validity checks. Full object containment is reported separately using all eight simulated box vertices.

Per-frame red-mark calibration compensates for small image movement. The target is fixed in table coordinates even when the hand or die covers it later. Marker parallax, hand measurements and lens distortion still limit accuracy.

## Tracking and replay

| Check | Result |
|---|---:|
| Video | 332 frames, 30 fps, 720 × 1280 |
| Object detections | 332 / 332 |
| Finger detections while visible | 201 frames, no internal gaps |
| Calibration fallback frames | 0 |
| Human die displacement | 11.08 cm |
| Simulated die displacement | 11.04 cm |
| Final simulated distance from independent cross | 1.90 mm |
| Final object centre inside square | Yes |
| All simulated box vertices inside square | Yes |
| Pre-push displacement | <0.001 mm |
| Tool-table contact control steps | 0 |
| Push reference tracking RMS error | 4.28 mm |
| Video frames decoded | 373 / 373 |

The contact segment **3.1–8.2 s** was selected by inspecting this recording's tracks and motion, not copied from the old pilot. The constant marker-to-tool offset is approximately **[17.63, 1.90] mm**. Desired motion remains the finger trajectory resampled at 20 Hz. The passive block is placed only at reset and moved by contact physics.

When an independent goal is present, the paddle rotates before contact to face the initial object-to-goal direction (here **1.32°**). That orientation remains fixed throughout this push. This pilot therefore does **not** demonstrate broad direction coverage or changing orientation during curved pushes. The old pilot retains its validated fixed orientation when no goal is supplied.

## Artifacts

- `data/processed/pilot_goal/tracking_overlay.mp4`: calibrated markers and magenta independent target overlay.
- `data/calibration/pilot_goal.json`: separate camera calibration, HSV thresholds and independent goal.
- `outputs/goal_replay/replay.mp4`: Panda overview and close-up with the square target.
- `outputs/goal_replay/metrics.json`: independent target distance, endpoint distance, containment and physical checks.
- `outputs/goal_replay/rollout.npz`: aligned pre-/post-action states, derived controller commands, target coordinates and references.

Selected simulation artifacts are included under `docs/examples/goal_replay/`. Original recordings and generated tracking outputs remain ignored by Git pending intentional submission packaging.

Seven tests cover calibration geometry, colour tracking, reference preservation, gap rejection and independent target selection. The original pilot was also rerun as a physics regression and still passed.

## Next collection batch

Record **3–5 additional clips** first, keeping the phone, square, marks, die and marker colours fixed. Start on the left of the square, varying the distance approximately 6–12 cm and vertical position modestly above/below the goal. Push towards the same cross with one finger, pause briefly at the end, withdraw, then leave the final die visible. Preserve each original as `goal_01.mp4`, `goal_02.mp4`, etc.

These are collection/tuning demonstrations. The eventual held-out simulation starts must be specified separately and excluded from parameter tuning. No policy has been trained. After the batch transfers reliably, collect the remaining demonstrations and compare replay/relative retargeting before fitting a small policy.

## Media cleanup

At the user's request, failed replay videos/previews and regenerable tracking overlays were deleted. Original recordings, unique successful simulation videos, tracks, numerical rollouts, failure metrics and logs remain. Successful example videos are primarily under `docs/examples/`; identical video copies in `outputs/` were removed. Run commands regenerate outputs when needed. Historical paths to removed media are not available until regenerated. See [cleanup-report.json](cleanup-report.json) for the exact deletion list and verified original hashes.
