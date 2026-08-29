"""space_map.api — stable publication-facing shell.

A thin facade over the space_map registration kernel. It does not change kernel
behaviour; it provides a stable, reproducible entry point (:func:`register`),
a typed configuration (:class:`RegistrationConfig`), and a self-describing
result (:class:`RegistrationResult`) with QC, provenance, and replayable
transforms.

Example
-------
>>> from space_map.api import register, RegistrationConfig
>>> result = register(layers, RegistrationConfig(workdir="run-out", seed=0))
>>> result.save("run-out")
"""
from .config import RegistrationConfig
from .result import RegistrationResult
from .register import register
from .qc import compute_qc
from .transform import build_archive, replay_affine, verify_affine_replay

__all__ = ["RegistrationConfig", "RegistrationResult", "register",
           "compute_qc", "build_archive", "replay_affine",
           "verify_affine_replay"]
