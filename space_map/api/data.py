"""Column presets for the Space-map example datasets.

These datasets are provided as gzipped CSVs; supply your own local path when
loading them. Each entry records the coordinate and layer column names so you
do not have to remember them per platform. For ``codex_duodenum`` the file
merges the registration input (``raw_x``/``raw_y``) with a reference alignment
(``x``/``y``); registration uses the ``raw_*`` columns.
"""
from __future__ import annotations

from typing import Dict, List

# Logical dataset name -> suggested file name and column preset.
DATASETS: Dict[str, Dict] = {
    "xenium_polyp": {
        "filename": "xenium_polyp.csv.gz",
        "x_col": "x", "y_col": "y", "layer_col": "layer",
    },
    "codex_colon": {
        "filename": "codex_colon.csv.gz",
        "x_col": "x", "y_col": "y", "layer_col": "array",
    },
    "codex_duodenum": {
        "filename": "codex_duodenum.csv.gz",
        "x_col": "raw_x", "y_col": "raw_y", "layer_col": "layer",
    },
}


def available() -> List[str]:
    """Names of the known datasets."""
    return list(DATASETS)


def columns(name: str) -> Dict[str, str]:
    """Return the ``x_col``/``y_col``/``layer_col`` preset for a dataset."""
    if name not in DATASETS:
        raise ValueError(f"unknown dataset '{name}'; available: {available()}")
    d = DATASETS[name]
    return {"x_col": d["x_col"], "y_col": d["y_col"], "layer_col": d["layer_col"]}
