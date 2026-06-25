"""Smoke tests for the physics engine."""
import numpy as np
import pytest
from tmpc_platform.physics_engine import (
    ToroidalSurface, Ray, reflect, GaussianBeam,
    TMPCConfig, simulate_tmpc, compute_losses,
    stability_parameter, is_stable, reentrance_score,
)


def test_reflection_law():
    n = np.array([0.0, 0.0, 1.0])
    d_in = np.array([1.0, 0.0, -1.0]) / np.sqrt(2)
    d_out = reflect(d_in, n)
    expected = np.array([1.0, 0.0, 1.0]) / np.sqrt(2)
    assert np.allclose(d_out, expected, atol=1e-9)


def test_toroidal_intersection_sphere_limit():
    # Sphere limit: R_t == R_s; ray straight at the centre should hit at z=0
    s = ToroidalSurface(R_t=50.0, R_s=50.0, aperture=10.0,
                        center=np.array([0., 0., 0.]),
                        normal=np.array([0., 0., 1.]),
                        sag_axis=np.array([0., 1., 0.]))
    t, p = s.intersect(np.array([0., 0., -10.]), np.array([0., 0., 1.]))
    assert t is not None
    assert np.isclose(p[2], 0.0, atol=1e-6)


def test_stability_and_reentrance():
    assert is_stable(50.0, 100.0)
    assert not is_stable(300.0, 100.0)
    # coprime: N=8, k=3 -> period 8 -> reentrance = 1.0
    assert np.isclose(reentrance_score(8, 3), 1.0)
    # non-coprime: N=8, k=2 -> period 4 -> 0.5
    assert np.isclose(reentrance_score(8, 2), 0.5)


def test_gaussian_beam():
    b = GaussianBeam(wavelength=1.654e-3, w0=0.5)
    assert b.w(0.0) == pytest.approx(0.5, rel=1e-9)
    assert b.w(b.zR) == pytest.approx(0.5 * np.sqrt(2), rel=1e-9)


def test_loss_budget_monotone():
    a = compute_losses(50, 0.999, w_max=1.0, aperture=8.0,
                       beam_diameter_in=1.0, clipped=False)
    b = compute_losses(100, 0.999, w_max=1.0, aperture=8.0,
                       beam_diameter_in=1.0, clipped=False)
    assert b.throughput < a.throughput


def test_simulate_tmpc_runs():
    cfg = TMPCConfig(N=8, chord_skip=3, n_passes=16)
    res = simulate_tmpc(cfg)
    assert res.bounces > 0
    assert res.opl > 0
    assert 0.0 <= res.throughput <= 1.0
    assert res.spot_pattern.shape[1] == 3
