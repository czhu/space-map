"""Helpers to turn 10x / Xenium sparse expression matrices into the wide
DataFrame that ``Slice.init_df`` consumes.

These are *input helpers only* — they do not change how a slice is initialized.
You load a matrix, join expression onto per-cell coordinates by cell id, pick a
few genes, and get back a wide ``[x, y, celltype?, <gene>...]`` DataFrame to
pass straight into ``init_df`` (or ``FlowImport.init_multi`` per layer).

A 10x matrix directory holds:
    matrix.mtx.gz     MatrixMarket sparse counts, shape (n_features, n_cells)
    features.tsv.gz   gene table (ENSEMBL id, symbol, type)
    barcodes.tsv.gz   one cell barcode per column of the matrix

The matrix has no coordinates; barcodes are joined to a coordinate table
(the main CSV) on its cell-id column.
"""
from __future__ import annotations

import gzip
import os
from typing import List, Optional, Sequence

import numpy as np
import pandas as pd


def _read_lines(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt") as f:
        return [ln.rstrip("\n") for ln in f]


def load_10x_matrix(matrix_dir: str, use_symbol: bool = True):
    """Read a 10x matrix directory into a dense ``(cells x genes)`` DataFrame.

    Returns a DataFrame indexed by barcode, one column per gene. Only call this
    for a manageable gene panel (Xenium panels are hundreds of genes); it
    densifies the matrix.
    """
    from scipy.io import mmread

    mpath = os.path.join(matrix_dir, "matrix.mtx.gz")
    if not os.path.exists(mpath):
        mpath = os.path.join(matrix_dir, "matrix.mtx")
    fpath = os.path.join(matrix_dir, "features.tsv.gz")
    if not os.path.exists(fpath):
        fpath = os.path.join(matrix_dir, "features.tsv")
    bpath = os.path.join(matrix_dir, "barcodes.tsv.gz")
    if not os.path.exists(bpath):
        bpath = os.path.join(matrix_dir, "barcodes.tsv")

    mat = mmread(mpath).tocsr()  # (n_features, n_cells)
    barcodes = _read_lines(bpath)
    feat_rows = [ln.split("\t") for ln in _read_lines(fpath)]
    if use_symbol:
        genes = [r[1] if len(r) > 1 else r[0] for r in feat_rows]
    else:
        genes = [r[0] for r in feat_rows]

    # -> (cells x genes)
    dense = np.asarray(mat.todense()).T
    df = pd.DataFrame(dense, index=barcodes, columns=genes)
    # collapse duplicate gene symbols by summing
    if df.columns.duplicated().any():
        df = df.T.groupby(level=0).sum().T
    return df


def top_genes(expr: pd.DataFrame, n: int) -> List[str]:
    """The ``n`` genes with the highest total expression across cells."""
    return list(expr.sum(axis=0).sort_values(ascending=False).index[:n])


def build_wide_df(coords: pd.DataFrame,
                  expr: pd.DataFrame,
                  cell_id_col: str = "cell_id",
                  x_col: str = "x", y_col: str = "y",
                  celltype_col: Optional[str] = "cell_type",
                  genes: Optional[Sequence[str]] = None,
                  top_n: Optional[int] = None,
                  rename_celltype: bool = True) -> pd.DataFrame:
    """Join expression onto coordinates and return an ``init_df`` wide frame.

    coords: per-cell table with x/y, a cell-id column matching the matrix
        barcodes, and optionally a cell-type column.
    expr: cells x genes DataFrame from :func:`load_10x_matrix` (index = barcode).
    genes / top_n: pick genes explicitly, or the top-N by total expression.
        Exactly one should be given (``genes`` wins if both are).

    The result has columns ``[x, y, (celltype), <gene1>, <gene2>, ...]`` where x
    is renamed to ``x`` and y to ``y`` — feed it straight to ``Slice.init_df``.
    Each selected gene becomes its own channel; cells missing from the matrix
    get 0 expression.

    ``rename_celltype`` (default True) renames the cell-type column to the name
    ``Slice.init_df`` expects by default (``"celltype"``), so the wide frame can
    be passed as ``init_df(wide)`` with no extra ``celltype_col=`` argument and
    still auto-expand to one-hot channels.
    """
    if genes is None:
        if top_n is None:
            raise ValueError("pass either genes=[...] or top_n=N")
        genes = top_genes(expr, top_n)
    else:
        missing = [g for g in genes if g not in expr.columns]
        if missing:
            raise ValueError(f"genes not in matrix: {missing}")

    keep = [x_col, y_col, cell_id_col]
    has_ct = bool(celltype_col) and celltype_col in coords.columns
    if has_ct:
        keep.append(celltype_col)
    base = coords[keep].copy()

    sub = expr[list(genes)].reindex(base[cell_id_col]).fillna(0.0)
    sub.index = base.index
    colmap = {x_col: "x", y_col: "y"}
    if has_ct and rename_celltype and celltype_col != "celltype":
        colmap[celltype_col] = "celltype"
    wide = base.drop(columns=[cell_id_col]).rename(columns=colmap)
    for g in genes:
        wide[g] = sub[g].to_numpy()
    return wide
