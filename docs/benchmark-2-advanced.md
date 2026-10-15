# Benchmark 2: larger recurrent policy, ready for user-started training

This is a proposed capacity upgrade, not an established performance improvement. The current best full-episode controller remains the original 64-unit GRU trained for 1,000 epochs (selected epoch 877, 5/9 validation successes). The 2,000-epoch original model fit demonstrations better but achieved only 3/9. The user has now completed training and evaluation: the minimum-loss epoch-857 checkpoint achieves 1/9 physically valid validation successes. See [loss audit, failure analysis and retained failure videos](benchmark-2-advanced-results.md).

## Current and proposed architecture

| Component | Current policy | New policy |
|---|---|---|
| State inputs | Same 15 causal features | Same 15 causal features |
| State encoder | Linear 15→64, ReLU | Linear 15→128, layer normalization, SiLU; residual 128→128→128 block |
| Temporal memory | One 64-unit GRU | Two stacked 128-unit GRU layers; 10% dropout between layers |
| Current-state path | Through the GRU | Encoder output added to GRU output, followed by layer normalization |
| Phase head | Linear 64→3 | MLP 128→64→3 |
| Movement heads | Linear 64→18, interpreted as three 6-action heads | Three MLPs, each 128→64→6 |
| Final action | Predicted phase-probability mixture of bounded action heads | Same mixture and action limits |
| Trainable parameters | 27,349 | 268,373 |

Both models receive relative end-effector/cube/goal XY, end-effector/cube height, cube heading, grip-site rotation and known-goal containment. Hidden state provides memory; ground-truth phase is a supervised target only. Actions are world-frame XYZ and three rotation-vector OSC commands. The gripper stays closed. The new model does not add future trajectory inputs, scripted movement, a world model or new human data.

The hypothesis is that more recurrent capacity and deeper heads can represent orientation/contact-dependent actions better. The direct current-state path may preserve precise geometric information that would otherwise have to pass entirely through memory. Layer normalization and dropout add normalization/regularization to the larger architecture. These are design hypotheses; our small dataset and prior loss-versus-success regression mean a larger model is not guaranteed to control better. It is a combined architecture/regularization upgrade, not an isolated hidden-width-only ablation.

PyTorch implements [stacked GRUs and inter-layer dropout](https://docs.pytorch.org/docs/2.14/generated/torch.nn.GRU.html). Implementation uses the existing pinned PyTorch 2.5.1 APIs; the documentation link explains the general mechanism, not a dependency upgrade.

## GPU setup

The TITAN V uses the pinned **PyTorch 2.5.1 CUDA 11.8** wheel from the [official installation index](https://pytorch.org/get-started/previous-versions/#v251). This is installed separately in `.venv-gpu`; the existing CPU `.venv` and system driver/CUDA installation remain unchanged. The lockfile defines mutually exclusive `learning` (CPU) and `learning-gpu` extras.

Already installed on this PC. For a fresh checkout:

```bash
UV_PROJECT_ENVIRONMENT=.venv-gpu uv sync --locked --extra learning-gpu --group dev
```

Use `python` after activation for this run. An unqualified `uv run` can select the default CPU project environment; if using uv, keep the explicit `UV_PROJECT_ENVIRONMENT` and GPU extra.

## Start training yourself

Run in your Linux terminal:

```bash
cd /home/zhangzhiy/git/humanoid-push
source .venv-gpu/bin/activate
python -u -m humanoid_push.advanced_train \
  --device cuda \
  --epochs 2000 \
  --output outputs/benchmark2_training_advanced_gpu
```

This means **2,000 epochs**, matching the previous experiments, not 2,000 minibatch updates. The startup message must identify `cuda` and the NVIDIA TITAN V. Explicit CUDA selection fails early if the wrong environment is active; it does not silently fall back to CPU.

Training uses the existing 37 full training episodes and six successful validation references, seed 7, Adam learning rate 0.001, eight episodes per batch, the same phase-balanced action loss plus 0.2 phase cross-entropy, and the same action bounds. The full dataset, model and loss run on the GPU. CUDA deterministic settings and backend/version/device metadata are recorded; cross-device bitwise equality with CPU runs is not promised. This experiment changes both model architecture/regularization and compute backend, which must be disclosed in comparisons.

The output folder contains:

- `best.pt`: checkpoint with the lowest supervised validation joint loss, not necessarily the best physical controller.
- `last.pt`: final epoch.
- `epoch_0100.pt`, `epoch_0200.pt`, …: snapshots every 100 epochs for later task-based checkpoint assessment; `--save-every 0` disables these.
- `history.json` and `configuration.json`: losses, phase accuracy, architecture and GPU/version metadata.

Existing output directories are protected. Use a new `--output` directory for another run. Test data are not used.

## Validate after training

```bash
MUJOCO_GL=egl python -m humanoid_push.advanced_eval \
  --checkpoint outputs/benchmark2_training_advanced_gpu/best.pt \
  --output outputs/benchmark2_validation_advanced_gpu
```

This reuses the unchanged full-episode evaluator and all nine validation starts: 10-second push budget, 30-second total cap, whole-cube dwell and learned withdrawal clearance. Policy inference is on CPU after loading the GPU-trained checkpoint; GPU rendering is independent. No scripted Cartesian motion or true phase is supplied. Successful videos are retained by recording side, up to three. Failed numeric evidence remains; failed videos are removed.

Because supervised loss has previously selected a weaker controller, periodic checkpoints are available for a separately documented closed-loop validation comparison. Keep test data out of selection. The existing 5/9 controller is retained until measured success supports replacing it.

## Preflight verification (no actual training)

Both the original CPU environment and the new CUDA environment pass all 36 tests. The TITAN V reports compute capability 7.0 and the installed wheel includes `sm_70`. An actual-sized 8 × 419 × 15 training-input batch passed GPU forward/backward with finite gradients, and the six validation-reference sequences passed a GPU forward pass. Peak allocated VRAM was approximately 165 MB. No optimizer update, training epoch or trained-model output directory was created. [Preflight metadata](examples/benchmark2_advanced/gpu_preflight.json). The prior frozen model/evaluation/training source files retain their recorded hashes.

## Requested failure-video retention

The user requested preserving the eight failures from this run. They are retained as `failure.mp4` beside each failed rollout, with exact saved-action replay verification, plus public copies and links in [the results report](benchmark-2-advanced-results.md). The evaluator’s automatic failed-video deletion does not delete these separately rendered reference files.
