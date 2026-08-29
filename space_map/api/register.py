"""``register()`` — the single supported entry point of the shell.

Drives the space_map kernel's canonical Flow4 path
(FlowImport -> AutoFlowMultiCenter4.affine -> .ldm_pair) without modifying it,
then reads aligned coordinates back and assembles a reproducible
:class:`RegistrationResult`.
"""
from __future__ import annotations

import os
import time
import random
from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np

from .config import RegistrationConfig
from .result import RegistrationResult

InputData = Union[Sequence[np.ndarray], str]


def _seed_everything(seed: Optional[int]) -> None:
    if seed is None:
        return
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except Exception:
        pass


def _provenance(config: RegistrationConfig, device: str,
                layer_ids: List[str], input_hash: Optional[str]) -> Dict[str, Any]:
    import space_map
    manifest: Dict[str, Any] = {
        "software": {"space_map_version": getattr(space_map, "__version__", "unknown")},
        "config": config.to_dict(),
        "device": device,
        "seed": config.seed,
        "layer_ids": layer_ids,
        "globals": {
            "XYRANGE": int(getattr(space_map, "XYRANGE", 0)),
            "XYD": int(getattr(space_map, "XYD", 0)),
        },
        "timings": {},
    }
    if input_hash is not None:
        manifest["input_sha256"] = input_hash
    return manifest


def _hash_arrays(xys: Sequence[np.ndarray]) -> str:
    import hashlib
    h = hashlib.sha256()
    for a in xys:
        arr = np.ascontiguousarray(np.asarray(a, dtype=np.float64))
        h.update(arr.tobytes())
    return h.hexdigest()


def register(data: InputData, config: Optional[RegistrationConfig] = None,
             **kwargs: Any) -> RegistrationResult:
    """Run a full registration and return aligned coordinates + provenance.

    Parameters
    ----------
    data:
        Either a list of ``(N, 2)`` coordinate arrays (one per layer, in order)
        or a path to a CODEX-style CSV with ``array``/``x``/``y`` columns.
    config:
        A :class:`RegistrationConfig`. Any keyword arguments override its
        fields. ``workdir`` must be resolvable (from config or kwargs).
    """
    import space_map
    from space_map import Slice
    from space_map.flow import FlowImport, AutoFlowMultiCenter4

    config = config or RegistrationConfig()
    if kwargs:
        merged = config.to_dict()
        merged.update(kwargs)
        config = RegistrationConfig.from_dict(merged)

    if not config.workdir:
        raise ValueError("register() requires config.workdir (or workdir=...)")

    warnings: List[Dict[str, Any]] = []
    timings: Dict[str, float] = {}

    _seed_everything(config.seed)

    # Device: honour explicit override, else keep kernel auto-detection.
    if config.device is not None:
        space_map.DEVICE = config.device
    device = str(getattr(space_map, "DEVICE", "cpu"))

    if config.imgconf_raw is not None:
        space_map.IMGCONF = {"raw": config.imgconf_raw}

    os.makedirs(config.workdir, exist_ok=True)

    # ---- Stage 0: import (also re-points kernel BASE + logger to workdir) ----
    t0 = time.time()
    flow = FlowImport(config.workdir)
    flow.ratio = config.ratio
    input_hash: Optional[str] = None

    resume_used = bool(config.resume and os.path.exists(
        os.path.join(config.workdir, "conf.json")))
    if isinstance(data, str):
        if resume_used and flow.slices:
            slices = flow.slices
        else:
            slices = flow.init_from_codex(data)
        layer_ids = [s.index for s in slices]
    else:
        xys = [np.ascontiguousarray(np.asarray(a, dtype=np.float64)) for a in data]
        for i, a in enumerate(xys):
            if a.ndim != 2 or a.shape[1] != 2:
                raise ValueError(f"layer {i}: expected (N,2) array, got {a.shape}")
            if not np.isfinite(a).all():
                raise ValueError(f"layer {i}: coordinates contain non-finite values")
            if len(a) == 0:
                raise ValueError(f"layer {i}: empty coordinate array")
        input_hash = _hash_arrays(xys)
        ids = [str(i) for i in range(len(xys))]
        if resume_used and flow.slices:
            slices = flow.slices
            layer_ids = [s.index for s in slices]
        else:
            slices = flow.init_xys(xys, ids)
            layer_ids = ids
    timings["import"] = time.time() - t0

    # ---- Stage 1: affine ----
    t0 = time.time()
    af = AutoFlowMultiCenter4(slices, initJKey=Slice.rawKey,
                              alignMethod=config.method)
    af.affine(useKey="DF", show=False)
    timings["affine"] = time.time() - t0

    # ---- Stage 2: non-rigid (SVF-LDDMM) ----
    t0 = time.time()
    af.ldm_pair(Slice.align1Key, Slice.align2Key, show=False)
    timings["ldm"] = time.time() - t0

    # ---- Read aligned coordinates back (align2 is Flow4's final output) ----
    aligned: List[np.ndarray] = []
    raw_norm: List[np.ndarray] = []
    for s in slices:
        ps = np.asarray(s.ps(Slice.align2Key), dtype=np.float64)
        if not np.isfinite(ps).all():
            warnings.append({
                "type": "nonfinite_output", "layer": s.index, "blocking": True,
                "message": f"layer {s.index} has non-finite aligned coordinates",
            })
        aligned.append(ps)
        try:
            raw_norm.append(np.asarray(s.ps(Slice.rawKey), dtype=np.float64))
        except Exception:
            raw_norm.append(np.empty((0, 2)))

    from .qc import compute_qc
    qc = compute_qc(layer_ids, raw_norm, aligned)
    # Promote dropped cells to warnings (blocking under strict mode).
    for lid, dropped in qc["finiteness"].get("dropped_cells", {}).items():
        if dropped and dropped > 0:
            warnings.append({
                "type": "dropped_cells", "layer": lid, "blocking": True,
                "count": int(dropped),
                "message": f"layer {lid} dropped {dropped} cells during registration",
            })

    manifest = _provenance(config, device, layer_ids, input_hash)
    manifest["timings"] = timings

    # Versioned transform archive (affine replayable; non-rigid point-authoritative).
    from .transform import build_archive
    transforms = build_archive(
        slices, first_index=slices[0].index, affine_tag="cell",
        xyrange=int(getattr(space_map, "XYRANGE", 0)),
        xyd=int(getattr(space_map, "XYD", 0)),
        software_version=getattr(space_map, "__version__", "unknown"),
    )

    result = RegistrationResult(
        layer_ids=layer_ids,
        aligned=aligned,
        transforms=transforms,
        qc=qc,
        manifest=manifest,
        warnings=warnings,
        workdir=config.workdir,
    )

    if config.strict and result.has_blocking_warnings():
        raise RuntimeError(
            "strict mode: registration produced blocking warnings: "
            + "; ".join(w["message"] for w in warnings if w.get("blocking"))
        )
    return result
