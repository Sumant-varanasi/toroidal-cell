"""Tolerance-engine tests: reproducibility, zero-spec invariance, RSS budget."""
import numpy as np

from tmpc_platform_v5 import (TMPCConfig, ToleranceSpec, monte_carlo,
                              sensitivity, tolerance_budget, summarise_mc)


def _cfg():
    c = TMPCConfig(N=12, R_ring=60, H=40, R_t=120, R_s=120, chord_skip=5, w0=0.5)
    c.n_passes = 8 * c.N
    return c


def test_mc_reproducible_under_seed():
    cfg = _cfg()
    spec = ToleranceSpec.research_grade()
    a = monte_carlo(cfg, spec, n_trials=30, seed=7)
    b = monte_carlo(cfg, spec, n_trials=30, seed=7)
    assert np.allclose(a["throughput"].to_numpy(), b["throughput"].to_numpy())
    assert np.allclose(a["exit_drift_mrad"].to_numpy(),
                       b["exit_drift_mrad"].to_numpy())


def test_zero_spec_no_drift():
    cfg = _cfg()
    spec = ToleranceSpec()  # all sigmas zero
    mc = monte_carlo(cfg, spec, n_trials=10, seed=1)
    assert np.allclose(mc["exit_drift_mrad"], 0.0, atol=1e-9)
    assert np.allclose(mc["spot_walk_mm"], 0.0, atol=1e-9)
    # throughput identical across trials (deterministic)
    assert mc["throughput"].std() < 1e-9


def test_sensitivity_ranks_alignment_dominant():
    cfg = _cfg()
    spec = ToleranceSpec.research_grade()
    s = sensitivity(cfg, spec, metric="exit_drift_mrad", n_trials_per_param=15)
    top = s.iloc[0]["param"]
    # per-mirror decenter or tilt should dominate exit pointing
    assert top in ("sigma_d_lateral", "sigma_tilt", "sigma_d_axial")


def test_budget_rss_meets_target():
    cfg = _cfg()
    spec = ToleranceSpec.research_grade()
    s = sensitivity(cfg, spec, metric="exit_drift_mrad", n_trials_per_param=15)
    b = tolerance_budget(s, delta_target=1.0)
    assert np.isclose(b.attrs["rss_combined"], 1.0, rtol=1e-6)
    # every allocated sigma is positive and finite
    assert (b["allocated_sigma"] > 0).all()


def test_summarise_reports_yield():
    cfg = _cfg()
    mc = monte_carlo(cfg, ToleranceSpec.research_grade(), n_trials=40, seed=3)
    summ = summarise_mc(mc, throughput_threshold=0.5)
    assert 0.0 <= summ.attrs["yield_throughput"] <= 1.0
    assert summ.attrs["n_trials"] == 40
