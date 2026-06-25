"""Interactive 3D visualisation of a toroidal multipass cell run.

Renders the mirror ring, ray trajectory between bounces, spot pattern
on each mirror, and per-bounce beam radius. Output is a standalone
HTML file you open in a browser and rotate.

Usage:
    python -m tmpc_platform.scripts.visualise_3d --preset bo_best_one_inch
    python -m tmpc_platform.scripts.visualise_3d --preset longest_opl
    python -m tmpc_platform.scripts.visualise_3d --N 15 --skip 7 --R_ring 116 \
        --H 21 --R_t 1500 --w0 0.75 --bounces 120 --R 0.98
"""
from __future__ import annotations
import argparse, os, json
import numpy as np
import plotly.graph_objects as go

from tmpc_platform.physics_engine.multipass import TMPCConfig, simulate_tmpc
from tmpc_platform.physics_engine.gaussian_beam import GaussianBeam, propagate_through_cell


PRESETS = {
    "bo_best_one_inch": dict(
        N=10, chord_skip=7, R_ring=63.14, H=21.6,
        R_t=100.0, R_s=100.0, mirror_aperture=11.4,
        w0=0.98, input_offset_z=-1.99, input_angle=-0.0481,
        n_passes=80, reflectivity=0.98,
        label="BO best (one_inch, R=0.98)"),
    "bo_best_half_inch": dict(
        N=8, chord_skip=3, R_ring=49.22, H=35.30,
        R_t=100.0, R_s=100.0, mirror_aperture=5.7,
        w0=1.22, input_offset_z=2.29, input_angle=0.0334,
        n_passes=64, reflectivity=0.98,
        label="BO best (half_inch, R=0.98)"),
    "longest_opl": dict(
        N=16, chord_skip=7, R_ring=119.24, H=36.43,
        R_t=500.0, R_s=500.0, mirror_aperture=11.4,
        w0=1.17, input_offset_z=2.2, input_angle=0.022,
        n_passes=128, reflectivity=0.98,
        label="Longest OPL (29.9 m @ R=0.98 -> 7.3% T)"),
    "sweet_spot_120": dict(
        N=15, chord_skip=7, R_ring=116.18, H=20.97,
        R_t=1500.0, R_s=1500.0, mirror_aperture=11.4,
        w0=0.75, input_offset_z=1.6, input_angle=0.018,
        n_passes=120, reflectivity=0.98,
        label="Sweet spot: 27.7 m @ 8.85% T"),
    "toroidal_lissajous": dict(
        N=16, chord_skip=7, R_ring=119.24, H=36.43,
        R_t=500.0, R_s=300.0, mirror_aperture=11.4,
        w0=1.17, input_offset_z=2.2, input_angle=0.022,
        n_passes=128, reflectivity=0.98,
        label="Toroidal (R_t=500, R_s=300) -- Lissajous demo"),
}


def _mirror_surface_mesh(center, normal, sag_axis, aperture, R_t, R_s, n=24):
    """Return x,y,z arrays for a toroidal mirror patch centred at `center`.

    The patch is the small region of a toroid visible through the circular
    aperture. We parameterise it on a local (u,v) grid with u along the
    tangential (in-ring) direction and v along the sagittal (vertical) axis.
    """
    # local frame: e_n = normal, e_s = sag_axis, e_t = e_s x e_n
    e_n = np.asarray(normal) / np.linalg.norm(normal)
    e_s = np.asarray(sag_axis) / np.linalg.norm(sag_axis)
    e_t = np.cross(e_s, e_n)
    e_t /= np.linalg.norm(e_t)
    a = aperture
    u = np.linspace(-a, a, n)
    v = np.linspace(-a, a, n)
    U, V = np.meshgrid(u, v)
    mask = U**2 + V**2 <= a**2
    # sag (depth) at (u,v) on a toroid with R_t along u and R_s along v
    # second-order sag approximation, plenty for visualisation
    sag = (U**2) / (2 * R_t) + (V**2) / (2 * R_s)
    sag = np.where(mask, sag, np.nan)
    pts = (center[None, None, :] +
           U[..., None] * e_t +
           V[..., None] * e_s -
           sag[..., None] * e_n)  # mirror curves *away* from incoming ray
    return pts[..., 0], pts[..., 1], pts[..., 2]


def _per_bounce_beam_radius(cfg: TMPCConfig, n_bounces: int):
    chord = 2 * cfg.R_ring * np.sin(np.pi * cfg.chord_skip / cfg.N)
    f_t = cfg.R_t / 2.0
    f_s = cfg.R_s / 2.0
    beam = GaussianBeam(wavelength=cfg.wavelength, w0=cfg.w0)
    prop = propagate_through_cell(
        beam,
        segments=[chord] * max(1, n_bounces),
        focal_tan=[f_t] * max(1, n_bounces),
        focal_sag=[f_s] * max(1, n_bounces),
    )
    # propagate_through_cell typically returns per-segment beam widths;
    # if not available, return the max repeated.
    if "w_tan" in prop and "w_sag" in prop:
        w_t = np.asarray(prop["w_tan"])
        w_s = np.asarray(prop["w_sag"])
    else:
        w_t = np.full(n_bounces, prop["w_max"])
        w_s = w_t
    return w_t[:n_bounces], w_s[:n_bounces]


def compute_abcd_spot_pattern(cfg: TMPCConfig, n_bounces: int) -> np.ndarray:
    """Predict bounce-by-bounce spot positions from the paraxial ABCD model.

    For each bounce the (position, slope) pair in the tangential and
    sagittal axes is propagated by the per-bounce ray-transfer matrix
        M = [[1, c], [-2/R, 1 - 2c/R]]
    where c is the chord length between mirrors. The eigenvalues are
    exp(+/- i*theta) with cos(theta) = 1 - c/R, so the position on each
    successive bounce traces a sinusoid in i. When R_t != R_s the two
    axes have different phase advances and the per-mirror revisit
    pattern is a Lissajous figure -- the realistic Herriott / toroidal
    spot constellation.
    """
    c = 2 * cfg.R_ring * np.sin(np.pi * cfg.chord_skip / cfg.N)
    def per_bounce(R):
        return np.array([[1.0,        c],
                         [-2.0 / R,   1.0 - 2 * c / R]])
    M_t = per_bounce(cfg.R_t)
    M_s = per_bounce(cfg.R_s)

    # initial (position, slope) on mirror 0 in local (tangential, sagittal)
    # tangential: enter on-axis with tilt = input_angle
    # sagittal:   enter at z = input_offset_z, zero slope
    state_t = np.array([0.0, cfg.input_angle])
    state_s = np.array([cfg.input_offset_z, 0.0])

    positions = np.zeros((n_bounces, 3))
    for i in range(n_bounces):
        k = (i * cfg.chord_skip) % cfg.N
        theta = 2 * np.pi * k / cfg.N
        centre = np.array([cfg.R_ring * np.cos(theta),
                           cfg.R_ring * np.sin(theta), 0.0])
        normal = -np.array([np.cos(theta), np.sin(theta), 0.0])
        sag = np.array([0.0, 0.0, 1.0])
        tan = np.cross(sag, normal)
        positions[i] = centre + state_t[0] * tan + state_s[0] * sag
        state_t = M_t @ state_t
        state_s = M_s @ state_s
    return positions


def build_mirror_constellations(cfg: TMPCConfig, spots: np.ndarray,
                                model_label: str = "raytrace"):
    """For each mirror, project the hits onto the mirror's local (tangential,
    sagittal) plane. Returns a plotly Figure with one subplot per mirror.
    """
    import math
    from plotly.subplots import make_subplots

    # build per-mirror local frame matching multipass._build_mirror_ring
    per_mirror_hits = [[] for _ in range(cfg.N)]
    # assign each spot to its mirror by index in the chord sequence
    for i, p in enumerate(spots):
        k = (i * cfg.chord_skip) % cfg.N  # mirror visited at bounce i
        per_mirror_hits[k].append(p)

    ncols = min(cfg.N, 4)
    nrows = math.ceil(cfg.N / ncols)
    fig = make_subplots(
        rows=nrows, cols=ncols,
        subplot_titles=[f"mirror {k}" for k in range(cfg.N)],
        horizontal_spacing=0.04, vertical_spacing=0.06)

    for k in range(cfg.N):
        theta = 2 * np.pi * k / cfg.N
        c = np.array([cfg.R_ring * np.cos(theta),
                      cfg.R_ring * np.sin(theta), 0.0])
        normal = -np.array([np.cos(theta), np.sin(theta), 0.0])
        sag = np.array([0.0, 0.0, 1.0])
        tan = np.cross(sag, normal); tan /= np.linalg.norm(tan)
        hits = np.array(per_mirror_hits[k]) if per_mirror_hits[k] else np.empty((0, 3))
        if len(hits):
            local = hits - c
            u = local @ tan       # tangential offset
            v = local @ sag       # sagittal (z) offset
            order = np.arange(len(hits))
        else:
            u, v, order = [], [], []
        row, col = k // ncols + 1, k % ncols + 1
        # aperture circle
        th = np.linspace(0, 2*np.pi, 64)
        fig.add_trace(go.Scatter(
            x=cfg.mirror_aperture*np.cos(th),
            y=cfg.mirror_aperture*np.sin(th),
            mode="lines", line=dict(color="#5b88b0", width=1),
            showlegend=False, hoverinfo="skip"), row=row, col=col)
        fig.add_trace(go.Scatter(
            x=u, y=v, mode="markers+lines",
            marker=dict(size=5, color=order, colorscale="Plasma",
                        showscale=(k == 0),
                        colorbar=dict(title="visit #", x=1.02) if k == 0 else None),
            line=dict(color="rgba(255,200,100,0.25)", width=1),
            showlegend=False,
            hovertemplate="visit %{marker.color}<br>u=%{x:.2f}<br>v=%{y:.2f}<extra></extra>"),
            row=row, col=col)
        fig.update_xaxes(scaleanchor=f"y{k+1 if k else ''}",
                         scaleratio=1, row=row, col=col,
                         range=[-cfg.mirror_aperture*1.1, cfg.mirror_aperture*1.1])
        fig.update_yaxes(range=[-cfg.mirror_aperture*1.1, cfg.mirror_aperture*1.1],
                         row=row, col=col)

    fig.update_layout(
        title=(f"Per-mirror spot constellations &mdash; <b>{model_label}</b> "
               f"model  (aperture = {cfg.mirror_aperture} mm)"),
        paper_bgcolor="#101418", plot_bgcolor="#181c20",
        font=dict(color="#eaeaea", size=11),
        height=260 * nrows, width=260 * ncols + 80,
        margin=dict(l=20, r=20, t=70, b=20))
    return fig


def build_figure(cfg: TMPCConfig, label: str):
    res = simulate_tmpc(cfg)
    spots = res.spot_pattern  # (n,3)
    n_b = res.bounces

    # ----- mirror surfaces -----
    mirror_traces = []
    for k in range(cfg.N):
        theta = 2 * np.pi * k / cfg.N
        c = np.array([cfg.R_ring * np.cos(theta),
                      cfg.R_ring * np.sin(theta), 0.0])
        normal = -np.array([np.cos(theta), np.sin(theta), 0.0])
        sag = np.array([0.0, 0.0, 1.0])
        X, Y, Z = _mirror_surface_mesh(c, normal, sag, cfg.mirror_aperture,
                                       cfg.R_t, cfg.R_s, n=20)
        mirror_traces.append(go.Surface(
            x=X, y=Y, z=Z,
            showscale=False, opacity=0.45,
            colorscale=[[0, "#7faed1"], [1, "#3d6c92"]],
            hoverinfo="skip", name=f"mirror {k}"))

    # ----- ray path -----
    ray_trace = go.Scatter3d(
        x=spots[:, 0], y=spots[:, 1], z=spots[:, 2],
        mode="lines",
        line=dict(color="rgba(255,80,80,0.85)", width=3),
        name=f"ray ({n_b} bounces)", hoverinfo="skip")

    # ----- spot markers, coloured by bounce order -----
    spot_trace = go.Scatter3d(
        x=spots[:, 0], y=spots[:, 1], z=spots[:, 2],
        mode="markers",
        marker=dict(
            size=4,
            color=np.arange(n_b),
            colorscale="Plasma",
            colorbar=dict(title="bounce #", x=1.02, len=0.6),
            showscale=True),
        text=[f"bounce {i}<br>x={p[0]:.1f}<br>y={p[1]:.1f}<br>z={p[2]:.1f}"
              for i, p in enumerate(spots)],
        hoverinfo="text", name="spots")

    # ----- beam radius envelope (cones along the path) -----
    # Use small spheres at each spot scaled by local beam width.
    w_t, w_s = _per_bounce_beam_radius(cfg, n_b)
    w_avg = 0.5 * (w_t + w_s)
    spot_size_trace = go.Scatter3d(
        x=spots[:, 0], y=spots[:, 1], z=spots[:, 2],
        mode="markers",
        marker=dict(size=w_avg * 6, color="rgba(255,200,100,0.18)",
                    line=dict(width=0)),
        hoverinfo="skip", name="beam radius")

    # ----- entry ray (so user sees where it comes in) -----
    if n_b > 0:
        first = spots[0]
        # back-extrapolate using direction from first->second bounce
        if n_b > 1:
            d = spots[1] - first
            d /= np.linalg.norm(d)
            entry = first - 1.5 * cfg.R_ring * d
            entry_trace = go.Scatter3d(
                x=[entry[0], first[0]], y=[entry[1], first[1]],
                z=[entry[2], first[2]],
                mode="lines",
                line=dict(color="#33cc33", width=5, dash="dash"),
                name="input beam")
        else:
            entry_trace = None
    else:
        entry_trace = None

    fig = go.Figure(data=mirror_traces + [ray_trace, spot_trace, spot_size_trace]
                    + ([entry_trace] if entry_trace else []))

    title = (f"<b>{label}</b><br>"
             f"N={cfg.N} skip={cfg.chord_skip} R_ring={cfg.R_ring:.1f} "
             f"H={cfg.H:.1f} R_t={cfg.R_t:.0f} w0={cfg.w0:.2f}<br>"
             f"OPL={res.opl*1e-3:.2f} m | bounces={n_b} | "
             f"throughput={res.throughput*100:.2f}% | clipped={res.clipped}")
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=14)),
        scene=dict(
            xaxis_title="x [mm]", yaxis_title="y [mm]", zaxis_title="z [mm]",
            aspectmode="data",
            bgcolor="#101418"),
        paper_bgcolor="#101418", font=dict(color="#eaeaea"),
        margin=dict(l=0, r=0, t=80, b=0),
        legend=dict(x=0.02, y=0.98, bgcolor="rgba(0,0,0,0.4)"))
    return fig, res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", choices=list(PRESETS.keys()), default=None)
    ap.add_argument("--all", action="store_true",
                    help="render every preset")
    ap.add_argument("--out", default="results/visualisations",
                    help="output directory for HTML files")
    # manual override (overrides preset)
    ap.add_argument("--N", type=int)
    ap.add_argument("--skip", type=int)
    ap.add_argument("--R_ring", type=float)
    ap.add_argument("--H", type=float)
    ap.add_argument("--R_t", type=float)
    ap.add_argument("--R_s", type=float)
    ap.add_argument("--aperture", type=float, default=11.4)
    ap.add_argument("--w0", type=float)
    ap.add_argument("--bounces", type=int, default=128)
    ap.add_argument("--R", type=float, default=0.98)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    if args.all:
        targets = list(PRESETS.items())
    elif args.preset:
        targets = [(args.preset, PRESETS[args.preset])]
    elif args.N is not None:
        targets = [("custom", dict(
            N=args.N, chord_skip=args.skip or 1,
            R_ring=args.R_ring or 50, H=args.H or 30,
            R_t=args.R_t or 100, R_s=args.R_s or (args.R_t or 100),
            mirror_aperture=args.aperture, w0=args.w0 or 0.5,
            n_passes=args.bounces, reflectivity=args.R, label="custom"))]
    else:
        targets = list(PRESETS.items())  # default: render all

    index_links = []
    for name, params in targets:
        label = params.pop("label", name)
        cfg = TMPCConfig(**params)
        fig, res = build_figure(cfg, label)
        out_path = os.path.join(args.out, f"{name}.html")
        fig.write_html(out_path, include_plotlyjs="cdn", full_html=True)
        # per-mirror spot constellations: raytrace + ABCD model
        const_rt = build_mirror_constellations(cfg, res.spot_pattern, "raytrace")
        const_rt_path = os.path.join(args.out, f"{name}_mirrors_raytrace.html")
        const_rt.write_html(const_rt_path, include_plotlyjs="cdn", full_html=True)
        abcd_spots = compute_abcd_spot_pattern(cfg, res.bounces)
        const_abcd = build_mirror_constellations(cfg, abcd_spots, "ABCD / Lissajous")
        const_abcd_path = os.path.join(args.out, f"{name}_mirrors_abcd.html")
        const_abcd.write_html(const_abcd_path, include_plotlyjs="cdn", full_html=True)
        print(f"[viz] {name}: bounces={res.bounces} OPL={res.opl*1e-3:.2f} m "
              f"T={res.throughput*100:.2f}%")
        index_links.append((name, label, out_path,
                            const_rt_path, const_abcd_path, res))

    # index.html with thumbnails / links
    if len(index_links) > 1:
        rows = "\n".join(
            f"<li><b>{n}</b> &mdash; {lab} "
            f"(OPL {r.opl*1e-3:.2f} m, T {r.throughput*100:.2f}%, "
            f"{r.bounces} bounces)<br>"
            f"&nbsp;&nbsp;<a href='{os.path.basename(p3d)}'>3D cell view</a> &middot; "
            f"<a href='{os.path.basename(prt)}'>spots (raytrace)</a> &middot; "
            f"<a href='{os.path.basename(pab)}'>spots (ABCD / Lissajous)</a></li>"
            for (n, lab, p3d, prt, pab, r) in index_links)
        idx_path = os.path.join(args.out, "index.html")
        with open(idx_path, "w") as f:
            f.write(f"<html><body style='font-family:sans-serif;background:#101418;color:#eee'>"
                    f"<h2>TMPC 3D visualisations</h2><ul>{rows}</ul></body></html>")
        print(f"[viz] index -> {idx_path}")


if __name__ == "__main__":
    main()
