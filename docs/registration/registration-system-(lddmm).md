# LDDMM Refinement

The [paper](https://doi.org/10.1038/s41592-026-03310-8) combines coarse affine alignment with large deformation
diffeomorphic metric mapping (LDDMM) for local refinement. The method is designed
to preserve topology and microanatomy; inspect numerical results rather than
assuming every discretized deformation is fold-free or biologically correct.

## Published method and current implementation

The study describes multiresolution composite refinement and dataset-specific
settings in Methods and Supplementary Note 1. The current public wrapper calls
Flow4's `ldm_pair()`, which uses the `SVFLDDMM` adapter. That adapter invokes
`run_high_res_loss_low_res_grid()`: a low-resolution stationary velocity field
is integrated and evaluated against higher-resolution density images.

Flow4 currently sets an 8 by 8 control grid, and that inner routine defaults to
200 iterations. These are source-code defaults, not a replacement for the
published multiresolution schedule. Older LDDMM classes in the repository use
other parameter conventions; their iteration tables do not describe this path.

## Low-level call

After the affine stage has produced `Slice.align1Key`:

```python
from space_map import Slice

manager.ldm_pair(Slice.align1Key, Slice.align2Key, show=False)
aligned = [section.ps(Slice.align2Key) for section in slices]
```

See the [complete workflow](../workflow/key-workflows.md). Flow4 processes
refinement from the middle section outward and updates density coordinates.
Auxiliary-channel refinement and transform replay limitations are described
in that workflow guide.

## Devices and resource use

LoFTR and refinement have CPU implementations; an NVIDIA GPU is not a mandatory
input requirement. The package detects CUDA, then MPS, then CPU, but individual
helpers also choose devices internally. In particular, the SVF adapter constructs
an internal optimizer using its own default backend; assigning `ldm.device` later
does not reconstruct it. Do not treat a global or manifest device value as proof
of the backend used by every stage. Check the actual stage configuration.

Memory and runtime depend on image resolution, deformation, optimization
settings, and hardware. The paper's measurements apply to its tested data and
machines. This documentation does not promise a generic GPU speedup, runtime per
pair, or an accuracy gain for a different implementation or parameter schedule.

## Resolution

For fixed canvas extent, a larger `XYD` means fewer density pixels and lower
spatial detail. Import can reset `XYD`; low-level workflows must configure it
after import and before creating their manager. Coarse grids can obscure fine
morphology. Sub-grid relationships are not directly represented in the objective.

## Sources

- [Flow4](https://github.com/czhu/space-map/blob/master/space_map/flow/afFlowMultiCenter4.py)
- [SVF adapter](https://github.com/czhu/space-map/blob/master/space_map/registration/svf/adapter.py)
- [SVF optimization](https://github.com/czhu/space-map/blob/master/space_map/registration/svf/svf_lddmm.py)
- [Legacy LDDMM implementation](https://github.com/czhu/space-map/blob/master/space_map/registration/lddmm.py)
