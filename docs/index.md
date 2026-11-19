# Space-map

Han, R., Ruan, C., Zhao, B. *et al.* [Space-map: 3D single-cell atlas reconstruction from serial sections](https://doi.org/10.1038/s41592-026-03310-8). *Nat Methods* (2026).

[![Documentation](https://img.shields.io/badge/docs-repository-blue.svg)](https://github.com/czhu/space-map/tree/master/docs)
[![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial-blue.svg)](https://github.com/czhu/space-map/blob/master/LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-space--map-blue.svg)](https://github.com/czhu/space-map)

---

## Overview

Space-map is an accurate and efficient method for reconstructing 3D tissue models from high-content spatial molecular profiles. It combines multiscale feature matching with large deformation diffeomorphic metric mapping (LDDMM) to automate global alignment across serial sections while preserving local microanatomy.

## Guides

- [Method and Scope](method.md): the published method, datasets, and limitations.
- [Installation and Configuration](getting-started/installation.md).
- [Quick Start](getting-started/quickstart.md): ordered inputs, registration, and saved output.
- [Inputs and Outputs](data/data-management.md): coordinate frames, stages, and optional constraints.
- [Registration Workflow](workflow/key-workflows.md) and [Python API](api/api.md).
- [Example Notebooks](examples/examples.md) and [3D Visualization](reconstruction/3d-reconstruction.md).
- [Evaluation and Downstream Analysis](analysis/spatial-transcriptomics-analysis.md).

## Data availability

| Dataset | Raw data | Processed data |
|---------|----------|----------------|
| Xenium-Polyp | [HTAN / Synapse](https://humantumoratlas.org/publications/hta10_2026__rongduo-han?tab=10x-xenium-iss) | [Supplementary Dataset 1](https://static-content.springer.com/esm/art%3A10.1038%2Fs41592-026-03310-8/MediaObjects/41592_2026_3310_MOESM8_ESM.zip) |
| CODEX-Duodenum | [HuBMAP HBM632.RMQV.469](https://doi.org/10.35079/HBM632.RMQV.469) | [Supplementary Dataset 2](https://static-content.springer.com/esm/art%3A10.1038%2Fs41592-026-03310-8/MediaObjects/41592_2026_3310_MOESM8_ESM.zip) |
| CODEX-Sigmoid | [HuBMAP HBM458.CTTZ.946](https://doi.org/10.35079/HBM458.CTTZ.946) | [Supplementary Dataset 3](https://static-content.springer.com/esm/art%3A10.1038%2Fs41592-026-03310-8/MediaObjects/41592_2026_3310_MOESM8_ESM.zip) |

More Info on available data please see [Snyder Lab Space-map page](https://snyderlabs.stanford.edu/spacemap/).

An [online platform](https://spacemap.dataguide.club) is also available.

## Citation and License

The citation above refers to the Nature Methods paper. Full machine-readable
metadata are available in [CITATION.cff](https://github.com/czhu/space-map/blob/master/CITATION.cff).
Software use is covered by the [PolyForm Noncommercial License 1.0.0](https://github.com/czhu/space-map/blob/master/LICENSE).
For support, open an [issue](https://github.com/czhu/space-map/issues).
