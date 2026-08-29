#!/usr/bin/env python
"""Run Space-map registration on Xenium or CODEX serial sections.

Uses the stable ``space_map.api`` facade. Both platforms share the same
pipeline; only the coordinate/layer column names differ, which this script
presets per platform (override with --x-col/--y-col/--layer-col).

Examples
--------
Xenium (transcriptomics; layers in ``index``, coordinates in ``Xt``/``Yt``)::

    python examples/run_platforms.py xenium wd_final_celltype_min.csv.gz \\
        --output xenium-out

CODEX (proteomics; sections in ``array``, coordinates in ``x``/``y``)::

    python examples/run_platforms.py codex B014_reg001_celltype_new.csv.gz \\
        --output codex-out

Verified end-to-end on the manuscript Xenium and CODEX datasets (affine replay
reproduces the aligned coordinates within tolerance).
"""
from __future__ import annotations

import argparse
import json
import sys

import numpy as np
import pandas as pd

# Per-platform default column names (override on the command line if needed).
PRESETS = {
    "xenium": {"x": "Xt", "y": "Yt", "layer": "index"},
    "codex": {"x": "x", "y": "y", "layer": "array"},
    "generic": {"x": "x", "y": "y", "layer": "layer"},
}


def _layer_sort_key(v):
    """Sort CODEX-style labels like S1, S2, ... S10 numerically; fall back to
    natural ordering for plain integers or arbitrary strings."""
    s = str(v)
    if len(s) > 1 and s[0].isalpha() and s[1:].isdigit():
        return (0, int(s[1:]))
    try:
        return (0, int(s))
    except ValueError:
        return (1, s)


def load_layers(path, x_col, y_col, layer_col, subsample=None, seed=0):
    df = pd.read_csv(path, usecols=[x_col, y_col, layer_col])
    for col in (x_col, y_col, layer_col):
        if col not in df.columns:
            sys.exit(f"Error: column '{col}' not found. Available: {list(df.columns)}")
    rng = np.random.RandomState(seed)
    keys = sorted(df[layer_col].unique(), key=_layer_sort_key)
    xys, ids = [], []
    for k in keys:
        sub = df[df[layer_col] == k]
        if subsample and len(sub) > subsample:
            sub = sub.sample(n=subsample, random_state=rng)
        xys.append(sub[[x_col, y_col]].to_numpy(np.float64))
        ids.append(str(k))
    total = sum(len(a) for a in xys)
    print(f"loaded {len(xys)} layers, {total:,} cells "
          f"({layer_col}={ids[:5]}{'...' if len(ids) > 5 else ''})")
    return xys, ids


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("platform", choices=list(PRESETS),
                   help="column-name preset (xenium/codex/generic)")
    p.add_argument("input", help="input CSV (.csv or .csv.gz)")
    p.add_argument("--output", "-o", required=True, help="output directory")
    p.add_argument("--x-col", help="override x column")
    p.add_argument("--y-col", help="override y column")
    p.add_argument("--layer-col", help="override layer/section column")
    p.add_argument("--device", default=None, help="torch device (cuda:0/mps/cpu)")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--subsample", type=int, default=None,
                   help="max cells per layer (for a fast smoke run)")
    p.add_argument("--method", default="sift_vgg")
    args = p.parse_args(argv)

    from space_map.api import register, RegistrationConfig, verify_affine_replay
    from space_map.flow import FlowImport

    preset = PRESETS[args.platform]
    x_col = args.x_col or preset["x"]
    y_col = args.y_col or preset["y"]
    layer_col = args.layer_col or preset["layer"]

    xys, ids = load_layers(args.input, x_col, y_col, layer_col,
                           subsample=args.subsample, seed=args.seed)

    cfg = RegistrationConfig(workdir=f"{args.output}/_work", device=args.device,
                             seed=args.seed, method=args.method, strict=False)
    result = register(xys, cfg)
    result.save(args.output)

    print(f"registered -> {args.output}")
    print("timings:", result.manifest["timings"])
    pairs = result.qc["internal_consistency"]["pairs"]
    improved = sum(1 for q in pairs
                   if q.get("chamfer_aligned") is not None
                   and q.get("chamfer_raw") is not None
                   and q["chamfer_aligned"] < q["chamfer_raw"])
    print(f"QC: {improved}/{len(pairs)} adjacent pairs improved (Chamfer); "
          f"all finite = {result.qc['finiteness']['all_finite']}")
    if result.warnings:
        print(f"warnings: {len(result.warnings)} (see {args.output}/warnings.json)")

    # Confirm the saved affine transforms replay to the kernel's align1.
    slices = FlowImport(cfg.workdir).slices
    rep = verify_affine_replay(slices, result.transforms, slices[0].index)
    print(f"affine replay within tolerance: {rep['within_tol']} "
          f"(max abs error {rep['max_abs_error']:.3g})")


if __name__ == "__main__":
    main()
