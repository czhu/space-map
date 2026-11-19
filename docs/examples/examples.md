# Example Notebooks

The notebooks in the repository demonstrate inputs, registration, and output
inspection. Download the study data using the [raw and processed data links](../index.md#data-availability),
then set local paths and column names. The notebook filenames and default CSV
paths are local conventions, not the names of every file in a data archive.

- [xenium_polyp.ipynb](https://github.com/czhu/space-map/blob/master/examples/xenium_polyp.ipynb):
  end-to-end 3D reconstruction for the Xenium-Polyp dataset.
- [codex_duodenum.ipynb](https://github.com/czhu/space-map/blob/master/examples/codex_duodenum.ipynb):
  end-to-end 3D reconstruction for the CODEX-Duodenum dataset.
- [xenium_celltype.ipynb](https://github.com/czhu/space-map/blob/master/examples/xenium_celltype.ipynb):
  3D reconstruction using cell-type annotations as an additional constraint for
  the Xenium-Polyp dataset.
- [xenium_gene_expression.ipynb](https://github.com/czhu/space-map/blob/master/examples/xenium_gene_expression.ipynb):
  3D reconstruction using gene expression as an additional constraint for the
  Xenium-Polyp dataset; requires a 10x sparse matrix directory per section.
- [section_order_check.ipynb](https://github.com/czhu/space-map/blob/master/examples/section_order_check.ipynb):
  compare supplied order with a similarity-based suggestion and flag dissimilar
  sections for inspection before registration. The suggestion is a heuristic,
  not a replacement for acquisition records.

## Relating inputs to the paper

The final Xenium-Polyp reconstruction uses sections 3–22 (20 sections), although
30 sections were profiled. Use original input coordinate fields when rerunning
registration; the supplementary datasets also contain already-aligned coordinates.
For CODEX, inspect which columns represent original, corrected, and aligned
coordinates rather than selecting fields by filename alone.

Cell-type and gene-expression inputs contribute to affine selection in current
Flow4. Non-rigid refinement updates the primary density coordinates; auxiliary
exports can retain affine positions. See [Inputs and Outputs](../data/data-management.md#optional-cell-types-and-gene-expression)
before interpreting channel-specific previews as refined 3D results.

## Running from the command line

From the repository root, with locally prepared notebook inputs:

```bash
python examples/run_all.py xenium --data examples/data/xenium_polyp.csv.gz -o out
python examples/run_all.py duodenum --data examples/data/codex_duodenum.csv.gz -o out
python examples/run_all.py celltype --data examples/data/xenium_polyp.csv.gz -o out --top-n 10
```

Inspect each mode's output and options using `python examples/run_all.py --help`.
For arbitrary column names, use the public CLI from the [quick start](../getting-started/quickstart.md).
The example runner's outputs and export modes differ between coordinate-only and
cell-type workflows; do not assume every mode produces the same files.

Density TIFFs and static scatter previews support inspection. Their automatic
Z spacing does not encode measured physical section depth. Final publication
renderings also used Imaris and Blender, as described in the paper.
