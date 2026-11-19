# Method and Scope

Space-map is an accurate and efficient method for reconstructing 3D tissue
models from high-content spatial molecular profiles. The [published paper](https://doi.org/10.1038/s41592-026-03310-8)
describes multiscale feature matching and large deformation diffeomorphic metric
mapping (LDDMM) for multisection global alignment while preserving local microanatomy.

## Inputs and alignment

Cell centroids, or coordinates extracted from cell masks, are rasterized into
2D cell-density maps. Coordinate normalization puts sections in a common frame.
Coarse alignment uses SIFT and LoFTR feature correspondences, robust filtering,
and RANSAC-based transformation estimation. LDDMM refines local deformation.
Information from multiple sections reduces cumulative drift across a serial
stack; residual registration error can remain.

Cell-type annotations and gene-expression profiles are optional constraints.
Corresponding H&E images can be transformed to complement the coordinate-based
reconstruction. This does not establish general cross-modality registration of
arbitrary stains or assays.

## Study datasets

- Xenium-Polyp: approximately 2.7 million cell profiles across 30 sections
  (3–32). The final 3D reconstruction uses sections 3–22 (20 sections), because
  a morphological discontinuity was observed between sections 22 and 23.
- CODEX-Duodenum: approximately 3.1 million cell profiles across 16 sections.
- CODEX-Sigmoid: approximately 1.7 million cell profiles across 16 sections.
- Public MERFISH and CyCIF data provide additional evaluation datasets.

The CODEX datasets total approximately 4.8 million cell profiles. Counts across
serial sections can include portions of the same biological cell in adjacent
sections; they are not counts of unique, fully reconstructed 3D cells.
Raw and processed data links are on the [documentation homepage](index.md#data-availability).

## Interpretation and limitations

The paper evaluates continuous serial sections, commonly 5 micrometers thick.
Space-map registers observed sections; it does not impute missing sections or
infer missing molecular measurements. Moderate gaps were evaluated, with
accuracy declining as correspondence decreased. Large gaps, variable spacing,
and weakly corresponding sections require additional validation.

A grid-resolution trade-off limits the spatial detail represented in the
registration objective. Cell-level coordinate outputs do not establish an
independent ground truth for cell shape, cell correspondence, or sub-grid
spatial relationships. Physical Z coordinates must come from acquisition metadata.
Real-world light-sheet fluorescence microscopy was not tested in the paper,
and systematic cross-modality evaluation remains future work.

Published performance and accuracy results refer to the evaluated datasets,
metrics, hardware, and study settings. Runtime depends on raster resolution,
deformation, and inter-section similarity as well as input size. Repository
examples do not reproduce the complete comparison against PASTE and STalign-GT.
See Methods, Supplementary Notes 1–5, and the supplementary tables in the paper.

## Software examples versus the published analysis

The public [Python API](api/api.md) currently wraps the Flow4 implementation.
It runs an affine stage followed by SVF-LDDMM refinement. Its defaults and output
archives should not be presented as the paper's complete dataset-specific
multiresolution schedules or analysis scripts. Reproducing a study result also
requires the reported preprocessing, section selection, and evaluation settings.
