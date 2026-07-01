"""Tolerance estimation for toroidal multipass cells.

Three complementary analyses, all driven by the same `ToleranceSpec`:

1. Monte-Carlo (`monte_carlo`)
       Draw N random realisations of every perturbation, simulate each,
       return a DataFrame of throughput / OPL / bounces / w_max / clipping.
       Use `summarise_mc` to get percentiles and yield (P[throughput ≥ τ]).

2. One-at-a-time sensitivity (`sensitivity`)
       Finite-difference dY/dσ at the nominal point. Cheap (≤ 2 sims per
       tolerance) and gives the "blame table" for which tolerance dominates.

3. Tolerance budget allocator (`tolerance_budget`)
       Given an acceptable throughput drop ΔT_max and a sensitivity table,
       allocate per-tolerance 1-σ values so the RSS combination stays under
       budget. Honors `weights` so you can make the cheap ones (R_ring) loose
       and the expensive ones (per-mirror tilt) tight.

Perturbation taxonomy
---------------------
Per-mirror (N copies, independent):
    sigma_d_lateral [mm]   tangential & sagittal decenter (same σ)
    sigma_d_axial   [mm]   axial position error
    sigma_tilt      [mrad] tip/tilt about both axes (same σ)
    sigma_dR        [mm]   ROC error (tangential and sagittal share σ unless
                           you split them via `sigma_dR_s`)
    sigma_dR_s      [mm]   if not None, overrides sagittal ROC σ
    aperture_drop   [mm]   reduction in usable clear-aperture radius
Global (one draw per trial):
    sigma_R_ring    [mm]
    sigma_H         [mm]
    sigma_input_pos [mm]   launch position (Δx, Δy, Δz)
    sigma_input_tilt[mrad] launch direction (Δθx, Δθy)
    sigma_refl      [-]    per-mirror reflectivity drift
    sigma_lambda    [mm]   wavelength drift (e.g. 1e-7 mm = 0.1 ppm)

Environmental presets are computed from physical drivers:
    `thermal_perturbation(spec, dT, CTE_mirror, CTE_mount)` returns a
    GlobalPerturbation with dR_ring, dH and dR_t, dR_s already inflated by
    the expected thermal expansion.
    `vibration_spec(rms_tilt_mrad)` returns a ToleranceSpec with only the
    per-mirror tilt populated, suitable for drone-vibration noise studies.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from .physics import (
    TMPCConfig, SimResult, MirrorPerturbation, GlobalPerturbation,
    simulate_tmpc,
)


# =============================================================================
# 1. Tolerance specification
# =============================================================================
@dataclass
class ToleranceSpec:
    # ---- per-mirror (sigma values; all distributions are Gaussian unless noted) ----
    sigma_d_lateral: float = 0.0      # [mm]
    sigma_d_axial: float = 0.0        # [mm]
    sigma_tilt: float = 0.0           # [mrad]
    sigma_dR: float = 0.0             # [mm], tangential ROC error
    sigma_dR_s: Optional[float] = None  # [mm], overrides sagittal if not None
    aperture_drop: float = 0.0        # [mm], deterministic clear-aperture reduction

    # ---- global ----
    sigma_R_ring: float = 0.0         # [mm]
    sigma_H: float = 0.0              # [mm]
    sigma_input_pos: float = 0.0      # [mm]   per axis (x,y,z)
    sigma_input_tilt: float = 0.0     # [mrad] per axis
    sigma_refl: float = 0.0           # [-]    fractional drift
    sigma_lambda: float = 0.0         # [mm]   wavelength drift

    # ---- distribution control ----
    truncate_sigmas: float = 3.0      # clip at ±N·σ

    # ---- presets ----
    @classmethod
    def loose(cls) -> "ToleranceSpec":
        """Hobby / breadboard tolerances. Things that an Optomech 101 student
        can hit on a workbench with off-the-shelf mounts."""
        return cls(
            sigma_d_lateral=0.20, sigma_d_axial=0.30, sigma_tilt=2.0,
            sigma_dR=2.0,
            sigma_R_ring=0.5, sigma_H=0.5,
            sigma_input_pos=0.20, sigma_input_tilt=2.0,
            sigma_refl=0.002, sigma_lambda=2e-6,
        )

    @classmethod
    def research_grade(cls) -> "ToleranceSpec":
        """Typical numbers for a TRL-5 lab build with kinematic mounts and
        commercial mirrors. Roughly Thorlabs catalog spec."""
        return cls(
            sigma_d_lateral=0.050, sigma_d_axial=0.10, sigma_tilt=0.5,
            sigma_dR=1.0,
            sigma_R_ring=0.10, sigma_H=0.10,
            sigma_input_pos=0.050, sigma_input_tilt=0.5,
            sigma_refl=0.001, sigma_lambda=1e-7,
        )

    @classmethod
    def flight_grade(cls) -> "ToleranceSpec":
        """Tight tolerances appropriate for a drone-mounted, glued/welded
        cell intended to survive vibration. Per-mirror tilt is what hurts
        most in a vibrating airframe."""
        return cls(
            sigma_d_lateral=0.020, sigma_d_axial=0.030, sigma_tilt=0.10,
            sigma_dR=0.5,
            sigma_R_ring=0.030, sigma_H=0.030,
            sigma_input_pos=0.020, sigma_input_tilt=0.10,
            sigma_refl=0.0005, sigma_lambda=1e-7,
        )

    def names(self) -> List[str]:
        """Tolerance parameter names with non-zero σ (used by sensitivity)."""
        return [k for k, v in asdict(self).items()
                if isinstance(v, (int, float)) and v and k.startswith("sigma_")]


# =============================================================================
# 2. Drawing perturbations
# =============================================================================
def _truncnorm(rng: np.random.Generator, sigma: float, n: int,
               clip: float) -> np.ndarray:
    """Truncated normal: |x| ≤ clip·σ."""
    if sigma <= 0:
        return np.zeros(n)
    out = rng.normal(0.0, sigma, n)
    lim = clip * sigma
    np.clip(out, -lim, lim, out=out)
    return out


def sample_perturbations(spec: ToleranceSpec, N_mirrors: int,
                         rng: Optional[np.random.Generator] = None
                         ) -> Tuple[List[MirrorPerturbation], GlobalPerturbation]:
    """Draw one (perturbations, global) realisation from `spec`."""
    rng = rng if rng is not None else np.random.default_rng()
    clip = spec.truncate_sigmas

    d_tan = _truncnorm(rng, spec.sigma_d_lateral, N_mirrors, clip)
    d_sag = _truncnorm(rng, spec.sigma_d_lateral, N_mirrors, clip)
    d_ax  = _truncnorm(rng, spec.sigma_d_axial,   N_mirrors, clip)
    sig_t_rad = spec.sigma_tilt * 1e-3       # mrad -> rad
    tilt_t = _truncnorm(rng, sig_t_rad, N_mirrors, clip)
    tilt_s = _truncnorm(rng, sig_t_rad, N_mirrors, clip)
    dR_t = _truncnorm(rng, spec.sigma_dR, N_mirrors, clip)
    dR_s_sig = spec.sigma_dR_s if spec.sigma_dR_s is not None else spec.sigma_dR
    dR_s = _truncnorm(rng, dR_s_sig, N_mirrors, clip)
    ap_scale_drop = spec.aperture_drop  # deterministic

    mirror_perts = [
        MirrorPerturbation(
            d_tan=float(d_tan[k]), d_sag=float(d_sag[k]), d_ax=float(d_ax[k]),
            tilt_tan=float(tilt_t[k]), tilt_sag=float(tilt_s[k]),
            dR_t=float(dR_t[k]), dR_s=float(dR_s[k]),
            aperture_scale=1.0 if ap_scale_drop <= 0
                           else max(1e-3, 1.0 - ap_scale_drop),
        )
        for k in range(N_mirrors)
    ]

    g_pert = GlobalPerturbation(
        dR_ring=float(_truncnorm(rng, spec.sigma_R_ring, 1, clip)[0]),
        dH=float(_truncnorm(rng, spec.sigma_H, 1, clip)[0]),
        d_input_x=float(_truncnorm(rng, spec.sigma_input_pos, 1, clip)[0]),
        d_input_y=float(_truncnorm(rng, spec.sigma_input_pos, 1, clip)[0]),
        d_input_z=float(_truncnorm(rng, spec.sigma_input_pos, 1, clip)[0]),
        d_input_tilt_x=float(_truncnorm(rng, spec.sigma_input_tilt * 1e-3, 1, clip)[0]),
        d_input_tilt_y=float(_truncnorm(rng, spec.sigma_input_tilt * 1e-3, 1, clip)[0]),
        d_reflectivity=float(_truncnorm(rng, spec.sigma_refl, 1, clip)[0]),
        d_wavelength=float(_truncnorm(rng, spec.sigma_lambda, 1, clip)[0]),
    )
    return mirror_perts, g_pert


# =============================================================================
# 3. Environmental presets
# =============================================================================
def thermal_perturbation(cfg: TMPCConfig, dT: float,
                         CTE_struct: float = 23e-6,   # aluminium ring
                         CTE_mirror: float = 8.5e-6,  # Zerodur substrate
                         ) -> GlobalPerturbation:
    """Convert a temperature excursion ΔT [K] into a deterministic
    GlobalPerturbation. Use this as a single MC trial or as a worst-case
    additive on top of a random perturbation.

    Default CTEs:  aluminium mounting (23 ppm/K), Zerodur mirror (8.5 ppm/K).
    The ROC of a curved mirror scales with substrate CTE.
    """
    return GlobalPerturbation(
        dR_ring=cfg.R_ring * CTE_struct * dT,
        dH=cfg.H * CTE_struct * dT,
        # ROC scaling handled by passing per-mirror ΔR via a separate call
        # to simulate_tmpc with a MirrorPerturbation list; we just expose dR
        # here as part of the global preset for convenience:
    )


def thermal_mirror_perturbations(cfg: TMPCConfig, dT: float,
                                 CTE_mirror: float = 8.5e-6
                                 ) -> List[MirrorPerturbation]:
    """Per-mirror ΔR_t / ΔR_s for a uniform temperature excursion."""
    dR = cfg.R_t * CTE_mirror * dT
    dR_s = cfg.R_s * CTE_mirror * dT
    return [MirrorPerturbation(dR_t=dR, dR_s=dR_s) for _ in range(cfg.N)]


def vibration_spec(rms_tilt_mrad: float,
                   rms_decenter_um: float = 0.0) -> ToleranceSpec:
    """ToleranceSpec for vibration-induced random per-mirror tilt/decenter
    only. Drone studies typically use rms_tilt_mrad in [0.1, 5]."""
    return ToleranceSpec(
        sigma_tilt=float(rms_tilt_mrad),
        sigma_d_lateral=float(rms_decenter_um) * 1e-3,
    )


# =============================================================================
# 4. Monte-Carlo
# =============================================================================
def _exit_dir(res) -> Optional[np.ndarray]:
    if res.exit_ray is None:
        return None
    d = np.asarray(res.exit_ray.direction, dtype=float)
    n = np.linalg.norm(d)
    return d / n if n > 1e-12 else None


def _drift_mrad(d_pert: Optional[np.ndarray],
                d_nom: Optional[np.ndarray]) -> float:
    if d_pert is None or d_nom is None:
        return 0.0
    cosang = float(np.clip(d_pert @ d_nom, -1, 1))
    return float(np.arccos(cosang) * 1e3)


def _trial(args):
    cfg, spec, seed, nom_exit, nom_centroid = args
    rng = np.random.default_rng(seed)
    mp, gp = sample_perturbations(spec, cfg.N, rng)
    try:
        res = simulate_tmpc(cfg, perturbations=mp, global_pert=gp)
    except Exception:
        return None
    # spot-centroid walk vs nominal (mean |Δ| of hit positions, mm)
    centroid_walk = 0.0
    if nom_centroid is not None and len(res.spot_pattern):
        m = min(len(res.spot_pattern), len(nom_centroid))
        if m:
            centroid_walk = float(np.mean(
                np.linalg.norm(res.spot_pattern[:m] - nom_centroid[:m], axis=1)))
    return {
        "seed": int(seed),
        "bounces": res.bounces,
        "opl_m": res.opl * 1e-3,
        "throughput": res.throughput,
        "w_max_mm": res.w_max,
        "clipped": int(res.clipped),
        "stability_g": res.stability_g,
        "aoi_mean": float(np.mean(res.aoi)) if len(res.aoi) else 0.0,
        "aoi_max":  float(np.max(res.aoi))  if len(res.aoi) else 0.0,
        "exit_drift_mrad": _drift_mrad(_exit_dir(res), nom_exit),
        "spot_walk_mm": centroid_walk,
        "refl_loss":  res.loss_budget.reflectivity_loss,
        "clip_loss":  res.loss_budget.clipping_loss,
        "ap_loss":    res.loss_budget.aperture_loss,
        "trunc_loss": res.loss_budget.truncation_loss,
        "dR_ring": gp.dR_ring, "dH": gp.dH,
        "d_input_tilt_x": gp.d_input_tilt_x,
        "d_input_tilt_y": gp.d_input_tilt_y,
        "d_wavelength": gp.d_wavelength,
        "d_reflectivity": gp.d_reflectivity,
    }


def monte_carlo(cfg: TMPCConfig, spec: ToleranceSpec,
                n_trials: int = 200, seed: int = 0,
                n_workers: Optional[int] = 1) -> pd.DataFrame:
    """Run N Monte-Carlo trials with random perturbations.

    Adds two differential metrics (vs the unperturbed run): `exit_drift_mrad`
    (exit-ray pointing error) and `spot_walk_mm` (mean bounce-position walk).
    These are continuous, so they tolerance well even where throughput is a
    near-step function dominated by clipping.

    n_workers=1 (default) is safest on Windows; pass >1 to fan out via
    ProcessPoolExecutor.
    """
    nominal = simulate_tmpc(cfg)
    nom_exit = _exit_dir(nominal)
    nom_centroid = nominal.spot_pattern.copy() if len(nominal.spot_pattern) else None

    seeds = np.arange(n_trials, dtype=int) + int(seed) * n_trials + 1
    rows: List[dict] = []
    if n_workers is None or n_workers <= 1:
        for s in seeds:
            r = _trial((cfg, spec, int(s), nom_exit, nom_centroid))
            if r is not None:
                rows.append(r)
    else:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(max_workers=n_workers) as ex:
            futs = [ex.submit(_trial, (cfg, spec, int(s), nom_exit, nom_centroid))
                    for s in seeds]
            for f in as_completed(futs):
                r = f.result()
                if r is not None:
                    rows.append(r)
    df = pd.DataFrame(rows).sort_values("seed").reset_index(drop=True)
    return df


def summarise_mc(df: pd.DataFrame,
                 throughput_threshold: float = 0.5) -> pd.DataFrame:
    """Per-metric percentile + yield table from a MC DataFrame."""
    metrics = ["bounces", "opl_m", "throughput", "w_max_mm",
               "stability_g", "aoi_mean", "aoi_max",
               "exit_drift_mrad", "spot_walk_mm"]
    rows = []
    for m in metrics:
        if m not in df.columns:
            continue
        s = df[m].astype(float)
        rows.append({
            "metric": m,
            "mean": float(s.mean()),
            "std": float(s.std()),
            "p05": float(s.quantile(0.05)),
            "p50": float(s.quantile(0.50)),
            "p95": float(s.quantile(0.95)),
            "min": float(s.min()),
            "max": float(s.max()),
        })
    out = pd.DataFrame(rows)
    # yield row
    if "throughput" in df.columns:
        yield_frac = float((df["throughput"] >= throughput_threshold).mean())
        clip_rate = float(df.get("clipped", pd.Series(dtype=int)).mean())
        out.attrs["yield_throughput"] = yield_frac
        out.attrs["throughput_threshold"] = throughput_threshold
        out.attrs["clipping_rate"] = clip_rate
        out.attrs["n_trials"] = int(len(df))
    return out


# =============================================================================
# 5. One-at-a-time sensitivity (mini-MC per tolerance)
# =============================================================================
def _isolated_spec(base: ToleranceSpec, name: str) -> ToleranceSpec:
    """Return a ToleranceSpec with only `name` non-zero (keeps base's value)."""
    d = asdict(base)
    iso = {k: (0.0 if (isinstance(v, (int, float)) and k.startswith("sigma_"))
               else v)
           for k, v in d.items()}
    iso["sigma_dR_s"] = None  # follow sigma_dR
    iso[name] = d[name]
    iso["truncate_sigmas"] = d.get("truncate_sigmas", 3.0)
    return ToleranceSpec(**iso)


def sensitivity(cfg: TMPCConfig, spec: ToleranceSpec,
                metric: str = "throughput",
                n_trials_per_param: int = 40,
                probe_factor: float = 3.0,
                seed: int = 0) -> pd.DataFrame:
    """Mini-Monte-Carlo isolation: for each tolerance with σ>0, run
    `n_trials_per_param` simulations with ONLY that tolerance active at
    `probe_factor × σ`, then rescale the response back to per-σ units.

    Why probe at >1σ:  for a system where a single tolerance at its native
    σ never trips clipping (a step nonlinearity), the at-σ std is exactly
    zero while the at-3σ std is finite and a much more honest linearised
    slope. `dY_dsigma` is then `std(Y@probe) / probe_σ`, equivalent to a
    finite-difference derivative made robust by averaging over independent
    random draws.

    Returned columns:
        param, sigma, probe_sigma, Y_nominal, Y_mean, Y_std, mean_shift,
        dY_dsigma, abs_delta_at_1sigma
    """
    nominal = simulate_tmpc(cfg)
    nom_exit = _exit_dir(nominal)
    nom_centroid = nominal.spot_pattern.copy() if len(nominal.spot_pattern) else None
    Y0 = _get_metric(nominal, metric, nom_exit, nom_centroid)
    rows = []
    for i, name in enumerate(spec.names()):
        sigma = float(asdict(spec)[name])
        if sigma <= 0:
            continue
        probe_sigma = sigma * probe_factor
        iso = _isolated_spec(spec, name)
        # boost the isolated spec's value by probe_factor
        setattr(iso, name, probe_sigma)
        rng = np.random.default_rng(seed * 1_000_003 + i * 9973 + 1)
        ys: List[float] = []
        for _ in range(n_trials_per_param):
            mp, gp = sample_perturbations(iso, cfg.N, rng)
            try:
                r = simulate_tmpc(cfg, perturbations=mp, global_pert=gp)
                ys.append(_get_metric(r, metric, nom_exit, nom_centroid))
            except Exception:
                pass
        ys_arr = np.array(ys) if ys else np.array([Y0])
        # RMS deviation from nominal: equals std for symmetric metrics
        # (throughput, opl) and the full magnitude for one-sided drift metrics
        # (exit_drift_mrad, spot_walk_mm) whose nominal value is ~0.
        rms_dev = float(np.sqrt(np.mean((ys_arr - Y0) ** 2)))
        slope = rms_dev / probe_sigma if probe_sigma > 0 else 0.0
        rows.append({
            "param": name,
            "sigma": sigma,
            "probe_sigma": probe_sigma,
            "Y_nominal": Y0,
            "Y_mean": float(ys_arr.mean()),
            "Y_std": float(ys_arr.std(ddof=1)) if len(ys_arr) > 1 else 0.0,
            "mean_shift": float(ys_arr.mean() - Y0),
            "dY_dsigma": slope,
            "abs_delta_at_1sigma": slope * sigma,
        })
    out = pd.DataFrame(rows).sort_values("abs_delta_at_1sigma", ascending=False)
    out.attrs["metric"] = metric
    out.attrs["n_trials_per_param"] = int(n_trials_per_param)
    out.attrs["probe_factor"] = float(probe_factor)
    return out


def _get_metric(res: SimResult, metric: str,
                nom_exit: Optional[np.ndarray] = None,
                nom_centroid: Optional[np.ndarray] = None) -> float:
    if metric == "throughput":   return res.throughput
    if metric == "opl_m":        return res.opl * 1e-3
    if metric == "bounces":      return float(res.bounces)
    if metric == "w_max_mm":     return res.w_max
    if metric == "stability_g":  return res.stability_g
    if metric == "aoi_mean":     return float(np.mean(res.aoi)) if len(res.aoi) else 0.0
    if metric == "exit_drift_mrad":
        return _drift_mrad(_exit_dir(res), nom_exit)
    if metric == "spot_walk_mm":
        if nom_centroid is None or not len(res.spot_pattern):
            return 0.0
        m = min(len(res.spot_pattern), len(nom_centroid))
        return float(np.mean(np.linalg.norm(
            res.spot_pattern[:m] - nom_centroid[:m], axis=1))) if m else 0.0
    raise KeyError(metric)


# =============================================================================
# 6. RSS tolerance-budget allocator
# =============================================================================
def tolerance_budget(sens: pd.DataFrame, delta_target: float,
                     weights: Optional[Dict[str, float]] = None
                     ) -> pd.DataFrame:
    """Allocate per-tolerance σ so the RSS combination stays ≤ Δ_target.

    Inputs
    ------
    sens          : DataFrame from `sensitivity(...)`. Must contain columns
                    `param` and `dY_dsigma`.
    delta_target  : Maximum acceptable change in the metric (same units).
    weights       : optional {param: w}. The σ allocated to each param is
                    proportional to w / |dY/dσ|. Larger w = looser tolerance.

    RSS model
    ---------
    Combined error = sqrt( Σ_i (s_i · σ_i)² ) ≤ Δ_target
    where s_i = |dY_dsigma_i|. With per-param weights w_i:
        σ_i = (Δ_target / s_i) · w_i / sqrt( Σ_j w_j² )

    With equal weights this gives σ_i = (Δ_target / s_i) / √N.
    """
    sens = sens.copy()
    sens["s"] = sens["dY_dsigma"].abs().replace(0, np.nan)
    sens = sens.dropna(subset=["s"])
    N = len(sens)
    if N == 0:
        return sens.assign(allocated_sigma=[], allocated_delta=[])
    if weights is None:
        w = np.ones(N)
    else:
        w = np.array([weights.get(p, 1.0) for p in sens["param"]])
    denom = np.sqrt(np.sum(w ** 2))
    alloc = (delta_target / sens["s"].to_numpy()) * (w / denom)
    sens["weight"] = w
    sens["allocated_sigma"] = alloc
    sens["allocated_delta"] = sens["s"].to_numpy() * alloc
    out = sens[["param", "sigma", "dY_dsigma", "weight",
                "allocated_sigma", "allocated_delta"]].reset_index(drop=True)
    out.attrs["delta_target"] = float(delta_target)
    out.attrs["rss_combined"] = float(np.sqrt(np.sum(out["allocated_delta"] ** 2)))
    return out


# =============================================================================
# 7. Convenience: full tolerance report
# =============================================================================
def full_report(cfg: TMPCConfig, spec: ToleranceSpec,
                n_trials: int = 200, metric: str = "throughput",
                seed: int = 0) -> dict:
    """Run MC + sensitivity + budget allocation. Returns a dict of frames."""
    mc = monte_carlo(cfg, spec, n_trials=n_trials, seed=seed)
    summary = summarise_mc(mc)
    sens = sensitivity(cfg, spec, metric=metric)
    # default budget target: 5% throughput drop
    delta = 0.05 if metric == "throughput" else float(sens["abs_delta_at_1sigma"].max())
    budget = tolerance_budget(sens, delta_target=delta)
    return {"mc": mc, "summary": summary, "sensitivity": sens, "budget": budget}
