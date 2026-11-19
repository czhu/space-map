# Software Architecture

For the scientific method, see [Method and Scope](../method.md). This page
identifies the implementation used by the public API and distinguishes it from
other research workflows retained in the repository.

## Public entry point

`space_map.api.register()` orchestrates import, affine alignment, and Flow4
SVF-LDDMM refinement, then returns `RegistrationResult` with coordinates,
QC, provenance, warnings, and transform records. `RegistrationConfig` records
run settings. The CLI calls this same wrapper.

## Kernel components

- `FlowImport`: imports ordered coordinates and optional auxiliary inputs,
  normalizes the canvas, and creates per-section `Slice` objects.
- `Slice` and `SliceImg`: separate data channels from processing-stage keys.
  Density is stored under `"DF"`; section identifiers use `Slice.index`.
- `AutoFlowMultiCenter4`: the workflow called by the public wrapper; its affine
  and non-rigid stages use different traversal/reference strategies.
- `matches` and `affine_block`: density-feature matching, robust transformation
  estimation, and candidate scoring.
- `registration.svf`: the refinement adapter used by Flow4. Legacy LDDMM modules
  have different interfaces and parameter schedules.
- `FlowExport`: coordinate tables, density TIFFs, and static 3D previews.
- `io`: selected 10x sparse-expression input helpers.
- `qc`: heuristic section-order inspection; `api.qc` produces per-run internal QC.

`TransformDB` is a legacy transform-file reader, not the storage backend for
every public registration run. Flow4 saves final point coordinates without a
replayable dense non-rigid field. See [Grid Transformations](../grid/grid-transformations.md).

## Configuration boundaries

`base/root.py` defines initial `XYRANGE=4000`, `XYD=10`, `IMGCONF={"raw": 1}`,
and device detection. `FlowImport` recalculates canvas extent and grid spacing.
Changing `space_map.base.root` attributes is not necessarily the same as changing
the package-level names used by the kernel. Public configuration also includes
fields whose propagation is incomplete; see the [API notes](../api/api.md#implementation-notes).
Do not infer accelerator use, worker count, or scientific accuracy from a manifest alone.

## Sources

- [Public registration wrapper](https://github.com/czhu/space-map/blob/master/space_map/api/register.py)
- [Configuration](https://github.com/czhu/space-map/blob/master/space_map/api/config.py)
- [Flow4](https://github.com/czhu/space-map/blob/master/space_map/flow/afFlowMultiCenter4.py)
- [Kernel defaults](https://github.com/czhu/space-map/blob/master/space_map/base/root.py)
- [Input conventions](../data/data-management.md)
