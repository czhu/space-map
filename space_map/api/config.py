"""Stable configuration for a space_map registration run.

This is part of the publication-facing shell (``space_map.api``). It does not
change kernel behaviour; it only records the effective settings a run was
launched with so the result is reproducible and self-describing.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any


@dataclass
class RegistrationConfig:
    """Effective settings for one registration run.

    Attributes
    ----------
    method:
        Affine matching method passed to the kernel (``alignMethod``). ``None``
        lets the kernel choose its default (``sift_vgg``). Accepted values
        mirror the kernel: ``"sift"``, ``"sift_vgg"``, ``"loftr"``, ``"auto"``.
    device:
        Torch device string (``"cuda:0"``, ``"mps"``, ``"cpu"``). ``None`` uses
        the kernel's auto-detection (cuda -> mps -> cpu).
    seed:
        Seed applied to numpy / torch / python random before the run for
        reproducibility. ``None`` leaves RNGs untouched.
    workers:
        Worker-process count for the kernel's parallel affine search. ``None``
        keeps the kernel default.
    workdir:
        Directory the kernel initialises as its project (raw/imgs/outputs).
        Required at run time; may be set later via :func:`register`.
    resume:
        If True and ``workdir`` already holds a ``conf.json``, reuse it instead
        of re-importing coordinates.
    strict:
        Publication mode. When True the shell rejects any run that produced
        silent stage fallback, dropped cells, or non-finite output.
    imgconf_raw:
        Value for ``space_map.IMGCONF["raw"]`` (1 keeps density, 0 binarizes).
    ratio:
        Canvas padding ratio forwarded to ``FlowImport.ratio`` (kernel default
        1.4).
    """

    method: Optional[str] = None
    device: Optional[str] = None
    seed: Optional[int] = None
    workers: Optional[int] = None
    workdir: Optional[str] = None
    resume: bool = False
    strict: bool = True
    imgconf_raw: int = 1
    ratio: float = 1.4
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RegistrationConfig":
        known = {f: d[f] for f in cls.__dataclass_fields__ if f in d}
        return cls(**known)
