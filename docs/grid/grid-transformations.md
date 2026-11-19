# Grid Transformations

Some low-level Space-map workflows represent nonlinear mappings as 2D grids and
sample coordinates or images through them. This is interpolation of a spatial
transformation, not interpolation or imputation of missing tissue sections.

## Coordinates and direction

Grid helpers use normalized sampling coordinates and an explicit scale between
coordinate units and pixels (`xyd`). Depending on the helper, a grid represents
absolute sampling locations or a displacement/flow tensor. Do not treat these
representations as interchangeable. Image sampling typically uses an output-to-input
mapping; applying it to points requires the matching direction or an inverse map.

`grid3.py` provides `grid_sample_points_vectorized()`, `inverse_grid_train()`, and
`merge_grid_img()`. Inverse-map estimation is numerical, and composition order
matters. Confirm conventions against the specific helper and a known mapping.

## Archives

Legacy `TransformDB(path, ...)` reads a NumPy archive containing compatible affine
and grid arrays. It exposes `apply_img()`, `apply_point()`, `apply_imgs()`, and
`apply_points()`. It does not implement an empty database API for adding and
saving arbitrary transformations.

The public Flow4 path is different: its transform JSON records replayable affine
matrices and explicitly marks its non-rigid stage as not replayable. Its saved
aligned coordinate arrays are the final point output. Do not assume that every
Space-map run produces an invertible dense-grid archive.

## Spatial resolution

Raster and control-grid resolutions trade spatial detail against computational
cost. The [paper](https://doi.org/10.1038/s41592-026-03310-8) notes that spatial relationships below the chosen
grid resolution are not directly preserved in the registration objective.
Numerical interpolation does not restore unobserved cell geometry.

## Sources

- [Grid operations](https://github.com/czhu/space-map/blob/master/space_map/utils/grid3.py)
- [Point-derived grid helpers](https://github.com/czhu/space-map/blob/master/space_map/utils/grid_points.py)
- [Legacy transform reader](https://github.com/czhu/space-map/blob/master/space_map/flow/outputs.py)
- [Public archive conventions](https://github.com/czhu/space-map/blob/master/space_map/api/transform.py)
