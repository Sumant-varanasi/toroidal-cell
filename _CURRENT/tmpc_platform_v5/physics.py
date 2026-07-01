"""Toroidal-multipass-cell physics core (self-contained).

Combines what v4 split across six files:
    - ToroidalSurface (implicit torus, analytic normal, Newton intersect)
    - Ray + reflect + trace_ray
    - GaussianBeam + ABCD propagation (separate tangential & sagittal)
    - LossBudget + compute_losses
    - stability_parameter, is_stable, reentrance_score
    - TMPCConfig + SimResult + simulate_tmpc

Adds first-class support for per-mirror and global perturbations so the
tolerance module can drive Monte-Carlo without touching this file.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from math import gcd
from typing import List, Optional, Sequence, Tuple

import numpy as np


# =============================================================================
# 1. Utility
# =============================================================================
def _unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / n if n > 1e-20 else v


def _rot_axis_angle(axis: np.ndarray, angle: float) -> np.ndarray:
    """Rodrigues rotation matrix."""
    axis = _unit(np.asarray(axis, dtype=float))
    c, s = np.cos(angle), np.sin(angle)
    K = np.array([[0, -axis[2], axis[1]],
                  [axis[2], 0, -axis[0]],
                  [-axis[1], axis[0], 0]])
    return np.eye(3) * c + s * K + (1 - c) * np.outer(axis, axis)


# =============================================================================
# 2. Toroidal surface
# =============================================================================
@dataclass
class ToroidalSurface:
    R_t: float
    R_s: float
    aperture: float
    center: np.ndarray
    normal: np.ndarray          # outward optical axis (unit)
    sag_axis: np.ndarray        # sagittal direction (unit, ⟂ normal)

    def __post_init__(self):
        self.center = np.asarray(self.center, dtype=float)
        self.normal = _unit(np.asarray(self.normal, dtype=float))
        self.sag_axis = _unit(np.asarray(self.sag_axis, dtype=float))
        # re-orthogonalise sag to normal (in case caller fed in a near-aligned pair)
        self.sag_axis = _unit(self.sag_axis - (self.sag_axis @ self.normal) * self.normal)
        self.tan_axis = _unit(np.cross(self.sag_axis, self.normal))

    # ---- frame transforms ----
    def to_local(self, p: np.ndarray) -> np.ndarray:
        d = p - self.center
        return np.array([d @ self.tan_axis, d @ self.sag_axis, d @ self.normal])

    def to_world(self, q: np.ndarray) -> np.ndarray:
        return (self.center + q[0] * self.tan_axis
                + q[1] * self.sag_axis + q[2] * self.normal)

    def dir_to_local(self, v: np.ndarray) -> np.ndarray:
        return np.array([v @ self.tan_axis, v @ self.sag_axis, v @ self.normal])

    def dir_to_world(self, v: np.ndarray) -> np.ndarray:
        return v[0] * self.tan_axis + v[1] * self.sag_axis + v[2] * self.normal

    # ---- implicit surface ----
    def F_local(self, q: np.ndarray) -> float:
        x, y, z = q
        a = np.sqrt((self.R_t - z) ** 2 + x ** 2) - (self.R_t - self.R_s)
        return a ** 2 + y ** 2 - self.R_s ** 2

    def grad_local(self, q: np.ndarray) -> np.ndarray:
        x, y, z = q
        s = np.sqrt((self.R_t - z) ** 2 + x ** 2) + 1e-30
        a = s - (self.R_t - self.R_s)
        return np.array([2 * a * x / s, 2 * y, -2 * a * (self.R_t - z) / s])

    def normal_at(self, p_world: np.ndarray) -> np.ndarray:
        q = self.to_local(p_world)
        n_local = _unit(self.grad_local(q))
        if n_local[2] < 0:
            n_local = -n_local
        return self.dir_to_world(n_local)

    # ---- ray intersection ----
    def intersect(self, origin: np.ndarray, direction: np.ndarray,
                  t_max: float = 1e4, tol: float = 1e-9, max_iter: int = 40
                  ) -> Tuple[Optional[float], Optional[np.ndarray]]:
        o = self.to_local(origin)
        d = self.dir_to_local(direction)
        if abs(d[2]) < 1e-12:
            return None, None
        t = -o[2] / d[2]
        if t < tol or t > t_max:
            t = max(1e-3, t)
        for _ in range(max_iter):
            q = o + t * d
            F = self.F_local(q)
            if abs(F) < tol:
                break
            dFdt = self.grad_local(q) @ d
            if abs(dFdt) < 1e-20:
                return None, None
            t_new = t - F / dFdt
            if t_new < 0:
                return None, None
            if abs(t_new - t) < tol:
                t = t_new
                break
            t = t_new
        else:
            return None, None
        q = o + t * d
        if np.hypot(q[0], q[1]) > self.aperture:
            return t, None
        return t, self.to_world(q)


# =============================================================================
# 3. Rays + reflection
# =============================================================================
@dataclass
class Ray:
    origin: np.ndarray
    direction: np.ndarray
    path_length: float = 0.0
    alive: bool = True
    history: List[np.ndarray] = field(default_factory=list)

    def __post_init__(self):
        self.origin = np.asarray(self.origin, dtype=float)
        self.direction = _unit(np.asarray(self.direction, dtype=float))
        if not self.history:
            self.history = [self.origin.copy()]

    def advance(self, t: float):
        self.origin = self.origin + t * self.direction
        self.path_length += t
        self.history.append(self.origin.copy())


def reflect(direction: np.ndarray, normal: np.ndarray) -> np.ndarray:
    d = _unit(direction)
    n = _unit(normal)
    return _unit(d - 2.0 * (d @ n) * n)


def trace_ray(ray: Ray, surfaces: Sequence[ToroidalSurface],
              max_bounces: int = 1000,
              aoi_record: Optional[List[float]] = None) -> dict:
    bounces, clipped = 0, False
    for surf in surfaces[:max_bounces]:
        t, p = surf.intersect(ray.origin, ray.direction)
        if t is None:
            ray.alive = False
            break
        if p is None:
            clipped = True
            ray.alive = False
            break
        ray.advance(t)
        n = surf.normal_at(p)
        if aoi_record is not None:
            cos_i = abs(ray.direction @ n)
            aoi_record.append(float(np.degrees(np.arccos(np.clip(cos_i, 0, 1)))))
        ray.direction = reflect(ray.direction, n)
        bounces += 1
    return {"bounces": bounces, "opl": ray.path_length,
            "clipped": clipped, "exit_ray": ray}


# =============================================================================
# 4. Gaussian beam (ABCD, tangential + sagittal)
# =============================================================================
@dataclass
class GaussianBeam:
    wavelength: float
    w0: float
    z0: float = 0.0

    @property
    def zR(self) -> float:
        return np.pi * self.w0 ** 2 / self.wavelength

    def q(self, z: float = 0.0) -> complex:
        return (z - self.z0) + 1j * self.zR

    def w(self, z: float) -> float:
        return self.w0 * np.sqrt(1.0 + ((z - self.z0) / self.zR) ** 2)


def _free_space(d: float) -> np.ndarray:
    return np.array([[1.0, d], [0.0, 1.0]])


def _thin_mirror(f: float) -> np.ndarray:
    return np.array([[1.0, 0.0], [-1.0 / f, 1.0]])


def abcd_propagate(q_in: complex, M: np.ndarray) -> complex:
    A, B = M[0]; C, D = M[1]
    return (A * q_in + B) / (C * q_in + D)


def _w_from_q(q: complex, wavelength: float) -> float:
    inv_q = 1.0 / q
    inv_w2 = -inv_q.imag * np.pi / wavelength
    return np.sqrt(1.0 / inv_w2) if inv_w2 > 0 else float("inf")


def propagate_through_cell(beam: GaussianBeam,
                           segments: Sequence[float],
                           focal_tan: Sequence[float],
                           focal_sag: Sequence[float]) -> dict:
    q_t = beam.q(0.0); q_s = beam.q(0.0)
    w_t = [beam.w0]; w_s = [beam.w0]
    for i, d in enumerate(segments):
        q_t = abcd_propagate(q_t, _free_space(d))
        q_s = abcd_propagate(q_s, _free_space(d))
        if i < len(focal_tan):
            q_t = abcd_propagate(q_t, _thin_mirror(focal_tan[i]))
            q_s = abcd_propagate(q_s, _thin_mirror(focal_sag[i]))
        w_t.append(_w_from_q(q_t, beam.wavelength))
        w_s.append(_w_from_q(q_s, beam.wavelength))
    return {"w_tangential": np.array(w_t), "w_sagittal": np.array(w_s),
            "w_max": max(max(w_t), max(w_s))}


# =============================================================================
# 5. Loss budget
# =============================================================================
@dataclass
class LossBudget:
    reflectivity_loss: float
    clipping_loss: float
    aperture_loss: float
    truncation_loss: float
    total_loss: float
    throughput: float


def compute_losses(bounces: int, reflectivity: float,
                   w_max: float, aperture: float,
                   beam_diameter_in: float, hole_diameter: float = 3.0,
                   clipped: bool = False) -> LossBudget:
    refl_loss = 1.0 - reflectivity ** max(0, bounces)
    clip_loss = 1.0 if clipped else 0.0
    if w_max >= aperture:
        ap_loss = 1.0
    else:
        ap_loss = float(np.exp(-2.0 * (aperture / max(w_max, 1e-6)) ** 2))
    if beam_diameter_in >= hole_diameter:
        trunc_loss = 1.0
    else:
        trunc_loss = float(np.exp(-2.0 * (hole_diameter / max(beam_diameter_in, 1e-6)) ** 2))
    T = (1 - refl_loss) * (1 - clip_loss) * (1 - ap_loss) * (1 - trunc_loss)
    T = float(np.clip(T, 0.0, 1.0))
    return LossBudget(refl_loss, clip_loss, ap_loss, trunc_loss, 1 - T, T)


# =============================================================================
# 6. Stability + re-entrance
# =============================================================================
def stability_parameter(chord_length: float, ROC: float) -> float:
    g = 1.0 - chord_length / ROC
    return g * g


def is_stable(chord_length: float, ROC: float, eps: float = 1e-6) -> bool:
    return -eps <= stability_parameter(chord_length, ROC) <= 1.0 + eps


def reentrance_score(N: int, chord_skip: int) -> float:
    if N <= 0 or chord_skip <= 0:
        return 0.0
    return (N // gcd(N, chord_skip)) / N


# =============================================================================
# 7. Per-mirror & global perturbations
# =============================================================================
@dataclass
class MirrorPerturbation:
    """One mirror's deviations from the nominal ring position.

    All offsets are in the mirror's local frame:
        d_tan, d_sag, d_ax : decenter along tangential / sagittal / axial
        tilt_tan, tilt_sag : tilts about tangential / sagittal axes [rad]
        dR_t, dR_s         : ROC errors [mm] (added to nominal)
        aperture_scale     : multiplier on clear aperture (e.g. 0.98)
    """
    d_tan: float = 0.0
    d_sag: float = 0.0
    d_ax: float = 0.0
    tilt_tan: float = 0.0
    tilt_sag: float = 0.0
    dR_t: float = 0.0
    dR_s: float = 0.0
    aperture_scale: float = 1.0


@dataclass
class GlobalPerturbation:
    """Cell-wide deviations applied before per-mirror perturbations."""
    dR_ring: float = 0.0          # ring radius error [mm]
    dH: float = 0.0               # cell height error [mm]
    d_input_x: float = 0.0        # launch position offsets [mm]
    d_input_y: float = 0.0
    d_input_z: float = 0.0
    d_input_tilt_x: float = 0.0   # launch direction tilts [rad]
    d_input_tilt_y: float = 0.0
    d_reflectivity: float = 0.0
    d_wavelength: float = 0.0     # [mm]


# =============================================================================
# 8. Config + result
# =============================================================================
@dataclass
class TMPCConfig:
    N: int = 8
    R_ring: float = 50.0
    H: float = 40.0
    R_t: float = 100.0
    R_s: float = 100.0
    mirror_aperture: float = 8.0
    chord_skip: int = 1
    n_passes: int = 64
    wavelength: float = 1.654e-3
    w0: float = 0.5
    M2: float = 1.0                 # beam-quality factor (1.0 = diffraction limited)
    input_offset_z: float = 0.0     # launch vertical (sagittal) offset [mm]
    input_offset_t: float = 0.0     # launch in-plane (tangential) offset [mm]
    input_angle: float = 0.0        # launch tilt about sagittal axis [rad]
    input_angle_sag: float = 0.0    # launch tilt about tangential axis [rad]
    reflectivity: float = 0.999
    hole_radius: float = 1.5        # entrance/exit hole radius [mm]
    # ---- topology ----
    #   "ring"   : single ring, beam advances by `chord_skip` mirrors per bounce
    #              (Herriott-style rotating polygon pattern).
    #   "spiral" : beam enters a hole at z=-H/2, spirals UP the polygon, hits a
    #              top retroreflector at z=+H/2, spirals back DOWN, exits the
    #              hole. Closure needs N*M_halflaps even (the Tuzson/Graf cell).
    topology: str = "ring"
    M_halflaps: int = 8             # spiral topology: half-laps before top retro
    astigmatic: bool = True         # use off-axis astigmatic mirror focal lengths

    def __post_init__(self):
        if self.N < 3:
            raise ValueError("N must be >= 3")
        if self.topology not in ("ring", "spiral"):
            raise ValueError("topology must be 'ring' or 'spiral'")
        if self.topology == "ring":
            if self.chord_skip < 1 or self.chord_skip >= self.N:
                raise ValueError("chord_skip must be in [1, N-1]")
        if self.topology == "spiral" and (self.N * self.M_halflaps) % 2 != 0:
            raise ValueError("spiral topology needs N*M_halflaps even")


@dataclass
class SimResult:
    config: TMPCConfig
    bounces: int
    opl: float
    spot_pattern: np.ndarray
    aoi: np.ndarray
    w_max: float
    clipped: bool
    throughput: float
    stability_g: float
    volume_utilisation: float
    loss_budget: LossBudget
    reentrance: float
    # per-plane astigmatic stability (|m|<=1 stable). isotropic g kept above.
    stability_tan: float = 0.0
    stability_sag: float = 0.0
    # realistic-beam extras (per bounce; len = bounces+1, includes waist):
    w_tangential: np.ndarray = field(default_factory=lambda: np.empty(0))
    w_sagittal: np.ndarray = field(default_factory=lambda: np.empty(0))
    mirror_sequence: np.ndarray = field(default_factory=lambda: np.empty(0, int))
    chords: np.ndarray = field(default_factory=lambda: np.empty(0))
    exit_ray: Optional["Ray"] = None
    # spot-pattern diagnostics:
    min_spot_separation: float = 0.0      # closest two distinct spots on a mirror [mm]
    max_spots_per_mirror: int = 0
    spots_overlap: bool = False
    mirror_fill_fraction: float = 0.0
    notes: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        c = self.config
        return {
            "N": c.N, "R_ring": c.R_ring, "H": c.H, "R_t": c.R_t, "R_s": c.R_s,
            "mirror_aperture": c.mirror_aperture, "chord_skip": c.chord_skip,
            "w0": c.w0, "M2": c.M2, "wavelength": c.wavelength,
            "reflectivity": c.reflectivity, "topology": c.topology,
            "input_offset_z": c.input_offset_z, "input_offset_t": c.input_offset_t,
            "input_angle": c.input_angle, "input_angle_sag": c.input_angle_sag,
            "bounces": self.bounces, "opl_m": self.opl * 1e-3,
            "w_max_mm": self.w_max, "clipped": int(self.clipped),
            "throughput": self.throughput, "stability_g": self.stability_g,
            "stability_tan": self.stability_tan, "stability_sag": self.stability_sag,
            "volume_utilisation": self.volume_utilisation,
            "reentrance": self.reentrance,
            "aoi_mean": float(np.mean(self.aoi)) if len(self.aoi) else 0.0,
            "aoi_max":  float(np.max(self.aoi))  if len(self.aoi) else 0.0,
            "min_spot_sep_mm": self.min_spot_separation,
            "max_spots_per_mirror": self.max_spots_per_mirror,
            "spots_overlap": int(self.spots_overlap),
            "mirror_fill_fraction": self.mirror_fill_fraction,
            "refl_loss":  self.loss_budget.reflectivity_loss,
            "clip_loss":  self.loss_budget.clipping_loss,
            "ap_loss":    self.loss_budget.aperture_loss,
            "trunc_loss": self.loss_budget.truncation_loss,
        }

    def exit_pointing_error(self, nominal_dir: Optional[np.ndarray] = None) -> float:
        """Angular deviation [mrad] of the exit ray from a nominal direction
        (defaults to the launch direction reversed). Useful for alignment
        tolerancing — small per-mirror errors walk the exit beam off-axis."""
        if self.exit_ray is None or len(self.spot_pattern) < 2:
            return 0.0
        d = _unit(self.exit_ray.direction)
        if nominal_dir is None:
            nominal_dir = _unit(self.spot_pattern[1] - self.spot_pattern[0])
        cosang = float(np.clip(d @ _unit(nominal_dir), -1, 1))
        return float(np.arccos(abs(cosang)) * 1e3)  # rad -> mrad


# =============================================================================
# 9. Mirror ring construction (with perturbations)
# =============================================================================
def build_mirror_ring(cfg: TMPCConfig,
                      perturbations: Optional[Sequence[MirrorPerturbation]] = None,
                      global_pert: Optional[GlobalPerturbation] = None
                      ) -> List[ToroidalSurface]:
    R_ring = cfg.R_ring + (global_pert.dR_ring if global_pert else 0.0)
    mirrors: List[ToroidalSurface] = []
    perts = list(perturbations) if perturbations else [MirrorPerturbation()] * cfg.N
    if len(perts) != cfg.N:
        raise ValueError(f"need {cfg.N} mirror perturbations, got {len(perts)}")

    for k in range(cfg.N):
        theta = 2 * np.pi * k / cfg.N
        nominal_center = np.array([R_ring * np.cos(theta),
                                   R_ring * np.sin(theta), 0.0])
        nominal_normal = -np.array([np.cos(theta), np.sin(theta), 0.0])
        nominal_sag = np.array([0.0, 0.0, 1.0])
        nominal_tan = _unit(np.cross(nominal_sag, nominal_normal))

        p = perts[k]
        # apply tilts to the optical axis (and follow with the sag axis)
        n = nominal_normal.copy()
        s = nominal_sag.copy()
        if p.tilt_tan != 0.0:
            R = _rot_axis_angle(nominal_tan, p.tilt_tan)
            n = R @ n; s = R @ s
        if p.tilt_sag != 0.0:
            R = _rot_axis_angle(nominal_sag, p.tilt_sag)
            n = R @ n
        # apply decenter
        c = (nominal_center
             + p.d_tan * nominal_tan
             + p.d_sag * nominal_sag
             + p.d_ax * nominal_normal)
        mirrors.append(ToroidalSurface(
            R_t=cfg.R_t + p.dR_t,
            R_s=cfg.R_s + p.dR_s,
            aperture=cfg.mirror_aperture * p.aperture_scale,
            center=c, normal=n, sag_axis=s,
        ))
    return mirrors


# =============================================================================
# 10. Bounce sequence + entrance ray
# =============================================================================
def _bounce_sequence(cfg: TMPCConfig) -> List[int]:
    seq = [0]; k = 0
    for _ in range(cfg.n_passes - 1):
        k = (k + cfg.chord_skip) % cfg.N
        seq.append(k)
    return seq


def _entrance_ray(cfg: TMPCConfig,
                  mirrors: Sequence[ToroidalSurface],
                  global_pert: Optional[GlobalPerturbation] = None,
                  first_idx: int = 0, second_idx: Optional[int] = None) -> Ray:
    """Build the launch ray hitting `first_idx` then heading to `second_idx`.

    Supports arbitrary start-spot offset (tangential + sagittal) and two
    independent launch tilts (about the sagittal and tangential axes).
    """
    if second_idx is None:
        second_idx = cfg.chord_skip % cfg.N
    m0 = mirrors[first_idx].center
    m1 = mirrors[second_idx].center

    # local frame at the launch mirror
    n0 = _unit(-m0) if np.linalg.norm(m0) > 1e-9 else np.array([-1.0, 0.0, 0.0])
    sag0 = np.array([0.0, 0.0, 1.0])
    sag0 = _unit(sag0 - (sag0 @ n0) * n0)
    tan0 = _unit(np.cross(sag0, n0))

    desired_out = _unit(m1 - m0 + cfg.input_offset_z * sag0)
    comp_n = (desired_out @ n0) * n0
    d_in = _unit((desired_out - comp_n) - comp_n)

    # launch tilt about sagittal axis (in-plane steering)
    if cfg.input_angle != 0.0:
        d_in = _unit(_rot_axis_angle(sag0, cfg.input_angle) @ d_in)
    # launch tilt about tangential axis (out-of-plane / vertical steering)
    if cfg.input_angle_sag != 0.0:
        d_in = _unit(_rot_axis_angle(tan0, cfg.input_angle_sag) @ d_in)

    if global_pert is not None:
        if global_pert.d_input_tilt_x != 0.0:
            d_in = _unit(_rot_axis_angle(np.array([1.0, 0.0, 0.0]),
                                         global_pert.d_input_tilt_x) @ d_in)
        if global_pert.d_input_tilt_y != 0.0:
            d_in = _unit(_rot_axis_angle(np.array([0.0, 1.0, 0.0]),
                                         global_pert.d_input_tilt_y) @ d_in)

    entry = m0 - 1.5 * cfg.R_ring * d_in
    # start-spot offset across the launch mirror face
    entry = entry + cfg.input_offset_t * tan0 + cfg.input_offset_z * sag0
    if global_pert is not None:
        entry = entry + np.array([global_pert.d_input_x,
                                  global_pert.d_input_y,
                                  global_pert.d_input_z])
    return Ray(origin=entry, direction=d_in)


# =============================================================================
# 11. Volume utilisation Monte-Carlo
# =============================================================================
def _volume_utilisation(spots: np.ndarray, cfg: TMPCConfig,
                        n_samples: int = 2000, beam_radius: float = 2.0,
                        seed: int = 0) -> float:
    if len(spots) < 2:
        return 0.0
    rng = np.random.default_rng(seed)
    r = cfg.R_ring * 0.9 * np.sqrt(rng.random(n_samples))
    th = 2 * np.pi * rng.random(n_samples)
    z = (cfg.H * 0.5) * (2 * rng.random(n_samples) - 1)
    pts = np.column_stack([r * np.cos(th), r * np.sin(th), z])
    A, B = spots[:-1], spots[1:]
    seg = B - A
    seg_len2 = np.einsum("ij,ij->i", seg, seg) + 1e-12
    hits = 0
    for p in pts:
        ap = p[None, :] - A
        t = np.clip(np.einsum("ij,ij->i", ap, seg) / seg_len2, 0, 1)
        closest = A + t[:, None] * seg
        if np.min(np.sum((closest - p) ** 2, axis=1)) < beam_radius ** 2:
            hits += 1
    return hits / n_samples


# =============================================================================
# 11b. Spot-pattern diagnostics
# =============================================================================
def mirror_footprints(spots: np.ndarray, mirror_seq: np.ndarray,
                      cfg: TMPCConfig) -> dict:
    """Project every bounce hit onto the local (tangential, sagittal) face of
    the mirror it landed on.

    Returns {k: ndarray of shape (m, 3)} where the columns are
    (u_tangential, v_sagittal, visit_order). This is the single source of
    truth for both `spot_diagnostics` and the per-mirror constellation plots.
    """
    out: dict = {}
    if len(spots) == 0:
        return {k: np.empty((0, 3)) for k in range(cfg.N)}
    for k in range(cfg.N):
        idx = np.where(mirror_seq == k)[0]
        if len(idx) == 0:
            out[k] = np.empty((0, 3))
            continue
        theta = 2 * np.pi * k / cfg.N
        c = np.array([cfg.R_ring * np.cos(theta),
                      cfg.R_ring * np.sin(theta), 0.0])
        n = -np.array([np.cos(theta), np.sin(theta), 0.0])
        sag = np.array([0.0, 0.0, 1.0])
        tan = _unit(np.cross(sag, n))
        local = spots[idx] - c
        out[k] = np.column_stack([local @ tan, local @ sag, idx.astype(float)])
    return out


def spot_diagnostics(spots: np.ndarray, mirror_seq: np.ndarray,
                     cfg: TMPCConfig, w_mean: float,
                     dedup_tol: float = 1e-3) -> dict:
    """Closest distinct-spot spacing, max spots on any one mirror, whether any
    two spots overlap (closer than 2*w_mean), and the worst-case fraction of a
    mirror face covered by spots. Built on `mirror_footprints`."""
    if len(spots) == 0:
        return {"min_sep": 0.0, "max_spots": 0, "overlap": False, "fill": 0.0}
    A_mirror = np.pi * cfg.mirror_aperture ** 2
    min_sep = np.inf
    max_spots = 0
    overlap = False
    worst_fill = 0.0
    foot = mirror_footprints(spots, mirror_seq, cfg)
    for k in range(cfg.N):
        uv = foot[k][:, :2] if len(foot[k]) else np.empty((0, 2))
        # dedup coincident revisits
        kept: List[np.ndarray] = []
        for p in uv:
            if all(np.linalg.norm(p - q) > dedup_tol for q in kept):
                kept.append(p)
        kept = np.array(kept)
        max_spots = max(max_spots, len(kept))
        if len(kept) >= 2:
            for i in range(len(kept)):
                for j in range(i + 1, len(kept)):
                    d = float(np.linalg.norm(kept[i] - kept[j]))
                    min_sep = min(min_sep, d)
                    if d < 2 * w_mean:
                        overlap = True
        fill = len(kept) * np.pi * w_mean ** 2 / A_mirror
        worst_fill = max(worst_fill, fill)
    return {"min_sep": float(min_sep) if np.isfinite(min_sep) else 0.0,
            "max_spots": int(max_spots),
            "overlap": bool(overlap),
            "fill": float(min(worst_fill, 1.0))}


# =============================================================================
# 11c. Spiral (retroreflector) topology — analytic trace
# =============================================================================
def _spiral_trace(cfg: TMPCConfig) -> dict:
    """Tuzson/Graf up-down spiral: enter at a hole on mirror 0 at z=-H/2,
    spiral up by one mirror per chord, hit a top retroreflector, spiral back
    down, exit the hole. Returns hit points, mirror ids, per-bounce AOI, OPL.

    AOI at every ring mirror of a regular N-gon path is pi/2 - pi/N.
    """
    N = cfg.N
    j_up = N * cfg.M_halflaps // 2
    L_chord = 2 * cfg.R_ring * np.sin(np.pi / N)
    alpha = np.arctan2(cfg.H, max(j_up, 1) * L_chord)   # spiral pitch angle
    dz = L_chord * np.tan(alpha)
    leg = L_chord / np.cos(alpha)
    aoi_deg = np.degrees(np.pi / 2 - np.pi / N)

    total = 2 * j_up
    hits = np.zeros((total, 3))
    mseq = np.zeros(total, dtype=int)
    z = -cfg.H / 2.0
    path = 0.0
    opl = 0.0
    for j in range(j_up):              # upgoing
        z += dz
        opl += leg
        mid = (j + 1) % N
        theta = 2 * np.pi * mid / N
        hits[j] = [cfg.R_ring * np.cos(theta), cfg.R_ring * np.sin(theta), z]
        mseq[j] = mid
    for j in range(j_up, total):       # downgoing (reverse order)
        z -= dz
        opl += leg
        k_down = j - j_up + 1
        mid = (j_up - k_down + 1) % N
        theta = 2 * np.pi * mid / N
        hits[j] = [cfg.R_ring * np.cos(theta), cfg.R_ring * np.sin(theta), z]
        mseq[j] = mid
    return {"hits": hits, "mirror_seq": mseq,
            "aoi": np.full(total, aoi_deg), "opl": opl,
            "L_chord": L_chord, "leg": leg, "alpha": alpha,
            "bounces": total}


# =============================================================================
# 12. Top-level simulator
# =============================================================================
def simulate_tmpc(cfg: TMPCConfig,
                  perturbations: Optional[Sequence[MirrorPerturbation]] = None,
                  global_pert: Optional[GlobalPerturbation] = None,
                  hole_diameter: Optional[float] = None) -> SimResult:
    """Run the full multipass simulation.

    Optional `perturbations` (length-N list of MirrorPerturbation) and
    `global_pert` (single GlobalPerturbation) let the tolerance module inject
    fabrication/alignment/thermal/launch deviations without copying anything.

    Beam propagation uses the realistic ASTIGMATIC mirror focal lengths
    (f_tan = R cos θ /2, f_sag = R/(2 cos θ)) with the actual per-bounce AOI
    and the actual chord lengths between hits, plus the M² beam-quality factor.
    """
    from .beam import AstigBeam, propagate_astigmatic

    eff_cfg = cfg
    if global_pert is not None and (global_pert.d_reflectivity != 0.0
                                     or global_pert.d_wavelength != 0.0):
        eff_cfg = replace(
            cfg,
            reflectivity=float(np.clip(cfg.reflectivity + global_pert.d_reflectivity,
                                       0.0, 1.0)),
            wavelength=cfg.wavelength + global_pert.d_wavelength,
        )
    if hole_diameter is None:
        hole_diameter = 2.0 * eff_cfg.hole_radius

    # -------- geometry / ray path --------
    if eff_cfg.topology == "spiral":
        sp = _spiral_trace(eff_cfg)
        hits = sp["hits"]
        mirror_seq = sp["mirror_seq"]
        aoi_record = list(sp["aoi"])
        opl = sp["opl"]
        bounces = sp["bounces"]
        geom_clip = False
        chords = np.full(max(1, bounces), sp["leg"])
        exit_ray = None
    else:
        mirrors = build_mirror_ring(eff_cfg, perturbations, global_pert)
        sequence = _bounce_sequence(eff_cfg)
        surf_seq = [mirrors[i] for i in sequence]
        ray = _entrance_ray(eff_cfg, mirrors, global_pert)
        aoi_record = []
        res = trace_ray(ray, surf_seq, max_bounces=eff_cfg.n_passes,
                        aoi_record=aoi_record)
        bounces = res["bounces"]
        hits = (np.array(ray.history[1:1 + bounces])
                if bounces else np.empty((0, 3)))
        mirror_seq = np.array(sequence[:bounces], dtype=int)
        opl = res["opl"]
        geom_clip = res["clipped"]
        exit_ray = ray
        if len(hits) >= 2:
            chords = np.linalg.norm(np.diff(hits, axis=0), axis=1)
            chords = np.append(chords, chords[-1])
        else:
            chords = np.full(max(1, bounces),
                             2 * eff_cfg.R_ring *
                             np.sin(np.pi * eff_cfg.chord_skip / eff_cfg.N))

    n_b = max(1, bounces)

    # -------- realistic astigmatic beam along the actual path --------
    aoi_rad = (np.radians(aoi_record) if len(aoi_record)
               else np.full(n_b, np.pi / 2 - np.pi / eff_cfg.N))
    seg = chords[:n_b] if len(chords) >= n_b else np.full(n_b, float(chords[-1]))
    if eff_cfg.astigmatic:
        Rt = np.full(n_b, eff_cfg.R_t)
        Rs = np.full(n_b, eff_cfg.R_s)
        aoi_for_beam = aoi_rad[:n_b] if len(aoi_rad) >= n_b else np.full(n_b, aoi_rad[-1] if len(aoi_rad) else 0.0)
    else:
        # paraxial: collapse astigmatism by forcing AOI=0
        Rt = np.full(n_b, eff_cfg.R_t)
        Rs = np.full(n_b, eff_cfg.R_s)
        aoi_for_beam = np.zeros(n_b)
    beam = AstigBeam(wavelength=eff_cfg.wavelength, w0=eff_cfg.w0, M2=eff_cfg.M2)
    prop = propagate_astigmatic(beam, list(seg), list(Rt), list(Rs),
                                list(aoi_for_beam))
    w_t = prop["w_tangential"]
    w_s = prop["w_sagittal"]
    w_max = prop["w_max"]
    w_mean = prop["w_mean"]
    clipped = bool(geom_clip or w_max >= eff_cfg.mirror_aperture)

    loss = compute_losses(
        bounces=bounces, reflectivity=eff_cfg.reflectivity,
        w_max=w_max, aperture=eff_cfg.mirror_aperture,
        beam_diameter_in=2 * eff_cfg.w0, hole_diameter=hole_diameter,
        clipped=clipped,
    )
    throughput = loss.throughput

    # -------- stability (isotropic g + per-plane astigmatic m) --------
    from .beam import unit_cell_stability
    chord_mean = float(np.mean(seg))
    g = 1.0 - chord_mean / eff_cfg.R_t
    stability_g = g * g
    aoi_typ = float(np.median(aoi_for_beam)) if len(aoi_for_beam) else 0.0
    m_tan = unit_cell_stability(chord_mean, eff_cfg.R_t, aoi_typ, "tangential")
    m_sag = unit_cell_stability(chord_mean, eff_cfg.R_s, aoi_typ, "sagittal")

    vol = _volume_utilisation(hits, eff_cfg) if len(hits) > 1 else 0.0
    diag = spot_diagnostics(hits, mirror_seq, eff_cfg, w_mean)

    return SimResult(
        config=cfg,
        bounces=bounces, opl=opl,
        spot_pattern=hits, aoi=np.array(aoi_record),
        w_max=float(w_max), clipped=clipped,
        throughput=float(throughput), stability_g=float(stability_g),
        volume_utilisation=float(vol),
        loss_budget=loss,
        reentrance=reentrance_score(eff_cfg.N, eff_cfg.chord_skip)
        if eff_cfg.topology == "ring" else 1.0,
        stability_tan=float(m_tan), stability_sag=float(m_sag),
        w_tangential=w_t, w_sagittal=w_s,
        mirror_sequence=mirror_seq, chords=np.asarray(seg),
        exit_ray=exit_ray,
        min_spot_separation=diag["min_sep"],
        max_spots_per_mirror=diag["max_spots"],
        spots_overlap=diag["overlap"],
        mirror_fill_fraction=diag["fill"],
    )
