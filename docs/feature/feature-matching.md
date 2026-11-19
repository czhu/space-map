# Feature Matching

Space-map uses SIFT and LoFTR (Local Feature Transformer) to obtain correspondences
between density maps derived from cell coordinates. The [paper](https://doi.org/10.1038/s41592-026-03310-8)
describes multilevel feature filtering and RANSAC-based coarse alignment.
Feature matching is followed by non-rigid refinement; it is not cell-to-cell
identity matching across sections.

## Matcher settings

The public configuration and low-level `alignMethod` accept `"auto"`, `"sift"`,
`"sift_vgg"`, and `"loftr"`. The default `"auto"` path uses SIFT and LoFTR-based
matching. LoFTR is provided by Kornia and downloads a pretrained checkpoint on
first use. It can execute on CPU as well as supported accelerators.

In this repository, the `"sift_vgg"` branch of the OpenCV helper detects and
computes SIFT descriptors. Its historical name does not mean a VGG neural
network is loaded. It is a checkpoint-free option, not an independently
benchmarked improvement over ordinary SIFT.

## Density versus optional constraints

Feature extraction in Flow4 uses density maps. Cell-type annotations and gene
expression can supply auxiliary channels used to score candidate affine
transformations; they do not replace the density matcher with a joint learned
molecular embedding. Current input and export details are in
[Data Management](../data/data-management.md).

## Estimation and inspection

The implementation includes feature-quality filtering, RANSAC-based candidate
estimation, and section-history scoring. Some low-level helpers return 3 by 3
homography matrices; that storage convention is not a separate biological model
or a guarantee that all candidate transformations are suitable. Evaluate the
resulting coordinates and tissue morphology.

The section-order notebook uses pairwise SIFT match counts to visualize similarity
and suggest a heuristic order. Similarity alone cannot establish the true
histological order or prove that a section is damaged.

## Sources

- [Automatic matcher](https://github.com/czhu/space-map/blob/master/space_map/affine_block/AutoAffineImgKey.py)
- [SIFT helper](https://github.com/czhu/space-map/blob/master/space_map/matches/siftFind.py)
- [LoFTR helper](https://github.com/czhu/space-map/blob/master/space_map/matches/LOFTR.py)
- [Candidate scoring](https://github.com/czhu/space-map/blob/master/space_map/affine_block/matchEachImg.py)
- [Section-order QC](https://github.com/czhu/space-map/blob/master/space_map/qc/section_similarity.py)
