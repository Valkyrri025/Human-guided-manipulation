# First training batch review — 10 October 2026

**Collection recommendation: proceed with the remaining 30 training slots, `train_013.mp4` through `train_042.mp4`. Keep validation/test recording for after training-data tracking/retargeting settings are stable. No rerecording of the first 12 is required.**

All 12 originals calibrated and tracked successfully using native phone display orientation, the shared paper-to-robot convention, and the unchanged 30 × 29.7 cm measured rectangle. Original SHA-256 hashes were checked after processing. Every source is assigned to training; no held-out pool was used for tuning.

## Tracking and replay results

The green patch was detected in every frame; the orange patch had no missing detections between first and last visibility. All selected contact segments have continuous valid finger detections. The expected left/right/above recording sides were checked from measured starts and source previews. Start distances are approximate: observed primary offsets vary from 6.2 to 11.4 cm and lateral offsets from 2.2 to 4.4 cm. Preserve these measured starts; do not rewrite them to match the schedule.

Opening-frame corners and the independent drawn square were reviewed. The goal remained separate from the demonstrated endpoint. A 15-pixel corner-displacement guard prevents the hand/marker being mistaken for a moving calibration mark. Clips 002, 006 and 008 used opening-frame fallback for 6, 56 and 4 frames respectively; no phone movement was evident in the reviewed source frames. All others retained detected calibration throughout.

| Clip | Recording side | Object detected | Fallback frames | Robot final target distance (mm) | Physical replay |
|---|---|---:|---:|---:|---|
| train_001 | left | 301/301 | 0 | 4.27 | Success |
| train_002 | right | 254/254 | 6 | 3.20 | Success |
| train_003 | above | 233/233 | 0 | 7.42 | Timeout: footprint outside square |
| train_004 | left | 289/289 | 0 | 5.28 | Success |
| train_005 | right | 275/275 | 0 | 4.61 | Success |
| train_006 | above | 254/254 | 56 | 8.84 | Timeout: footprint outside square |
| train_007 | left | 308/308 | 0 | 4.51 | Success |
| train_008 | right | 282/282 | 4 | 8.09 | Timeout: footprint outside square |
| train_009 | above | 251/251 | 0 | 6.34 | Timeout: footprint outside square |
| train_010 | left | 295/295 | 0 | 4.77 | Success |
| train_011 | right | 297/297 | 0 | 4.16 | Success |
| train_012 | above | 273/273 | 0 | 4.34 | Success |

**8/12** robot replays reach the square under the existing whole-footprint containment rule, 0.2-second dwell, and 8-second push cap. Clips **003, 006, 008 and 009** time out close to the target because the whole projected cube is not inside. Their centre distances alone do not establish success. All 12 runs remained finite and on the table, with no excessive lift or pre-push cube displacement.

The failed simulations remain recorded as failures and are not imitation expert episodes. Their original human tracks remain usable data. Shallow-centre misses and paddle/contact differences need retargeting work; do not reduce the recording coverage merely to make this baseline score higher. Exact causes of the individual misses have not been isolated through rendered failure inspection. There is no learned policy yet.

## Contact selection and reviewed exception

Initial proposals bracket object movement beyond 2 mm from the opening/final median, with a 4-frame lead and 5-frame tail, bounded to visible finger frames. Opening/middle/end source frames and resulting tracks were reviewed. Human approach and withdrawal are excluded; robot approach, lowering, height/orientation and withdrawal remain scripted.

`train_002` has a late isolated 3.3 mm object-centroid wobble during withdrawal. It did not warrant rerecording. Its contact endpoint was reviewed and shortened from 6.60 s to **5.967 s**, leaving the final contact pause and excluding withdrawal. The corrected replay still succeeds (3.20 mm final centre distance). The initial numerical metrics remain locally archived; current summaries use the corrected replay. No missing coordinates were interpolated or target-driven corrections added.

Above-side replays use the already established 180° symmetric paddle-face option; other sides use 0°. No simulator, controller, tool geometry, success rule or physics parameters were changed for this batch.

## Saved data and reproduction

- `data/calibration/train_001.json` through `train_012.json`: reviewed per-clip corners, goal and native frame.
- `data/processed/train_*/`: previews, CSV/NPZ tracks, quality reports and processing logs.
- `data/manifests/training_batch_01.json`: source hashes, splits, contact times and expert eligibility.
- `outputs/training_batch_01/`: simulated observations/actions, phases, metrics and failure evidence. All related descendants stay in training.
- `docs/examples/training_batch_01/`: small persistent metric/quality snapshots, including failed replay metrics.
- `data/samples/train_*/tracks.npz` and `public_training_batch_01.json`: small numeric samples enabling replay without private raw recordings.

For one source video, regenerate tracking using its saved calibration:

```bash
uv run --locked push-track --video data/raw/train_001.mp4 \
  --calibration data/calibration/train_001.json \
  --output data/processed/train_001 --no-overlay
```

Reproduce all twelve simulation outcomes from bundled numeric tracks:

```bash
MUJOCO_GL=egl uv run --locked python scripts/run_batch.py \
  --manifest data/manifests/public_training_batch_01.json \
  --push-timeout-s 8 --no-video --output outputs/training_batch_01
```

Omit `--no-video` for inspection. Tracking overlays and failed replay videos were not generated in this review, consistent with the earlier cleanup request. The batch driver retains physical failures as measured results; its exit code reports processing errors separately.

## Next recordings

Follow rows `train_013`–`train_042` in [recording-schedule.csv](recording-schedule.csv), preferably uploading groups of 10 so new coverage is checked promptly. Keep the camera, paper, colours, die and target fixed. Put the **die centre** approximately at the requested offsets in your native recording view, and slide it naturally into the square. All corners/goal should be visible for the opening pause; both patches should remain visible through contact. No need to reproduce an exact trajectory, add below-side clips, or redo the first batch.

The new training clips can proceed while retargeting is improved. Hold the nine validation and nine test slots until that pipeline is frozen. The 8/12 figure is a training-batch replay result, not a held-out policy score.
