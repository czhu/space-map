# Space-map

Space-map is an open-source framework for reconstructing atlas-level single-cell 3D tissue maps from serial sections. It integrates single-cell coordinates with optional histological image features to assemble serial sections into 3D models, combining multi-scale feature matching with large-deformation diffeomorphic metric mapping (LDDMM) to deliver global reconstructions while preserving local micro-anatomy.

[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://czhu.github.io/space-map)
[![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial-blue.svg)](LICENSE)

## Key Features

- **Multi-modal Registration**: Combines cell coordinates, cell types, gene expression, and histological images for robust alignment
- **Multi-channel Affine Scoring**: Auxiliary channels (cell types, marker genes) weighted by cell count refine the choice of the affine transform
- **Two-stage Registration Approach**: Efficient coarse alignment followed by precise fine registration
- **Advanced Feature Matching**: Combines deep learning (LoFTR) with traditional computer vision methods (SIFT)
- **GPU-accelerated LDDMM**: Optimized for handling large-scale cellular data from multiple tissue sections
- **Global Consistency**: Ensures structural coherence between non-adjacent sections
- **3D Outputs**: Per-layer Imaris-ready TIFF stacks, aligned coordinate tables, and cell-type-colored 3D previews
- **Built-in QC**: SIFT-based section-similarity check to catch mis-ordered or damaged sections before registration
- **High Performance**: Designed to run on standard laptop hardware. Accuracy comparisons against PASTE and STalign are reported in the manuscript; see [`benchmarks/README.md`](benchmarks/README.md) to reproduce them.

## Installation

```bash
# Clone the repository
git clone https://github.com/czhu/space-map.git
cd space-map

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies and Space-map in development mode
pip install -r requirement.txt
pip install -e .
```

Or install directly from GitHub: `pip install git+https://github.com/czhu/space-map.git`

> **Note**: Space-map will be available on PyPI soon. For now, please install from source.

## Getting Started — Example Notebooks

The recommended way to learn Space-map is through the notebooks in
[`examples/`](examples/). Each notebook's first cell holds its input paths
(`DATA`; the expression notebook uses `COORDS` + `MATRIX_DIRS`) — point them
at your local copies of the data, then **Run All**.

| Notebook | What it shows | Input |
|----------|---------------|-------|
| [`xenium_polyp.ipynb`](examples/xenium_polyp.ipynb) | End-to-end 3D reconstruction from cell coordinates (Xenium polyp, 20 layers, ~1.9M cells; ≈2 min on a laptop) | CSV with `x`, `y`, `layer` |
| [`codex_duodenum.ipynb`](examples/codex_duodenum.ipynb) | Same pipeline on CODEX proteomics sections | CSV with `raw_x`, `raw_y`, `layer` |
| [`xenium_celltype.ipynb`](examples/xenium_celltype.ipynb) | **Multi-channel** registration: cell-type channels weight the affine selection; cell-type-colored 3D view; per-channel Imaris TIFF export | CSV with `x`, `y`, `layer`, `cell_type` |
| [`xenium_expression.ipynb`](examples/xenium_expression.ipynb) | **Multi-channel** with gene-expression channels loaded from 10x sparse matrices (`space_map.io`) | coordinates CSV + per-layer 10x `matrix/` dirs |
| [`section_order_check.ipynb`](examples/section_order_check.ipynb) | QC before registration: pairwise SIFT similarity matrix, suggested section order, outlier flagging | CSV with `x`, `y`, `layer` |

Every reconstruction notebook writes to an `out/` folder:

- `c_{layer}.tiff` / `c_{layer}_{channel}.tiff` — per-layer single-channel TIFFs ready for Imaris
- aligned per-cell coordinate tables (raw → aligned)
- a ~45° 3D reconstruction PNG (colored by cell type when available)

### Example datasets

| Name | File | Platform / tissue | Layers | Columns |
|------|------|-------------------|--------|---------|
| `xenium_polyp` | `xenium_polyp.csv.gz` | Xenium (transcriptomics), polyp | 20 | `x`, `y`, `layer`, `cell_type`, `cell_id` |
| `codex_duodenum` | `codex_duodenum.csv.gz` | CODEX (proteomics), duodenum | 16 | `raw_x`, `raw_y`, `x`, `y`, `layer` |

Obtain the files from your dataset source and place them in `examples/data/`
so the notebooks' default `DATA = 'data/...'` paths work as-is (or set `DATA`
to any local file). Any long-format CSV (one row per cell, with x/y and a
layer column) works the same way. The reconstruction notebooks also show
their command-line equivalent in the final cell.

### Scripted runs

The same flows are available from the command line:

```bash
# One-click runner for the example flows (xenium | duodenum | celltype | all)
python examples/run_all.py xenium   --data /path/xenium_polyp.csv.gz   -o out/xenium
python examples/run_all.py celltype --data /path/xenium_polyp.csv.gz   --top-n 10

# Your own data: the space-map CLI (installed with the package)
space-map register /path/your_cells.csv.gz --output out/run --seed 0 \
    --x-col x --y-col y --layer-col layer
```

The default matching method is `auto` (SIFT + the LoFTR deep matcher; LoFTR
downloads a checkpoint on first use). For a lighter, checkpoint-free run pass
`--method sift_vgg` (CLI) or `method="sift_vgg"`.

## Python API

For programmatic use, the stable `space_map.api` facade runs a full
registration and returns aligned coordinates plus quality-control and
provenance metadata.

```python
import pandas as pd
from space_map.api import register, RegistrationConfig

# Load cell coordinates and split into per-layer (N, 2) arrays
df = pd.read_csv("cells.csv.gz")
xys = [g[["x", "y"]].to_numpy(float)
       for _, g in df.groupby("layer", sort=True)]

# Run registration (affine + non-rigid) and write outputs
result = register(xys, RegistrationConfig(workdir="run-out", seed=0))
result.save("run-out")

aligned = result.aligned      # list of (N, 2) aligned coordinate arrays
print(result.qc)              # quality-control report
print(result.manifest)        # versions, seed, device, timings, checksums
```

Or from the command line:

```bash
space-map register cells.csv.gz --output run-out --seed 0
# CODEX-style CSV (array/x/y columns) is auto-detected; otherwise pass
# --x-col/--y-col/--layer-col to name the coordinate and layer columns.
```

The facade wraps the kernel's two-stage pipeline (`FlowImport` →
`AutoFlowMultiCenter4`) and reads back the final aligned coordinates; you do not
need to drive the flow classes directly.

### Multi-channel registration

For finer control, `Slice.init_df` accepts a dict of channels or a wide
DataFrame. `density` (the cell coordinates) is always the primary channel used
for feature extraction; auxiliary channels — one-hot cell types or per-gene
counts — are weighted by cell count when scoring candidate affine transforms
(`space_map.find.WeightedFinder`). See
[`xenium_celltype.ipynb`](examples/xenium_celltype.ipynb) and
[`xenium_expression.ipynb`](examples/xenium_expression.ipynb) for worked
examples, and `space_map.io` for loading 10x sparse expression matrices.

### Section-order QC

```python
import space_map
result = space_map.qc.check_order_from_csv("cells.csv.gz",
                                           x_col="x", y_col="y", layer_col="layer")
print(result["suggested_order"], result["flagged"])
```

## Reproduce Results

A toy dataset is included so you can verify the pipeline in ~1 minute:

```bash
python benchmarks/run.py examples/toy_data.csv.gz
```

For the full dataset (32 layers, ~2.9M cells, ~1 hour):
`python benchmarks/run.py examples/xenium_full.csv.gz`

See [`benchmarks/README.md`](benchmarks/README.md) and
[`benchmarks/example_notebook.ipynb`](benchmarks/example_notebook.ipynb) for
the manuscript-metric reproduction (PASTE / STalign comparisons).

## Documentation

- **[Installation](https://czhu.github.io/space-map/getting-started/installation/)** - Setup and requirements
- **[Quick Start Guide](https://czhu.github.io/space-map/getting-started/quickstart/)** - Complete tutorial
- **[Example Notebooks](examples/)** - Tutorials for each platform and feature (see table above)
- **[API Reference](#python-api)** - The stable `space_map.api` facade

## Applications

Space-map has been successfully applied to build high-resolution 3D tissue maps of:
- Serial sectioned spatial transcriptomics (Xenium, ~2.9M cells)
- Spatial proteomics dataset (CODEX, ~2.4M cells)
- 3D models for diseased (colon polyp) and reference colon

## Architecture

### Core Components

- **`flow.FlowImport`**: Data import and initialization (`init_multi` for multi-channel)
- **`flow.AutoFlowMultiCenter4/5`**: Registration workflow orchestration
- **`base.Slice`**: Individual tissue section management (per-channel `SliceImg`s)
- **`registration`**: LDDMM and deformable registration
- **`matches`**: Feature matching and alignment
- **`find.WeightedFinder`**: Cell-count-weighted multi-channel affine scoring
- **`flow.FlowExport`**: Results export — Imaris TIFFs, channel tables, 3D plots
- **`io`**: 10x sparse-matrix loading and wide-table assembly
- **`qc`**: Section-similarity matrix, order suggestion, outlier flagging

### Project Structure

```
space_map/
├── affine/              # Affine transformation code
├── affine_block/        # Block-based affine processing
├── base/                # Core classes (Slice, SliceImg, etc.)
├── flow/                # Flow-based registration pipeline
├── matches/             # Feature matching algorithms
├── registration/        # LDDMM registration
├── find/                # Feature detection, error analysis, weighted scoring
├── io/                  # 10x matrix loading helpers
├── qc/                  # Section-order / similarity QC tools
├── api/                 # Stable publication-facing facade (config/register/CLI/QC)
└── utils/               # Utility functions
```

## Key Concepts

### Two-Stage Registration

1. **Affine Registration (Coarse)**: Global alignment using density fields
   - Fast and robust
   - Handles rotation, scaling, translation
   - Avoids local optima
   - Optionally scored across cell-type / gene-expression channels

2. **LDDMM (Fine)**: Local non-rigid deformation
   - Preserves topology
   - GPU-accelerated
   - Maintains micro-anatomical structures

### Data Keys

- `Slice.rawKey`: Original data
- `Slice.align1Key`: After affine registration
- `Slice.align2Key`: After LDDMM registration
- `Slice.finalKey`: Final output

## Requirements

Main dependencies:
- Python >= 3.10
- OpenCV
- NumPy
- PyTorch
- Kornia
- scikit-learn
- pandas
- matplotlib
- tifffile
- numba
- scipy
- tqdm

See [`requirement.txt`](requirement.txt) for complete list.

## Citation

If you use Space-map in your research, please cite our paper:

```bibtex
@article{spacemap2024,
  title={Space-map: Reconstructing atlas-level single-cell 3D tissue maps from serial sections},
  author={Han, Rongduo and Zhu, Chenchen and Ruan, Cihan and Snyder, Michael},
  journal={Nature Methods (under review)},
  year={2024}
}
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Space-map is licensed under the **PolyForm Noncommercial License 1.0.0** — see
the [LICENSE](LICENSE) file for the full terms.

- **Noncommercial use is free**: academic, educational, personal, and other
  noncommercial research is permitted at no cost.
- **Commercial / industrial use requires a separate paid license.** To request
  one, contact **Michael Snyder** (Stanford University).

## Support

- **Documentation**: https://czhu.github.io/space-map
- **Issues**: https://github.com/czhu/space-map/issues
- **Discussions**: https://github.com/czhu/space-map/discussions

## Authors

- **Rongduo Han** - Nankai University
- **Chenchen Zhu** - Stanford School of Medicine
- **Cihan Ruan** - Santa Clara University
- **Michael Snyder** - Stanford School of Medicine

See [full author list](https://czhu.github.io/space-map/#authors) for complete credits.

## Acknowledgments

This work was funded by:
- NIH Common Fund HuBMAP program (U54HG010426, U54HG012723)
- NCI HTAN program (U2CCA233311)
- HuBMAP JumpStart Fellowship (3OT2OD033759-01S3)
- AWS Cloud Credit for Research
