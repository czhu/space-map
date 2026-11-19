# 3D Reconstruction and Visualization

Space-map aligns observed serial sections into a shared in-plane coordinate
system. The [paper](https://doi.org/10.1038/s41592-026-03310-8) uses these coordinates to reconstruct intestinal
tissue architecture and visualize cell-type distributions through tissue depth.
This is serial-section reconstruction rather than direct volumetric imaging or
segmentation of complete 3D cells.

## Coordinate and density outputs

The public API returns aligned `(N, 2)` cell coordinates for each section.
Use the [quick start](../getting-started/quickstart.md) to retain original section
IDs and metadata. The low-level `FlowExport` also exports density TIFFs and
scatter previews after a workflow has produced the requested stage.

For a low-level workflow with aligned `slices`:

```python
from space_map import Slice
from space_map.flow import FlowExport

export = FlowExport(slices)
export.export_imaris_tiff("out/imaris", key=Slice.align2Key, channels=["DF"])
export.plot_3d(key=Slice.align2Key, channel="DF", by_celltype=False,
               save="out/reconstruction.png")
```

The current Flow4 non-rigid step refines only density coordinates. Auxiliary
cell-type or gene channels can retain affine coordinates, as explained in
[Data Management](../data/data-management.md). Their previews must not be
presented as proof of non-rigid registration of those channels.

## Physical depth

`FlowExport.plot_3d()` chooses an automatic Z gap for display unless one is
provided. It does not infer section thickness or missing depth. TIFF stacks
also need correct voxel spacing in the downstream viewer. Use acquisition
metadata for physical Z positions and account for known gaps.

The final Xenium-Polyp model in the paper uses 20 sections (3–22), not every
section in the profiled 30-section dataset. CODEX duodenum and sigmoid models
each use 16 sections; the study describes 80-micrometer reconstructed volumes.

## Meshes and downstream analyses

The paper used Imaris and Blender for final visualization. A TIFF export is not
an Imaris `.ims` project or a surface mesh, and the public API does not expose
one-command OBJ/PLY/IMS export. Published meshes and additional data are linked
from the [data page](../index.md#data-availability).

Reconstruction can support morphology and cell-distribution analysis. A smooth
rendering alone does not validate individual cell shape or true cross-section
cell identity. The paper reports evaluation of lumen continuity and spatial
organization; see its figures and supplementary analyses for their definitions.

## Sources

- [Coordinate results](https://github.com/czhu/space-map/blob/master/space_map/api/result.py)
- [TIFF and preview exports](https://github.com/czhu/space-map/blob/master/space_map/flow/flowExport.py)
- [Legacy image/grid helpers](https://github.com/czhu/space-map/blob/master/space_map/utils/model3d.py)
