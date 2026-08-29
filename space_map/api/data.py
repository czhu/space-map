"""Locate Space-map example datasets on disk.

Three serial-section datasets are distributed via a public Google Drive folder.
Download them once into a local data directory, then :func:`fetch` returns the
path to each file. The directory defaults to ``~/.cache/spacemap-data`` and can
be overridden with the ``SPACEMAP_DATA_DIR`` environment variable.

Google Drive folder:
https://drive.google.com/drive/folders/1vjsjZSWu7b8wZgmIUHY3kMTj8POUOOjj
"""
from __future__ import annotations

import os
from typing import Dict, List

GDRIVE_FOLDER = ("https://drive.google.com/drive/folders/"
                 "1vjsjZSWu7b8wZgmIUHY3kMTj8POUOOjj")


def data_dir() -> str:
    """Local directory holding the downloaded datasets."""
    return os.environ.get("SPACEMAP_DATA_DIR",
                          os.path.expanduser("~/.cache/spacemap-data"))


# Logical dataset name -> file name and column preset. For codex_duodenum the
# file merges the registration input (raw_x/raw_y) with a reference alignment
# (x/y); registration uses the raw_* columns.
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


def fetch(name: str) -> str:
    """Return the local path to a dataset file.

    Looks in :func:`data_dir` (``SPACEMAP_DATA_DIR`` or ``~/.cache/spacemap-data``).
    Raises :class:`FileNotFoundError` with download instructions if the file is
    not present — download the datasets once from the Google Drive folder into
    that directory.
    """
    if name not in DATASETS:
        raise ValueError(f"unknown dataset '{name}'; available: {available()}")
    path = os.path.join(data_dir(), DATASETS[name]["filename"])
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"dataset file not found: {path}\n"
            f"Download '{DATASETS[name]['filename']}' from the Google Drive "
            f"folder into {data_dir()} (or set SPACEMAP_DATA_DIR):\n"
            f"  {GDRIVE_FOLDER}"
        )
    return path


def columns(name: str) -> Dict[str, str]:
    """Return the ``x_col``/``y_col``/``layer_col`` preset for a dataset."""
    if name not in DATASETS:
        raise ValueError(f"unknown dataset '{name}'; available: {available()}")
    d = DATASETS[name]
    return {"x_col": d["x_col"], "y_col": d["y_col"], "layer_col": d["layer_col"]}
