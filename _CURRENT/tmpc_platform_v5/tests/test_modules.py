"""Integration tests for the new modules: presets, pareto, validate, viz3d."""
import os
import numpy as np
import pytest

from tmpc_platform_v5 import TMPCConfig, simulate_tmpc


def test_presets_all_simulate():
    from tmpc_platform_v5 import presets
    names = presets.list_presets()
    assert names
    for name in names:
        cfg = presets.get_preset(name)
        res = simulate_tmpc(cfg)
        assert res.bounces > 0


def test_pareto_front_basic():
    from tmpc_platform_v5 import pareto
    rows = [{"a": 1, "b": 1}, {"a": 2, "b": 2}, {"a": 1, "b": 3}]
    # maximise both: (2,2) and (1,3) are non-dominated; (1,1) is dominated
    front = pareto.pareto_front(rows, ["a", "b"], [True, True])
    assert 0 not in front
    assert 1 in front and 2 in front


def test_pareto_search_runs():
    from tmpc_platform_v5 import pareto
    df = pareto.pareto_search(n_samples=32, objectives=("opl_m", "throughput"))
    assert "on_pareto" in df.columns
    assert df["on_pareto"].sum() >= 1


def test_validate_analytic_passes():
    from tmpc_platform_v5 import validate
    cfg = TMPCConfig(N=8, R_ring=50, H=40, R_t=200, R_s=200, chord_skip=1, w0=0.5)
    out = validate.analytic_checks(cfg)
    assert out["pass"]
    assert abs(out["aoi_analytic_deg"] - np.degrees(np.pi/2 - np.pi/8)) < 1e-6


def test_viz3d_writes_html(tmp_path):
    plotly = pytest.importorskip("plotly")
    from tmpc_platform_v5 import viz3d
    cfg = TMPCConfig(N=10, R_ring=60, H=30, R_t=120, R_s=120, chord_skip=3, w0=0.5)
    cfg.n_passes = 6 * cfg.N
    res = simulate_tmpc(cfg)
    paths = viz3d.write_visualisation_bundle(res, cfg, str(tmp_path), name="t")
    for p in paths.values():
        assert os.path.exists(p) and os.path.getsize(p) > 1000
