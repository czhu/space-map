"""Result object for a space_map registration run.

Part of the publication-facing shell (``space_map.api``). Holds the aligned
coordinates read back from the kernel plus reproducibility metadata (QC,
timings, warnings, provenance) and knows how to persist itself.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np


def _json_default(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    raise TypeError(f"not JSON serializable: {type(o)}")


@dataclass
class RegistrationResult:
    """Aligned output plus provenance for one run.

    ``aligned`` is a list of ``(N, 2)`` float arrays, one per layer, in layer
    order. ``layer_ids`` are the string identifiers matching ``aligned``.
    ``transforms`` holds per-layer transform archive records (see
    :mod:`space_map.api.transform`). ``qc`` is the structured quality-control
    report. ``manifest`` records versions, seed, device, hashes, and timings.
    ``warnings`` collects structured warnings (fallback, dropped cells, folds).
    """

    layer_ids: List[str]
    aligned: List[np.ndarray]
    transforms: List[Dict[str, Any]] = field(default_factory=list)
    qc: Dict[str, Any] = field(default_factory=dict)
    manifest: Dict[str, Any] = field(default_factory=dict)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    workdir: Optional[str] = None

    def save(self, out_dir: str) -> str:
        """Write aligned coordinates, transforms, QC and manifest to ``out_dir``.

        Returns the output directory. Coordinates are saved as ``.npy`` per
        layer; metadata as JSON with ``allow_nan=False`` so no non-standard
        NaN/Infinity tokens leak into the archive.
        """
        os.makedirs(out_dir, exist_ok=True)
        coords_dir = os.path.join(out_dir, "aligned")
        os.makedirs(coords_dir, exist_ok=True)
        for lid, arr in zip(self.layer_ids, self.aligned):
            np.save(os.path.join(coords_dir, f"{lid}.npy"), np.asarray(arr))

        for name, payload in (
            ("transforms.json", self.transforms),
            ("qc.json", self.qc),
            ("manifest.json", self.manifest),
            ("warnings.json", self.warnings),
        ):
            with open(os.path.join(out_dir, name), "w") as f:
                json.dump(payload, f, indent=2, allow_nan=False,
                          default=_json_default)
        return out_dir

    def has_blocking_warnings(self) -> bool:
        """True if any warning is severe enough to fail a publication run."""
        return any(w.get("blocking") for w in self.warnings)
