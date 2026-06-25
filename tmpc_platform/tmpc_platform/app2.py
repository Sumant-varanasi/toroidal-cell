"""Interactive TMPC explorer.

Run with:
    streamlit run app.py

Sliders on the left, live spot pattern + beam evolution + metrics on the right.
"""
import os, sys
# add parent of tmpc_platform/ package to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from tmpc_platform.physics_engine import TMPCConfig, simulate_tmpc
from tmpc_platform.physics_engine.gaussian_beam import GaussianBeam, propagate_through_cell
from tmpc_platform.physics_engine.losses import compute_losses


st.set_page_config(page_title="TMPC Explorer", layout="wide")
st.title("Toroidal Multipass Cell Explorer")
st.caption("Adjust parameters on the left — geometry, beam, metrics update live.")

# ---------------- sidebar controls ----------------
with st.sidebar:
    st.header("Geometry")
    N = st.slider("N (mirrors)", 6, 20, 12)
    chord_skip = st.slider("chord skip", 1, N - 1, min(5, N - 1))
    R_ring = st.slider("Ring radius R_ring [mm]", 20.0, 100.0, 60.0, step=1.0)
    H = st.slider("Cell height H [mm]", 10.0, 80.0, 40.0, step=1.0)

    st.header("Mirror")
    R_t = st.slider("Tangential ROC R_t [mm]", 30.0, 300.0, 120.0, step=5.0)
    R_s = st.slider("Sagittal ROC R_s [mm]", 30.0, 300.0, 120.0, step=5.0)
    aperture = st.slider("Mirror aperture [mm]", 3.0, 15.0, 8.0, step=0.5)
    reflectivity = st.slider("Reflectivity per bounce", 0.990, 0.9999, 0.999,
                             step=0.0001, format="%.4f")

    st.header("Beam")
    w0 = st.slider("Input waist w0 [mm]", 0.1, 2.0, 0.5, step=0.05)
    wavelength_nm = st.slider("Wavelength [nm]", 800.0, 2500.0, 1654.0, step=1.0)
    input_offset_z = st.slider("Input z offset [mm]", -5.0, 5.0, 0.0, step=0.1)
    input_angle_mrad = st.slider("Input tilt [mrad]", -50.0, 50.0, 0.0, step=0.5)

    st.header("Passes")
    n_passes = st.slider("n_passes", 8, 256, 8 * N, step=2)

# ---------------- build config and simulate ----------------
cfg = TMPCConfig(
    N=N, R_ring=R_ring, H=H,
    R_t=R_t, R_s=R_s,
    mirror_aperture=aperture,
    chord_skip=chord_skip,
    n_passes=n_passes,
    wavelength=wavelength_nm * 1e-6,  # nm -> mm
    w0=w0,
    input_offset_z=input_offset_z,
    input_angle=input_angle_mrad * 1e-3,
    reflectivity=reflectivity,
)

@st.cache_data(show_spinner=False)
def _simulate(cfg_tuple):
    keys, vals = zip(*cfg_tuple)
    cfg_dict = dict(zip(keys, vals))
    cfg = TMPCConfig(**cfg_dict)
    res = simulate_tmpc(cfg)
    loss = compute_losses(res.bounces, cfg.reflectivity, res.w_max,
                          cfg.mirror_aperture, 2 * cfg.w0, clipped=res.clipped)
    chord = 2 * cfg.R_ring * np.sin(np.pi * cfg.chord_skip / cfg.N)
    beam = GaussianBeam(wavelength=cfg.wavelength, w0=cfg.w0)
    prop = propagate_through_cell(beam, [chord] * cfg.n_passes,
                                  [cfg.R_t / 2] * cfg.n_passes,
                                  [cfg.R_s / 2] * cfg.n_passes)
    return cfg, res, loss, prop, chord

cfg_tuple = tuple(sorted(cfg.__dict__.items()))
cfg, res, loss, prop, chord = _simulate(cfg_tuple)

# ---------------- top metrics ----------------
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Bounces", res.bounces)
c2.metric("OPL", f"{res.opl * 1e-3:.2f} m")
c3.metric("Throughput", f"{loss.throughput * 100:.1f}%")
c4.metric("Vol. utilisation", f"{res.volume_utilisation * 100:.1f}%")
c5.metric("Max beam w", f"{res.w_max:.2f} mm",
          delta=f"aperture {cfg.mirror_aperture:.1f}",
          delta_color="inverse")

c6, c7, c8, c9, c10 = st.columns(5)
c6.metric("Stability g²", f"{res.stability_g:.3f}",
          delta="stable" if 0 <= res.stability_g <= 1 else "UNSTABLE",
          delta_color="normal" if 0 <= res.stability_g <= 1 else "inverse")
c7.metric("AOI mean", f"{res.aoi.mean():.2f}°" if len(res.aoi) else "—")
c8.metric("AOI max", f"{res.aoi.max():.2f}°" if len(res.aoi) else "—")
c9.metric("Chord length", f"{chord:.1f} mm")
c10.metric("Clipped", "yes" if res.clipped else "no",
           delta=None,
           delta_color="inverse" if res.clipped else "normal")

# ---------------- 3D spot pattern ----------------
left, right = st.columns([3, 2])

with left:
    st.subheader("3D bounce trajectory")
    show_animation = st.checkbox("Animate bounce-by-bounce (play / step slider)", value=False)
    if len(res.spot_pattern) > 0:
        sp = res.spot_pattern
        th = np.linspace(0, 2 * np.pi, cfg.N, endpoint=False)
        mirror_x = cfg.R_ring * np.cos(th)
        mirror_y = cfg.R_ring * np.sin(th)
        mirror_z = np.zeros_like(th)

        if not show_animation:
            # ---- static full trajectory ----
            fig = go.Figure()
            fig.add_trace(go.Scatter3d(
                x=mirror_x, y=mirror_y, z=mirror_z, mode="markers",
                marker=dict(size=6, color="red"), name="mirrors"))
            fig.add_trace(go.Scatter3d(
                x=sp[:, 0], y=sp[:, 1], z=sp[:, 2],
                mode="lines+markers",
                line=dict(color="royalblue", width=2),
                marker=dict(size=3, color=np.arange(len(sp)),
                            colorscale="Viridis", showscale=True,
                            colorbar=dict(title="bounce #")),
                name="trajectory"))
            # cell outline
            zc = np.array([-cfg.H / 2, cfg.H / 2])
            for ang in np.linspace(0, 2 * np.pi, 24, endpoint=False):
                fig.add_trace(go.Scatter3d(
                    x=[cfg.R_ring * np.cos(ang)] * 2,
                    y=[cfg.R_ring * np.sin(ang)] * 2,
                    z=zc, mode="lines",
                    line=dict(color="lightgray", width=1),
                    showlegend=False, hoverinfo="skip"))
            fig.update_layout(
                scene=dict(aspectmode="data",
                           xaxis_title="x [mm]", yaxis_title="y [mm]",
                           zaxis_title="z [mm]"),
                height=520, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            # ---- animated build-up ----
            step = st.slider("Show up to bounce #", 1, len(sp), len(sp), key="bounce_step")
            sp_partial = sp[:step]

            # build all frames for the Play/Pause buttons
            frames = []
            for k in range(1, len(sp) + 1):
                spk = sp[:k]
                frames.append(go.Frame(
                    data=[
                        go.Scatter3d(x=mirror_x, y=mirror_y, z=mirror_z,
                                     mode="markers",
                                     marker=dict(size=6, color="red"), name="mirrors"),
                        go.Scatter3d(x=spk[:, 0], y=spk[:, 1], z=spk[:, 2],
                                     mode="lines+markers",
                                     line=dict(color="royalblue", width=3),
                                     marker=dict(size=4,
                                                 color=np.arange(len(spk)),
                                                 colorscale="Viridis",
                                                 cmin=0, cmax=len(sp)),
                                     name="trajectory"),
                        go.Scatter3d(x=[spk[-1, 0]], y=[spk[-1, 1]], z=[spk[-1, 2]],
                                     mode="markers",
                                     marker=dict(size=10, color="orange",
                                                 symbol="diamond"),
                                     name=f"bounce {k}"),
                    ],
                    name=str(k)))

            fig = go.Figure(
                data=frames[step - 1].data,
                frames=frames,
            )
            # cell outline as static decoration
            zc = np.array([-cfg.H / 2, cfg.H / 2])
            for ang in np.linspace(0, 2 * np.pi, 24, endpoint=False):
                fig.add_trace(go.Scatter3d(
                    x=[cfg.R_ring * np.cos(ang)] * 2,
                    y=[cfg.R_ring * np.sin(ang)] * 2,
                    z=zc, mode="lines",
                    line=dict(color="lightgray", width=1),
                    showlegend=False, hoverinfo="skip"))

            fig.update_layout(
                scene=dict(aspectmode="data",
                           xaxis_title="x [mm]", yaxis_title="y [mm]",
                           zaxis_title="z [mm]"),
                height=520, margin=dict(l=0, r=0, t=10, b=0),
                updatemenus=[dict(
                    type="buttons",
                    showactive=False,
                    y=1.05, x=0.05, xanchor="left", yanchor="top",
                    buttons=[
                        dict(label="▶ Play", method="animate",
                             args=[None, dict(frame=dict(duration=150, redraw=True),
                                              fromcurrent=True,
                                              transition=dict(duration=0))]),
                        dict(label="⏸ Pause", method="animate",
                             args=[[None], dict(frame=dict(duration=0, redraw=False),
                                                mode="immediate",
                                                transition=dict(duration=0))]),
                    ])],
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"Orange diamond = current bounce. "
                       f"At bounce {step}: position ({sp_partial[-1,0]:.1f}, "
                       f"{sp_partial[-1,1]:.1f}, {sp_partial[-1,2]:.2f}) mm. "
                       f"Total path so far = "
                       f"{np.sum(np.linalg.norm(np.diff(sp_partial, axis=0), axis=1)):.1f} mm.")
    else:
        st.warning("No bounces — ray missed the first mirror or geometry is invalid.")

with right:
    st.subheader("Per-bounce AOI")
    if len(res.aoi) > 0:
        fig_aoi = go.Figure(go.Scatter(
            x=np.arange(1, len(res.aoi) + 1), y=res.aoi,
            mode="lines+markers", line=dict(color="darkorange")))
        fig_aoi.update_layout(
            xaxis_title="bounce #", yaxis_title="AOI [deg]",
            height=240, margin=dict(l=10, r=10, t=10, b=30))
        st.plotly_chart(fig_aoi, use_container_width=True)

    st.subheader("Gaussian beam evolution")
    fig_beam = go.Figure()
    fig_beam.add_trace(go.Scatter(y=prop["w_tangential"],
                                  mode="lines", name="tangential",
                                  line=dict(color="steelblue", width=2)))
    fig_beam.add_trace(go.Scatter(y=prop["w_sagittal"],
                                  mode="lines", name="sagittal",
                                  line=dict(color="darkorange", width=2)))
    fig_beam.add_hline(y=cfg.mirror_aperture, line=dict(color="red", dash="dash"),
                       annotation_text="aperture", annotation_position="top right")
    fig_beam.update_layout(
        xaxis_title="bounce #", yaxis_title="beam radius w [mm]",
        height=240, margin=dict(l=10, r=10, t=10, b=30))
    st.plotly_chart(fig_beam, use_container_width=True)

# ---------------- loss breakdown ----------------
st.subheader("Loss breakdown")
losses = {
    "Reflectivity": loss.reflectivity_loss * 100,
    "Clipping":     loss.clipping_loss     * 100,
    "Aperture":     loss.aperture_loss     * 100,
    "Truncation":   loss.truncation_loss   * 100,
}
fig_loss = go.Figure(go.Bar(
    x=list(losses.keys()), y=list(losses.values()),
    marker_color=["steelblue", "crimson", "orange", "purple"],
    text=[f"{v:.2f}%" for v in losses.values()], textposition="auto"))
fig_loss.update_layout(yaxis_title="loss [%]", height=300,
                       margin=dict(l=10, r=10, t=10, b=30))
st.plotly_chart(fig_loss, use_container_width=True)

# ---------------- design summary table ----------------
with st.expander("Full design summary"):
    summary = pd.DataFrame({
        "parameter": ["N", "chord_skip", "R_ring [mm]", "H [mm]",
                      "R_t [mm]", "R_s [mm]", "aperture [mm]",
                      "w0 [mm]", "wavelength [nm]",
                      "input z offset [mm]", "input tilt [mrad]",
                      "reflectivity",
                      "----",
                      "bounces", "OPL [m]", "throughput",
                      "vol. util.", "stability g²",
                      "AOI mean [deg]", "AOI max [deg]",
                      "max beam w [mm]", "clipped"],
        "value": [N, chord_skip, R_ring, H, R_t, R_s, aperture,
                  w0, wavelength_nm, input_offset_z, input_angle_mrad,
                  reflectivity, "",
                  res.bounces, f"{res.opl*1e-3:.3f}", f"{loss.throughput:.4f}",
                  f"{res.volume_utilisation:.3f}", f"{res.stability_g:.4f}",
                  f"{res.aoi.mean():.2f}" if len(res.aoi) else "—",
                  f"{res.aoi.max():.2f}" if len(res.aoi) else "—",
                  f"{res.w_max:.3f}",
                  "yes" if res.clipped else "no"],
    })
    st.dataframe(summary, use_container_width=True, height=600)

# ---------------- load existing dataset / Pareto if available ----------------
with st.expander("Compare to dataset / Pareto front"):
    ds_path = st.text_input("dataset.csv path", "results/dataset.csv")
    if os.path.exists(ds_path):
        df = pd.read_csv(ds_path)
        st.caption(f"Loaded {len(df)} configurations")
        fig_ds = go.Figure(go.Scatter(
            x=df["opl_m"], y=df["throughput_full"],
            mode="markers",
            marker=dict(size=5, color=df["quality"], colorscale="Viridis",
                        showscale=True, colorbar=dict(title="quality")),
            text=[f"N={int(n)}, skip={int(k)}, R_t={r:.0f}"
                  for n, k, r in zip(df["N"], df["chord_skip"], df["R_t"])],
            name="dataset"))
        fig_ds.add_trace(go.Scatter(
            x=[res.opl * 1e-3], y=[loss.throughput],
            mode="markers", marker=dict(size=18, color="red", symbol="star"),
            name="current config"))
        fig_ds.update_layout(xaxis_title="OPL [m]", yaxis_title="throughput",
                             height=480, margin=dict(l=10, r=10, t=10, b=30))
        st.plotly_chart(fig_ds, use_container_width=True)
    else:
        st.info("Run `python -m tmpc_platform.scripts.run_all` first to generate a dataset.")