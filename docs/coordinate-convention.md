# Recording directions and robot-table directions

The user's explicit convention is authoritative:

| Start/approach side in the user's recording | Start/approach side in the robot-arm table view |
|---|---|
| Left | Below |
| Right | Above |
| Above | Left |
| Below | Right |

These labels describe the side of the target where the cube and pushing contact begin. The robot-table view has the robot base below the table. A left-to-centre recording therefore becomes a below-to-centre robot push.

The stored convention is `data/manifests/coordinate_convention.json`. All active calibrations and tracks now use the original phone **display orientation**, including embedded rotation metadata decoded in memory. Raw files are unchanged. Preview images stay in that same orientation.

After planar calibration, paper coordinates are centred: u increases towards recording right and v towards recording below. The shared conversion is robot X = u, robot Y = −v, stored as `paper_to_robot_matrix = [[1, 0], [0, -1]]`. Robot X points away from the base; robot Y points towards robot-view left. This implements all four correspondences above without per-video yaw guesses. A perspective rendering may look different; use the robot-aligned table view to check directions.

All nine recordings were regenerated and physically replayed with this mapping. All eight drawn-goal episodes succeeded. See [the orientation standardisation report](orientation-standardisation.md) for current results and archived legacy inputs.

## Rectangle dimensions

For every recording, horizontal = **30 cm** and vertical = **29.7 cm**. In the robot-arm table view, horizontal = **29.7 cm** and vertical = **30 cm**. These dimensions accompany the direction convention above; do not swap the recording calibration dimensions based on a filename or approach direction. Pixel/table tracking uses the recording dimensions, and registration maps the measured rectangle into the robot frame.
