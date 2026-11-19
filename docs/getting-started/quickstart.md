# Quick Start

This guide runs coordinate-based registration and saves aligned coordinates.
For the scientific method and its scope, see [Method and Scope](../method.md).

## Prepare the input

Install Space-map using the [installation guide](installation.md).
Use one row per cell profile, with x/y coordinates and a section identifier:

```csv
x,y,layer
100.5,200.3,3
150.2,180.7,3
95.3,205.1,4
```

Use consistent coordinate units and the known serial-section order. Numeric
identifiers sort numerically; labels such as `S1`, `S10`, and `S2` need an explicit
acquisition order. Keep the original cell identifiers and annotations for joining
metadata to the aligned output.

## Command line

```bash
space-map register cells.csv.gz --output out/run --seed 0 \
    --x-col x --y-col y --layer-col layer
```

Replace the column names as needed. `--method sift_vgg` uses SIFT without a
LoFTR checkpoint download. Run `space-map register --help` for the CLI options.

## Python

```python
import pandas as pd
from space_map.api import register, RegistrationConfig

cells = pd.read_csv("cells.csv.gz")
layer_order = sorted(cells["layer"].unique())  # Set acquisition order explicitly if needed.
groups = [cells.loc[cells["layer"] == layer].copy() for layer in layer_order]
layers = [group[["x", "y"]].to_numpy(float) for group in groups]

config = RegistrationConfig(workdir="out/run/_work", seed=0)
result = register(layers, config)
result.save("out/run")

# Keep the original section IDs and metadata when exporting coordinates.
for group, aligned in zip(groups, result.aligned):
    if len(group) != len(aligned):
        raise ValueError("Cell counts differ; inspect the QC report before joining metadata.")
    group["x_aligned"] = aligned[:, 0]
    group["y_aligned"] = aligned[:, 1]
pd.concat(groups, ignore_index=True).to_csv("out/run/aligned_cells.csv.gz", index=False)
```

The array-input API assigns positional string layer IDs internally. The explicit
`groups` above retains the input section IDs and row order. Imported coordinates
are centered on the registration canvas; retain the input coordinates rather
than treating the saved normalized `raw` stage as the original acquisition frame.

## Inspect the output

`result.aligned` contains one `(N, 2)` array per section. `result.save()` writes
these arrays under `aligned/`, plus `qc.json`, `manifest.json`, `transforms.json`,
and `warnings.json`. Inspect both alignment overlays and the QC report. Internal
agreement between adjacent sections is not independent biological ground truth.

The API saves point coordinates after non-rigid refinement. The transform
archive supports affine replay; Flow4 does not export a replayable dense
non-rigid field. See the [API reference](../api/api.md).

Use the [example notebooks](../examples/examples.md) for TIFF export,
visualization, and optional cell-type or gene-expression inputs. A 3D preview's
automatic Z spacing is for display; use measured section positions for physical
3D distances or volumes.
