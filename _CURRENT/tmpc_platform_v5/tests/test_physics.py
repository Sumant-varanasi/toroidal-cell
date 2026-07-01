"""Physics-core tests: reflection law, surface limits, simulation invariants."""
import numpy as np
import pytest

from tmpc_platform_v5 import (TMPCConfig, simulate_tmpc, reflect,
                              ToroidalSurface, compute_losses)


def test_reflection_law_specular():
    # incoming at 45 deg onto a +z normal reflects to mirror angle
    d = np.array([1.0, 0.0, -1.0]) / np.sqrt(2)
    n = np.array([0.0, 0.0, 1.0])
    r = reflect(d, n)
    assert np.allclose(r, np.array([1.0, 0.0, 1.0]) / np.sqrt(2), atol=1e-9)
    # reflection preserves the tangential component, flips the normal one
    assert np.isclose(r @ n, -(d @ n), atol=1e-9)


def test_toroidal_reduces_to_sphere():
    # R_t == R_s : normal at vertex points along the optical axis
    s = ToroidalSurface(R_t=100, R_s=100, aperture=10,
                        center=np.zeros(3),
                        normal=np.array([0, 0, 1.0]),
                        sag_axis=np.array([0, 1.0, 0]))
    n = s.normal_at(np.array([0.0, 0.0, 0.0]))
    assert np.allclose(np.abs(n), np.array([0, 0, 1.0]), atol=1e-6)


def test_loss_monotonic_in_bounces():
    a = compute_losses(50, 0.99, 1.0, 8.0, 1.0)
    b = compute_losses(100, 0.99, 1.0, 8.0, 1.0)
    assert b.reflectivity_loss > a.reflectivity_loss
    assert b.throughput < a.throughput


def test_clipping_zeroes_throughput():
    clipped = compute_losses(10, 0.99, 9.0, 8.0, 1.0, clipped=True)
    assert clipped.throughput == 0.0


def test_simulate_ring_smoke():
    cfg = TMPCConfig(N=12, R_ring=60, H=40, R_t=120, R_s=120,
                     chord_skip=5, w0=0.5)
    cfg.n_passes = 8 * cfg.N
    res = simulate_tmpc(cfg)
    assert res.bounces > 0
    assert res.opl > 0
    assert 0.0 <= res.throughput <= 1.0
    assert res.spot_pattern.shape[1] == 3
    assert len(res.w_tangential) == res.bounces + 1
    assert len(res.aoi) == res.bounces


def test_simulate_spiral_closure_and_aoi():
    cfg = TMPCConfig(N=8, R_ring=50, H=40, R_t=1e9, R_s=1e9,
                     topology="spiral", M_halflaps=16, w0=1.0)
    res = simulate_tmpc(cfg)
    # spiral visits 2*j_up = N*M_halflaps bounces
    assert res.bounces == cfg.N * cfg.M_halflaps
    # AOI of a regular polygon path
    assert np.isclose(res.aoi.mean(), np.degrees(np.pi/2 - np.pi/cfg.N), atol=1e-6)
    # beam spans the full cell height
    assert res.spot_pattern[:, 2].max() > 0 and res.spot_pattern[:, 2].min() < 0


def test_chord_skip_validation():
    with pytest.raises(ValueError):
        TMPCConfig(N=8, chord_skip=8)  # must be < N
    with pytest.raises(ValueError):
        TMPCConfig(N=2)                # N >= 3


def test_opl_grows_with_chord_skip():
    def opl(skip):
        c = TMPCConfig(N=12, R_ring=60, H=40, R_t=120, R_s=120, chord_skip=skip)
        c.n_passes = 8 * c.N
        return simulate_tmpc(c).opl
    # longer chords (bigger skip, up to N/2) => longer OPL
    assert opl(5) > opl(1)
