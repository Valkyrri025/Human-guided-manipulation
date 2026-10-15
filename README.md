# Human-guided manipulation

A small robot-learning project built from personally collected phone videos of a finger pushing a block into a square. We track the block and finger, calibrate their 2D positions, and retarget the recorded motion to a Panda arm in MuJoCo/robosuite. Successful simulated teacher rollouts provide state/action pairs for behavior cloning.

## Benchmarks

| Benchmark | What the policy learns | Validation | Test |
|---|---|---:|---:|
| **1: learned pushing** | XY pushing actions; approach, height, orientation and withdrawal are scripted | **7/9** | **8/9** |
| **2: full-episode learning** | Approach, pushing, withdrawal, end-effector height/orientation and phase selection | **5/9** | Not evaluated |

Benchmark 1 uses a small MLP; benchmark 2 uses a GRU. Policies act from current simulator state and the known goal, without reading future human trajectories. Benchmark 2 is concluded; its best original GRU64 is retained. These are small fixed evaluation sets, not evidence of broad robustness.

[Benchmark 1 details](docs/benchmark-1.md) · [Benchmark 2 final report](docs/benchmark-2.md) · [Results and videos](results/README.md)

## Limitations

We do not have access to a real robot arm for this project, so human videos are transferred through a scripted simulation teacher rather than collected as direct robot demonstrations. This 2D setup necessarily loses height, force and detailed contact information. A flexible finger can change contact and follow curves that our rigid, fixed-orientation paddle cannot always reproduce.

Human object trajectories guide pushing, while the teacher supplies approach, orientation, height and withdrawal labels. Learning the full sequence therefore adds control difficulty without corresponding measured human supervision. Simulation friction and geometry are approximations, and policies use simulator-state observations rather than camera images. The results demonstrate learning from human-derived data within these limits.

## Installation and quick check

Requires Linux, Python 3.12 and [uv](https://docs.astral.sh/uv/getting-started/installation/). Dependencies are pinned in `uv.lock`.

```bash
git clone https://github.com/Valkyrri025/Human-guided-manipulation.git
cd Human-guided-manipulation
uv sync --locked --extra learning --group dev
source .venv/bin/activate
MUJOCO_GL=egl push-smoke --output outputs/checks/smoke
python -m pytest -q
```

For CUDA PyTorch, create a separate environment with `UV_PROJECT_ENVIRONMENT=.venv-gpu uv sync --locked --extra learning-gpu --group dev`, then activate `.venv-gpu/bin/activate`. This does not change system CUDA.

**[Original human recordings](data/raw/)** are included: 48 training videos, nine validation videos, nine test videos and nine earlier pilot/development videos, personally recorded by the project author. For examples, see [a training push](data/raw/train_001.mp4), [pause/resume](data/raw/train_045.mp4) and [a curved push](data/raw/train_048.mp4).

Calibrated tracks, teacher rollouts, selected models and evaluation videos are also included. Installed environments remain local. See the [data workflow](docs/data.md) for dataset preparation, benchmark reports for train/evaluate commands, and [folder guide](docs/artifacts.md) for the file inventory.

Built with [robosuite](https://github.com/ARISE-Initiative/robosuite) and [MuJoCo](https://github.com/google-deepmind/mujoco); upstream assets retain their licences.
