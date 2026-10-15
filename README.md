# Human-guided manipulation

Personally collected overhead phone recordings guide a simulated Panda pushing a 17 mm block into a drawn square. Human object motion is retargeted into physical simulator rollouts; behavior cloning learns robot actions from those rollouts. These are human-derived robot labels, not direct robot demonstrations.

| Method | Validation | Test | What controls the robot |
|---|---:|---:|---|
| Recorded-object teacher | 6/9 | — | Scripted feedback tracking human object motion |
| **Benchmark 1: pushing-only MLP** | **7/9** | **8/9** | Learned pushing XY; scripted approach, height, orientation and withdrawal |
| Benchmark 2: GRU64, 200 epochs | 2/9 | — | Learned full episode and phase selection |
| **Benchmark 2: GRU64, 1,000 epochs** | **5/9** | — | Current best full-episode controller; selected epoch 877 |
| Benchmark 2: GRU64, 2,000 epochs | 3/9 | — | Selected epoch 1,958 by validation loss |
| Benchmark 2: residual GRU128, GPU | 1/9 | — | Selected epoch 857; two additional completions fail table-contact validity |

These are small fixed episode sets. Lower demonstration loss did not reliably imply better closed-loop control. Benchmark 1's test set has been seen; it is not a fresh blind test for later methods. Benchmark 2 has no test score.

## Start here

- [Data and workflow](docs/data.md): human recordings → calibration/tracks → teacher → state/action labels; split and provenance rules.
- [Benchmark 1](docs/benchmark-1.md): model, results, train/evaluate commands.
- [Benchmark 2](docs/benchmark-2.md): architectures, comparisons, GPU commands and failure analysis.
- [Failure videos](docs/failure-videos.md): all eight explicitly retained larger-model failures.
- [Recording guide](docs/recording.md) and [60-episode schedule](docs/recording-schedule.csv).
- [Folder guide](docs/artifacts.md): where to find data, models, videos and historical evidence.

## Environment

Linux and Python 3.12; dependencies are pinned in `uv.lock`. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if needed.

```bash
git clone https://github.com/Valkyrri025/Human-guided-manipulation.git
cd Human-guided-manipulation
uv sync --locked --extra learning --group dev
source .venv/bin/activate
MUJOCO_GL=egl push-smoke --output outputs/checks/smoke
python -m pytest -q
```

For the NVIDIA TITAN V, use the separate CUDA environment (already installed on this PC):

```bash
UV_PROJECT_ENVIRONMENT=.venv-gpu uv sync --locked --extra learning-gpu --group dev
source .venv-gpu/bin/activate
```

GPU PyTorch is 2.5.1+cu118; system CUDA and the CPU environment are unchanged. Activate the desired environment and use `python`; an unqualified `uv run` may select the default CPU environment.

`results/` contains the canonical public checkpoints, evaluation rollouts, metrics and videos. The original phone recordings remain local in `data/raw/`; calibrated numeric tracks and derived teacher rollouts are public, so training/evaluation can run without the raw videos. No training is launched automatically.

## Attribution and limitations

[robosuite](https://github.com/ARISE-Initiative/robosuite) supplies the Panda assets and OSC control; [MuJoCo](https://github.com/google-deepmind/mujoco) supplies physics/rendering. Upstream assets retain their licences. Reference: Zhu et al., *robosuite: A Modular Simulation Framework and Benchmark for Robot Learning*, arXiv:2009.12293.

Policies observe simulator state and a known goal; they are not vision-language models or world models. Scripted synthetic labels, planar calibration, assumed friction and limited initial-pose coverage are disclosed in the guides. The user reported a challenge deadline extension; no updated deadline is recorded.
