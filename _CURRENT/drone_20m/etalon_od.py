"""Static etalon-limited OD noise floor of the TMPC (Benoy methodology).

Implements the coherent multi-path OD calculation of the 2026-07-18
"COMSOL_Full_Physics_Static_Etalon_OD_Noise_Methodology" for OUR cell
class: windowless open-path TMPC, opaque gold mirrors, one injection/
exit hole, free-space detector behind the hole.  Of the 13 ghost
families in the methodology's Table 1, the ones that physically exist
here are:

  * cross-order multipass (hole-revisit) ghosts: the trace is continued
    for several extra pattern cycles; every later spot that lands on the
    holed mirror couples a Gaussian-overlap fraction of its power out of
    the hole with its own OPL,
  * hole rim clipping of entry/exit beams (eta = D_beam/D_hole ~ 0.25,
    so tail clipping ~ exp(-2 (r_h/w)^2) ~ 1e-14 -- reported, negligible),
  * detector-return ghost: detector reflection re-enters the hole; the
    fraction of the returned Gaussian that hits the gold annulus around
    the hole forms a short 2*L_det etalon (the only short-OPL etalon the
    cell can make),
  * mirror-scatter recoupling floor: per-bounce total integrated scatter
    (4 pi sigma cos(theta) / lambda)^2 with mode-solid-angle recoupling.

Windows, substrates, chamfer/bore specular ghosts are absent by
construction (no windows; opaque gold; hole is a through-hole in a
25.4 mm substrate whose bore is never illuminated by the ~0.33 mm beam
4x inside the 1.3 mm hole radius).

Outputs per design (methodology Table 0): zero-gas OD spectrum, raw
peak-to-peak OD, raw RMS, residual RMS after cubic baseline removal,
fringe FFT with path attribution, ghost-path table.

Usage (from _CURRENT/):
    ../.venv/Scripts/python.exe drone_20m/etalon_od.py --design D150_14cm_flight
    ../.venv/Scripts/python.exe drone_20m/etalon_od.py --all
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

from tmpc_platform_v5 import TMPCConfig, simulate_tmpc                 # noqa
from comsol_gen import SPECS                                           # noqa

C_MM = 2.99792458e11            # mm/s
DNU_L = 2e6                     # laser Lorentzian FWHM [Hz] (DFB typical)
R_DET = 0.02                    # detector residual reflectivity (AR InGaAs)
L_DET = 10.0                    # detector standoff behind hole [mm]
SIGMA_RMS_NM = 2.0              # gold mirror roughness for scatter floor
P_FLOOR = 1e-16                 # ignore families below this power fraction


def _disk_integral(d: float, wx: float, wy: float, r0: float, r1: float,
                   n: int = 241) -> float:
    """Power fraction of an elliptical Gaussian (1/e^2 radii wx, wy,
    centre offset d along x) in the annulus r0 <= r <= r1."""
    r = np.linspace(r0, r1, n)
    th = np.linspace(0.0, 2 * np.pi, n, endpoint=False)
    R, T = np.meshgrid(r, th, indexing="ij")
    X = R * np.cos(T) - d
    Y = R * np.sin(T)
    I = np.exp(-2 * (X ** 2 / wx ** 2 + Y ** 2 / wy ** 2))
    integ = np.trapezoid(np.trapezoid(I * R, th, axis=1), r)
    return float(integ / (np.pi * wx * wy / 2.0))


def gauss_disk_fraction(d: float, wx: float, wy: float, rh: float) -> float:
    """Stable Gaussian power fraction inside a disk of radius rh.

    Near-unity fractions are computed via the complement (power OUTSIDE
    the disk) so that ~1e-14 tails are not swamped by quadrature error.
    """
    w = max(wx, wy)
    if d + 3 * w < rh:                       # beam well inside: complement
        # tail outside the disk: integrate rh .. d+9w (beyond = nothing)
        tail = _disk_integral(d, wx, wy, rh, d + 9 * w + rh)
        return 1.0 - tail
    return _disk_integral(d, wx, wy, 0.0, rh)


def mode_overlap(dd: float, dth: float, w: float, lam: float) -> float:
    """|<E1|E2>| for two equal-waist Gaussians displaced by dd [mm] and
    tilted by dth [rad] (standard displaced/tilted mode overlap)."""
    return float(np.exp(-dd ** 2 / (4 * w ** 2)
                        - (np.pi * w * dth) ** 2 / lam ** 2 / 4.0))


def analyze(design: str, cycles: int = 3, span_cm: float = 1.0,
            fig_dir: str | None = None) -> dict:
    with open(os.path.join(_HERE, "designs", SPECS[design]),
              "r", encoding="utf-8") as fh:
        spec = json.load(fh)
    n_exit = int(spec["metrics"]["n_exit"])
    cfg = TMPCConfig(**spec["cfg"])
    cfg.n_passes = cycles * (n_exit + 1) + 2
    res = simulate_tmpc(cfg)
    spots = np.asarray(res.spot_pattern[: res.bounces])
    mseq = np.asarray(res.mirror_sequence[: res.bounces])
    w_t = np.asarray(res.w_tangential)
    w_s = np.asarray(res.w_sagittal)
    lam = float(cfg.wavelength)              # mm
    R = float(cfg.reflectivity)
    rh = float(cfg.hole_radius)
    hole = spots[0]
    m0 = int(mseq[0])

    # ---- enumerate exit events: spots on the holed mirror --------------
    # power bookkeeping: attenuate by R each bounce; at each mirror-0
    # visit, couple f (Gaussian-over-disk) out of the hole, keep 1-f.
    chords = np.linalg.norm(np.diff(spots, axis=0), axis=1)
    opl_at = np.concatenate([[0.0], np.cumsum(chords)])   # OPL at spot k
    families = []
    P = 1.0
    for k in range(1, len(spots)):
        P *= R
        if int(mseq[k]) != m0:
            continue
        d = float(np.linalg.norm(spots[k] - hole))
        wk_t = float(w_t[k]) if k < len(w_t) else float(w_t[-1])
        wk_s = float(w_s[k]) if k < len(w_s) else float(w_s[-1])
        f = gauss_disk_fraction(d, wk_t, wk_s, rh)
        if f <= 0.0:
            continue
        exit_dir = (spots[k] - spots[k - 1])
        exit_dir = exit_dir / np.linalg.norm(exit_dir)
        fam = dict(bounce=k, d_mm=d, w_mm=0.5 * (wk_t + wk_s),
                   f_hole=f, P=P * f, opl_mm=opl_at[k], dir=exit_dir)
        if P * f > P_FLOOR:
            families.append(fam)
        P *= (1.0 - f)
        if P < P_FLOOR:
            break

    if not families:
        raise SystemExit(f"{design}: no exit families found")
    main = max(families, key=lambda F: F["P"])

    # ---- detector-return ghost ----------------------------------------
    # main beam -> detector (R_DET) -> returns; after 2*L_det of extra
    # propagation the fraction of the returned Gaussian OUTSIDE the hole
    # hits the gold annulus and can come back: a short 2*L_det etalon.
    # Worst case: untilted detector, full mode overlap on return.
    w_exit = main["w_mm"]
    zr_exit = np.pi * w_exit ** 2 / lam
    w_back = w_exit * np.sqrt(1.0 + (2 * L_DET / zr_exit) ** 2)
    f_ann = 1.0 - gauss_disk_fraction(0.0, w_back, w_back, rh)
    P_detret = main["P"] * R_DET * f_ann * R
    if P_detret > P_FLOOR:
        families.append(dict(bounce=-1, d_mm=0.0, w_mm=w_exit,
                             f_hole=f_ann, P=P_detret,
                             opl_mm=main["opl_mm"] + 2 * L_DET,
                             dir=main["dir"]))
    # max detector standoff keeping this etalon below OD 1e-5 / 1e-4
    Ls = np.linspace(2.0, 400.0, 400)
    wb = w_exit * np.sqrt(1.0 + (2 * Ls / zr_exit) ** 2)
    fa = np.array([1.0 - gauss_disk_fraction(0.0, w, w, rh) for w in wb])
    od_det = 2 * np.sqrt(np.clip(R_DET * fa * R, 0, None))
    L_safe5 = float(Ls[od_det < 1e-5].max()) if (od_det < 1e-5).any() else 0.0
    L_safe4 = float(Ls[od_det < 1e-4].max()) if (od_det < 1e-4).any() else 0.0

    # ---- scatter floor (incoherent estimate, reported separately) ------
    aoi = np.asarray(res.aoi)
    cos_aoi = np.cos(np.radians(aoi[: n_exit])) if len(aoi) else 1.0
    tis = (4 * np.pi * (SIGMA_RMS_NM * 1e-6) * np.mean(cos_aoi) / lam) ** 2
    w_mean = float(np.mean(0.5 * (w_t[:n_exit] + w_s[:n_exit])))
    mode_solid = lam ** 2 / (np.pi * w_mean ** 2) / (2 * np.pi)
    P_scatter = n_exit * tis * mode_solid * main["P"]
    od_scatter = 2 * np.sqrt(max(P_scatter, 0.0) / main["P"])

    # ---- coherent zero-gas spectrum -----------------------------------
    sig0 = 1.0 / (lam * 0.1)                 # wavenumber [1/cm]
    dopl_max = max(abs(F["opl_mm"] - main["opl_mm"]) for F in families)
    n_pts = 4096 if dopl_max == 0 else int(min(300000, max(
        4096, 25 * span_cm / (1.0 / (dopl_max * 0.1)))))
    sig = np.linspace(sig0 - span_cm / 2, sig0 + span_cm / 2, n_pts)
    I = np.zeros_like(sig)
    Iref = sum(F["P"] for F in families)
    for j, Fj in enumerate(families):
        I += Fj["P"]
    rows = []
    for j, Fj in enumerate(families):
        for kk, Fk in enumerate(families):
            if kk <= j:
                continue
            dopl = (Fj["opl_mm"] - Fk["opl_mm"]) * 0.1       # cm
            gam = np.exp(-np.pi * DNU_L * abs(dopl * 1e-2) / 2.99792458e8)
            dd = abs(Fj["d_mm"] - Fk["d_mm"])
            dth = float(np.arccos(np.clip(Fj["dir"] @ Fk["dir"], -1, 1)))
            ov = mode_overlap(dd, dth, main["w_mm"], lam)
            amp = 2 * np.sqrt(Fj["P"] * Fk["P"]) * gam * ov
            if amp / Iref < 1e-12:
                continue
            I += amp * np.cos(2 * np.pi * sig * dopl)
            rows.append(dict(j=Fj["bounce"], k=Fk["bounce"],
                             dopl_m=abs(dopl) / 100.0,
                             fsr_cm=1.0 / abs(dopl) if dopl else np.inf,
                             coherence=float(gam), overlap=ov,
                             od_pp=2 * amp / Iref))
    od = -np.log(I / Iref)
    od_pp = float(od.max() - od.min())
    od_rms = float(od.std())
    B = np.polyval(np.polyfit(sig - sig0, od, 3), sig - sig0)
    od_res = float((od - B).std())
    # detection-relevant metrics: a line fit averages OD over a spectral
    # window d_sig (~one absorption linewidth); a fringe of period
    # 1/DeltaOPL is suppressed by |sinc(pi d_sig DeltaOPL)|.  Fringes
    # slower than the window (DeltaOPL < ~20 cm) survive unsuppressed.
    D_SIG = 0.1                              # averaging window [cm^-1]
    od_eff = 0.0
    od_pp_slow = 0.0
    od_eff_tilt = 0.0                        # detector tilted ~2 deg:
    for rr in rows:                          # det-return overlap -> 0
        d_cm = rr["dopl_m"] * 100.0
        x = np.pi * D_SIG * d_cm
        supp = abs(np.sin(x) / x) if x > 0 else 1.0
        od_eff += (rr["od_pp"] * supp) ** 2
        if not (rr["j"] < 0 or rr["k"] < 0):
            od_eff_tilt += (rr["od_pp"] * supp) ** 2
        if d_cm < 20.0:
            od_pp_slow += rr["od_pp"]
    od_eff = float(np.sqrt(od_eff))
    od_eff_tilt = float(np.sqrt(od_eff_tilt))

    # rim-clip sanity numbers (methodology section 4)
    eta = 2 * main["w_mm"] / (2 * rh)
    clip = float(np.exp(-2 * (rh / main["w_mm"]) ** 2))
    # same-cycle hole clearance: nearest non-exit spot on the holed
    # mirror (the design's built-in etalon immunity)
    d_cyc = [float(np.linalg.norm(spots[k] - hole))
             for k in range(1, min(n_exit, len(spots)))
             if int(mseq[k]) == m0]
    d_min_cycle = min(d_cyc) if d_cyc else np.inf

    print(f"{design}: {len(families)} detector-coupled families "
          f"(main bounce {main['bounce']}, P_main {main['P']:.4f})")
    for F in sorted(families, key=lambda F: -F["P"])[:6]:
        tag = "detector-return" if F["bounce"] < 0 else f"bounce {F['bounce']}"
        print(f"   {tag:>16}: P/Pmain {F['P'] / main['P']:.3e}  "
              f"d={F['d_mm']:.3f} mm  f_hole={F['f_hole']:.3e}  "
              f"OPL {F['opl_mm'] / 1e3:.3f} m")
    print(f"   eta=D_beam/D_hole {eta:.3f}; rim tail clip {clip:.2e}; "
          f"nearest same-cycle spot to hole {d_min_cycle:.2f} mm")
    print(f"   detector standoff keeping det-return etalon < 1e-5: "
          f"<= {L_safe5:.0f} mm  (< 1e-4: <= {L_safe4:.0f} mm)")
    print(f"   scatter upper bound (sigma={SIGMA_RMS_NM} nm, fully "
          f"coherent): OD ~ {od_scatter:.2e} (appears as broad pedestal, "
          f"not a discrete fringe)")
    print(f"   OD raw p2p {od_pp:.3e}  raw RMS {od_rms:.3e}  "
          f"residual RMS {od_res:.3e}")
    print(f"   slow fringes (DeltaOPL<20cm, survive line fits): "
          f"p2p {od_pp_slow:.3e}; scan-averaged effective OD {od_eff:.3e}")
    print(f"   with tilted detector (det-return suppressed): "
          f"effective OD {od_eff_tilt:.3e}")

    out = dict(design=design, n_families=len(families),
               P_main=main["P"], eta=eta, rim_clip=clip,
               d_min_cycle_mm=float(d_min_cycle),
               L_det_safe_1e5_mm=L_safe5, L_det_safe_1e4_mm=L_safe4,
               od_pp=od_pp, od_rms=od_rms, od_res=od_res,
               od_pp_slow=od_pp_slow, od_eff_averaged=od_eff,
               od_eff_tilted_det=od_eff_tilt,
               od_scatter=od_scatter,
               strongest_ghost_rel=max(
                   (F["P"] / main["P"] for F in families
                    if F is not main), default=0.0))

    if fig_dir:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4))
            a1.plot(sig - sig0, od * 1e6, lw=0.6)
            a1.set_xlabel(r"$\sigma-\sigma_0$ [cm$^{-1}$]")
            a1.set_ylabel(r"apparent OD [$\times10^{-6}$]")
            a1.set_title(f"{design}: zero-gas OD baseline\n"
                         f"p2p {od_pp:.2e}, residual RMS {od_res:.2e}")
            a1.grid(alpha=0.3)
            fam_srt = sorted(families, key=lambda F: -F["P"])[1:8]
            a2.bar(range(len(fam_srt)),
                   [F["P"] / main["P"] for F in fam_srt],
                   tick_label=["det-ret" if F["bounce"] < 0
                               else f"b{F['bounce']}" for F in fam_srt])
            a2.set_yscale("log")
            a2.set_ylabel("family power / main")
            a2.set_title("ghost families")
            a2.grid(alpha=0.3, axis="y")
            fig.tight_layout()
            p = os.path.join(fig_dir, f"etalon_od_{design}.png")
            fig.savefig(p, dpi=170)
            plt.close(fig)
            print(f"   wrote {p}")
        except Exception as exc:                              # noqa: BLE001
            print("   plot skipped:", exc)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", choices=sorted(SPECS))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--cycles", type=int, default=3)
    args = ap.parse_args()
    designs = sorted(SPECS) if args.all else [args.design]
    if not designs[0]:
        ap.error("--design or --all required")
    fig_dir = os.path.join(_HERE, "designs", "figures")
    rows = []
    for d in designs:
        rows.append(analyze(d, cycles=args.cycles, fig_dir=fig_dir))
    out = os.path.join(_HERE, "designs", "comsol", "etalon_od.csv")
    df = pd.DataFrame(rows)
    if os.path.exists(out):
        old = pd.read_csv(out)
        old = old[~old["design"].isin(df["design"])]
        df = pd.concat([old, df], ignore_index=True)
    df.to_csv(out, index=False)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
