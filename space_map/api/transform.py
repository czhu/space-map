"""Versioned transform archive + replay (shell layer).

Reads the affine matrices the kernel saved during a Flow4 run and packages them
into a self-describing, versioned archive. The archive records conventions,
shapes, preprocessing, software version, and data checksums so a saved run can
be replayed and checked against the in-memory result.

Scope note (Flow4): the affine stage is fully replayable from the saved 3x3
matrices. The non-rigid (SVF-LDDMM) stage applies its deformation to points
directly and exports no dense grid, so it cannot be replayed from a matrix; the
authoritative non-rigid output is the saved aligned point set. The archive marks
the non-rigid part as ``replayable: false`` with that reason rather than
implying a reproducibility it cannot deliver.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

import numpy as np

ARCHIVE_VERSION = "1.0"


def _checksum(arr: np.ndarray) -> str:
    return hashlib.sha256(
        np.ascontiguousarray(np.asarray(arr, dtype=np.float64)).tobytes()
    ).hexdigest()


def build_archive(slices, first_index: str, affine_tag: str = "cell",
                  xyrange: int = 0, xyd: int = 0,
                  software_version: str = "unknown") -> List[Dict[str, Any]]:
    """Build per-layer transform records from the kernel's saved matrices.

    ``slices`` are kernel ``Slice`` objects after a run; ``first_index`` is the
    reference layer (``slices[0].index``) affines accumulate toward.
    """
    records: List[Dict[str, Any]] = []
    for s in slices:
        H = s.data.loadH(first_index, affine_tag)
        if H is None:
            H = np.eye(3)
        records.append({
            "archive_version": ARCHIVE_VERSION,
            "software_version": software_version,
            "source_layer": s.index,
            "target_layer": first_index,
            "affine": {
                "convention": "image-space 3x3 homography (bottom row [0,0,1]); "
                              "apply to points with applyH_np(p, H, xyd=xyd, "
                              "fromImgH=True) which scales translation by xyd; "
                              "maps source-layer coords toward the reference layer",
                "space": "image",
                "matrix": np.asarray(H, dtype=np.float64).tolist(),
                "checksum": _checksum(H),
                "replayable": True,
            },
            "nonrigid": {
                "method": "svf_lddmm",
                "replayable": False,
                "reason": "Flow4 applies the SVF deformation to points directly "
                          "and saves no dense grid; the authoritative non-rigid "
                          "output is the saved aligned point set.",
            },
            "preprocessing": {
                "xyrange": int(xyrange),
                "xyd": int(xyd),
                "note": "coordinates are recentered to xyrange//2 by FlowImport",
            },
            "interpolation": {"boundary": "zero", "order": 1},
        })
    return records


def replay_affine(raw_points: np.ndarray, record: Dict[str, Any]) -> np.ndarray:
    """Apply a record's affine matrix to raw points, reproducing the align1
    coordinates.

    The saved matrix is an *image-space* homography (the kernel forces its
    bottom row to [0,0,1] and stores ``resultH_img()``). The kernel applies it
    to points via ``applyH_np(ps, H, fromImgH=True)``, which scales the
    translation by ``xyd`` before applying. We reproduce that exactly, passing
    the archived ``xyd`` so replay is independent of the current global XYD.
    """
    import space_map
    H = np.asarray(record["affine"]["matrix"], dtype=np.float64)
    xyd = record.get("preprocessing", {}).get("xyd") or None
    return space_map.points.applyH_np(
        np.asarray(raw_points, dtype=np.float64), H, xyd=xyd, fromImgH=True)


def verify_affine_replay(slices, records: List[Dict[str, Any]],
                         first_index: str, tol: float = 1e-6) -> Dict[str, Any]:
    """Check that replaying each affine record on raw points reproduces the
    kernel's saved align1 coordinates within ``tol``."""
    import space_map
    from space_map import Slice
    max_err = 0.0
    per_layer = {}
    for s, rec in zip(slices, records):
        raw = np.asarray(s.ps(Slice.rawKey), dtype=np.float64)
        replayed = replay_affine(raw, rec)
        try:
            expected = np.asarray(s.ps(Slice.align1Key), dtype=np.float64)
        except Exception:
            per_layer[s.index] = None
            continue
        if replayed.shape != expected.shape:
            per_layer[s.index] = float("inf")
            max_err = float("inf")
            continue
        err = float(np.abs(replayed - expected).max()) if len(raw) else 0.0
        per_layer[s.index] = err
        max_err = max(max_err, err)
    return {"max_abs_error": max_err, "within_tol": max_err <= tol,
            "tol": tol, "per_layer": per_layer}
