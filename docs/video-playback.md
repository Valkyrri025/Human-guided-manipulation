# Raw-video playback and viewing copies

`goal_right1.mp4` and `goal_above1.mp4` remain intact: both match the SHA-256 values verified at cleanup and FFmpeg fully decodes every frame. They are HEVC/H.265 Main 10, 10-bit HLG HDR (BT.2020), approximately 60 fps. The working `goal_below1.mp4` is H.264, 8-bit SDR BT.709 at 30 fps. The likely cause of IDE preview failure is unsupported HEVC/HDR playback, rather than damaged recordings; the particular IDE decoder has not been inspected.

Both HEVC originals also carry a display rotation of −90°. Tracking now honours this metadata **in memory**, producing upright 1080 × 1920 frames like the phone display. Earlier tracking used stored 1920 × 1080 frames; those calibrations and tracks have been archived. All active previews and tracks now follow the native recording view and the shared user convention. See [orientation standardisation](orientation-standardisation.md).

Compatible copies are saved separately:

- `data/viewing/goal_right1_h264.mp4`
- `data/viewing/goal_above1_h264.mp4`

These are small H.264/yuv420p 8-bit SDR BT.709 previews at 540 × 960 and 30 fps. Conversion applies display rotation, tone maps HLG HDR into SDR, strips audio, and places MP4 metadata at the start for playback. Originals are untouched. Source hashes, preview dimensions/frame counts and full-decode validation are recorded in `data/viewing/preview-report.json`; conversion logs are alongside the previews.

**Viewing copies are not tracking/training inputs.** Conversion changes resolution, frame sampling and colour appearance. Continue using the originals and reviewed calibrations for processing. `data/viewing/` is ignored by Git apart from its placeholder and can be regenerated; it is intentionally separate from source provenance and successful simulation replays.
