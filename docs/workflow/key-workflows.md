# Registration Workflow

The [paper](https://doi.org/10.1038/s41592-026-03310-8) describes density-field normalization, coarse affine
alignment, and topology-preserving LDDMM refinement, incorporating multiple
sections to reduce cumulative drift. The current public API uses Flow4.

## Coordinate-based entry point

Use the [quick start](../getting-started/quickstart.md) for a complete example
with CSV loading, explicit section order, registration, and saved results.
`register()` wraps `FlowImport` and `AutoFlowMultiCenter4`; it does not require
calling workflow classes directly.

## Low-level Flow4 sequence

Here `layers` is a list of `(N, 2)` coordinate arrays in acquisition order, and
`section_ids` contains corresponding strings:

```python
from space_map import Slice
from space_map.flow import FlowImport, AutoFlowMultiCenter4, FlowExport

importer = FlowImport("out/low-level")
slices = importer.init_xys(layers, ids=section_ids)
manager = AutoFlowMultiCenter4(slices, initJKey=Slice.rawKey, alignMethod="auto")
manager.affine(useKey="DF", show=False)
manager.ldm_pair(Slice.align1Key, Slice.align2Key, show=False)
export = FlowExport(slices)
export.export_dfs({Slice.align2Key: "aligned"}, path="out/low-level/aligned.csv.gz")
```

This low-level sequence does not automatically create the public API's QC report
or provenance manifest. Use the public wrapper when those records are needed.

## What Flow4 currently does

The affine stage estimates adjacent-section transformations, accumulates them
toward the first section, and uses the affine matcher's section-history scoring.
The SVF-LDDMM stage proceeds from the middle section outward in both directions,
using previously aligned density images in its reference construction. Describing
both stages simply as independent pairwise registration, or both as starting from
the middle, loses this distinction.

`AutoFlowMultiCenter3` and `AutoFlowMultiCenter5` are alternative implementations,
not interchangeable settings with established superiority or identical method
signatures. The public wrapper uses `AutoFlowMultiCenter4`.

## Using annotations or expression

The paper allows cell-type information and gene-expression profiles as optional
constraints. The corresponding [notebooks](../examples/examples.md) prepare
auxiliary inputs for affine-transform scoring; density remains the matching input.

In current Flow4, `ldm_pair()` copies all channels from `align1` to `align2`, then
`_ldm_pair()` saves refined points only to `sJ.imgs["DF"]`. Auxiliary `align2`
coordinates therefore remain affine-aligned. Use the refined primary coordinates
and an explicit metadata join for downstream cell-type or expression analyses.
A future implementation change would need to propagate refinement to auxiliary
channels before their exports can be described as fully non-rigidly aligned.

## Histology, transforms, and physical Z

The paper transforms corresponding H&E images to complement the cell-coordinate
reconstruction. The current public Flow4 archive provides affine replay and final
point coordinates, not a reusable dense non-rigid warp for arbitrary images.
Legacy grid-based workflows have separate export conventions.

Registration aligns the observed sections in-plane. Section depth and thickness
come from acquisition metadata. Running separate stacks in batches does not
place them into one common frame without additional alignment between batches.

## Sources

- [Public wrapper](https://github.com/czhu/space-map/blob/master/space_map/api/register.py)
- [Flow4 implementation](https://github.com/czhu/space-map/blob/master/space_map/flow/afFlowMultiCenter4.py)
- [Affine section-history scoring](https://github.com/czhu/space-map/blob/master/space_map/affine_block/matchEachImg.py)
- [Transform archive scope](https://github.com/czhu/space-map/blob/master/space_map/api/transform.py)
