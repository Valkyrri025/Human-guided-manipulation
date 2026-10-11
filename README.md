# Human-guided manipulation

Robot-learning internship challenge: use personally collected overhead phone video of a human pushing a block to drive a simulated Panda. The first comparison tests absolute replay and geometric retargeting on predefined new simulated starts.

**Current status:** the nine original pilot recordings use consistent native-display tracking and the user's fixed direction convention. All eight drawn-goal episodes physically replay successfully; the initial pilot also passes its separate endpoint diagnostic. See [current orientation and replay validation](docs/orientation-standardisation.md). An optional recorded-object feedback teacher now provides improved training rollouts; no policy has been trained. The earlier new-start comparison (2/8 absolute, 5/8 relative, 8/8 scaled) uses archived legacy inputs; it has not yet been rerun with the standardised dataset.

**Start with [the complete workflow](docs/workflow.md)** for recording, target definition, tracking, retargeting, saved labels, completed results and remaining work. The first additional batch is complete; use [the recording checklist](docs/recording.md) for any further clips.

## Training dataset status

Follow [the new recording plan](docs/recording-plan.md): **all 42 training sources tracked; clips 033–042 await robot replay**, covering left, right and above in your phone view. The full target is 60 new clips (42 training / 9 validation / 9 test). No additional below-side recording is required because of the wall. Exact filenames/positions are in [the schedule](docs/recording-schedule.csv). The [first batch review](docs/training-batch-01.md) reports 8/12 successful physical replays; the [second batch](docs/training-batch-02.md) adds 9/10. The [third batch](docs/training-batch-03.md) adds 3/10 validated successes at the new 10-second push limit. All 42 source clips track continuously during contact. The new [recorded-object feedback teacher](docs/object-trajectory-teacher.md) validates 28/32 rollouts (versus 20/32 for finger-only replay). Failed replays remain explicit.

## Replay from the public numeric samples

Nine pilot samples plus 42 new training trajectory samples are included under `data/samples/`; original phone videos stay local. With the environment installed as below:

```bash
MUJOCO_GL=egl uv run --locked python scripts/run_batch.py \
  --manifest data/manifests/public_replay.json --no-video --output outputs/public_replay
```

Current successful videos cover [recording left](docs/examples/native_directions/pilot_goal/replay.mp4), [right](docs/examples/native_directions/goal_right1/replay.mp4), [above](docs/examples/native_directions/goal_above1/replay.mp4) and [below](docs/examples/native_directions/goal_below1/replay.mp4).

Omit `--no-video` to render. These are human-derived simulation replays; no learned policy is included. Reproducing image tracking requires the original videos or your own recordings. See [sample provenance](data/samples/README.md).

## Run checkpoint 1

Tested on Linux, Python 3.12.3, NVIDIA TITAN V (12 GB), driver 580.178.04. No system CUDA changes are needed. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if unavailable, then:

```bash
git clone https://github.com/Valkyrri025/Human-guided-manipulation.git
cd Human-guided-manipulation
uv sync --locked --python 3.12
uv run --locked python scripts/check_machine.py
MUJOCO_GL=egl uv run --locked push-smoke
uv run --locked python -m pytest -q
```

Outputs:

- `outputs/smoke/panda_motion.mp4`: 9 seconds, 640 × 480, 20 fps.
- `outputs/smoke/metrics.json`: motion, tracking, finite-state and video-decode checks.
- `outputs/smoke/trajectory.npz`: scripted XYZ references, achieved XYZ and controller actions.
- `outputs/smoke/preview.png`: midpoint image.
- `outputs/machine.json`: Python, GPU, driver, compiler and package availability.

The script returns a nonzero exit code if it detects failed motion, excessive tracking error, nonfinite state, or an incomplete decoded video. Use `--seed 7 --steps 180 --output outputs/smoke` to specify the defaults explicitly. `--camera frontview` gives a view of the arm and table.

If NVIDIA EGL is unavailable, try `MUJOCO_GL=osmesa PYOPENGL_PLATFORM=osmesa uv run --locked push-smoke`; this requires a working OS Mesa library and has not been tested here. The default NVIDIA EGL backend **has** been tested. Library warnings about private macros, optional robot models, and optional whole-body IK did not prevent the Panda OSC test from passing.

## Example output

See [the video](docs/examples/panda_motion.mp4), [preview](docs/examples/preview.png), and [machine-readable metrics](docs/examples/metrics.json). These demonstrate setup only. They must not be counted as human-data replay or task success.

## Independent square-target pilot

The second user recording, `pilot_goal.mp4`, uses a drawn target calibrated from the opening frame. The replay moved the die 11.04 cm and finished 1.90 mm from that target, fully inside the square. This is a collection/tuning pilot, not held-out performance. See [the goal pilot report](docs/goal-pilot.md) for commands and limits, and [the simulation video](docs/examples/native_directions/pilot_goal/replay.mp4).

## Replay the human pilot (checkpoint 3)

See [the physical replay report](docs/pilot-replay.md) for commands, tool geometry, scripted components, action-label provenance, checks and failures.

```bash
uv run --locked push-replay --termination reference
```

Requires `data/processed/pilot/tracks.npz` (created below) and the saved calibration. Outputs go to `outputs/pilot_replay/`. Selected [video](docs/examples/pilot_replay/replay.mp4), [preview](docs/examples/pilot_replay/preview.png), and [metrics](docs/examples/pilot_replay/metrics.json) are included as examples.

## Track the pilot

One personally recorded pilot is now tracked. See [the pilot report](docs/pilot-report.md) for checks and limitations. The original remains at `data/raw/pilot_push.mp4` and is not committed.

```bash
# Use the saved, reviewed geometry and HSV settings:
uv run --locked push-track
# Independent geometry/detection checks:
uv run --locked python -m pytest -q tests/test_tracking.py
```

For a new camera setup, initialise a separate calibration from an opening frame with four unobstructed red L marks:

```bash
uv run --locked push-track --video data/raw/new_push.mp4 \
  --calibration data/calibration/new_push.json --initialise-calibration \
  --width-m 0.30 --height-m 0.297 --output data/processed/new_push
```

Inspect the overlay before accepting auto-detected corners. HSV thresholds, areas and corner search windows live in the calibration JSON. Missing marker detections are blank in CSV and NaN in NPZ. No missing motion is invented.

## Capture instructions

Follow [the pilot checklist](docs/recording.md). Copy your original recording to `data/raw/pilot_push.mp4`, and save actual measurements in `data/raw/pilot_notes.json`. Raw recordings are ignored by Git to preserve originals and avoid accidental uploads. A public submission will need an intentionally selected, personally collected sample plus its provenance and permission for any visible people.

## Implementation choices

- **Pinned MuJoCo 3.3.7 + robosuite 1.5.2 + Panda:** existing robot model and operational-space control; version lock reduces setup ambiguity.
- **20 Hz Cartesian control:** a desired world XYZ is converted to a normalised position correction `(desired_xyz - simulated_eef_xyz) / 0.05`, clipped to ±0.25 per axis. Orientation error is converted to a world rotation vector and divided by 0.5; gripper closure is commanded. These scale factors match the loaded controller configuration. The simulator converts these commands into joint torques.
- **Fixed orientation:** retain the initial end-effector orientation through feedback; pushing will later use a suitable fixed downward orientation and a contact height matched to the block.
- **No PyTorch dependency at checkpoint 1:** tracking and retargeting use NumPy/OpenCV. PyTorch is absent in the checked environments; GPU tensor compute is untested. GPU EGL rendering works. `nvidia-smi` advertises driver CUDA compatibility, while `nvcc` reports the installed compiler; neither demonstrates that a particular PyTorch wheel supports this GPU.
- **Preserve provenance:** personally captured videos → colour tracks → calibrated table XY → retargeted robot references → robot actions from simulated state and scripted controller. Do not describe the resulting action labels as directly recorded robot demonstrations.

## What worked / what did not

- Isolated Python 3.12 environment, the pinned simulator stack, Panda operational-space control, NVIDIA EGL video, and decoded-frame validation worked.
- Initial `agentview` framing cropped most of the robot; the example uses `frontview`.
- The Codex command sandbox failed at startup (`bwrap` network namespace error); approved direct commands were used. This was a tooling issue rather than a simulator failure.
- Pilot colour tracking and physical replay worked. A rounded contact missed the endpoint; a body-versus-grip-site orientation mismatch caused early contact and was fixed. The initial geometric comparison on new simulated starts is complete; held-out human-episode evaluation and policy fitting remain untested.

## Remaining checkpoints

1. **Done:** simulation starts, Panda moves, video renders.
2. **Done:** calibrate and track one personally recorded pilot; inspect overlay and missing detections.
3. **Done:** custom planar pushing scene and physical pilot replay; see the replay report.
4. **First batch done:** five goal demonstrations. New collection plan: 60 scheduled clips with a 42/9/9 episode split; inspect the first 12 training clips before continuing.
5. **First geometric comparison done:** eight new simulated starts, per-trial outcomes and representative failure/success videos. Next: compact imitation policy and separate closed-loop evaluation.
6. Repository: [Human-guided-manipulation](https://github.com/Valkyrri025/Human-guided-manipulation), with numeric samples, commands, results and attribution.

Choose the success threshold and held-out start set before the final comparison. Keep trajectory selection and parameter tuning separate from held-out evaluation. Report any use of simulator object/target state explicitly. Improvements to a hand-coded retargeter are a valid primary result.

Deadline: the user reports an extension; the new date has not been supplied. The original deadline was 9 October 2026, 23:59 BST / 10 October 2026, 00:59 Europe/Zurich. The challenge PDF has not been inspected on this machine.

## Attribution

[robosuite](https://github.com/ARISE-Initiative/robosuite) supplies the Panda model, Lift setup, controllers and render integration; [MuJoCo](https://github.com/google-deepmind/mujoco) supplies physics and rendering. Their assets and dependencies retain their upstream licences. Source references: [installation](https://robosuite.ai/docs/installation.html), [controller documentation](https://robosuite.ai/docs/modules/controllers.html).

Zhu et al., *robosuite: A Modular Simulation Framework and Benchmark for Robot Learning*, arXiv:2009.12293, 2020.

See [model directions](docs/model-directions.md) for how the task could support a VLA or learned dynamics model; neither is part of the current geometric baseline.

## Planned learning benchmarks

The agreed expansion is pushing-only imitation, then full-episode imitation with validated synthetic approach/withdrawal labels, then a compact learned dynamics model. See [the learning roadmap](docs/learning-roadmap.md). All four direction pilots passed; the active [recording plan](docs/recording-plan.md) covers left/right/above in the native recording view. Begin with 12 training clips, then continue after review. The wall-constrained below direction uses the existing pilot and separately labelled synthetic augmentation.

**Media cleanup:** original recordings and successful simulation videos remain; failed videos, tracking overlays and identical generated-video copies were removed. Small numerical failure evidence is retained. Successful examples live in `docs/examples/`. See [the cleanup audit](docs/cleanup-report.json). The isolated Python environment remains available.

## Artifact locations and retained videos

See [the folder guide](docs/artifacts.md) for canonical rollouts, successful videos and the latest cleanup. With `--no-video`, batch replay now retains up to three successfully rendered examples unless `--success-videos 0` is specified. All 42 training recordings are now tracked; next review the last ten robot replays.

The [fourth training-batch review](docs/training-batch-04.md) documents calibration/tracking for clips 033–042. Teacher results remain 28/32 while those ten robot replays are pending.
