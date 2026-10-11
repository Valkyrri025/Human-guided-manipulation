# Frozen pushing-only policy: final test evaluation

The epoch-143 policy achieved **8/9 test successes (88.9%)**, with **5.44 mm mean final target-centre distance** across all nine episodes. Validation was 7/9. These are small, separate nine-episode sets; the higher test fraction does not establish a general performance improvement.

## Evaluation protocol

Before test decoding, the selected checkpoint and task rules were recorded in [the frozen protocol](../data/manifests/bc_test_protocol.json). The evaluated checkpoint hash is `7ec5a1426abffb8601be95dcc826a842a64817f7fd966665c66dbf894501deb6`. Epoch 143 was selected solely by validation action loss. No additional training, checkpoint selection or parameter tuning occurred after test access.

The original recordings remain unchanged. Only their opening 30 frames were decoded for scene setup: red corner calibration, independent goal detection and median green-marker position. Maximum opening marker deviation was 1.18 mm. [All nine opening overlays](examples/bc_test/opening_review.jpg) were inspected before simulation. No test finger tracking, pushing trajectory, final human endpoint or teacher replay was used. Full source-file hashes were calculated for provenance without decoding the later frames.

Initial positions and goals are saved under `data/initial_scenes/` and indexed in [the test manifest](../data/manifests/public_test_initial_scenes.json). Coordinates retain native phone display orientation and the agreed paper-to-robot matrix. The 17 mm simulated cube starts with identity orientation, as in training/validation; human cube yaw is not retargeted. Camera calibration retains the existing planar approximation, without lens-distortion or marker-height correction.

The control loop, physics, initial-state-only scripted approach, fixed paddle yaw/height, scripted containment dwell and withdrawal match validation. The evaluator was extended only to load test opening-scene metadata instead of teacher metrics, check the frozen checkpoint/code hashes, save incremental progress and retain successful videos from different recording sides. It does not supply recorded future motion to the policy. Protocol and geometry were committed before running the test benchmark (commit `b4cc3b5`). Geometry/code hashes were checked after completion.

## Results

| Episode | Learned result | Push time (s) | Final target distance (mm) |
|---|---|---:|---:|
| test_001 | Success | 4.40 | 4.21 |
| test_002 | Success | 3.45 | 4.14 |
| test_003 | Timeout | 10.00 | 13.63 |
| test_004 | Success | 4.45 | 3.78 |
| test_005 | Success | 4.35 | 2.71 |
| test_006 | Success | 4.85 | 3.08 |
| test_007 | Success | 4.95 | 5.82 |
| test_008 | Success | 4.45 | 6.02 |
| test_009 | Success | 3.75 | 5.58 |

Episode 003 timed out at 10 seconds, ending 13.63 mm from the goal centre without satisfying whole-cube containment dwell. Its state/action rollout and failure metrics remain available. The other eight achieved 0.2 seconds of whole-cube containment and remained contained after withdrawal. All nine runs had finite states/actions, stayed on the table, had object lift below 5 mm and pre-push displacement below 2 mm. Cube orientation was not a success requirement; centre distance alone was not sufficient.

This benchmark demonstrates learned pushing from new, personally recorded starting scenes using privileged simulator state and a known goal. Approach and withdrawal are still scripted. It is not full-episode imitation, image-based control, a VLA or a world model. Robot training labels were generated from human motion through the scripted simulation teacher, not recorded directly from a robot.

## Retained evidence and reproduction

[Recording left / robot below: 001](examples/bc_test/test_001/policy.mp4) · [Recording right / robot above: 002](examples/bc_test/test_002/policy.mp4) · [Recording above / robot left: 006](examples/bc_test/test_006/policy.mp4)

All three videos were decoded completely and match their rollout frame counts. [The summary](examples/bc_test/summary.json) contains checkpoint metadata and all nine outcomes. Every episode has a public numeric rollout and metrics under `docs/examples/bc_test/`. Canonical local outputs remain in `outputs/bc_test/`. Failed videos were not retained.

Reproduce from the public checkpoint and opening-scene metadata, without needing raw videos:

```bash
cd /home/zhangzhiy/git/humanoid-push
source .venv/bin/activate
MUJOCO_GL=egl push-bc-evaluate \
  --checkpoint docs/examples/bc_validation/best.pt \
  --split test \
  --manifest data/manifests/public_test_initial_scenes.json \
  --protocol data/manifests/bc_test_protocol.json \
  --output outputs/bc_test_reproduction
```

Choose a fresh output directory. Install with `uv sync --locked --extra learning --group dev` if necessary. The frozen evaluator source must match the protocol hashes. `scripts/calibrate_initial_scene.py` implements the opening-only extraction for new recordings; it refuses to overwrite reviewed scene files.

All 30 regression tests pass, including rejection of missing test protocol and changed checkpoints. Benchmark 1 is now complete. Preserve this checkpoint/result as the baseline for subsequent methods; any future development informed by these test results must be disclosed.
