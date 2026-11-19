# Inputs, Coordinates, and Outputs

## Input coordinates

The public [API](../api/api.md) accepts one `(N, 2)` coordinate array per section.
The CLI accepts a long-format CSV with explicitly named coordinate and section
columns. Keep acquisition order, coordinate units, and original cell IDs.

The specialized `FlowImport.init_from_codex()` expects `x`, `y`, and `array`, with
section labels such as `S1`. For numeric or differently named identifiers, group
the data explicitly and use coordinate arrays or the generic CLI instead.
A platform name alone does not determine the schema of every downloaded table.

## Working directory and normalization

`FlowImport` centers each section using its coordinate bounding box by default,
sets a padded canvas extent, and calculates the density-grid spacing. This
normalization changes the coordinate frame. Keep a separate copy of the original
input table and acquisition metadata.

`XYRANGE` is the canvas extent and `XYD` is coordinate units per density-grid
pixel. For a fixed extent, increasing `XYD` produces a coarser raster. Import can
recompute both values; set a low-level override after import and before creating
the registration manager, rather than assuming a pre-import value persists.

## Channels and stages are different

A `Slice` has a string `index`, not an `id` attribute. Its `imgs` mapping contains
data channels: `"DF"` for cell density, plus optional molecular or image channels.
`Slice.rawKey`, `Slice.align1Key`, and `Slice.align2Key` identify processing stages,
not channels. Use these accessors after a low-level workflow has produced them:

```python
from space_map import Slice

slice_obj = slices[0]  # slices returned by FlowImport in a low-level workflow
raw_normalized = slice_obj.ps(Slice.rawKey)
affine_aligned = slice_obj.ps(Slice.align1Key)
aligned = slice_obj.ps(Slice.align2Key)
section_id = slice_obj.index
```

`Slice.finalKey` is used by some other workflows; Flow4's final coordinate output
is `Slice.align2Key`.

## Optional cell types and gene expression

`FlowImport.init_multi()` accepts per-section wide tables or channel dictionaries.
Density coordinates determine normalization, which is applied to every channel.
`Slice.init_df()` can expand cell types and selected gene columns. Feature
matching uses density; shared auxiliary channels contribute to candidate affine
scores. In the current scorer, channel weights use stored point/count totals;
these are implementation settings rather than a biological accuracy estimate.

Keep metadata out of feature columns unless it is intended as an input constraint.
For expression matrices, `space_map.io.load_10x_matrix()` and `build_wide_df()`
join selected genes to coordinates by cell ID. Matrix directories must correspond
to the same sections and cell IDs as the coordinate tables.

The current Flow4 non-rigid step updates only the `DF` coordinate channel.
Auxiliary channels copied into `align2` retain their affine coordinates; their
exports are not evidence of non-rigid refinement. For downstream annotations,
join metadata to the refined primary cell coordinates using verified cell IDs
and row correspondence. See the [workflow notes](../workflow/key-workflows.md).

## Saving results

The public `RegistrationResult.save()` writes final NumPy arrays under
`aligned/` and JSON files for QC, provenance, warnings, and transform records.
The kernel working directory contains `conf.json`, channel configuration files,
and stage-specific `.npy` coordinates under `outputs/`. Do not assume every
workflow writes CSV intermediates or dense deformation grids.

For an initialized low-level workflow, coordinate export uses a mapping from
stage keys to output prefixes:

```python
from space_map.flow import FlowExport

export = FlowExport(slices)
coordinates = export.export_dfs(
    {Slice.rawKey: "raw_normalized", Slice.align2Key: "aligned"},
    path="aligned_coordinates.csv.gz",
)
```

`TransformDB(path, ...)` loads an existing compatible NumPy transform archive;
it is not an empty database with `add_transform()`, `save()`, or `load()` methods.
Its legacy grid-based format is separate from `RegistrationResult`'s JSON archive.

## Source reference

- [Import and normalization](https://github.com/czhu/space-map/blob/master/space_map/flow/flowImport.py)
- [Slice and channel access](https://github.com/czhu/space-map/blob/master/space_map/base/slice.py)
- [Export methods](https://github.com/czhu/space-map/blob/master/space_map/flow/flowExport.py)
- [Legacy transform reader](https://github.com/czhu/space-map/blob/master/space_map/flow/outputs.py)
- [Expression input helpers](https://github.com/czhu/space-map/blob/master/space_map/io/matrix10x.py)
