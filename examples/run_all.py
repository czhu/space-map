#!/usr/bin/env python
"""One-click runner for the Space-map example datasets.

Runs any of three flows end-to-end and writes aligned points, per-channel
3D-volume TIFFs, and a 3D reconstruction PNG:

  xenium      Xenium polyp, single-channel (density) registration
  duodenum    CODEX duodenum, single-channel (raw_x/raw_y)
  celltype    Xenium polyp, MULTI-channel: density features + cell-type-weighted
              affine selection (uses FlowImport.init_from_codex_multi)

Data is assumed already downloaded; pass the local CSV path (or rely on the
built-in defaults). Examples::

    python examples/run_all.py all
    python examples/run_all.py xenium --data /path/xenium_polyp.csv.gz -o out
    python examples/run_all.py celltype --top-n 10
"""
from __future__ import annotations

import argparse
import os
import sys

# Ensure THIS repo's space_map wins over any editable/site-packages install.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")  # headless: save PNGs without a display

# Built-in default local paths (edit to your machine, or pass --data).
DEFAULTS = {
    "xenium": "/Users/hrd/CODE/works/3DCell/points2/spacemap_pack/data/hf_upload/xenium_polyp.csv.gz",
    "duodenum": "/Users/hrd/CODE/works/3DCell/points2/spacemap_pack/data/hf_upload/codex_duodenum.csv.gz",
    "celltype": "/Users/hrd/CODE/works/3DCell/points2/spacemap_pack/data/hf_upload/xenium_polyp.csv.gz",
}


def _layer_key(v):
    s = str(v)
    if len(s) > 1 and s[0].isalpha() and s[1:].isdigit():
        return (0, int(s[1:]))
    try:
        return (0, int(s))
    except ValueError:
        return (1, s)


def _load_layers(path, x_col, y_col, layer_col):
    import numpy as np
    import pandas as pd
    df = pd.read_csv(path, usecols=[x_col, y_col, layer_col])
    xys = []
    for k in sorted(df[layer_col].unique(), key=_layer_key):
        sub = df[df[layer_col] == k]
        xys.append(sub[[x_col, y_col]].to_numpy(np.float64))
    return xys


def _summarize(result):
    pairs = result.qc["internal_consistency"]["pairs"]
    improved = sum(1 for p in pairs
                   if p.get("chamfer_aligned") is not None
                   and p.get("chamfer_raw") is not None
                   and p["chamfer_aligned"] < p["chamfer_raw"])
    print(f"  QC: {improved}/{len(pairs)} adjacent pairs improved (Chamfer); "
          f"all finite = {result.qc['finiteness']['all_finite']}")
    print(f"  timings: {result.manifest['timings']}")


def run_single(name, data, out, x_col, y_col, layer_col, method):
    """Single-channel flow via the public register() API + 3D PNG."""
    import numpy as np
    from space_map.api import register, RegistrationConfig
    xys = _load_layers(data, x_col, y_col, layer_col)
    print(f"[{name}] {len(xys)} layers, {sum(len(a) for a in xys):,} cells")
    cfg = RegistrationConfig(workdir=f"{out}/_work", seed=0, method=method, strict=False)
    result = register(xys, cfg)
    result.save(out)
    _summarize(result)
    _plot_3d(result.aligned, f"{out}/reconstruction_3d.png", f"{name} - aligned 3D")
    print(f"[{name}] done -> {out}")


def _plot_3d(layers, save, title, subsample=8000, seed=0):
    import numpy as np
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    rng = np.random.RandomState(seed)
    spans = [max(np.ptp(a[:, 0]), np.ptp(a[:, 1])) for a in layers if len(a)]
    z_gap = (np.median(spans) / max(len(layers), 1)) if spans else 1.0
    fig = plt.figure(figsize=(9, 8))
    ax = fig.add_subplot(111, projection="3d")
    for i, a in enumerate(layers):
        if subsample and len(a) > subsample:
            a = a[rng.choice(len(a), subsample, replace=False)]
        ax.scatter(a[:, 0], a[:, 1], np.full(len(a), i * z_gap), s=0.3, alpha=0.4)
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("layer (Z)")
    ax.set_title(title)
    fig.tight_layout()
    os.makedirs(os.path.dirname(save), exist_ok=True)
    fig.savefig(save, dpi=150)
    print(f"  3D reconstruction -> {save}")


def run_celltype(data, out, layer_col, celltype_col, x_col, y_col, method,
                 top_n, ldm):
    """Multi-channel flow: density features + cell-type-weighted affine."""
    import space_map
    from space_map import Slice
    from space_map.flow import FlowImport, FlowExport, AutoFlowMultiCenter4
    fi = FlowImport(f"{out}/_work")
    slices = fi.init_from_codex_multi(
        data, layer_col=layer_col, celltype_col=celltype_col,
        x_col=x_col, y_col=y_col, top_n=top_n)
    print(f"[celltype] {len(slices)} slices; channels on slice0:",
          sorted(slices[0].imgs.keys()))
    af = AutoFlowMultiCenter4(slices, initJKey=Slice.rawKey, alignMethod=method)
    af.affine(useKey="DF", show=False)
    key = Slice.align1Key
    if ldm:
        af.ldm_pair(Slice.align1Key, Slice.align2Key, show=False)
        key = Slice.align2Key
    fe = FlowExport(slices)
    fe.export_all_channels(key, path=f"{out}/all_channels.csv")
    fe.export_imaris_tiff(f"{out}/imaris", key=key)
    tiffs = fe.export_channel_tiffs(f"{out}/tiff/vol", key=key)
    print(f"[celltype] wrote per-layer Imaris TIFFs and {len(tiffs)} per-channel volumes")
    fe.plot_3d(key=key, channel="DF", save=f"{out}/reconstruction_3d_density.png",
               title="celltype - density (aligned 3D)")
    ct = [k for k in slices[0].imgs if k.startswith("ct::")]
    if ct:
        fe.plot_3d(key=key, channel=ct[0],
                   save=f"{out}/reconstruction_3d_{ct[0].replace('::', '_')}.png",
                   title=f"celltype - {ct[0]} (aligned 3D)")
    print(f"[celltype] done -> {out}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("flow", choices=["xenium", "duodenum", "celltype", "all"])
    p.add_argument("--data", help="input CSV (.csv/.csv.gz); default is per-flow")
    p.add_argument("--out", "-o", default="out", help="output base dir")
    p.add_argument("--method", default="auto")
    p.add_argument("--top-n", type=int, default=10, help="celltype: top-N types")
    p.add_argument("--no-ldm", action="store_true",
                   help="celltype: affine only, skip the non-rigid step")
    args = p.parse_args(argv)

    flows = ["xenium", "duodenum", "celltype"] if args.flow == "all" else [args.flow]
    for f in flows:
        data = args.data or DEFAULTS[f]
        out = os.path.join(args.out, f)
        if f == "xenium":
            run_single("xenium", data, out, "x", "y", "layer", args.method)
        elif f == "duodenum":
            run_single("duodenum", data, out, "raw_x", "raw_y", "layer", args.method)
        elif f == "celltype":
            run_celltype(data, out, "layer", "cell_type", "x", "y",
                         args.method, args.top_n, not args.no_ldm)


if __name__ == "__main__":
    main()
