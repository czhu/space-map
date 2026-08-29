"""Quality-control diagnostics for a registration run (shell layer).

Computed independently from the kernel's own optimisation objective, over the
aligned coordinates the kernel produced. Split into:

* internal consistency — adjacent-layer bidirectional Chamfer distance and
  point-count conservation. This is a self-consistency (QC) measure, NOT an
  independent accuracy measurement against ground truth.
* finiteness — every aligned coordinate must be finite.

Deformation-field diagnostics (Jacobian determinant, fold count, forward/
inverse consistency) require the dense deformation grid. The default Flow4 path
applies the deformation directly to points and does not export a grid, so those
diagnostics are reported as unavailable-with-reason rather than fabricated.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np

try:
    from scipy.spatial import cKDTree
    _HAVE_KDTREE = True
except Exception:  # pragma: no cover
    _HAVE_KDTREE = False


def _chamfer(a: np.ndarray, b: np.ndarray) -> Optional[float]:
    """Symmetric mean nearest-neighbour distance between two point sets."""
    if len(a) == 0 or len(b) == 0:
        return None
    if _HAVE_KDTREE:
        da, _ = cKDTree(b).query(a)
        db, _ = cKDTree(a).query(b)
        return float((da.mean() + db.mean()) / 2)
    # Fallback: dense (only for small inputs).
    from scipy.spatial.distance import cdist
    dm = cdist(a, b)
    return float((dm.min(axis=1).mean() + dm.min(axis=0).mean()) / 2)


def compute_qc(layer_ids: List[str],
               raw: Optional[List[np.ndarray]],
               aligned: List[np.ndarray]) -> Dict[str, Any]:
    """Assemble the QC report for a run.

    ``raw`` (pre-registration coordinates, same order) is optional; when given,
    adjacent-layer Chamfer is reported before and after so the change is visible.
    """
    report: Dict[str, Any] = {
        "internal_consistency": {},
        "finiteness": {},
        "deformation": {
            "available": False,
            "reason": "Flow4 applies deformation to points directly and exports "
                      "no dense grid; Jacobian/fold/inverse diagnostics require "
                      "a grid-based (e.g. Flow5) run.",
        },
    }

    # --- finiteness + point counts ---
    counts = {}
    nonfinite = {}
    for lid, arr in zip(layer_ids, aligned):
        arr = np.asarray(arr)
        counts[lid] = int(len(arr))
        n_bad = int((~np.isfinite(arr)).any(axis=1).sum()) if len(arr) else 0
        nonfinite[lid] = n_bad
    report["finiteness"] = {
        "aligned_counts": counts,
        "nonfinite_rows": nonfinite,
        "all_finite": all(v == 0 for v in nonfinite.values()),
    }
    if raw is not None:
        raw_counts = {lid: int(len(np.asarray(a)))
                      for lid, a in zip(layer_ids, raw)}
        report["finiteness"]["raw_counts"] = raw_counts
        report["finiteness"]["dropped_cells"] = {
            lid: raw_counts[lid] - counts[lid] for lid in layer_ids
        }

    # --- adjacent-layer Chamfer (self-consistency) ---
    pairs = []
    for i in range(len(aligned) - 1):
        entry: Dict[str, Any] = {
            "layer_i": layer_ids[i], "layer_j": layer_ids[i + 1],
            "chamfer_aligned": _chamfer(np.asarray(aligned[i]),
                                        np.asarray(aligned[i + 1])),
        }
        if raw is not None:
            entry["chamfer_raw"] = _chamfer(np.asarray(raw[i]),
                                            np.asarray(raw[i + 1]))
        pairs.append(entry)
    report["internal_consistency"] = {
        "metric": "bidirectional_mean_chamfer",
        "note": "self-consistency QC, not independent accuracy",
        "pairs": pairs,
    }
    return report
