"""``space-map`` command-line interface.

Thin wrapper over :func:`space_map.api.register`. Reads a coordinate CSV,
runs the registration, and writes aligned coordinates + provenance to an
output directory. Only calls the shell facade; never touches the kernel.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Optional

import numpy as np


def _load_layers(csv_path: str, x_col: str, y_col: str, layer_col: str):
    """Return (xys, ids) from a generic long-format CSV, or None if the CSV is
    CODEX-style (has an ``array`` column) and should be passed through as a path.
    """
    import pandas as pd
    df = pd.read_csv(csv_path)
    cols = set(df.columns)
    if "array" in cols and layer_col not in cols:
        return None  # CODEX-style: let register() handle grouping by "array"
    missing = {x_col, y_col, layer_col} - cols
    if missing:
        raise SystemExit(
            f"CSV missing columns {sorted(missing)}; found {sorted(cols)}")
    xys: List[np.ndarray] = []
    ids: List[str] = []
    for layer, g in df.groupby(layer_col, sort=True):
        xys.append(g[[x_col, y_col]].to_numpy(dtype=np.float64))
        ids.append(str(layer))
    return xys, ids


def _cmd_register(args: argparse.Namespace) -> int:
    from .config import RegistrationConfig
    from .register import register

    config = RegistrationConfig(
        workdir=args.workdir or os.path.join(args.output, "_work"),
        method=args.method,
        device=args.device,
        seed=args.seed,
        workers=args.workers,
        resume=args.resume,
        strict=not args.no_strict,
    )
    if args.config:
        with open(args.config) as f:
            config = RegistrationConfig.from_dict({**config.to_dict(), **json.load(f)})

    loaded = _load_layers(args.input, args.x_col, args.y_col, args.layer_col)
    data = args.input if loaded is None else loaded[0]

    result = register(data, config)
    out = result.save(args.output)
    n = sum(len(a) for a in result.aligned)
    print(f"registered {len(result.aligned)} layers ({n} cells) -> {out}")
    if result.warnings:
        print(f"  {len(result.warnings)} warning(s); see {out}/warnings.json",
              file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="space-map",
                                description="space_map registration CLI")
    sub = p.add_subparsers(dest="command", required=True)

    r = sub.add_parser("register", help="register a stack of slices from a CSV")
    r.add_argument("input", help="input CSV (long-format x,y,layer or CODEX array/x/y)")
    r.add_argument("--output", "-o", required=True, help="output directory")
    r.add_argument("--workdir", help="kernel work dir (default: <output>/_work)")
    r.add_argument("--config", help="JSON file of RegistrationConfig overrides")
    r.add_argument("--method", default=None, help="affine method (sift/sift_vgg/loftr/auto)")
    r.add_argument("--device", default=None, help="torch device (cuda:0/mps/cpu)")
    r.add_argument("--seed", type=int, default=None, help="random seed")
    r.add_argument("--workers", type=int, default=None, help="parallel worker count")
    r.add_argument("--resume", action="store_true", help="reuse existing workdir/conf.json")
    r.add_argument("--no-strict", action="store_true", help="allow fallback/dropped cells")
    r.add_argument("--x-col", default="x")
    r.add_argument("--y-col", default="y")
    r.add_argument("--layer-col", default="layer")
    r.set_defaults(func=_cmd_register)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
