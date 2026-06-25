"""Top-level toroidal multipass cell simulation.

Combines the chord-pattern geometry (validated v1 + chord_skip extension)
with 3D ray tracing on toroidal surfaces and Gaussian beam propagation.

The mirrors are arranged uniformly on a ring of radius R_ring at height
z = +/- H/2 (two-tier configuration where appropriate; here we use a single
ring of N mirrors all facing the cell axis, as in the validated Tuzson/Graf
geometry).

Each pass follows a chord with index step `chord_skip` (mod N). For
chord_skip coprime with N the beam visits all N mirror positions before
returning, giving 2N bounces per revolution and a rich spot pattern.
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List
from .toroidal_surface import ToroidalSurface
from .ray_tracer import Ray, trace_ray
from .gaussian_beam import GaussianBeam, propagate_through_cell


@dataclass
class TMPCConfig:
    N: int = 8                      # number of mirrors
    R_ring: float = 50.0            # ring radius [mm]
    H: float = 40.0                 # cell height [mm]
    R_t: float = 100.0              # tangential ROC of each mirror [mm]
    R_s: float = 100.0              # sagittal   ROC of each mirror [mm]
    mirror_aperture: float = 8.0    # clear aperture radius [mm]
    chord_skip: int = 1             # mirror index step per bounce
    n_passes: int = 64              # target number of bounces
    wavelength: float = 1.654e-3    # [mm] 1654 nm
    w0: float = 0.5                 # input beam waist radius [mm]
    input_offset_z: float = 0.0     # vertical entrance offset
    input_angle: float = 0.0        # entrance tilt [rad]
    reflectivity: float = 0.999     # per-bounce mirror reflectivity

    def __post_init__(self):
        if self.N < 3:
            raise ValueError("N must be >= 3")
        if self.chord_skip < 1 or self.chord_skip >= self.N:
            raise ValueError("chord_skip must be in [1, N-1]")


@dataclass
class SimResult:
    config: TMPCConfig
    bounces: int
    opl: float
    spot_pattern: np.ndarray            # (n_bounces, 3) hit positions
    aoi: np.ndarray                     # per-bounce angle of incidence [deg]
    w_max: float                        # max beam radius during propagation
    clipped: bool
    throughput: float                   # net optical power transmission
    stability_g: float                  # cavity g parameter (effective)
    volume_utilisation: float           # fraction of cell interior swept
    notes: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "N": self.config.N, "R_ring": self.config.R_ring, "H": self.config.H,
            "R_t": self.config.R_t, "R_s": self.config.R_s,
            "chord_skip": self.config.chord_skip,
            "w0": self.config.w0, "wavelength": self.config.wavelength,
            "reflectivity": self.config.reflectivity,
            "input_offset_z": self.config.input_offset_z,
            "input_angle": self.config.input_angle,
            "bounces": self.bounces, "opl_m": self.opl * 1e-3,
            "w_max_mm": self.w_max, "clipped": int(self.clipped),
            "throughput": self.throughput, "stability_g": self.stability_g,
            "volume_utilisation": self.volume_utilisation,
            "aoi_mean": float(np.mean(self.aoi)) if len(self.aoi) else 0.0,
            "aoi_max":  float(np.max(self.aoi))  if len(self.aoi) else 0.0,
        }


def _build_mirror_ring(cfg: TMPCConfig) -> List[ToroidalSurface]:
    mirrors = []
    for k in range(cfg.N):
        theta = 2 * np.pi * k / cfg.N
        c = np.array([cfg.R_ring * np.cos(theta),
                      cfg.R_ring * np.sin(theta), 0.0])
        # mirror normal points inward (toward ring centre)
        n = -np.array([np.cos(theta), np.sin(theta), 0.0])
        # sagittal direction = vertical
        sag = np.array([0.0, 0.0, 1.0])
        mirrors.append(ToroidalSurface(
            R_t=cfg.R_t, R_s=cfg.R_s, aperture=cfg.mirror_aperture,
            center=c, normal=n, sag_axis=sag))
    return mirrors


def _bounce_sequence(cfg: TMPCConfig) -> List[int]:
    """Mirror indices visited in order, starting at mirror 0."""
    seq = [0]
    k = 0
    for _ in range(cfg.n_passes - 1):
        k = (k + cfg.chord_skip) % cfg.N
        seq.append(k)
    return seq


def _entrance_ray(cfg: TMPCConfig, mirrors: List[ToroidalSurface]) -> Ray:
    """Construct an entrance ray that hits mirror 0 first and then, after
    reflection, heads toward mirror `chord_skip` (i.e. obeys the chord pattern).

    Geometry: mirror 0 sits at (R,0,0) with inward normal n0=(-1,0,0).
    We want the *reflected* direction at mirror 0 to point from mirror 0 to
    mirror chord_skip (with small z-component for the helical / non-planar
    trajectory introduced by input_offset_z).
    """
    m0 = mirrors[0].center
    m1 = mirrors[cfg.chord_skip % cfg.N].center
    desired_out = m1 - m0
    desired_out = desired_out + np.array([0.0, 0.0, cfg.input_offset_z])
    desired_out /= np.linalg.norm(desired_out)

    # Incident direction d satisfies: d_out = d - 2(d.n)n
    # For mirror 0 with normal n0 = -m0/|m0| (inward), reflecting just flips
    # the component along n0. So incident = desired_out with that component
    # negated.
    n0 = -m0 / np.linalg.norm(m0)
    comp_along_n = (desired_out @ n0) * n0
    comp_perp = desired_out - comp_along_n
    d_in = comp_perp - comp_along_n  # flip the along-normal component
    d_in /= np.linalg.norm(d_in)

    # apply optional small extra tilt about sagittal (z) axis
    if cfg.input_angle != 0.0:
        ca, sa = np.cos(cfg.input_angle), np.sin(cfg.input_angle)
        x, y, z = d_in
        d_in = np.array([ca * x - sa * z, y, sa * x + ca * z])
        d_in /= np.linalg.norm(d_in)

    # entrance point: step backward along -d_in from mirror 0
    entry = m0 - 1.5 * cfg.R_ring * d_in
    return Ray(origin=entry, direction=d_in)


def _volume_utilisation(spot_pattern: np.ndarray, cfg: TMPCConfig,
                        n_samples: int = 2000, beam_radius: float = 2.0) -> float:
    """Monte-Carlo estimate of fraction of cell volume swept by the beam."""
    if len(spot_pattern) < 2:
        return 0.0
    rng = np.random.default_rng(0)
    # sample points inside cylindrical cell volume
    r = cfg.R_ring * 0.9 * np.sqrt(rng.random(n_samples))
    th = 2 * np.pi * rng.random(n_samples)
    z = (cfg.H * 0.5) * (2 * rng.random(n_samples) - 1)
    pts = np.column_stack([r * np.cos(th), r * np.sin(th), z])
    # consecutive bounce points = chord segments
    A = spot_pattern[:-1]
    B = spot_pattern[1:]
    seg = B - A
    seg_len2 = np.einsum("ij,ij->i", seg, seg) + 1e-12
    hits = 0
    for p in pts:
        ap = p[None, :] - A
        t = np.clip(np.einsum("ij,ij->i", ap, seg) / seg_len2, 0, 1)
        closest = A + t[:, None] * seg
        d2 = np.sum((closest - p) ** 2, axis=1)
        if np.min(d2) < beam_radius ** 2:
            hits += 1
    return hits / n_samples


def simulate_tmpc(cfg: TMPCConfig) -> SimResult:
    mirrors = _build_mirror_ring(cfg)
    sequence = _bounce_sequence(cfg)
    surf_seq = [mirrors[i] for i in sequence]

    ray = _entrance_ray(cfg, mirrors)
    aoi_record: List[float] = []
    res = trace_ray(ray, surf_seq, max_bounces=cfg.n_passes,
                    aoi_record=aoi_record)

    # spot pattern from ray history (skip the entrance point)
    hits = np.array(ray.history[1:1 + res["bounces"]]) if res["bounces"] else np.empty((0, 3))

    # Gaussian beam: chord length per pass ~ 2 R_ring sin(pi k / N)
    chord = 2 * cfg.R_ring * np.sin(np.pi * cfg.chord_skip / cfg.N)
    f_t = cfg.R_t / 2.0
    f_s = cfg.R_s / 2.0
    n_bounces = max(1, res["bounces"])
    beam = GaussianBeam(wavelength=cfg.wavelength, w0=cfg.w0)
    prop = propagate_through_cell(
        beam,
        segments=[chord] * n_bounces,
        focal_tan=[f_t] * n_bounces,
        focal_sag=[f_s] * n_bounces,
    )

    # clipping: beam radius vs aperture
    w_max = prop["w_max"]
    clipped = bool(res["clipped"] or w_max >= cfg.mirror_aperture)

    # throughput: per-mirror reflectivity ^ bounces  *  (1 - clipping penalty)
    R = cfg.reflectivity
    throughput = (R ** res["bounces"]) if not clipped else (R ** res["bounces"]) * 0.5

    # stability: g = 1 - d/R  per pass; cavity stable if 0 < g1*g2 < 1
    g = 1.0 - chord / cfg.R_t
    stability_g = g * g  # symmetric ring -> g1 == g2

    vol = _volume_utilisation(hits, cfg) if len(hits) > 1 else 0.0

    return SimResult(
        config=cfg,
        bounces=res["bounces"],
        opl=res["opl"],
        spot_pattern=hits,
        aoi=np.array(aoi_record),
        w_max=float(w_max),
        clipped=clipped,
        throughput=float(throughput),
        stability_g=float(stability_g),
        volume_utilisation=float(vol),
    )
