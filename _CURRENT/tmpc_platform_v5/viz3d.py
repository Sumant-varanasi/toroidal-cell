"""Interactive 3D visualisation of a TMPC simulation result.

Ported and modernised from tmpc_platform_v4/tmpc_platform/scripts/visualise_3d.py
with the following upgrades for v5:
  - Uses the real SimResult from simulate_tmpc (not a re-run inside the viewer)
  - Renders a smooth elliptical beam tube (Surface mesh) via envelope_along_path
  - Uses the canonical mirror_footprints() helper for per-mirror projections
  - Supports toroidal mirror surfaces (R_t != R_s), spiral topology, astigmatic beams
  - All plotly imports are soft-imported inside functions (pip install plotly)

Public API
----------
mirror_surface_mesh(center, normal, sag_axis, aperture, R_t, R_s, n=24) -> (X, Y, Z)
build_cell_figure(res, cfg, label='') -> plotly.graph_objects.Figure
compute_abcd_spot_pattern(cfg, n_bounces) -> ndarray (n, 3)
build_constellations(cfg, spots, mirror_seq, model_label='raytrace') -> plotly Figure
write_visualisation_bundle(res, cfg, out_dir, name='design', label='') -> dict
"""
from __future__ import annotations

import math
import os
from typing import Optional, Sequence

import numpy as np


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _unit(v: np.ndarray) -> np.ndarray:
    """Return unit vector; returns v unchanged if norm is near zero."""
    n = np.linalg.norm(v)
    return v / n if n > 1e-20 else v


# ---------------------------------------------------------------------------
# 1. Mirror surface mesh
# ---------------------------------------------------------------------------

def mirror_surface_mesh(
    center: np.ndarray,
    normal: np.ndarray,
    sag_axis: np.ndarray,
    aperture: float,
    R_t: float,
    R_s: float,
    n: int = 24,
):
    """Return (X, Y, Z) arrays for a toroidal mirror patch.

    Port of v4 ``_mirror_surface_mesh``.  The patch is parameterised on a
    local (u, v) grid:

      * u  -- tangential direction (in-ring plane)
      * v  -- sagittal direction (vertical / z)

    Second-order sag approximation (plenty for visualisation):
        sag(u, v) = u^2 / (2*R_t) + v^2 / (2*R_s)

    The mirror curves *away* from the incoming ray (sag subtracted along
    the inward normal direction).

    Parameters
    ----------
    center      : (3,) world-space position of the mirror centre
    normal      : (3,) surface normal pointing inward (toward the cell axis)
    sag_axis    : (3,) sagittal axis (unit, perpendicular to normal)
    aperture    : clear-aperture radius [mm]
    R_t         : tangential radius of curvature [mm]
    R_s         : sagittal radius of curvature [mm]
    n           : number of grid points along each axis (n×n grid)

    Returns
    -------
    X, Y, Z : (n, n) float arrays suitable for ``go.Surface``
    """
    e_n = _unit(np.asarray(normal, dtype=float))
    e_s = _unit(np.asarray(sag_axis, dtype=float))
    # tangential axis: right-hand rule  e_t = e_s × e_n
    e_t = np.cross(e_s, e_n)
    e_t = _unit(e_t)
    center = np.asarray(center, dtype=float)

    a = float(aperture)
    u = np.linspace(-a, a, n)
    v = np.linspace(-a, a, n)
    U, V = np.meshgrid(u, v)

    # circular aperture mask
    mask = U ** 2 + V ** 2 <= a ** 2

    # second-order sag (depth)
    R_t_safe = R_t if abs(R_t) > 1e-6 else 1e-6
    R_s_safe = R_s if abs(R_s) > 1e-6 else 1e-6
    sag = U ** 2 / (2.0 * R_t_safe) + V ** 2 / (2.0 * R_s_safe)
    sag = np.where(mask, sag, np.nan)

    # world-space coords
    pts = (center[None, None, :] +
           U[..., None] * e_t +
           V[..., None] * e_s -
           sag[..., None] * e_n)   # curves away from incoming beam

    return pts[..., 0], pts[..., 1], pts[..., 2]


# ---------------------------------------------------------------------------
# 2. Build the 3-D cell figure
# ---------------------------------------------------------------------------

def build_cell_figure(res, cfg, label: str = ""):
    """Build an interactive Plotly 3-D figure for a TMPC SimResult.

    Traces included
    ---------------
    * One ``go.Surface`` per mirror (toroidal mesh, semi-transparent steel-blue)
    * ``go.Scatter3d`` line connecting all bounce spots (ray path)
    * ``go.Scatter3d`` markers coloured by bounce order (Plasma, with colorbar)
    * Input ray  -- back-extrapolation of the first chord (dashed green)
    * Exit ray   -- propagated from ``res.exit_ray`` (dashed cyan)
    * Beam tube  -- smooth elliptical surface built from ``envelope_along_path``

    Parameters
    ----------
    res   : SimResult  (from simulate_tmpc)
    cfg   : TMPCConfig
    label : optional string appended to the figure title

    Returns
    -------
    plotly.graph_objects.Figure
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        raise ImportError(
            "plotly is required for viz3d — run: pip install plotly"
        )

    from tmpc_platform_v5.beam import AstigBeam, envelope_along_path

    spots = np.asarray(res.spot_pattern)   # (B, 3)
    n_b = int(res.bounces)
    traces = []

    # ------------------------------------------------------------------
    # Mirror surfaces
    # ------------------------------------------------------------------
    for k in range(cfg.N):
        theta = 2.0 * np.pi * k / cfg.N
        center = np.array([cfg.R_ring * np.cos(theta),
                           cfg.R_ring * np.sin(theta), 0.0])
        normal = -np.array([np.cos(theta), np.sin(theta), 0.0])
        sag = np.array([0.0, 0.0, 1.0])
        X, Y, Z = mirror_surface_mesh(
            center, normal, sag, cfg.mirror_aperture, cfg.R_t, cfg.R_s, n=20
        )
        traces.append(go.Surface(
            x=X, y=Y, z=Z,
            showscale=False,
            opacity=0.45,
            colorscale=[[0, "#7faed1"], [1, "#3d6c92"]],
            hoverinfo="skip",
            name=f"mirror {k}",
            legendgroup="mirrors",
            showlegend=(k == 0),
        ))

    # ------------------------------------------------------------------
    # Ray path (connected line through all bounce hits)
    # ------------------------------------------------------------------
    if n_b > 0:
        traces.append(go.Scatter3d(
            x=spots[:, 0], y=spots[:, 1], z=spots[:, 2],
            mode="lines",
            line=dict(color="rgba(255,80,80,0.85)", width=2),
            name=f"ray path ({n_b} bounces)",
            hoverinfo="skip",
        ))

    # ------------------------------------------------------------------
    # Spot markers (Plasma, coloured by bounce index)
    # ------------------------------------------------------------------
    if n_b > 0:
        traces.append(go.Scatter3d(
            x=spots[:, 0], y=spots[:, 1], z=spots[:, 2],
            mode="markers",
            marker=dict(
                size=4,
                color=np.arange(n_b),
                colorscale="Plasma",
                colorbar=dict(title="bounce #", x=1.02, len=0.55,
                              tickfont=dict(color="#eaeaea"),
                              title_font=dict(color="#eaeaea")),
                showscale=True,
            ),
            text=[
                f"bounce {i}<br>x={p[0]:.2f}<br>y={p[1]:.2f}<br>z={p[2]:.2f}"
                for i, p in enumerate(spots)
            ],
            hoverinfo="text",
            name="spots",
        ))

    # ------------------------------------------------------------------
    # Input ray: back-extrapolate from first chord direction
    # ------------------------------------------------------------------
    if n_b >= 2:
        d_in = _unit(spots[1] - spots[0])
        entry_pt = spots[0] - 1.5 * cfg.R_ring * d_in
        traces.append(go.Scatter3d(
            x=[entry_pt[0], spots[0][0]],
            y=[entry_pt[1], spots[0][1]],
            z=[entry_pt[2], spots[0][2]],
            mode="lines",
            line=dict(color="#33cc33", width=5, dash="dash"),
            name="input beam",
        ))

    # ------------------------------------------------------------------
    # Exit ray: from res.exit_ray if available
    # ------------------------------------------------------------------
    if res.exit_ray is not None:
        origin = np.asarray(res.exit_ray.origin, dtype=float)
        direction = _unit(np.asarray(res.exit_ray.direction, dtype=float))
        exit_end = origin + 1.5 * cfg.R_ring * direction
        traces.append(go.Scatter3d(
            x=[origin[0], exit_end[0]],
            y=[origin[1], exit_end[1]],
            z=[origin[2], exit_end[2]],
            mode="lines",
            line=dict(color="#00e5e5", width=4, dash="dash"),
            name="exit beam",
        ))

    # ------------------------------------------------------------------
    # Beam tube (elliptical surface mesh via envelope_along_path)
    # ------------------------------------------------------------------
    if n_b >= 2:
        try:
            beam = AstigBeam(
                wavelength=cfg.wavelength,
                w0=cfg.w0,
                M2=getattr(cfg, "M2", 1.0),
            )
            aoi_rad = np.deg2rad(np.asarray(res.aoi, dtype=float))
            n_seg = min(n_b, len(aoi_rad))
            R_t_list = [cfg.R_t] * n_seg
            R_s_list = [cfg.R_s] * n_seg
            env = envelope_along_path(
                beam, spots, R_t_list, R_s_list, aoi_rad,
                samples_per_segment=10,
            )
            P = np.asarray(env["points"])    # (M, 3)
            w_t = np.asarray(env["w_t"])     # (M,)
            w_s = np.asarray(env["w_s"])     # (M,)

            # guard against inf / nan — clip to a sane maximum
            w_max_safe = float(cfg.mirror_aperture)
            w_t = np.clip(np.where(np.isfinite(w_t), w_t, w_max_safe),
                          0.0, w_max_safe)
            w_s = np.clip(np.where(np.isfinite(w_s), w_s, w_max_safe),
                          0.0, w_max_safe)

            # build elliptical tube as a Surface (npoints × nphi)
            n_phi = 24
            phi = np.linspace(0.0, 2.0 * np.pi, n_phi, endpoint=False)
            cos_phi = np.cos(phi)
            sin_phi = np.sin(phi)
            M = len(P)

            # local tangent vectors at each sample
            # t[i] = direction from P[i] to P[i+1] (or P[i-1] at the end)
            tangents = np.zeros_like(P)
            tangents[:-1] = P[1:] - P[:-1]
            tangents[-1] = tangents[-2]
            tangents = np.array([_unit(t) for t in tangents])

            # tube_tan = unit(z × tangent); tube_sag = unit(tangent × tube_tan)
            z_ax = np.array([0.0, 0.0, 1.0])
            tube_Tx = np.zeros((M, 3))
            tube_Sx = np.zeros((M, 3))
            for i in range(M):
                t = tangents[i]
                cross = np.cross(z_ax, t)
                if np.linalg.norm(cross) < 1e-9:
                    cross = np.cross(np.array([1.0, 0.0, 0.0]), t)
                tx = _unit(cross)
                sx = _unit(np.cross(t, tx))
                tube_Tx[i] = tx
                tube_Sx[i] = sx

            # Surface grid: shape (M, n_phi) — rows = path samples, cols = angle
            # Xt[i, j] = P[i] + w_t[i]*cos(phi[j])*tube_Tx[i]
            #                  + w_s[i]*sin(phi[j])*tube_Sx[i]
            Xt = (P[:, 0:1] +
                  w_t[:, None] * cos_phi[None, :] * tube_Tx[:, 0:1] +
                  w_s[:, None] * sin_phi[None, :] * tube_Sx[:, 0:1])
            Yt = (P[:, 1:2] +
                  w_t[:, None] * cos_phi[None, :] * tube_Tx[:, 1:2] +
                  w_s[:, None] * sin_phi[None, :] * tube_Sx[:, 1:2])
            Zt = (P[:, 2:3] +
                  w_t[:, None] * cos_phi[None, :] * tube_Tx[:, 2:3] +
                  w_s[:, None] * sin_phi[None, :] * tube_Sx[:, 2:3])

            traces.append(go.Surface(
                x=Xt, y=Yt, z=Zt,
                showscale=False,
                opacity=0.22,
                colorscale=[[0, "#ff6a00"], [1, "#ee0979"]],
                hoverinfo="skip",
                name="beam tube",
                showlegend=True,
            ))
        except Exception:
            # beam tube is optional — never crash the main figure
            pass

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    title_text = (
        f"<b>{label}</b><br>"
        f"N={cfg.N}  skip={cfg.chord_skip}  R_ring={cfg.R_ring:.1f} mm  "
        f"H={cfg.H:.1f} mm  R_t={cfg.R_t:.0f}  R_s={cfg.R_s:.0f}<br>"
        f"OPL={res.opl * 1e-3:.3f} m | bounces={n_b} | "
        f"throughput={res.throughput * 100:.2f}% | clipped={res.clipped}"
    )
    fig = go.Figure(data=traces)
    fig.update_layout(
        title=dict(text=title_text, x=0.5, font=dict(size=13, color="#eaeaea")),
        scene=dict(
            xaxis_title="x [mm]",
            yaxis_title="y [mm]",
            zaxis_title="z [mm]",
            aspectmode="data",
            bgcolor="#101418",
            xaxis=dict(color="#9ab", gridcolor="#2a3040"),
            yaxis=dict(color="#9ab", gridcolor="#2a3040"),
            zaxis=dict(color="#9ab", gridcolor="#2a3040"),
        ),
        paper_bgcolor="#101418",
        font=dict(color="#eaeaea"),
        margin=dict(l=0, r=0, t=90, b=0),
        legend=dict(x=0.02, y=0.98, bgcolor="rgba(0,0,0,0.4)",
                    font=dict(color="#eaeaea")),
    )
    return fig


# ---------------------------------------------------------------------------
# 3. ABCD spot pattern (paraxial model)
# ---------------------------------------------------------------------------

def compute_abcd_spot_pattern(cfg, n_bounces: int) -> np.ndarray:
    """Predict spot positions from the paraxial ABCD ray-transfer model.

    Port of v4 ``compute_abcd_spot_pattern``.

    Each bounce the (position, slope) pair in the tangential and sagittal
    axes is propagated by the per-bounce ray-transfer matrix::

        M = [[1,  c],
             [-2/R, 1 - 2c/R]]

    where ``c = 2*R_ring*sin(pi*chord_skip/N)`` is the chord length.  When
    ``R_t != R_s`` the two axes have different phase advances and the
    per-mirror revisit pattern is a Lissajous figure.

    Parameters
    ----------
    cfg       : TMPCConfig
    n_bounces : number of bounces to simulate

    Returns
    -------
    positions : ndarray of shape (n_bounces, 3) in world mm
    """
    c = 2.0 * cfg.R_ring * np.sin(np.pi * cfg.chord_skip / cfg.N)

    def _M(R: float) -> np.ndarray:
        return np.array([[1.0, c],
                         [-2.0 / R, 1.0 - 2.0 * c / R]])

    M_t = _M(cfg.R_t)
    M_s = _M(cfg.R_s)

    # initial states in local mirror frame
    state_t = np.array([0.0, getattr(cfg, "input_angle", 0.0)])
    state_s = np.array([getattr(cfg, "input_offset_z", 0.0), 0.0])

    positions = np.zeros((n_bounces, 3))
    for i in range(n_bounces):
        k = (i * cfg.chord_skip) % cfg.N
        theta = 2.0 * np.pi * k / cfg.N
        centre = np.array([cfg.R_ring * np.cos(theta),
                           cfg.R_ring * np.sin(theta), 0.0])
        normal = -np.array([np.cos(theta), np.sin(theta), 0.0])
        sag = np.array([0.0, 0.0, 1.0])
        tan = _unit(np.cross(sag, normal))
        positions[i] = centre + state_t[0] * tan + state_s[0] * sag
        state_t = M_t @ state_t
        state_s = M_s @ state_s

    return positions


# ---------------------------------------------------------------------------
# 4. Per-mirror constellation plots
# ---------------------------------------------------------------------------

def build_constellations(cfg, spots: np.ndarray, mirror_seq: np.ndarray,
                         model_label: str = "raytrace"):
    """Per-mirror subplot grid showing spot footprints in local (u, v) coords.

    For the ray-trace model the (u, v, visit_order) data are obtained via the
    canonical ``mirror_footprints()`` helper.  For the ABCD model call this
    function with a synthetic mirror_seq built as ``k = (i*chord_skip) % N``.

    Parameters
    ----------
    cfg         : TMPCConfig
    spots       : (B, 3) array of bounce hit-points in world mm
    mirror_seq  : (B,) int array — which mirror each bounce hit
    model_label : title label (e.g. 'raytrace' or 'ABCD / Lissajous')

    Returns
    -------
    plotly.graph_objects.Figure with one subplot per mirror
    """
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        raise ImportError(
            "plotly is required for viz3d — run: pip install plotly"
        )

    from tmpc_platform_v5 import mirror_footprints

    footprints = mirror_footprints(
        np.asarray(spots, dtype=float),
        np.asarray(mirror_seq, dtype=int),
        cfg,
    )

    ncols = min(cfg.N, 4)
    nrows = math.ceil(cfg.N / ncols)
    fig = make_subplots(
        rows=nrows, cols=ncols,
        subplot_titles=[f"mirror {k}" for k in range(cfg.N)],
        horizontal_spacing=0.04,
        vertical_spacing=0.07,
    )

    th = np.linspace(0.0, 2.0 * np.pi, 64)
    aper_x = cfg.mirror_aperture * np.cos(th)
    aper_y = cfg.mirror_aperture * np.sin(th)

    for k in range(cfg.N):
        row = k // ncols + 1
        col = k % ncols + 1
        data = footprints.get(k, np.empty((0, 3)))  # (m, 3): u, v, order

        # aperture circle
        fig.add_trace(
            go.Scatter(
                x=aper_x, y=aper_y,
                mode="lines",
                line=dict(color="#5b88b0", width=1),
                showlegend=False,
                hoverinfo="skip",
            ),
            row=row, col=col,
        )

        if len(data) > 0:
            u_vals = data[:, 0]
            v_vals = data[:, 1]
            order = data[:, 2].astype(int)
        else:
            u_vals = np.array([])
            v_vals = np.array([])
            order = np.array([], dtype=int)

        fig.add_trace(
            go.Scatter(
                x=u_vals, y=v_vals,
                mode="markers+lines",
                marker=dict(
                    size=5,
                    color=order,
                    colorscale="Plasma",
                    showscale=(k == 0),
                    colorbar=(dict(title="visit #", x=1.02,
                                  tickfont=dict(color="#eaeaea"),
                                  title_font=dict(color="#eaeaea"))
                              if k == 0 else None),
                ),
                line=dict(color="rgba(255,200,100,0.25)", width=1),
                showlegend=False,
                hovertemplate=(
                    "visit %{marker.color}<br>"
                    "u=%{x:.2f} mm<br>v=%{y:.2f} mm<extra></extra>"
                ),
            ),
            row=row, col=col,
        )

        # equal-aspect axes locked to the aperture
        lim = cfg.mirror_aperture * 1.15
        fig.update_xaxes(range=[-lim, lim], row=row, col=col,
                         scaleanchor=f"y{k + 1 if k else ''}",
                         scaleratio=1)
        fig.update_yaxes(range=[-lim, lim], row=row, col=col)

    fig.update_layout(
        title=dict(
            text=(
                f"Per-mirror spot constellations — <b>{model_label}</b>"
                f"  (aperture radius = {cfg.mirror_aperture:.1f} mm)"
            ),
            x=0.5, font=dict(color="#eaeaea"),
        ),
        paper_bgcolor="#101418",
        plot_bgcolor="#181c20",
        font=dict(color="#eaeaea", size=11),
        height=260 * nrows,
        width=260 * ncols + 100,
        margin=dict(l=20, r=60, t=70, b=20),
    )
    # darken subplot backgrounds
    for annotation in fig.layout.annotations:
        annotation.font = dict(color="#ccc", size=10)

    return fig


# ---------------------------------------------------------------------------
# 5. Write the full visualisation bundle
# ---------------------------------------------------------------------------

def write_visualisation_bundle(res, cfg, out_dir: str, name: str = "design",
                               label: str = "") -> dict:
    """Write all three HTML visualisations and return a dict of file paths.

    Files written
    -------------
    ``<name>_cell3d.html``                  -- build_cell_figure
    ``<name>_constellations_raytrace.html`` -- build_constellations (raytrace)
    ``<name>_constellations_abcd.html``     -- ABCD model constellations

    Parameters
    ----------
    res     : SimResult
    cfg     : TMPCConfig
    out_dir : directory to write HTML files (created if absent)
    name    : filename prefix (no spaces)
    label   : human-readable label forwarded to build_cell_figure title

    Returns
    -------
    dict with keys 'cell3d', 'constellation_raytrace', 'constellation_abcd'
    mapping to absolute file paths.
    """
    try:
        import plotly  # noqa: F401 — just to give a clear error early
    except ImportError:
        raise ImportError(
            "plotly is required for viz3d — run: pip install plotly"
        )

    os.makedirs(out_dir, exist_ok=True)

    # ---------- 3-D cell view ----------
    cell_path = os.path.join(out_dir, f"{name}_cell3d.html")
    fig_cell = build_cell_figure(res, cfg, label=label)
    fig_cell.write_html(cell_path, include_plotlyjs="cdn", full_html=True)

    # ---------- ray-trace constellations ----------
    spots = np.asarray(res.spot_pattern, dtype=float)
    mirror_seq = np.asarray(res.mirror_sequence, dtype=int)
    rt_path = os.path.join(out_dir, f"{name}_constellations_raytrace.html")
    fig_rt = build_constellations(cfg, spots, mirror_seq, model_label="raytrace")
    fig_rt.write_html(rt_path, include_plotlyjs="cdn", full_html=True)

    # ---------- ABCD / Lissajous constellations ----------
    n_b = int(res.bounces)
    abcd_spots = compute_abcd_spot_pattern(cfg, n_b)
    abcd_seq = np.array([(i * cfg.chord_skip) % cfg.N for i in range(n_b)],
                        dtype=int)
    abcd_path = os.path.join(out_dir, f"{name}_constellations_abcd.html")
    fig_abcd = build_constellations(cfg, abcd_spots, abcd_seq,
                                    model_label="ABCD / Lissajous")
    fig_abcd.write_html(abcd_path, include_plotlyjs="cdn", full_html=True)

    return {
        "cell3d": os.path.abspath(cell_path),
        "constellation_raytrace": os.path.abspath(rt_path),
        "constellation_abcd": os.path.abspath(abcd_path),
    }


# ---------------------------------------------------------------------------
# Self-test / demo  (run as: python -m tmpc_platform_v5.viz3d)
# ---------------------------------------------------------------------------

def _self_test():
    """Quick smoke-test: simulate, write 3 HTML files, check sizes, clean up."""
    import shutil
    from tmpc_platform_v5 import TMPCConfig, simulate_tmpc

    cfg = TMPCConfig(
        N=12, R_ring=60, H=40, R_t=120, R_s=180,
        chord_skip=5, w0=0.5, input_offset_z=-2,
    )
    cfg.n_passes = 8 * cfg.N  # as specified
    res = simulate_tmpc(cfg)

    out_dir = os.path.join(
        os.path.dirname(__file__), "_selftest_viz"
    )
    paths = write_visualisation_bundle(res, cfg, out_dir, name="design",
                                       label="self-test")
    errors = []
    for key, path in paths.items():
        if not os.path.exists(path):
            errors.append(f"MISSING: {path}")
        elif os.path.getsize(path) < 1024:
            errors.append(f"TOO SMALL (<1 KB): {path}")

    shutil.rmtree(out_dir, ignore_errors=True)

    if errors:
        raise RuntimeError("Self-test FAILED:\n" + "\n".join(errors))
    print("OK — all 3 HTML files written and verified.")
    return paths


if __name__ == "__main__":
    _self_test()
