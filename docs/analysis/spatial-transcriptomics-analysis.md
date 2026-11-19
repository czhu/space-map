# Evaluation and Downstream Analysis

The [paper](https://doi.org/10.1038/s41592-026-03310-8) evaluates registration on in-house Xenium/CODEX and public
MERFISH/CyCIF data, then examines tissue morphology and cell-type distributions.
Alignment, molecular annotation, and biological interpretation are separate steps.

## Registration evaluation

Methods defines a soft Dice score from non-binarized cell-count density maps
rasterized on a shared coordinate range. For maps A and B, it uses twice the sum
of their per-pixel minimum divided by the sum of both maps. The default evaluation
grid is 512 by 512. The paper also reports binary occupancy Dice, boundary IoU,
Chamfer distance, density-map Pearson correlation, and MS-SSIM, with metric-specific
processing described in Methods, Extended Data Table 2, and Supplementary Note 4.
Do not treat those metrics as interchangeable or mix sparse/binary/soft Dice labels.

The repository's benchmark runner computes Dice, SSIM, PSNR, and MSE using its
current rendering helpers. The public API reports internal QC, including coordinate
finiteness and adjacent-section Chamfer distance. Those defaults do not reproduce
the full published metric suite, preprocessing, or PASTE/STalign-GT comparison.
See the [benchmark guide](https://github.com/czhu/space-map/blob/master/benchmarks/README.md).

Similarity between neighboring sections is not independent biological ground
truth. Tissue morphology naturally changes with depth. A higher score alone
does not prove correct cell correspondence or tissue shape.

## Cell types and expression

Keep cell IDs, section IDs, and molecular annotations with the source table, then
join them to the refined primary coordinates as in the
[quick start](../getting-started/quickstart.md). The current Flow4 auxiliary-channel
limitation is described in [Data Management](../data/data-management.md).

Space-map accepts annotations and selected expression profiles as optional
registration constraints. It does not automatically assign biological cell types,
infer expression in missing sections, or reconstruct complete cell volumes.

## Biological analyses reported in the paper

The study examines crypt/gland architecture, axial lumen continuity, regional
cell-type distributions, and cross-layer stromal–immune neighborhoods. Methods
identifies Squidpy for neighborhood enrichment analyses. Statistical definitions,
section selections, and experimental sample scope should follow the paper and
its supplementary notes, not a generic 3D scatter plot.

## Low-level research utilities

The repository contains expression-grid and boundary-comparison helpers. They
have dataset-specific inputs and are not automatically run by `register()`.
`calculate_layer_distances()` needs coordinate tables, grid parameters, and matrix
paths; it is not a one-argument function accepting expression matrices. Likewise,
`cmp_layers_label()` requires section ranges and annotated input tables. Consult
the signatures before using these research utilities.

- [Expression-grid comparisons](https://github.com/czhu/space-map/blob/master/space_map/utils/compare/cell_metrix.py)
- [Cell-type comparisons](https://github.com/czhu/space-map/blob/master/space_map/utils/compare/filt.py)
- [Boundary analysis](https://github.com/czhu/space-map/blob/master/space_map/find/nearBound.py)
- [Current QC implementation](https://github.com/czhu/space-map/blob/master/space_map/api/qc.py)
- [Image similarity helpers](https://github.com/czhu/space-map/blob/master/space_map/find/err.py)
