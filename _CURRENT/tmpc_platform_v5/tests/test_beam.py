"""Beam-physics tests: astigmatic split, M^2 scaling, envelope continuity."""
import numpy as np

from tmpc_platform_v5 import (AstigBeam, astigmatic_focal_lengths,
                              propagate_astigmatic, envelope_along_path)


def test_astigmatic_split_sign():
    # for theta > 0 the tangential focus is shorter, sagittal longer than R/2
    R = 100.0
    f_t, f_s = astigmatic_focal_lengths(R, R, np.radians(60))
    assert f_t < R / 2 < f_s
    # at normal incidence both equal R/2
    f_t0, f_s0 = astigmatic_focal_lengths(R, R, 0.0)
    assert np.isclose(f_t0, R / 2) and np.isclose(f_s0, R / 2)


def test_m2_increases_divergence():
    # higher M^2 => shorter Rayleigh range => faster expansion in free space
    seg = [500.0] * 4
    big_R = [1e9] * 4  # effectively flat: pure free-space expansion
    aoi = [0.0] * 4
    w1 = propagate_astigmatic(AstigBeam(1.654e-3, 0.5, M2=1.0),
                              seg, big_R, big_R, aoi)["w_max"]
    w2 = propagate_astigmatic(AstigBeam(1.654e-3, 0.5, M2=2.0),
                              seg, big_R, big_R, aoi)["w_max"]
    assert w2 > w1


def test_envelope_continuity_and_length():
    spots = np.array([[0, 0, 0], [10, 0, 0], [20, 0, 1.0], [30, 0, 2.0]],
                     dtype=float)
    beam = AstigBeam(1.654e-3, 0.5, M2=1.0)
    n = len(spots) - 1
    env = envelope_along_path(beam, spots, [1e9]*n, [1e9]*n, [0.0]*n,
                              samples_per_segment=10)
    # P = n_segments*samples + 1 endpoint
    assert env["points"].shape[0] == n * 10 + 1
    assert np.all(np.isfinite(env["w"]))
    # radii are positive and vary smoothly (no huge jumps)
    assert np.all(env["w"] > 0)
    assert np.max(np.abs(np.diff(env["w"]))) < 1.0


def test_astigmatic_radii_differ_under_tilt():
    # a real cell at AOI != 0 must split tangential vs sagittal radii
    seg = [100.0] * 8
    Rt = [120.0] * 8
    Rs = [120.0] * 8
    aoi = [np.radians(60)] * 8
    out = propagate_astigmatic(AstigBeam(1.654e-3, 0.5), seg, Rt, Rs, aoi)
    assert not np.allclose(out["w_tangential"], out["w_sagittal"])


def test_converging_injection_waist_inside_cell():
    # with input_waist_offset > 0 the beam is LARGER at the hole than its
    # waist, reaches the waist inside the cell, and the truncation loss is
    # driven by the hole-plane size, not the waist size
    from tmpc_platform_v5 import TMPCConfig, simulate_tmpc

    w0, off = 0.6, 400.0
    zR = np.pi * w0 ** 2 / 1.654e-3
    w_hole_expected = w0 * np.sqrt(1.0 + (off / zR) ** 2)

    base = dict(N=12, R_ring=60.0, H=40.0, R_t=120.0, R_s=120.0,
                chord_skip=5, w0=w0, n_passes=12, hole_radius=1.5)
    res0 = simulate_tmpc(TMPCConfig(**base))                    # legacy
    res1 = simulate_tmpc(TMPCConfig(**base, input_waist_offset=off))

    # legacy launch starts exactly at the waist
    assert np.isclose(res0.w_tangential[0], w0, rtol=1e-6)
    # converging launch starts larger, at the analytic hole-plane radius
    assert np.isclose(res1.w_tangential[0], w_hole_expected, rtol=1e-6)
    assert res1.w_tangential[0] > w0
