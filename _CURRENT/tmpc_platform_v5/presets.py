"""Named design presets for the TMPC platform v5.

Provides a registry of well-characterised operating points that can be used
by the CLI, viewers, and benchmarking scripts.

Public API
----------
PRESETS       : dict[str, dict]   — each value holds TMPCConfig kwargs plus a
                                    'label' key with a human-readable description.
list_presets()  -> list[str]      — alphabetically sorted preset names.
get_preset(name) -> TMPCConfig    — construct a validated TMPCConfig from a preset.
preset_label(name) -> str         — retrieve the human-readable label.
"""
from __future__ import annotations

from typing import Dict, List


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
# Every entry is a plain dict whose keys are valid TMPCConfig __init__
# arguments PLUS an extra 'label' key (popped before constructing TMPCConfig).
#
# v5 naming conventions that differ from v4:
#   - mirror_aperture is a clear-aperture RADIUS  [mm]  (v4 used diameter)
#   - chord_skip      (unchanged, v4 also used chord_skip)
#   - n_passes        (added explicitly; defaults to 8*N when absent)
#   - topology        'ring' | 'spiral'
#   - M_halflaps, astigmatic  (new v5 fields with sensible defaults)
# ---------------------------------------------------------------------------

PRESETS: Dict[str, dict] = {

    # ------------------------------------------------------------------
    # Ported from tmpc_platform_v4 visualise_3d.py
    # ------------------------------------------------------------------

    "bo_best_one_inch": dict(
        # Bayesian-optimised design, one-inch (25.4 mm diameter) mirrors.
        # mirror_aperture = 11.4 mm radius (clear-aperture radius as per v4).
        N=10,
        chord_skip=7,
        R_ring=63.14,
        H=21.6,
        R_t=100.0,
        R_s=100.0,
        mirror_aperture=11.4,      # radius [mm]
        w0=0.98,
        input_offset_z=-1.99,
        input_angle=-0.0481,
        n_passes=80,
        reflectivity=0.98,
        label="BO best (one_inch, R=0.98)",
    ),

    "bo_best_half_inch": dict(
        # Bayesian-optimised design, half-inch (12.7 mm diameter) mirrors.
        # mirror_aperture = 5.7 mm radius.
        N=8,
        chord_skip=3,
        R_ring=49.22,
        H=35.30,
        R_t=100.0,
        R_s=100.0,
        mirror_aperture=5.7,       # radius [mm]
        w0=1.22,
        input_offset_z=2.29,
        input_angle=0.0334,
        n_passes=64,
        reflectivity=0.98,
        label="BO best (half_inch, R=0.98)",
    ),

    "longest_opl": dict(
        # Maximum optical-path-length design (~30 m target).
        N=16,
        chord_skip=7,
        R_ring=119.24,
        H=36.43,
        R_t=500.0,
        R_s=500.0,
        mirror_aperture=11.4,
        w0=1.17,
        input_offset_z=2.2,
        input_angle=0.022,
        n_passes=128,
        reflectivity=0.98,
        label="Longest OPL (29.9 m @ R=0.98 -> 7.3% T)",
    ),

    "sweet_spot_120": dict(
        # A balanced design: long OPL with reasonable throughput.
        N=15,
        chord_skip=7,
        R_ring=116.18,
        H=20.97,
        R_t=1500.0,
        R_s=1500.0,
        mirror_aperture=11.4,
        w0=0.75,
        input_offset_z=1.6,
        input_angle=0.018,
        n_passes=120,
        reflectivity=0.98,
        label="Sweet spot: 27.7 m @ 8.85% T",
    ),

    "toroidal_lissajous": dict(
        # Toroidal mirrors (R_t != R_s) produce a Lissajous spot constellation
        # because the tangential and sagittal phase advances differ.
        N=16,
        chord_skip=7,
        R_ring=119.24,
        H=36.43,
        R_t=500.0,
        R_s=300.0,          # asymmetric — different focal power in each plane
        mirror_aperture=11.4,
        w0=1.17,
        input_offset_z=2.2,
        input_angle=0.022,
        n_passes=128,
        reflectivity=0.98,
        label="Toroidal (R_t=500, R_s=300) -- Lissajous demo",
    ),

    # ------------------------------------------------------------------
    # New presets exercising v5-specific features
    # ------------------------------------------------------------------

    "spiral_demo": dict(
        # Tuzson/Graf up-down spiral cell (topology='spiral').
        # Beam enters at z=-H/2, spirals up to a retroreflector at z=+H/2,
        # then spirals back down and exits.  N*M_halflaps must be even.
        topology="spiral",
        N=8,
        R_ring=50.0,
        H=40.0,
        R_t=1.0e9,          # nearly flat mirrors — long Rayleigh range
        R_s=1.0e9,
        mirror_aperture=8.0,
        M_halflaps=20,      # 20 half-laps => 160 bounces total
        w0=1.0,
        reflectivity=0.999,
        # chord_skip is ignored for spiral topology (always +1 per bounce)
        chord_skip=1,
        label="Spiral (Tuzson/Graf) topology demo — N=8, 20 half-laps",
    ),

    # ------------------------------------------------------------------
    # Drone designs (2026-07-02 search, drone_20m/search_drone20m.py v6):
    # verified by the exact tracer -- exit through the 1.3 mm hole,
    # hole-leak clearance, spot separation, aperture margin, stability,
    # packing, envelope. Mode-matched injection (waist inside the cell,
    # w(hole) <= 1.3 mm). Throughput scales as R^(n_passes-2).
    # ------------------------------------------------------------------

    "drone_20m": dict(
        # 20.38 m in a 180 mm envelope; 16 x CM254-150-M01 (ROC 300).
        # 144 chords / 143 reflections -> 86.7 % at R = 0.999.
        N=16, chord_skip=7, R_ring=72.1555, H=16.0,
        R_t=300.0, R_s=300.0, mirror_aperture=11.4,
        w0=0.3262, M2=1.0, input_waist_offset=102.07,
        input_offset_z=0.2709, input_angle=-0.030949,
        input_angle_sag=0.021673,
        reflectivity=0.999, hole_radius=1.3, n_passes=144,
        label="Drone 20.4 m @ 180 mm -- 16x CM254-150-M01, 86.7% T",
    ),

    "drone_25m": dict(
        # Max-OPL corner: 24.77 m in 180 mm; 16 x CM254-200-M01 (ROC 400).
        # 176 chords / 175 reflections -> 83.9 % at R = 0.999.
        N=16, chord_skip=7, R_ring=71.7583, H=22.0,
        R_t=400.0, R_s=400.0, mirror_aperture=11.4,
        w0=0.3134, M2=1.0, input_waist_offset=78.82,
        input_offset_z=0.0762, input_angle=0.026612,
        input_angle_sag=0.037692,
        reflectivity=0.999, hole_radius=1.3, n_passes=176,
        label="Drone 24.8 m @ 180 mm -- 16x CM254-200-M01, 83.9% T",
    ),

    "drone_22m": dict(
        # Mid Pareto point: 22.25 m in 172 mm; 14 x CM254-100-M01 (ROC 200).
        # 182 chords / 181 reflections -> 83.4 % at R = 0.999.
        N=14, chord_skip=5, R_ring=67.8486, H=26.0,
        R_t=200.0, R_s=200.0, mirror_aperture=11.4,
        w0=0.2, M2=1.0, input_waist_offset=45.15,
        input_offset_z=7.6485, input_angle=0.048492,
        input_angle_sag=-0.005229,
        reflectivity=0.999, hole_radius=1.3, n_passes=182,
        label="Drone 22.3 m @ 172 mm -- 14x CM254-100-M01",
    ),

    "drone_16cm": dict(
        # Compactness corner: 20.64 m in 159 mm; 13 x CM254-050-M01
        # (ROC 100, cheapest SKU). 169 chords -> 84.5 % at R = 0.999.
        N=13, chord_skip=6, R_ring=61.5187, H=18.0,
        R_t=100.0, R_s=100.0, mirror_aperture=11.4,
        w0=0.2, M2=1.0, input_waist_offset=84.03,
        input_offset_z=-0.045, input_angle=-0.043739,
        input_angle_sag=0.039149,
        reflectivity=0.999, hole_radius=1.3, n_passes=169,
        label="Drone 20.6 m @ 159 mm -- 13x CM254-050-M01, 84.5% T",
    ),

    "astig_toroidal": dict(
        # Ring cell with strongly asymmetric mirror curvatures and M2=1.2.
        # R_t >> R_s means very different focal lengths in the two planes,
        # producing a pronounced Lissajous/astigmatic spot pattern and a
        # large per-plane stability difference — good for testing astigmatic
        # propagation and the stability_tan / stability_sag outputs.
        topology="ring",
        N=12,
        chord_skip=5,
        R_ring=75.0,
        H=30.0,
        R_t=800.0,
        R_s=200.0,
        mirror_aperture=9.0,
        w0=0.8,
        M2=1.2,
        input_offset_z=1.5,
        input_angle=0.015,
        n_passes=96,
        reflectivity=0.98,
        astigmatic=True,
        label="Astigmatic toroidal ring (R_t=800, R_s=200, M2=1.2) — Lissajous spots",
    ),
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def list_presets() -> List[str]:
    """Return all registered preset names in sorted order."""
    return sorted(PRESETS.keys())


def get_preset(name: str):
    """Construct a :class:`tmpc_platform_v5.TMPCConfig` from a named preset.

    The 'label' key is stripped before construction.  If ``n_passes`` is
    absent from the preset kwargs it is set to ``8 * N`` (the platform
    default) before the config object is built.

    Parameters
    ----------
    name : str
        Key in :data:`PRESETS`.

    Returns
    -------
    TMPCConfig
        Fully validated configuration object.

    Raises
    ------
    KeyError
        If *name* is not a registered preset.
    """
    # Import here to avoid circular dependencies at module load time.
    from tmpc_platform_v5 import TMPCConfig  # noqa: PLC0415

    if name not in PRESETS:
        raise KeyError(
            f"Unknown preset {name!r}. Available: {list_presets()}"
        )
    kwargs = dict(PRESETS[name])        # shallow copy — do not mutate registry
    kwargs.pop("label", None)           # strip non-TMPCConfig key

    # Apply default n_passes = 8*N when the preset omits it.
    if "n_passes" not in kwargs:
        kwargs["n_passes"] = 8 * kwargs.get("N", TMPCConfig.N
                                             if isinstance(TMPCConfig.N, int)
                                             else 8)
    return TMPCConfig(**kwargs)


def preset_label(name: str) -> str:
    """Return the human-readable label for a preset.

    Parameters
    ----------
    name : str
        Key in :data:`PRESETS`.

    Returns
    -------
    str
        The 'label' string stored in the preset, or *name* if none is set.

    Raises
    ------
    KeyError
        If *name* is not a registered preset.
    """
    if name not in PRESETS:
        raise KeyError(
            f"Unknown preset {name!r}. Available: {list_presets()}"
        )
    return PRESETS[name].get("label", name)

