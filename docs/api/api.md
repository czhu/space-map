# Python API

Use `space_map.api` for coordinate-based registration, quality-control metadata,
and saved outputs. The example notebooks demonstrate optional cell-type and
gene-expression inputs through the lower-level workflow classes.

## Registration

```python
import pandas as pd
from space_map.api import register, RegistrationConfig

cells = pd.read_csv("cells.csv.gz")
layers = [group[["x", "y"]].to_numpy(float)
          for _, group in cells.groupby("layer", sort=True)]

config = RegistrationConfig(workdir="run-out/_work", seed=0)
result = register(layers, config)
result.save("run-out")
```

`register(data, config=None, **kwargs)` accepts an ordered sequence of `(N, 2)`
coordinate arrays, one per section. It also accepts a path to a CODEX-style CSV
with `array`, `x`, and `y` columns. Keyword arguments override configuration
fields. A working directory is required.

The wrapper uses `FlowImport`, followed by `AutoFlowMultiCenter4.affine()` and
`AutoFlowMultiCenter4.ldm_pair()`. Transformations are read back as aligned cell
coordinates. See the [implementation](https://github.com/czhu/space-map/blob/master/space_map/api/register.py).

## Configuration

`RegistrationConfig` exposes these settings:

- `workdir`: directory for intermediate registration data; required for a run.
- `method`: affine matching method (`"auto"`, `"sift"`, `"sift_vgg"`, or `"loftr"`);
  `None` uses the kernel default.
- `device`: requested package-level device setting; see backend propagation notes below.
- `seed`: optional random seed.
- `workers`: optional worker setting recorded in the run configuration.
- `resume`: reuse an existing working directory when possible; defaults to `False`.
- `strict`: reject blocking warnings such as dropped cells or non-finite outputs;
  defaults to `True`.
- `imgconf_raw`: density-map rendering mode; defaults to `1` (retain density).
- `ratio`: canvas padding ratio; defaults to `1.4`.

Use `config.to_dict()` and `RegistrationConfig.from_dict(...)` to serialize
settings. See the [configuration source](https://github.com/czhu/space-map/blob/master/space_map/api/config.py)
for the complete field definitions.

## Results and saved files

`register()` returns a `RegistrationResult` with:

- `aligned`: a list of aligned `(N, 2)` coordinate arrays.
- `layer_ids`: identifiers corresponding to those arrays.
- `qc`: quality-control metadata.
- `manifest`: software version, configuration, device, seed, checksums, and timings.
- `transforms`: transform archive records.
- `warnings`: structured run warnings.

`result.save(output_directory)` writes one NumPy coordinate file per section in
`aligned/`, plus `transforms.json`, `qc.json`, `manifest.json`, and `warnings.json`.
See the [result source](https://github.com/czhu/space-map/blob/master/space_map/api/result.py).

## Command line

The installed `space-map` command accepts a long-format coordinate CSV:

```bash
space-map register cells.csv.gz --output run-out --seed 0 \
    --x-col x --y-col y --layer-col layer
```

Use `space-map register --help` for available options. The [CLI source](https://github.com/czhu/space-map/blob/master/space_map/api/cli.py)
uses the same registration wrapper.

## Additional inputs and section-order inspection

- [Xenium-Polyp reconstruction](https://github.com/czhu/space-map/blob/master/examples/xenium_polyp.ipynb)
- [CODEX-Duodenum reconstruction](https://github.com/czhu/space-map/blob/master/examples/codex_duodenum.ipynb)
- [Cell types as additional input](https://github.com/czhu/space-map/blob/master/examples/xenium_celltype.ipynb)
- [Gene expression as additional input](https://github.com/czhu/space-map/blob/master/examples/xenium_gene_expression.ipynb)
- [Section-order check](https://github.com/czhu/space-map/blob/master/examples/section_order_check.ipynb)

## Implementation notes

The array-input wrapper assigns positional string IDs to sections. Preserve
source section IDs and cell metadata when exporting as shown in the
[quick start](../getting-started/quickstart.md). Import centers coordinates;
the saved raw stage is in the normalized canvas frame.

The transform archive supports affine replay. Flow4's non-rigid stage saves final
coordinates, not a reusable dense warp, and the archive marks that stage as
not replayable. `TransformDB` expects a different, legacy NumPy archive.

`workers` is recorded but is not forwarded by `register()` to the affine search;
the current search creates a pool using `os.cpu_count()`. `device` changes the
package-level setting, while the SVF adapter's internal optimizer chooses its
backend during construction. Check stage behavior before relying on worker or
backend overrides. A manifest records requested settings; it is not proof that
every kernel component honored them.

Optional annotations and expression are prepared through low-level notebook
workflows. Flow4 currently refines only density coordinates; consult the
[workflow notes](../workflow/key-workflows.md#using-annotations-or-expression)
before interpreting auxiliary-channel exports.

Study data sources are listed on the [documentation homepage](../index.md#data-availability).
