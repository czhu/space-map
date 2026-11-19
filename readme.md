# Space-map

Han, R., Ruan, C., Zhao, B. *et al.* [Space-map: 3D single-cell atlas reconstruction from serial sections](https://doi.org/10.1038/s41592-026-03310-8). *Nat Methods* (2026).

[![Documentation](https://img.shields.io/badge/docs-repository-blue.svg)](docs/index.md)
[![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial-blue.svg)](LICENSE)

Space-map is an accurate and efficient method for reconstructing 3D tissue models from high-content spatial molecular profiles. It combines multiscale feature matching with large deformation diffeomorphic metric mapping (LDDMM) to automate global alignment across serial sections while preserving local microanatomy.

## Installation

Requires Python 3.10 or later.

```bash
git clone https://github.com/czhu/space-map.git
cd space-map
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

## Getting Started

Open a notebook in [`examples/`](examples/), set the input paths in its first code cell, and run all cells. Use `DATA` for coordinate tables; the gene-expression example uses `COORDS` and per-section `MATRIX_DIRS`.

| Notebook | Content |
|----------|---------|
| [`xenium_polyp.ipynb`](examples/xenium_polyp.ipynb) | End-to-end 3D reconstruction for the Xenium polyp dataset |
| [`codex_duodenum.ipynb`](examples/codex_duodenum.ipynb) | End-to-end 3D reconstruction for the CODEX-Duodenum dataset |
| [`xenium_celltype.ipynb`](examples/xenium_celltype.ipynb) | 3D reconstruction using cell-type annotations as an additional constraint for the Xenium-Polyp dataset |
| [`xenium_gene_expression.ipynb`](examples/xenium_gene_expression.ipynb) | 3D reconstruction using gene expression as an additional constraint for the Xenium-Polyp dataset |
| [`section_order_check.ipynb`](examples/section_order_check.ipynb) | Compare the supplied section order with a similarity-based suggested order, and flag dissimilar sections before 3D reconstruction. |

Cell-type annotations and gene expression can be incorporated as optional constraints for 3D reconstruction.

### Example datasets

| Dataset | Raw data | Processed data |
|---------|----------|----------------|
| Xenium-Polyp | [HTAN / Synapse](https://humantumoratlas.org/publications/hta10_2026__rongduo-han?tab=10x-xenium-iss) | [Supplementary Dataset 1](https://static-content.springer.com/esm/art%3A10.1038%2Fs41592-026-03310-8/MediaObjects/41592_2026_3310_MOESM8_ESM.zip) |
| CODEX-Duodenum | [HuBMAP HBM632.RMQV.469](https://doi.org/10.35079/HBM632.RMQV.469) | [Supplementary Dataset 2](https://static-content.springer.com/esm/art%3A10.1038%2Fs41592-026-03310-8/MediaObjects/41592_2026_3310_MOESM8_ESM.zip) |
| CODEX-Sigmoid | [HuBMAP HBM458.CTTZ.946](https://doi.org/10.35079/HBM458.CTTZ.946) | [Supplementary Dataset 3](https://static-content.springer.com/esm/art%3A10.1038%2Fs41592-026-03310-8/MediaObjects/41592_2026_3310_MOESM8_ESM.zip) |

More Info on available data please see [Snyder Lab Space-map page](https://snyderlabs.stanford.edu/spacemap/).

### Command line

For your own coordinate CSV, specify the x, y, and section columns:

```bash
space-map register cells.csv.gz --output out/run --seed 0 --x-col x --y-col y --layer-col layer
```

The default matcher uses SIFT and LoFTR; LoFTR downloads a checkpoint on first use. Add `--method sift_vgg` to use SIFT without a checkpoint download.

## Documentation and Support

- [Installation and configuration](docs/getting-started/installation.md)
- [Quick start](docs/getting-started/quickstart.md) and [Python API](docs/api/api.md)
- [Report an issue](https://github.com/czhu/space-map/issues)

## License

[PolyForm Noncommercial License 1.0.0](LICENSE). For a commercial license, contact [Michael P. Snyder](mailto:mpsnyder@stanford.edu).
