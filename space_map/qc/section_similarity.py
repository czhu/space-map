"""Section similarity matrix from feature-point-pair counts.

Computes a pairwise similarity between slices by counting SIFT / LoFTR feature
matches between their density images. The resulting matrix supports:

* inspecting how alike any two sections are,
* ordering sections (greedy nearest-neighbour chain), and
* flagging dissimilar sections whose best match is weak, so they can be dropped.

Feature-pair count is a natural, monotone similarity: well-matched neighbouring
sections share many stable keypoints; a damaged / out-of-series section shares
few with everyone.
"""
from __future__ import annotations

from typing import List, Optional, Sequence

import numpy as np
import space_map


def _match_count(imgI, imgJ, method="sift", matchr=0.75):
    if method == "sift":
        m = space_map.matches.siftImageAlignment(imgI, imgJ, matchr=matchr)
    elif method in ("loftr", "loftr2"):
        m = space_map.matches.loftr_compute_matches(imgI, imgJ, matchr)
    else:
        raise ValueError("unknown method %r (use 'sift' or 'loftr')" % method)
    return int(len(m))


def similarity_matrix(slices: Sequence["space_map.Slice"],
                      dfKey=None, method="sift", matchr=0.75,
                      imgKey="DF", imgConf=None) -> np.ndarray:
    """Symmetric ``(n, n)`` matrix of feature-pair counts between slice images.

    slices: the slices to compare.
    dfKey: which stored key to render (default: raw).
    method: "sift" or "loftr".
    imgKey: which channel to compare (default density "DF").
    imgConf: point-render config; defaults to ``IMGCONF_CMP`` (dilated blobs),
        which gives SIFT/LoFTR stable structure to key on. Bare single-pixel
        dots (raw config) yield no keypoints.
    Diagonal is set to each row's max as a reference and is ignored by the
    helpers below.
    """
    from space_map import Slice
    if dfKey is None:
        dfKey = Slice.rawKey
    if imgConf is None:
        imgConf = space_map.IMGCONF_CMP
    imgs = []
    for s in slices:
        pts = s.imgs[imgKey].get_points(dfKey)
        imgs.append(space_map.show_img(pts, imgConf).astype(np.uint8))
    n = len(imgs)
    M = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i + 1, n):
            c = _match_count(imgs[i], imgs[j], method=method, matchr=matchr)
            M[i, j] = M[j, i] = c
    for i in range(n):
        M[i, i] = M[i].max() if n > 1 else 0.0
    return M


def section_order(M: np.ndarray, start: Optional[int] = None) -> List[int]:
    """Greedy nearest-neighbour ordering of sections by similarity.

    Starts from ``start`` (default: the section with the highest total
    similarity, i.e. the most "central" one) and repeatedly appends the most
    similar not-yet-visited section. Returns a list of indices.
    """
    n = M.shape[0]
    if n == 0:
        return []
    sim = M.copy()
    np.fill_diagonal(sim, -np.inf)
    if start is None:
        totals = np.where(np.isfinite(sim), sim, 0).sum(axis=1)
        start = int(np.argmax(totals))
    order = [start]
    visited = {start}
    while len(order) < n:
        last = order[-1]
        cand = [(sim[last, j], j) for j in range(n) if j not in visited]
        _, nxt = max(cand)
        order.append(nxt)
        visited.add(nxt)
    return order


def dissimilar_sections(M: np.ndarray, ids: Optional[Sequence] = None,
                        z_thresh: float = -1.5):
    """Flag sections whose best neighbour match is an outlier-low count.

    For each section, take its strongest match to any other section
    (``max`` over the off-diagonal row). Sections whose best-match count is more
    than ``|z_thresh|`` standard deviations below the mean are flagged as
    candidates to drop.

    Returns ``(flagged, best_match)`` where ``flagged`` is a list of indices
    (or ids, if provided) and ``best_match`` is the per-section best-match count.
    """
    n = M.shape[0]
    sim = M.copy()
    np.fill_diagonal(sim, -np.inf)
    best = np.array([sim[i][np.isfinite(sim[i])].max() if n > 1 else 0.0
                     for i in range(n)])
    mu, sd = best.mean(), best.std()
    if sd == 0:
        flagged_idx = []
    else:
        z = (best - mu) / sd
        flagged_idx = [i for i in range(n) if z[i] < z_thresh]
    flagged = [ids[i] for i in flagged_idx] if ids is not None else flagged_idx
    return flagged, best


def check_order_from_csv(csv_path, x_col="x", y_col="y", layer_col="layer",
                         method="sift", n_layers=None, plot=True,
                         save_matrix=None, save_plot=None):
    """One-call section-order check from a raw coordinate CSV.

    Builds temporary single-layer Slices from the CSV, computes the pairwise
    SIFT similarity matrix, suggests the correct section order, and flags any
    dissimilar (potentially out-of-order or damaged) sections.

    Parameters
    ----------
    csv_path: path to the CSV (gzipped ok).
    n_layers: limit to the first n layers for a quick check (None = all).
    plot: if True, show the similarity heatmap (requires matplotlib).
    save_matrix: path to save the matrix as .npy (optional).
    save_plot: path to save the heatmap PNG (optional).

    Returns
    -------
    dict with keys:
        ids          -- layer ids in input order
        matrix       -- (n, n) similarity matrix
        suggested_order -- ids in suggested order
        flagged      -- ids of potentially problematic sections
        best_match   -- per-section best match count
    """
    import os, tempfile, shutil
    import pandas as pd

    df = pd.read_csv(csv_path, usecols=[x_col, y_col, layer_col])

    def _layer_key(v):
        s = str(v)
        if len(s) > 1 and s[0].isalpha() and s[1:].isdigit():
            return (0, int(s[1:]))
        try:
            return (0, int(s))
        except ValueError:
            return (1, s)

    layer_ids = sorted(df[layer_col].unique(), key=_layer_key)
    if n_layers:
        layer_ids = layer_ids[:n_layers]

    wd = tempfile.mkdtemp()
    try:
        os.makedirs(wd + "/outputs", exist_ok=True)
        os.makedirs(wd + "/imgs", exist_ok=True)
        old_base = space_map.BASE
        space_map.BASE = wd

        # set XYRANGE from data extent
        sub = df[df[layer_col].isin(layer_ids)]
        span = max(sub[x_col].max() - sub[x_col].min(),
                   sub[y_col].max() - sub[y_col].min())
        from space_map.flow.flowImport import FlowImport
        target = max((int(span * 1.4 / 1000)) * 1000, 1000)
        space_map.XYRANGE = target
        space_map.XYD = int(target / 400 / 5) * 5 + 5

        slices = []
        for lid in layer_ids:
            s = space_map.Slice(index=str(lid), projectf=wd)
            pts = sub[sub[layer_col] == lid][[x_col, y_col]].to_numpy(float)
            mid = pts.max(0) / 2 + pts.min(0) / 2
            pts = pts - mid + target // 2
            import pandas as pd2
            s.init_df(pd2.DataFrame(pts, columns=["x", "y"]))
            slices.append(s)

        M = similarity_matrix(slices, method=method)
        space_map.BASE = old_base
    finally:
        shutil.rmtree(wd)

    ids = [str(lid) for lid in layer_ids]
    order_idx = section_order(M)
    suggested = [ids[i] for i in order_idx]
    flagged, best = dissimilar_sections(M, ids=ids)

    if save_matrix is not None:
        np.save(save_matrix, M)

    if plot or save_plot:
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        im = axes[0].imshow(M, cmap="YlOrRd")
        axes[0].set_title("Section similarity (SIFT match count)")
        axes[0].set_xticks(range(len(ids))); axes[0].set_xticklabels(ids, rotation=90, fontsize=8)
        axes[0].set_yticks(range(len(ids))); axes[0].set_yticklabels(ids, fontsize=8)
        plt.colorbar(im, ax=axes[0])

        axes[1].bar(range(len(ids)), best, color=["red" if id_ in flagged else "steelblue" for id_ in ids])
        axes[1].set_title("Best match per section (red = flagged)")
        axes[1].set_xticks(range(len(ids))); axes[1].set_xticklabels(ids, rotation=90, fontsize=8)
        axes[1].set_xlabel("section"); axes[1].set_ylabel("SIFT match count")
        fig.tight_layout()
        if save_plot:
            os.makedirs(os.path.dirname(save_plot) or ".", exist_ok=True)
            fig.savefig(save_plot, dpi=150)
        if plot:
            plt.show()
        plt.close(fig)

    return {"ids": ids, "matrix": M, "suggested_order": suggested,
            "flagged": flagged, "best_match": best}
