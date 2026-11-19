# Usage Guide

Use the maintained guides below for the current implementation:

- [Quick start](../getting-started/quickstart.md): coordinate CSVs, ordered arrays,
  registration, saved output, and joining source metadata.
- [Example notebooks](examples.md): Xenium, CODEX, optional annotations or
  expression constraints, and section-order inspection.
- [Inputs and Outputs](../data/data-management.md): normalization, channels,
  processing stages, and export formats.
- [Python API](../api/api.md): configuration, results, and CLI options.
- [3D reconstruction](../reconstruction/3d-reconstruction.md): density TIFFs,
  static previews, and physical-depth interpretation.
- [Method and Scope](../method.md): the published method, evaluated applications,
  and limitations.

The public registration entry point is `space_map.api.register()`. The package
does not expose the previously illustrated `multimodal_register()`,
`global_optimize()`, or one-command OBJ/PLY/IMS export functions. Use the API and
export methods documented above rather than treating pseudocode as callable code.
