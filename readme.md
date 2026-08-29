# Space-map

Space-map is an open-source framework for reconstructing atlas-level single-cell 3D tissue maps from serial sections. It integrates single-cell coordinates with optional histological image features to assemble serial sections into 3D models, combining multi-scale feature matching with large-deformation diffeomorphic metric mapping (LDDMM) to deliver global reconstructions while preserving local micro-anatomy.

[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://czhu.github.io/space-map)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Key Features

- **Multi-modal Registration**: Combines cell coordinates, cell types, gene expression, and histological images for robust alignment
- **Two-stage Registration Approach**: Efficient coarse alignment followed by precise fine registration
- **Advanced Feature Matching**: Combines deep learning (LoFTR) with traditional computer vision methods (SIFT)
- **GPU-accelerated LDDMM**: Optimized for handling large-scale cellular data from multiple tissue sections
- **Global Consistency**: Ensures structural coherence between non-adjacent sections
- **High Performance**: Designed to run on standard laptop hardware. Accuracy comparisons against PASTE and STalign are reported in the manuscript; see [`benchmarks/README.md`](benchmarks/README.md) to reproduce them.

## Quick Start

### Installation

#### Option 1: Install from Source (Recommended)

```bash
# Clone the repository
git clone https://github.com/czhu/space-map.git
cd space-map

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirement.txt

# Install Space-map in development mode
pip install -e .
```

#### Option 2: Direct Installation from GitHub

```bash
pip install git+https://github.com/czhu/space-map.git
```

> **Note**: Space-map will be available on PyPI soon. For now, please install from source.

### Basic Usage

The recommended entry point is the stable `space_map.api` facade, which runs a
full registration and returns aligned coordinates plus quality-control and
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

## Reproduce Results

A toy dataset is included so you can verify the pipeline in ~1 minute:

```bash
git clone https://github.com/czhu/space-map.git
cd space-map
pip install -e .
python benchmarks/run.py examples/toy_data.csv.gz
```

Or open the step-by-step notebook: [`benchmarks/example_notebook.ipynb`](benchmarks/example_notebook.ipynb)

### Example datasets

Three serial-section datasets are used in the examples below:

| Name | File | Platform / tissue | Layers | Columns |
|------|------|-------------------|--------|---------|
| `xenium_polyp` | `xenium_polyp.csv.gz` | Xenium (transcriptomics), polyp | 20 | `x`, `y`, `layer` |
| `codex_colon` | `codex_colon.csv.gz` | CODEX (proteomics), colon | 16 | `x`, `y`, `array` |
| `codex_duodenum` | `codex_duodenum.csv.gz` | CODEX (proteomics), duodenum | 16 | `raw_x`, `raw_y`, `x`, `y`, `layer` |

Place the three files in `examples/data/` (obtain them from your dataset
source).

**Test with the notebook** — open
[`examples/tutorial.ipynb`](examples/tutorial.ipynb) and run all cells; it
registers all three datasets and prints per-dataset QC.

**Test from the command line** — `examples/run_platforms.py` registers one
dataset at a time (pass the columns for that platform):

```bash
python examples/run_platforms.py xenium examples/data/xenium_polyp.csv.gz \
    --output out/xenium --x-col x --y-col y --layer-col layer
python examples/run_platforms.py codex  examples/data/codex_colon.csv.gz \
    --output out/codex  --layer-col array
python examples/run_platforms.py codex  examples/data/codex_duodenum.csv.gz \
    --output out/duodenum --x-col raw_x --y-col raw_y --layer-col layer
```

Add `--subsample 20000` for a quick smoke test on the full stacks.

The default matching method is `auto` (SIFT + the LoFTR deep matcher; LoFTR
downloads a checkpoint on first use). For a lighter, checkpoint-free run pass
`--method sift_vgg` (CLI) or `method="sift_vgg"` (`RegistrationConfig`).

For the full dataset (32 layers, ~2.9M cells, ~1 hour): `python benchmarks/run.py examples/cells2.csv.gz`

**Sample dataset with cell types** (20 layers, ~1.87M cells): download from [Releases](https://github.com/czhu/space-map/releases/download/v0.1.0/celltype_0427.csv.gz)

### Running Xenium and CODEX data

Both platforms use the same pipeline; only the coordinate/layer column names
differ. Use the stable `space-map` CLI (recommended), or `benchmarks/run.py`
to reproduce the manuscript metrics. Point the column flags at your file's
columns.

**Xenium** (spatial transcriptomics) — layers in `index`, coordinates in `Xt`/`Yt`:

```bash
# Recommended: stable CLI
space-map register xenium_cells.csv.gz --output xenium-out \
    --x-col Xt --y-col Yt --layer-col index --seed 0

# Reproduce manuscript metrics
python benchmarks/run.py xenium_cells.csv.gz --output results/xenium \
    --x-col Xt --y-col Yt --layer-col index
```

**CODEX** (spatial proteomics) — sections in `array`, coordinates in `x`/`y`:

```bash
# Recommended: stable CLI (array/x/y is auto-detected)
space-map register codex_cells.csv.gz --output codex-out --seed 0

# Reproduce manuscript metrics
python benchmarks/run.py codex_cells.csv.gz --output results/codex \
    --layer-col array
```

Any long-format CSV works the same way — pass `--x-col`/`--y-col`/`--layer-col`
to match your column names (defaults are `x`/`y`/`layer`).

A ready-to-run script with per-platform column presets is provided at
[`examples/run_platforms.py`](examples/run_platforms.py):

```bash
python examples/run_platforms.py xenium xenium_cells.csv.gz -o xenium-out
python examples/run_platforms.py codex  codex_cells.csv.gz  -o codex-out
# add --subsample 20000 for a fast smoke run on very large stacks
```

See [`benchmarks/README.md`](benchmarks/README.md) for details.

## Documentation

- **[Installation](https://czhu.github.io/space-map/getting-started/installation/)** - Setup and requirements
- **[Quick Start Guide](https://czhu.github.io/space-map/getting-started/quickstart/)** - Complete tutorial
- **[API Reference](#basic-usage)** - The stable `space_map.api` facade (see Basic Usage above)

### Example Notebooks

- [`benchmarks/example_notebook.ipynb`](benchmarks/example_notebook.ipynb) - Reproduce alignment results

## Applications

Space-map has been successfully applied to build high-resolution 3D tissue maps of:
- Serial sectioned spatial transcriptomics (Xenium, ~2.9M cells)
- Spatial proteomics dataset (CODEX, ~2.4M cells)
- 3D models for diseased (colon polyp) and reference colon

## Architecture

### Core Components

- **`flow.FlowImport`**: Data import and initialization
- **`flow.AutoFlowMultiCenter4/5`**: Registration workflow orchestration
- **`base.Slice`**: Individual tissue section management
- **`registration`**: LDDMM and deformable registration
- **`matches`**: Feature matching and alignment
- **`flow.FlowExport`**: Results export and visualization

### Project Structure

```
space_map/
├── affine/              # Affine transformation code
├── affine_block/        # Block-based affine processing
├── base/                # Core classes (Slice, SliceImg, etc.)
├── flow/                # Flow-based registration pipeline
├── matches/             # Feature matching algorithms
├── registration/        # LDDMM registration
├── find/                # Feature detection and error analysis
├── api/                 # Stable publication-facing facade (config/register/CLI/QC)
└── utils/               # Utility functions
```

## Key Concepts

### Two-Stage Registration

1. **Affine Registration (Coarse)**: Global alignment using density fields
   - Fast and robust
   - Handles rotation, scaling, translation
   - Avoids local optima

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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

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
