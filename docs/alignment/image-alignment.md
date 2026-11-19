# Density-map Alignment and Histology

Space-map primarily aligns cell-coordinate-derived density maps. The
[paper](https://doi.org/10.1038/s41592-026-03310-8) combines this registration with molecular annotations and
corresponding histology to display reconstructed tissue organization.

## Alignment sequence

1. Rasterize normalized cell coordinates into density maps.
2. Use SIFT/LoFTR feature correspondences and robust estimation for coarse alignment.
3. Refine local deformation with LDDMM and incorporate multisection context.
4. Apply the resulting registration to cell coordinates and inspect the stack.

Optional cell types and gene expression constrain affine selection in the current
implementation. See [Method and Scope](../method.md) and the
[current workflow](../workflow/key-workflows.md) for the distinction between
published method descriptions and software entry points.

## Corresponding H&E images

The study stained and imaged the Xenium sections with H&E and transformed
corresponding histology to complement the centroid-based reconstruction.
Applying a coordinate-derived transformation to an image requires the correct
coordinate origin, pixel scale, image orientation, and transform direction.
It is not enough to treat a coordinate-space matrix as an unscaled image warp.

Grid/image helpers and legacy `TransformDB` can apply compatible saved
transformations. The current public Flow4 archive does not contain a replayable
dense non-rigid field. Final point coordinates alone do not provide an exact
non-rigid image warp.

The paper does not validate arbitrary cross-stain, cross-platform, or cross-donor
registration. Systematic cross-modality testing remains future work.

## Sources and next steps

- [Input and channel conventions](../data/data-management.md)
- [Grid transforms](../grid/grid-transformations.md)
- [Image-grid helper](https://github.com/czhu/space-map/blob/master/space_map/utils/model3d.py)
- [Legacy transform application](https://github.com/czhu/space-map/blob/master/space_map/flow/outputs.py)
- [Transform archive scope](https://github.com/czhu/space-map/blob/master/space_map/api/transform.py)
