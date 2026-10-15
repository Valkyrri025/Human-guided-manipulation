# Original human demonstrations

These **75 videos were personally recorded by the project author** using a fixed phone camera. They show a finger pushing the green-marked die toward the drawn square, with an orange finger marker and red calibration corners. Originals are published unchanged; derived robot replays are separate.

| Files | Purpose |
|---|---|
| `train_001.mp4`–`train_042.mp4` | Original training collection |
| `train_043.mp4`–`train_048.mp4` | Six later augmentation pilots; only three successful robot teachers entered augmented learning |
| `validation_001.mp4`–`validation_009.mp4` | Validation recordings |
| `test_001.mp4`–`test_009.mp4` | Held-out source recordings; only opening scenes entered benchmark-1 evaluation |
| `pilot_push.mp4`, `pilot_goal.mp4`, `goal_*.mp4` | Nine early development/pilot recordings |
| `pilot_notes.json` | Original setup and approximate measurements |

Phone horizontal distance is 30 cm; vertical distance is 29.7 cm. These are human demonstrations, not recordings of a real robot. Source hashes, reviewed calibration and split/eligibility metadata are recorded in [manifests](../manifests/) and [calibration](../calibration/). Publishing test recordings does not make their future motion a policy input or training target. See the [workflow](../../docs/data.md).

GitHub may require downloading a video to play it locally; use its **Raw** or **Download raw file** button.
