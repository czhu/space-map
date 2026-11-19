# Space-map Reproducible Examples

Align your spatial transcriptomics serial sections with one command or one notebook.

These examples run Space-map and compute adjacent-section quality metrics.
They do not reproduce the full PASTE/STalign-GT comparison in the
[published paper](https://doi.org/10.1038/s41592-026-03310-8).
See the [README data sources](../readme.md#example-datasets) for the study data.
The bundled `xenium_full.csv.gz` is a legacy 32-section coordinate example;
the published Xenium study uses 30 sections, with sections 3–22 used for the
final 3D reconstruction.

## Quick Start

### Option 1: Command line

```bash
# Install
pip install git+https://github.com/czhu/space-map.git

# Quick test with toy data
python benchmarks/run.py examples/toy_data.csv.gz

# Larger coordinate example (legacy 32-section input)
python benchmarks/run.py examples/xenium_full.csv.gz

# Run with your own data
python benchmarks/run.py your_data.csv --output results/
```

### Option 2: Jupyter notebook

```bash
pip install git+https://github.com/czhu/space-map.git jupyter
jupyter notebook benchmarks/example_notebook.ipynb
```

Open the notebook, change the `DATA_PATH` to your file, and run all cells.

## Input Format

A CSV file (`.csv` or `.csv.gz`) with these columns:

| Column | Description | Example |
|--------|-------------|---------|
| `x` | x coordinate of each cell | 844.05 |
| `y` | y coordinate of each cell | 2610.31 |
| `layer` | Section / layer ID | 1 |

If your columns have different names, specify them:

```bash
python benchmarks/run.py data.csv --x-col cx --y-col cy --layer-col section
```

### Xenium and CODEX

The study data may use these columns; inspect your downloaded tables and pass the appropriate column names:

| Platform | x | y | layer/section | Command flags |
|----------|---|---|---------------|---------------|
| Xenium (transcriptomics) | `Xt` | `Yt` | `index` | `--x-col Xt --y-col Yt --layer-col index` |
| CODEX (proteomics) | `x` | `y` | `array` | `--layer-col array` |

```bash
# Xenium
python benchmarks/run.py xenium_cells.csv.gz --output results/xenium \
    --x-col Xt --y-col Yt --layer-col index

# CODEX
python benchmarks/run.py codex_cells.csv.gz --output results/codex \
    --layer-col array
```

## Output

The script produces three files in the output directory:

| File | Description |
|------|-------------|
| `aligned.csv.gz` | Your data with aligned x, y coordinates |
| `metrics.csv` | Per-layer-pair quality metrics |
| `summary.json` | Mean metrics across all pairs |

## Quality Metrics

These scores use the runner's current density rendering. They do not implement
all published preprocessing and metrics, including the shared 512 by 512
soft-Dice evaluation grid, boundary IoU, and MS-SSIM. Adjacent-section agreement
is internal QC, not independent biological ground truth.

Each adjacent pair of layers is compared before and after alignment:

| Metric | What it measures | Better |
|--------|-----------------|--------|
| **Dice** | Overlap of cell density | Higher (max 1.0) |
| **SSIM** | Structural similarity | Higher (max 1.0) |
| **PSNR** | Signal-to-noise ratio | Higher |
| **MSE** | Mean squared error | Lower (min 0.0) |

## File Structure

```
benchmarks/
├── run.py                 # Command-line script
├── example_notebook.ipynb # Step-by-step Jupyter notebook
├── evaluate.py            # Evaluation utilities
└── results/               # Output directory
```
