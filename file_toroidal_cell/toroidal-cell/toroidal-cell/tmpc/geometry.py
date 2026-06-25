"""
geometry.py
===========

Toroidal multipass cell geometry and ray tracing.

The cell consists of N flat mirrors arranged on a ring of radius R, with their
normals pointing radially inward. The beam enters through a small hole in
mirror 0 at the bottom of the cell (z = -H/2), spirals upward as it bounces
around the polygon, hits a flat top retroreflector at z = +H/2, then spirals
back down and exits through the same hole.

Chord-skip pattern
------------------
The ``chord_skip`` parameter controls which mirror is visited at each bounce:

  chord_skip = 1  (default)
      Beam hops to the neighbouring mirror: 0 -> 1 -> 2 -> ... -> N-1 -> 0
      Each chord is short (length 2R sin(pi/N)) and stays near the ring
      perimeter — the centre of the cell receives no light. AOI is large
      (pi/2 - pi/N).

  chord_skip = s  (general)
      Beam hops s mirrors at a time, modulo N: 0 -> s -> 2s -> 3s -> ...
      Each chord is longer (length 2R sin(s*pi/N)) and passes through the
      cell interior. AOI shrinks to pi/2 - s*pi/N. For s = N/2 the chords
      are diameters and AOI -> 0 (normal incidence).

      Choose gcd(s, N) = 1 so that every mirror is visited within the first
      N bounces — otherwise only a subset of the ring is used.

This generalisation matches the Tuzson/Graf/Chang toroidal-MPC literature,
where diagonal chords sample the entire cell volume rather than skimming
the perimeter.

Coordinate system
-----------------
* x, y : ring plane.
* z    : cell axis (vertical, perpendicular to the ring plane).
* Mirror k centred at  p_k = (R cos phi_k, R sin phi_k, 0)
  with phi_k = 2 pi k / N.
* Mirror normal points radially inward:  n_k = -(cos phi_k, sin phi_k, 0).
* Each mirror is a planar disc of diameter D, treated here as a rectangle
  of width D (in-plane chord direction) and height H (along z).

Closure / single-hole condition
-------------------------------
For the beam to return to the entrance hole, the number of upgoing reflections
j_up must be a multiple of N/2 (M half-laps), giving

    tan(alpha) = H_eff / (N * M * L_chord)

where L_chord = 2 R sin(s * pi/N) and H_eff is the axial extent traversed.

Outputs
-------
trace_cell() returns a dict of per-reflection numpy arrays:

    pass_no              integer index (1..total_reflections)
    mirror_id            int, 0..N-1 (or -1 for the top retroreflector)
    x, y, z              hit-point in cell coordinates [m]
    incident_angle_deg   angle of incidence at the mirror [deg]
    spot_radius          1/e^2 intensity radius of the Gaussian spot [m]
    path_length          cumulative optical-path length up to & including
                         this reflection [m]
    is_returning         bool — True for downgoing leg
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import math
import numpy as np


# ---------------------------------------------------------------------------
# Configuration dataclass
# ---------------------------------------------------------------------------
@dataclass
class TMPCConfig:
    """Geometric and optical configuration for a toroidal multipass cell."""

    # --- ring geometry ----------------------------------------------------
    N: int = 8                       # number of ring mirrors
    R: float = 50e-3                 # ring radius [m]
    H: float = 40e-3                 # cell height (axial extent) [m]

    # --- mirror properties -----------------------------------------------
    D_mirror: float = 25.4e-3        # mirror diameter (in-plane) [m]
    ROC: float = math.inf            # radius of curvature [m]  (inf == flat)

    # --- multipass structure ---------------------------------------------
    M_halfLaps: int = 66             # number of half-laps before top
                                     # retro (j_up = N * M / 2 reflections)
    chord_skip: int = 1              # mirrors hopped per bounce (1 = neighbour,
                                     # ~N/2 = diametrical). gcd(skip, N) = 1
                                     # ensures every mirror is visited.

    # --- entrance hole ---------------------------------------------------
    z_entry: Optional[float] = None  # z of entrance hole on mirror 0.
                                     # Default: z = -H/2 + ΔZ/2.

    # --- beam parameters --------------------------------------------------
    wavelength: float = 1.654e-6     # [m] (CH4 R(3) line, 2 nu_3 band)
    w0: float = 1.0e-3               # input collimated beam waist (1/e^2) [m]
    M2: float = 1.2                  # beam quality factor

    # --- waist placement along the beam path -----------------------------
    # 'center' places the waist at OPL/2 (symmetric expansion);
    # 'entrance' places it at the entry hole.
    waist_placement: str = "center"

    # --- derived (set by __post_init__) ----------------------------------
    L_chord: float = field(init=False)
    alpha_rad: float = field(init=False)
    total_reflections: int = field(init=False)
    OPL_design: float = field(init=False)

    def __post_init__(self) -> None:
        if self.chord_skip < 1 or self.chord_skip >= self.N:
            raise ValueError(
                f"chord_skip must be in [1, N-1]; got {self.chord_skip}"
            )
        # Chord length for the s-skipped polygon, in metres.
        self.L_chord = 2.0 * self.R * math.sin(
            self.chord_skip * math.pi / self.N
        )
        # j_up = N * M / 2 (must be integer)
        if (self.N * self.M_halfLaps) % 2 != 0:
            raise ValueError("N * M_halfLaps must be even (j_up must be int).")
        j_up = self.N * self.M_halfLaps // 2
        # The beam traverses (j_up + 0.5) chords axially between entry plane
        # and the top reflector if z_entry = -H/2 + 0.5*ΔZ (centred).
        # For simplicity place z_entry exactly at -H/2:
        if self.z_entry is None:
            self.z_entry = -self.H / 2.0
        # Then traversed axial distance during upgoing leg = H, over j_up chords:
        self.alpha_rad = math.atan2(self.H, j_up * self.L_chord)
        self.total_reflections = 2 * j_up  # plus 1 top retroreflection
        # OPL ignoring small top-retro detour:
        leg_len = self.L_chord / math.cos(self.alpha_rad)
        self.OPL_design = 2.0 * j_up * leg_len


# ---------------------------------------------------------------------------
# Geometric helpers
# ---------------------------------------------------------------------------
def mirror_centre(k: int, cfg: TMPCConfig) -> np.ndarray:
    phi = 2.0 * math.pi * k / cfg.N
    return np.array([cfg.R * math.cos(phi), cfg.R * math.sin(phi), 0.0])


def mirror_normal(k: int, cfg: TMPCConfig) -> np.ndarray:
    phi = 2.0 * math.pi * k / cfg.N
    return np.array([-math.cos(phi), -math.sin(phi), 0.0])


def incident_angle_deg(cfg: TMPCConfig) -> float:
    """Angle of incidence at every ring mirror, in degrees.

    For a chord that skips ``s`` mirrors on a regular N-gon, the chord
    subtends 2*pi*s/N at the centre. By the inscribed-angle / isoceles
    triangle relation, the chord meets the mirror normal (which is the
    inward radial direction) at angle  pi/2 - s_eff * pi/N, where
    s_eff = min(s, N - s) is the chord's geometric skip (a chord from
    mirror 0 to mirror N-s is the same chord as 0 to s, just traversed
    in the opposite sense).

    Limits:
        s_eff = 1      ->  AOI = pi/2 - pi/N   (grazing incidence)
        s_eff = N/2    ->  AOI = 0             (normal incidence, diameter)
    """
    s_eff = min(cfg.chord_skip, cfg.N - cfg.chord_skip)
    theta = math.pi / 2.0 - s_eff * math.pi / cfg.N
    return math.degrees(theta)


# ---------------------------------------------------------------------------
# Ray tracer
# ---------------------------------------------------------------------------
def trace_cell(cfg: TMPCConfig, *, gaussian: bool = True) -> dict:
    """Trace the full multipass path and return per-reflection data.

    Parameters
    ----------
    cfg      : TMPCConfig
    gaussian : if True, compute the 1/e^2 spot radius at each reflection
               using free-space Gaussian propagation (valid for ROC = inf).
               For curved mirrors a more elaborate model is needed (see
               gaussian.py for ABCD analysis).

    Returns
    -------
    data : dict of numpy arrays — see module docstring.
    """
    N = cfg.N
    j_up = cfg.N * cfg.M_halfLaps // 2          # reflections per leg
    dz_per_chord = cfg.L_chord * math.tan(cfg.alpha_rad)
    leg_len = cfg.L_chord / math.cos(cfg.alpha_rad)

    # --- pre-allocate output arrays --------------------------------------
    total = 2 * j_up
    pass_no  = np.arange(1, total + 1)
    mirror_id = np.empty(total, dtype=int)
    x   = np.empty(total)
    y   = np.empty(total)
    z   = np.empty(total)
    inc = np.full(total, incident_angle_deg(cfg))
    spotR = np.empty(total)
    path  = np.empty(total)
    is_back = np.zeros(total, dtype=bool)

    # --- in-plane (lateral) positions stay on mirror surfaces -----------
    # For the simple model, each reflection happens at the mirror centre
    # in the (x, y) plane, with z incrementing by dz_per_chord per chord.
    # Real beams have small offsets from the centre; that detail is
    # captured by Gaussian beam analysis (gaussian.py) rather than ray
    # geometry.

    # Physical model: a corner-cube top retroreflector at z = +H/2 retraces
    # the upgoing beam EXACTLY back through itself. Downgoing reflections
    # therefore re-visit the upgoing mirror sequence in REVERSE order, at
    # the same z values. Each "distinct spot" on a ring mirror is visited
    # twice (once on each leg). The exit chord goes from mirror 1 back to
    # the entry hole on mirror 0.
    z_run = cfg.z_entry
    path_run = 0.0
    s = cfg.chord_skip

    # ---- upgoing leg --------------------------------------------------
    for j in range(j_up):
        z_run += dz_per_chord
        path_run += leg_len
        mid = ((j + 1) * s) % N      # mirror hit at pass j+1 (s-skipped)
        mirror_id[j] = mid
        p = mirror_centre(mid, cfg)
        x[j] = p[0]; y[j] = p[1]; z[j] = z_run
        path[j] = path_run

    # conceptual top-retro event between pass j_up and pass j_up+1 -----
    # (folded invisibly into the path; adds a small offset 2*L2 we neglect)

    # ---- downgoing leg (mirrors visited in reverse order) ------------
    for j in range(j_up, total):
        z_run -= dz_per_chord
        path_run += leg_len
        k_down = j - j_up + 1                      # 1-indexed downgoing pass
        mid = ((j_up - k_down + 1) * s) % N        # retraced (reverse) order
        is_back[j] = True
        mirror_id[j] = mid
        p = mirror_centre(mid, cfg)
        x[j] = p[0]; y[j] = p[1]; z[j] = z_run
        path[j] = path_run

    # --- Gaussian spot radius at each hit --------------------------------
    if gaussian:
        # place waist either at centre of path or at the entrance
        if cfg.waist_placement == "center":
            z_waist = path[-1] / 2.0
        elif cfg.waist_placement == "entrance":
            z_waist = 0.0
        else:
            raise ValueError("waist_placement must be 'center' or 'entrance'.")
        # Embedded-Gaussian formula with M^2:
        # w(z) = w0 * sqrt(1 + ((z - z_waist) / zR_eff)^2),
        # zR_eff = pi * w0^2 / (M^2 * lambda)
        zR = math.pi * cfg.w0 ** 2 / (cfg.M2 * cfg.wavelength)
        spotR[:] = cfg.w0 * np.sqrt(1.0 + ((path - z_waist) / zR) ** 2)
    else:
        spotR[:] = cfg.w0

    return {
        "pass_no": pass_no,
        "mirror_id": mirror_id,
        "x": x, "y": y, "z": z,
        "incident_angle_deg": inc,
        "spot_radius": spotR,
        "path_length": path,
        "is_returning": is_back,
    }


# ---------------------------------------------------------------------------
# Spot-pattern utilities
# ---------------------------------------------------------------------------
def per_mirror_z_spots(data: dict, N: int) -> dict[int, np.ndarray]:
    """Group reflection z-coordinates by mirror_id for spot-pattern plots."""
    out = {}
    for k in range(N):
        sel = data["mirror_id"] == k
        out[k] = data["z"][sel]
    return out


def distinct_spots_per_mirror(data: dict, N: int,
                                tol: float = 1e-6) -> dict[int, np.ndarray]:
    """Group hits by mirror, then deduplicate z values within ``tol`` (m).
    With a corner-cube top retroreflector, going-up and going-down hits
    coincide; this returns the unique physical spot positions."""
    out: dict[int, np.ndarray] = {}
    for k in range(N):
        sel = data["mirror_id"] == k
        zs = np.sort(data["z"][sel])
        if len(zs) == 0:
            out[k] = zs
            continue
        keep = [zs[0]]
        for z in zs[1:]:
            if z - keep[-1] > tol:
                keep.append(float(z))
        out[k] = np.array(keep)
    return out


def min_spot_separation(data: dict, N: int) -> float:
    """Smallest centre-to-centre spacing between distinct spots on the
    same mirror, in metres. Retraced duplicates are merged before the
    spacing is computed."""
    grouped = distinct_spots_per_mirror(data, N)
    dmin = math.inf
    for k, zs in grouped.items():
        if len(zs) < 2:
            continue
        diffs = np.diff(zs)
        if diffs.min() < dmin:
            dmin = float(diffs.min())
    return dmin if math.isfinite(dmin) else 0.0


def spots_overlap(data: dict, cfg: TMPCConfig,
                   sep_factor: float = 2.0) -> bool:
    """True if any two distinct same-mirror spots are closer than
    sep_factor times the mean 1/e^2 spot radius on that mirror."""
    grouped = distinct_spots_per_mirror(data, cfg.N)
    for k, zs in grouped.items():
        if len(zs) < 2:
            continue
        sel = data["mirror_id"] == k
        w_mean = float(data["spot_radius"][sel].mean())
        diffs = np.diff(zs)
        if diffs.min() < sep_factor * w_mean:
            return True
    return False


def mirror_fill_fraction(data: dict, cfg: TMPCConfig) -> float:
    """Estimate of the fraction of a mirror's area covered by Gaussian
    spots (capped at 1). A value approaching 1 means the beam saturates
    the mirror — when this occurs, clipping losses grow rapidly."""
    A_mirror = math.pi * (cfg.D_mirror / 2.0) ** 2
    grouped = distinct_spots_per_mirror(data, cfg.N)
    worst = 0.0
    for k, zs in grouped.items():
        if len(zs) == 0:
            continue
        sel = data["mirror_id"] == k
        w_mean = float(data["spot_radius"][sel].mean())
        coverage = len(zs) * math.pi * w_mean ** 2 / A_mirror
        if coverage > worst:
            worst = coverage
    return min(worst, 1.0)


def max_radial_extent(data: dict, cfg: TMPCConfig) -> float:
    """Maximum 1/e^2 radius reached anywhere on the path [m]. Compare to
    D_mirror/2 to flag clipping."""
    return float(data["spot_radius"].max())


# ---------------------------------------------------------------------------
# Volume-utilisation metric
# ---------------------------------------------------------------------------
def _chord_segments(data: dict, cfg: TMPCConfig) -> np.ndarray:
    """Return all chord segments as an array of shape (n_chords, 2, 3),
    where each segment is [(x0, y0, z0), (x1, y1, z1)] in metres.

    The path consists of: launch hole (-> first bounce) (-> bounce 2) ...
    (-> last bounce -> exit hole). We include the launch and exit chords.
    """
    x = np.asarray(data["x"])
    y = np.asarray(data["y"])
    z = np.asarray(data["z"])
    # Launch point: entry hole on mirror 0 at z = z_entry
    p0 = mirror_centre(0, cfg).copy()
    p0[2] = cfg.z_entry
    # Exit point: same as launch (single-hole geometry)
    pN = p0.copy()
    # Full path: launch -> b1 -> b2 -> ... -> bM -> exit
    pts = np.vstack([p0, np.stack([x, y, z], axis=1), pN])
    # Segments: (pts[i], pts[i+1]) for i = 0..len(pts)-2
    return np.stack([pts[:-1], pts[1:]], axis=1)


def _point_to_segment_distance(p: np.ndarray, a: np.ndarray,
                                b: np.ndarray) -> np.ndarray:
    """Vectorised distance from points ``p`` (shape (M, 3)) to a single
    line segment from ``a`` to ``b`` (each shape (3,)). Returns shape (M,)."""
    ab = b - a
    L2 = float(np.dot(ab, ab))
    if L2 < 1e-30:
        return np.linalg.norm(p - a, axis=1)
    t = np.clip(((p - a) @ ab) / L2, 0.0, 1.0)
    closest = a + np.outer(t, ab)
    return np.linalg.norm(p - closest, axis=1)


def volume_utilisation(data: dict, cfg: TMPCConfig, *,
                        threshold: Optional[float] = None,
                        n_samples: int = 20_000,
                        seed: int = 2026) -> dict:
    """Estimate the fraction of cell volume swept by the laser beam.

    A Monte Carlo sample of points is drawn uniformly inside the
    cylindrical cell (radius R, height H). For each point, the minimum
    perpendicular distance to any chord segment in the trace is computed.
    Points within ``threshold`` of the nearest chord are counted as
    'covered'.

    Parameters
    ----------
    data       : output of ``trace_cell``.
    cfg        : the matching TMPCConfig.
    threshold  : coverage radius in metres. Default: mean Gaussian beam
                 radius across the trace (so coverage ~ 1/e^2 of beam
                 energy is captured).
    n_samples  : Monte Carlo sample count.
    seed       : RNG seed for reproducibility.

    Returns
    -------
    dict with keys:
        utilisation        fraction of cell volume covered
        threshold_m        coverage radius used
        mean_distance_m    mean (over sampled points) of distance to
                           nearest chord
        median_distance_m  median distance to nearest chord
        cell_volume_m3     cylindrical cell volume used as denominator
    """
    if threshold is None:
        threshold = float(np.asarray(data["spot_radius"]).mean())

    rng = np.random.default_rng(seed)
    # Sample uniformly inside the cylindrical cell of radius R, height H.
    # (r ~ sqrt(U), so density per unit area is uniform.)
    r = cfg.R * np.sqrt(rng.random(n_samples))
    th = 2.0 * np.pi * rng.random(n_samples)
    zs = -cfg.H / 2.0 + cfg.H * rng.random(n_samples)
    pts = np.stack([r * np.cos(th), r * np.sin(th), zs], axis=1)

    # Compute min distance to all chord segments.
    segs = _chord_segments(data, cfg)         # (n_chords, 2, 3)
    min_d = np.full(n_samples, np.inf)
    for k in range(segs.shape[0]):
        d = _point_to_segment_distance(pts, segs[k, 0], segs[k, 1])
        np.minimum(min_d, d, out=min_d)

    covered = float((min_d < threshold).mean())
    cell_volume = math.pi * cfg.R ** 2 * cfg.H
    return {
        "utilisation":       covered,
        "threshold_m":       float(threshold),
        "mean_distance_m":   float(min_d.mean()),
        "median_distance_m": float(np.median(min_d)),
        "cell_volume_m3":    float(cell_volume),
    }
