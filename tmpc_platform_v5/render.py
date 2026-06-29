"""tmpc_platform_v5.render — photo-realistic 3-D Plotly render of the TMPC assembly.

Distinct from viz3d's schematic: this module renders the physical optical
components (mirror substrates, mount posts, breadboard, laser beam tube) in a
way that resembles a photograph of the actual hardware.

Public API
----------
render_experiment(res, cfg, out_path, family='one_inch', show_beam=True) -> out_path

Helper
------
_cylinder_mesh(center, axis, radius, length, n=32) -> (X, Y, Z)
    Generates X/Y/Z arrays for a capped cylinder Mesh3d.
"""
from __future__ import annotations

import os
from math import radians
from typing import Optional, Sequence, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Internal geometry helpers
# ---------------------------------------------------------------------------

def _unit(v: np.ndarray) -> np.ndarray:
    """Return a unit vector, or the zero vector if degenerate."""
    n = np.linalg.norm(v)
    return v / n if n > 1e-15 else v


def _perpendicular(v: np.ndarray) -> np.ndarray:
    """Return an arbitrary unit vector perpendicular to *v*."""
    v = _unit(v)
    # choose the axis least aligned with v
    candidates = [np.array([1.0, 0.0, 0.0]),
                  np.array([0.0, 1.0, 0.0]),
                  np.array([0.0, 0.0, 1.0])]
    dots = [abs(float(v @ c)) for c in candidates]
    ref = candidates[int(np.argmin(dots))]
    return _unit(np.cross(v, ref))


def _cylinder_mesh(center: np.ndarray,
                   axis: np.ndarray,
                   radius: float,
                   length: float,
                   n: int = 32
                   ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build a *capped* cylinder (two discs + side wall) as a Mesh3d mesh.

    Parameters
    ----------
    center : (3,) midpoint of the cylinder axis
    axis   : (3,) unit vector along the cylinder axis
    radius : cylinder radius [mm]
    length : full length of the cylinder [mm]
    n      : number of azimuthal facets

    Returns
    -------
    X, Y, Z : (nv,) vertex coordinate arrays (pass directly to Mesh3d x/y/z)
    I, J, K : triangle index arrays  — returned as a 4-tuple with (X,Y,Z) wrapped;
              use the secondary return value.

    Actually this function returns X, Y, Z, I, J, K so unpack accordingly::

        X, Y, Z, I, J, K = _cylinder_mesh(...)
    """
    axis = _unit(np.asarray(axis, dtype=float))
    center = np.asarray(center, dtype=float)
    # two orthogonal directions in the plane perpendicular to axis
    u = _perpendicular(axis)
    v = _unit(np.cross(axis, u))

    half = length / 2.0
    phi = np.linspace(0, 2 * np.pi, n, endpoint=False)
    rim = radius * (np.cos(phi)[:, None] * u + np.sin(phi)[:, None] * v)  # (n, 3)

    # vertices: top rim, bottom rim, top centre, bottom centre
    top_rim = (center + half * axis)[None, :] + rim        # (n, 3)
    bot_rim = (center - half * axis)[None, :] + rim        # (n, 3)
    top_ctr = center + half * axis                         # (3,)
    bot_ctr = center - half * axis                         # (3,)

    verts = np.vstack([top_rim, bot_rim,
                       top_ctr[None, :], bot_ctr[None, :]])  # (2n+2, 3)
    X = verts[:, 0]
    Y = verts[:, 1]
    Z = verts[:, 2]

    # indices
    I_list, J_list, K_list = [], [], []
    tc = 2 * n      # index of top centre
    bc = 2 * n + 1  # index of bottom centre

    for i in range(n):
        i1 = (i + 1) % n
        # top cap
        I_list.append(tc);  J_list.append(i);   K_list.append(i1)
        # bottom cap
        I_list.append(bc);  J_list.append(n + i1); K_list.append(n + i)
        # side quad -> two triangles
        I_list.append(i);     J_list.append(n + i);  K_list.append(i1)
        I_list.append(i1);    J_list.append(n + i);  K_list.append(n + i1)

    I_arr = np.array(I_list)
    J_arr = np.array(J_list)
    K_arr = np.array(K_list)
    return X, Y, Z, I_arr, J_arr, K_arr


# ---------------------------------------------------------------------------
# Beam tube helpers
# ---------------------------------------------------------------------------

def _tube_surface(pts: np.ndarray, radii: np.ndarray,
                  n: int = 16) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build a smooth tube surface from centre-line pts and per-point radii.

    Returns (X, Y, Z) arrays of shape (n, P) suitable for go.Surface.
    """
    P = len(pts)
    if P < 2:
        # degenerate – return a single ring
        r = radii[0] if len(radii) else 1.0
        phi = np.linspace(0, 2 * np.pi, n)
        circ = r * np.array([np.cos(phi), np.sin(phi), np.zeros(n)]).T
        X = circ[:, 0:1]; Y = circ[:, 1:2]; Z = circ[:, 2:3]
        return X, Y, Z

    # build per-point frames using parallel transport
    # initial tangent
    tangents = np.zeros((P, 3))
    for i in range(P - 1):
        d = pts[i + 1] - pts[i]
        ln = np.linalg.norm(d)
        tangents[i] = d / ln if ln > 1e-12 else tangents[max(i - 1, 0)]
    tangents[-1] = tangents[-2]

    u0 = _perpendicular(tangents[0])
    us = np.zeros((P, 3))
    us[0] = u0
    for i in range(1, P):
        # project previous u onto plane perpendicular to new tangent
        t = tangents[i]
        u_prev = us[i - 1]
        u_proj = u_prev - (u_prev @ t) * t
        n_proj = np.linalg.norm(u_proj)
        us[i] = u_proj / n_proj if n_proj > 1e-12 else _perpendicular(t)

    phi = np.linspace(0, 2 * np.pi, n, endpoint=True)
    # X,Y,Z have shape (n, P)
    Xg = np.zeros((n, P))
    Yg = np.zeros((n, P))
    Zg = np.zeros((n, P))
    for i in range(P):
        r = float(radii[i])
        t = tangents[i]
        u = us[i]
        vv = _unit(np.cross(t, u))
        ring = pts[i] + r * (np.cos(phi)[:, None] * u + np.sin(phi)[:, None] * vv)
        Xg[:, i] = ring[:, 0]
        Yg[:, i] = ring[:, 1]
        Zg[:, i] = ring[:, 2]
    return Xg, Yg, Zg


# ---------------------------------------------------------------------------
# Mirror frame helper (matches physics.build_mirror_ring convention)
# ---------------------------------------------------------------------------

def _mirror_frame(k: int, N: int, R_ring: float):
    """Return (center, normal_inward, sag, tan) for mirror k."""
    theta = 2.0 * np.pi * k / N
    center = np.array([R_ring * np.cos(theta), R_ring * np.sin(theta), 0.0])
    normal = -np.array([np.cos(theta), np.sin(theta), 0.0])   # points inward
    sag = np.array([0.0, 0.0, 1.0])
    tan = _unit(np.cross(sag, normal))
    return center, normal, sag, tan


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def render_experiment(res,
                      cfg,
                      out_path: str,
                      family: str = "one_inch",
                      show_beam: bool = True) -> str:
    """Render a photo-realistic Plotly 3-D view of the TMPC assembly.

    Parameters
    ----------
    res       : SimResult (from simulate_tmpc)
    cfg       : TMPCConfig
    out_path  : where to write the standalone HTML file
    family    : mirror catalogue family ('one_inch' or 'half_inch')
    show_beam : whether to draw the intra-cavity beam tube

    Returns
    -------
    out_path  : same string that was passed in
    """
    # --- soft-import Plotly ---------------------------------------------------
    try:
        import plotly.graph_objects as go
    except ImportError:
        raise ImportError(
            "plotly is required for render_experiment. "
            "Install it with:  pip install plotly"
        )

    # --- pull catalogue dimensions -------------------------------------------
    from tmpc_platform_v5.samplers import get_family as _get_family
    fam = _get_family(family)
    mirror_diam_mm = fam["diameter_mm"]          # 25.4 or 12.7
    mirror_radius = mirror_diam_mm / 2.0
    substrate_thickness = 6.0                    # mm — physical substrate depth

    # --- derived geometry -----------------------------------------------------
    baseplate_z = -cfg.H / 2.0 - 15.0           # breadboard plane
    post_radius = 3.0                            # mm

    # aesthetic constants
    GOLD = "#d4af37"
    GOLD_DARK = "#8b7117"
    MOUNT_COLOUR = "#6e6e6e"
    BEAM_COLOUR = "#ff3300"
    HOLE_COLOUR = "#1a1a1a"
    BP_COLOUR = "#b0b0b0"

    MIRROR_LIGHTING = dict(
        ambient=0.35, diffuse=0.7,
        specular=0.8, roughness=0.3, fresnel=0.2
    )

    traces = []

    # =========================================================================
    # 1.  Mirror substrates (thick cylinders, gold, with reflective face inward)
    # =========================================================================
    for k in range(cfg.N):
        center, normal, sag, tan = _mirror_frame(k, cfg.N, cfg.R_ring)

        # The cylinder axis is along *normal* (inward), i.e. the optical axis.
        # We offset the center so that the FRONT face (reflective) is at center,
        # and the substrate extends *away* from the cavity interior.
        # "inward" normal points toward the ring center, so the back of the
        # mirror (away from beam) is at center + normal * thickness.
        # We place the geometric cylinder mid-point at center + normal * (t/2).
        cyl_center = center + normal * (substrate_thickness / 2.0)

        X, Y, Z, I, J, K = _cylinder_mesh(
            cyl_center, normal, mirror_radius, substrate_thickness
        )
        traces.append(go.Mesh3d(
            x=X, y=Y, z=Z,
            i=I, j=J, k=K,
            color=GOLD,
            flatshading=False,
            lighting=MIRROR_LIGHTING,
            lightposition=dict(x=1, y=1, z=2),
            name=f"Mirror {k}",
            showlegend=(k == 0),
            legendgroup="mirrors",
            legendgrouptitle_text="Mirrors" if k == 0 else None,
            hovertemplate=f"Mirror {k}<extra></extra>",
            opacity=1.0,
        ))

    # =========================================================================
    # 2.  Entrance/exit hole on mirror 0 — dark disc on the reflective face
    # =========================================================================
    c0, n0, s0, t0 = _mirror_frame(0, cfg.N, cfg.R_ring)
    # Small disc at the face of mirror 0, slightly proud of the surface (~0.1 mm)
    hole_center = c0 + n0 * 0.1
    n_hole = 24
    phi_h = np.linspace(0, 2 * np.pi, n_hole, endpoint=False)
    hr = cfg.hole_radius
    hole_rim = (hole_center[None, :]
                + hr * (np.cos(phi_h)[:, None] * t0
                        + np.sin(phi_h)[:, None] * s0))
    hole_verts = np.vstack([hole_rim, hole_center[None, :]])
    Ih = np.arange(n_hole)
    Jh = np.roll(Ih, -1)
    Kh = np.full(n_hole, n_hole)
    traces.append(go.Mesh3d(
        x=hole_verts[:, 0], y=hole_verts[:, 1], z=hole_verts[:, 2],
        i=Ih, j=Jh, k=Kh,
        color=HOLE_COLOUR,
        opacity=1.0,
        name="Entrance/exit hole",
        showlegend=True,
        hovertemplate="Entrance/exit hole<extra></extra>",
    ))

    # =========================================================================
    # 3.  Mount posts — thin grey cylinders from mirror center to baseplate
    # =========================================================================
    for k in range(cfg.N):
        center, _, _, _ = _mirror_frame(k, cfg.N, cfg.R_ring)
        post_top = center                        # starts at mirror center
        post_bot = np.array([center[0], center[1], baseplate_z])
        post_length = float(np.linalg.norm(post_top - post_bot))
        post_mid = 0.5 * (post_top + post_bot)
        post_axis = _unit(post_top - post_bot)

        X, Y, Z, I, J, K = _cylinder_mesh(
            post_mid, post_axis, post_radius, post_length, n=16
        )
        traces.append(go.Mesh3d(
            x=X, y=Y, z=Z,
            i=I, j=J, k=K,
            color=MOUNT_COLOUR,
            flatshading=True,
            name="Mount post" if k == 0 else None,
            showlegend=(k == 0),
            legendgroup="posts",
            legendgrouptitle_text="Mount posts" if k == 0 else None,
            hovertemplate="Mount post<extra></extra>",
            opacity=0.85,
        ))

    # =========================================================================
    # 4.  Baseplate / breadboard
    # =========================================================================
    bp_extent = cfg.R_ring + mirror_radius + 20.0   # mm beyond ring edge
    bp_res = 4
    bp_x = np.linspace(-bp_extent, bp_extent, bp_res)
    bp_y = np.linspace(-bp_extent, bp_extent, bp_res)
    BPX, BPY = np.meshgrid(bp_x, bp_y)
    BPZ = np.full_like(BPX, baseplate_z)

    traces.append(go.Surface(
        x=BPX, y=BPY, z=BPZ,
        colorscale=[[0, BP_COLOUR], [1, BP_COLOUR]],
        showscale=False,
        opacity=0.55,
        name="Breadboard",
        showlegend=True,
        hovertemplate="Breadboard<extra></extra>",
        lighting=dict(ambient=0.5, diffuse=0.6, specular=0.3),
    ))

    # Tapped-hole grid (25 mm pitch), as small dark scatter dots on the board
    pitch = 25.0
    hx = np.arange(-bp_extent, bp_extent + pitch, pitch)
    hy = np.arange(-bp_extent, bp_extent + pitch, pitch)
    HX, HY = np.meshgrid(hx, hy)
    HX = HX.ravel(); HY = HY.ravel()
    mask = np.sqrt(HX**2 + HY**2) < bp_extent  # keep inside square (all pass)
    traces.append(go.Scatter3d(
        x=HX[mask], y=HY[mask], z=np.full(mask.sum(), baseplate_z + 0.2),
        mode="markers",
        marker=dict(size=2, color="#333333", symbol="circle"),
        name="Tap holes",
        showlegend=True,
        hovertemplate="Tap hole<extra></extra>",
    ))

    # =========================================================================
    # 5.  Laser beam tube (intra-cavity path)
    # =========================================================================
    if show_beam and res.spot_pattern is not None and len(res.spot_pattern) >= 2:
        from tmpc_platform_v5.beam import AstigBeam, envelope_along_path

        spots = np.asarray(res.spot_pattern, dtype=float)
        B = len(spots)

        # AOI per bounce in radians
        aoi_deg = np.asarray(res.aoi, dtype=float)
        aoi_rad_arr = np.deg2rad(aoi_deg)
        # Pad / trim to length B
        aoi_rad_list = list(np.resize(aoi_rad_arr, B))

        beam = AstigBeam(
            wavelength=cfg.wavelength,
            w0=cfg.w0,
            M2=cfg.M2,
        )

        env = envelope_along_path(
            beam, spots,
            [cfg.R_t] * B,
            [cfg.R_s] * B,
            aoi_rad_list,
            samples_per_segment=8,
        )

        tube_pts = np.asarray(env["points"], dtype=float)
        tube_w = np.asarray(env["w"], dtype=float)

        # Clip non-finite radii; fall back to w0
        bad = ~np.isfinite(tube_w) | (tube_w <= 0)
        tube_w[bad] = cfg.w0
        # clamp extremely large radii to mirror aperture to keep plot sane
        tube_w = np.clip(tube_w, 1e-4, cfg.mirror_aperture)

        # Scale beam tube for visibility (1/e^2 radius * scale)
        BEAM_SCALE = 3.0
        Xb, Yb, Zb = _tube_surface(tube_pts, tube_w * BEAM_SCALE, n=12)

        traces.append(go.Surface(
            x=Xb, y=Yb, z=Zb,
            colorscale=[[0, BEAM_COLOUR], [1, "#ff9966"]],
            showscale=False,
            opacity=0.65,
            name="Intra-cavity beam",
            showlegend=True,
            lighting=dict(ambient=0.8, diffuse=0.5, specular=0.5),
            hovertemplate="Intra-cavity beam<extra></extra>",
        ))

    # =========================================================================
    # 6.  Input beam (from outside to mirror 0)
    # =========================================================================
    if show_beam:
        # Entrance: approach mirror 0 from outside
        c0, n0_inw, _, _ = _mirror_frame(0, cfg.N, cfg.R_ring)
        # incoming direction: opposite of inward normal (rough approximation)
        # use the actual entry spot if available
        if res.exit_ray is not None and hasattr(res.exit_ray, "history") and len(res.exit_ray.history) >= 1:
            first_hit = np.asarray(res.exit_ray.history[0], dtype=float)
        elif res.spot_pattern is not None and len(res.spot_pattern) >= 1:
            first_hit = np.asarray(res.spot_pattern[0], dtype=float)
        else:
            first_hit = c0

        # draw input beam: from 3*R_ring outside the hole, to the first hit
        input_dir = _unit(first_hit - c0)
        input_start = c0 - 3.0 * cfg.R_ring * (-n0_inw)   # outside the ring
        input_pts = np.array([input_start, first_hit])
        input_w = np.array([cfg.w0, cfg.w0]) * 2.5

        Xi, Yi, Zi = _tube_surface(input_pts, input_w, n=10)
        traces.append(go.Surface(
            x=Xi, y=Yi, z=Zi,
            colorscale=[[0, "#cc0000"], [1, "#ff6600"]],
            showscale=False,
            opacity=0.7,
            name="Input beam",
            showlegend=True,
            hovertemplate="Input beam<extra></extra>",
        ))

    # =========================================================================
    # 7.  Exit beam (from exit_ray)
    # =========================================================================
    if show_beam and res.exit_ray is not None:
        exit_origin = np.asarray(res.exit_ray.origin, dtype=float)
        exit_dir = np.asarray(res.exit_ray.direction, dtype=float)
        exit_end = exit_origin + 2.0 * cfg.R_ring * exit_dir
        exit_pts = np.array([exit_origin, exit_end])
        exit_w = np.array([cfg.w0, cfg.w0]) * 2.5

        Xe, Ye, Ze = _tube_surface(exit_pts, exit_w, n=10)
        traces.append(go.Surface(
            x=Xe, y=Ye, z=Ze,
            colorscale=[[0, "#cc0000"], [1, "#ff6600"]],
            showscale=False,
            opacity=0.7,
            name="Exit beam",
            showlegend=True,
            hovertemplate="Exit beam<extra></extra>",
        ))

    # =========================================================================
    # 8.  Layout / camera / scene
    # =========================================================================
    opl_m = res.opl * 1e-3
    T_pct = res.throughput * 100.0
    title = (
        f"TMPC — as-built view  "
        f"(N={cfg.N}, OPL={opl_m:.2f} m, T={T_pct:.1f}%)"
    )

    fig = go.Figure(data=traces)
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16, color="#e0e0e0"),
            x=0.5, xanchor="center",
        ),
        paper_bgcolor="#0d0d0d",
        plot_bgcolor="#0d0d0d",
        scene=dict(
            bgcolor="#0d0d0d",
            aspectmode="data",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                       title="", backgroundcolor="#0d0d0d"),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                       title="", backgroundcolor="#0d0d0d"),
            zaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                       title="", backgroundcolor="#0d0d0d"),
            camera=dict(
                eye=dict(x=1.6, y=-1.6, z=1.2),
                up=dict(x=0, y=0, z=1),
                center=dict(x=0, y=0, z=0),
            ),
        ),
        legend=dict(
            font=dict(color="#cccccc"),
            bgcolor="rgba(20,20,20,0.7)",
            bordercolor="#444444",
            borderwidth=1,
        ),
        margin=dict(l=0, r=0, t=50, b=0),
    )

    # Ensure output directory exists
    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(out_dir, exist_ok=True)

    fig.write_html(out_path, include_plotlyjs="cdn")
    return out_path


# ---------------------------------------------------------------------------
# Self-test (run as script or imported with __name__ guard)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import shutil
    import sys

    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parents[1]))
    from tmpc_platform_v5 import TMPCConfig, simulate_tmpc

    cfg = TMPCConfig(
        N=10, R_ring=63, H=22, R_t=100, R_s=100,
        chord_skip=7, w0=0.8, mirror_aperture=11.4,
    )
    cfg.n_passes = 8 * cfg.N

    res = simulate_tmpc(cfg)
    out_dir = "tmpc_platform_v5/_selftest_render"
    out_path = os.path.join(out_dir, "exp.html")
    render_experiment(res, cfg, out_path, family="one_inch", show_beam=True)

    size = os.path.getsize(out_path)
    assert size > 1024, f"Output file too small: {size} bytes"
    print(f"OK — wrote {out_path} ({size} bytes)")

    # clean up
    shutil.rmtree(out_dir, ignore_errors=True)
    print("Self-test directory cleaned up.")
