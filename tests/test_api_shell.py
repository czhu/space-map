"""Tests for the space_map.api shell facade.

These exercise the shell, not the kernel internals: config/result plumbing,
QC computation, transform archive + affine replay, and JSON serialization
safety. The end-to-end registration test is marked slow and uses a tiny
synthetic stack so it runs on CPU in seconds.
"""
import json
import os

import numpy as np
import pytest


def _synthetic_stack(n=400, layers=3, seed=0):
    """A small stack: a base point cloud copied across layers with a known
    per-layer translation, so registration has an easy, well-defined target."""
    rng = np.random.RandomState(seed)
    base = rng.uniform(500, 3500, size=(n, 2))
    xys = []
    for i in range(layers):
        shift = np.array([15.0 * i, -10.0 * i])
        xys.append(base + shift + rng.normal(0, 1.5, size=base.shape))
    return xys


def test_config_roundtrip():
    from space_map.api import RegistrationConfig
    c = RegistrationConfig(workdir="w", seed=7, method="sift_vgg")
    d = c.to_dict()
    c2 = RegistrationConfig.from_dict(d)
    assert c2 == c
    # unknown keys are ignored
    c3 = RegistrationConfig.from_dict({**d, "bogus": 1})
    assert c3.seed == 7


def test_result_save_rejects_nan(tmp_path):
    from space_map.api import RegistrationResult
    r = RegistrationResult(
        layer_ids=["0"], aligned=[np.zeros((3, 2))],
        qc={"bad": float("nan")},
    )
    with pytest.raises(ValueError):
        r.save(str(tmp_path / "out"))


def test_result_save_writes_expected_files(tmp_path):
    from space_map.api import RegistrationResult
    r = RegistrationResult(
        layer_ids=["a", "b"],
        aligned=[np.ones((5, 2)), np.zeros((4, 2))],
        qc={"ok": True}, manifest={"v": "x"}, warnings=[],
    )
    out = r.save(str(tmp_path / "out"))
    assert os.path.exists(os.path.join(out, "manifest.json"))
    assert os.path.exists(os.path.join(out, "aligned", "a.npy"))
    loaded = np.load(os.path.join(out, "aligned", "a.npy"))
    assert loaded.shape == (5, 2)


def test_qc_chamfer_and_finiteness():
    from space_map.api import compute_qc
    a = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])
    qc = compute_qc(["0", "1"], [a, a], [a, a.copy()])
    pair = qc["internal_consistency"]["pairs"][0]
    assert pair["chamfer_aligned"] == pytest.approx(0.0, abs=1e-9)
    assert qc["finiteness"]["all_finite"] is True
    assert qc["deformation"]["available"] is False


def test_input_validation_rejects_bad_shapes(tmp_path):
    from space_map.api import register, RegistrationConfig
    cfg = RegistrationConfig(workdir=str(tmp_path / "w"))
    with pytest.raises(ValueError):
        register([np.zeros((10, 3))], cfg)  # not (N,2)
    with pytest.raises(ValueError):
        register([np.array([[1.0, np.nan]])], cfg)  # non-finite


@pytest.mark.slow
def test_end_to_end_toy(tmp_path):
    from space_map.api import register, RegistrationConfig, verify_affine_replay
    from space_map.flow import FlowImport

    xys = _synthetic_stack()
    wd = str(tmp_path / "work")
    cfg = RegistrationConfig(workdir=wd, seed=0, device="cpu",
                             method="sift_vgg", strict=False)
    res = register(xys, cfg)
    assert len(res.aligned) == 3
    assert all(np.isfinite(a).all() for a in res.aligned)
    assert res.qc["finiteness"]["all_finite"]
    assert len(res.transforms) == 3
    out = res.save(str(tmp_path / "out"))
    assert os.path.exists(os.path.join(out, "transforms.json"))

    # affine replay reproduces the kernel's align1 coordinates
    slices = FlowImport(wd).slices
    rep = verify_affine_replay(slices, res.transforms, slices[0].index)
    assert rep["within_tol"], f"affine replay error {rep['max_abs_error']}"
