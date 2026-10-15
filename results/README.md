# Canonical benchmark evidence

| Result | Validation | Test | Folder |
|---|---:|---:|---|
| Pushing-only MLP | 7/9 | 8/9 | [Benchmark 1](benchmark1/) |
| Full episode GRU64, 200 epochs | 2/9 | — | [Initial run](benchmark2/gru64_200/) |
| **Full episode GRU64, 1,000 epochs** | **5/9** | — | [Best controller](benchmark2/gru64_1000/) |
| Full episode GRU64, 2,000 epochs | 3/9 | — | [Longer run](benchmark2/gru64_2000/) |
| Residual stacked-GRU128, GPU | 1/9 | — | [Larger model](benchmark2/gru128_gpu/) |
| GRU64, three additional successful teachers | 1/9 | — | [Augmented model](benchmark2/gru64_augmented/) |

Each experiment retains its selected checkpoint, history/configuration, summary and complete numerical evaluation episodes. Video files are in episode subfolders. [Larger-model and augmentation failure clips](../docs/failure-videos.md) are retained on request. The teacher has 37/42 training and 6/9 validation successes; [teacher examples](teacher/).

Offline loss selected checkpoints but did not reliably rank physical control success. See [benchmark 1](../docs/benchmark-1.md) and [benchmark 2](../docs/benchmark-2.md) for protocols, commands and limitations.

Benchmark 2 is closed. Six additional recording pilots yielded three successful teachers; their videos and audit are under [teacher/augmentation](teacher/augmentation/). The augmented selected checkpoint, training history and all nine evaluations are under `benchmark2/gru64_augmented/`. Historical configuration/checkpoint provenance preserves original pre-cleanup paths.
