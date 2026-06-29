"""One-page text report combining physics, losses and tolerance results."""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from .physics import TMPCConfig, SimResult, simulate_tmpc, propagate_through_cell, GaussianBeam


def physics_report(cfg: TMPCConfig, title: str = "DESIGN") -> str:
    res = simulate_tmpc(cfg)
    chord = float(np.mean(res.chords)) if len(res.chords) else 0.0
    lines = []
    add = lines.append
    add("=" * 72)
    add(f"  {title}")
    add("=" * 72)
    add(f"TOPOLOGY     {cfg.topology}"
        + (f"   M_halflaps={cfg.M_halflaps}" if cfg.topology == "spiral"
           else f"   chord_skip={cfg.chord_skip}"))
    add(f"GEOMETRY     N={cfg.N}   R_ring={cfg.R_ring:.2f} mm   "
        f"H={cfg.H:.2f} mm")
    add(f"MIRROR       R_t={cfg.R_t:.2f} mm   R_s={cfg.R_s:.2f} mm   "
        f"aperture={cfg.mirror_aperture:.2f} mm   R={cfg.reflectivity:.4f}")
    add(f"BEAM         lambda={cfg.wavelength*1e6:.2f} nm   "
        f"w0={cfg.w0:.3f} mm   M2={cfg.M2:.2f}")
    add(f"LAUNCH       offset(t,z)=({cfg.input_offset_t:.2f},{cfg.input_offset_z:.2f}) mm"
        f"   tilt(in,out)=({cfg.input_angle*1e3:.2f},{cfg.input_angle_sag*1e3:.2f}) mrad")
    add("")
    add(f"BOUNCES        {res.bounces:>6d}")
    add(f"OPL            {res.opl*1e-3:>7.3f}  m   "
        f"(chord/bounce = {chord:.2f} mm)")
    add(f"AOI mean       {(res.aoi.mean() if len(res.aoi) else 0):>7.2f}  deg")
    add(f"AOI max        {(res.aoi.max()  if len(res.aoi) else 0):>7.2f}  deg")
    add(f"Beam w_max     {res.w_max:>7.3f}  mm   "
        f"(aperture {cfg.mirror_aperture:.2f} mm)")
    wt0, wt1 = (res.w_tangential.min(), res.w_tangential.max()) if len(res.w_tangential) else (0, 0)
    ws0, ws1 = (res.w_sagittal.min(), res.w_sagittal.max()) if len(res.w_sagittal) else (0, 0)
    add(f"  w_tangential {wt0:>5.3f} - {wt1:<5.3f} mm   "
        f"w_sagittal {ws0:>5.3f} - {ws1:<5.3f} mm  (astigmatic)")
    add(f"Vol. util.     {res.volume_utilisation*100:>7.2f}  %")
    add(f"Stability g^2  {res.stability_g:>7.4f}      "
        f"{'STABLE' if 0 <= res.stability_g <= 1 else 'UNSTABLE'}")
    add(f"  m_tan {res.stability_tan:>+6.3f}   m_sag {res.stability_sag:>+6.3f}   "
        f"{'both planes STABLE' if abs(res.stability_tan) <= 1 and abs(res.stability_sag) <= 1 else 'UNSTABLE plane!'}")
    add(f"Re-entrance    {res.reentrance:>7.3f}")
    add("")
    add("SPOT PATTERN")
    add(f"  max spots / mirror     {res.max_spots_per_mirror:>5d}")
    add(f"  min spot separation    {res.min_spot_separation:>7.3f} mm")
    add(f"  spots overlap          {'YES' if res.spots_overlap else 'no':>7}")
    add(f"  mirror fill fraction   {res.mirror_fill_fraction*100:>6.2f} %")
    add(f"  clipped                {'YES' if res.clipped else 'no':>7}")
    add("")
    add("LOSS BUDGET")
    L = res.loss_budget
    add(f"  reflectivity loss  {L.reflectivity_loss*100:>6.3f} %")
    add(f"  clipping loss      {L.clipping_loss*100:>6.3f} %")
    add(f"  aperture loss      {L.aperture_loss*100:>6.3f} %")
    add(f"  truncation loss    {L.truncation_loss*100:>6.3f} %")
    add(f"  -----------------------------")
    add(f"  total throughput   {L.throughput*100:>6.3f} %")
    add("")
    return "\n".join(lines)


def tolerance_report(summary_df: pd.DataFrame, sens_df: pd.DataFrame,
                     budget_df: pd.DataFrame,
                     metric: str = "throughput",
                     header: str = "TOLERANCE REPORT") -> str:
    lines = []
    add = lines.append
    add("=" * 72)
    add(f"  {header}")
    add("=" * 72)
    n = summary_df.attrs.get("n_trials", len(summary_df))
    thr = summary_df.attrs.get("throughput_threshold", 0.5)
    yld = summary_df.attrs.get("yield_throughput", float("nan"))
    clip = summary_df.attrs.get("clipping_rate", float("nan"))
    add(f"Monte-Carlo trials       : {n}")
    add(f"Yield (throughput >= {thr:.2f}) : {yld*100:.1f}%")
    add(f"Clipping rate            : {clip*100:.1f}%")
    add("")
    add(f"{'metric':<14} {'mean':>10} {'std':>10} {'p05':>10} {'p50':>10} {'p95':>10}")
    add("-" * 66)
    for _, r in summary_df.iterrows():
        add(f"{r['metric']:<14} {r['mean']:>10.4g} {r['std']:>10.4g} "
            f"{r['p05']:>10.4g} {r['p50']:>10.4g} {r['p95']:>10.4g}")
    add("")
    add(f"SENSITIVITY  (one-at-a-time, target metric = {metric})")
    add(f"{'param':<22} {'sigma':>10} {'dY/dsigma':>14} {'|dY|@1sig':>12}")
    add("-" * 60)
    for _, r in sens_df.iterrows():
        add(f"{r['param']:<22} {r['sigma']:>10.3g} "
            f"{r['dY_dsigma']:>14.4g} {r['abs_delta_at_1sigma']:>12.4g}")
    add("")
    add("RSS TOLERANCE BUDGET")
    add(f"  target dY = {budget_df.attrs.get('delta_target', float('nan')):.4g}")
    add(f"  combined  = {budget_df.attrs.get('rss_combined', float('nan')):.4g}")
    add(f"{'param':<22} {'allocated sig':>14} {'contributed dY':>16}")
    add("-" * 56)
    for _, r in budget_df.iterrows():
        add(f"{r['param']:<22} {r['allocated_sigma']:>14.4g} "
            f"{r['allocated_delta']:>16.4g}")
    add("")
    return "\n".join(lines)
