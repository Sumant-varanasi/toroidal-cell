"""Generate COMSOL Ray Optics models that carry the GAUSSIAN BEAM WIDTH.

A Gaussian beam's 1/e^2 radius is exactly the envelope of the paraxial
ray family   x(z) = w0*cos(phi) + theta_d*z*sin(phi)   released from the
waist (theta_d = M2*lambda/(pi*w0)).  Second moments of any ray set
propagate by the same ABCD matrices as the beam's complex q, so the
bundle's transverse moment widths ARE w(z) — through every mirror bounce,
in plain (already-validated) Ray Optics.  No wave-optics solve needed.

Two model kinds:
  --design freespace          textbook check: w(z) law in an empty block
  --design D150_14cm_flight   full TMPC: bundle traced through all bounces

The bundle: 1 chief ray + 2 ring families (nphi rays each) in the two
transverse axes, released with the design's actual (w0, M2, waist offset)
at the same release point comsol_gen.py uses.  comsol_beam_extract.py
computes moment widths per time step and scores them against the
platform's astigmatic ABCD envelope.

Usage (from _CURRENT/):
    ../.venv/Scripts/python.exe drone_20m/comsol_beam_gen.py --design freespace
    ../.venv/Scripts/python.exe drone_20m/comsol_beam_gen.py --design D150_14cm_flight
Then comsolcompile + comsolbatch as usual.
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
from tmpc_platform_v5 import TMPCConfig as _Cfg, simulate_tmpc as _sim  # noqa
from comsol_gen import SPECS, f                                        # noqa

C_MM_NS = 299.792458

# free-space case mirrors the flight design's beam so the panel is relevant
FS = dict(w0=0.2913, M2=1.1, lam=1.654e-3, Lz=610.0)


def bundle(rel: np.ndarray, u: np.ndarray, w0: float, theta_d: float,
           z_rel: float, nphi: int):
    """(pos, dir) for chief + 2 ring families at distance z_rel from waist."""
    e1 = np.cross(u, np.array([0.0, 0.0, 1.0]))
    if np.linalg.norm(e1) < 1e-6:
        e1 = np.cross(u, np.array([1.0, 0.0, 0.0]))
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(u, e1)
    e2 /= np.linalg.norm(e2)
    rays = [(rel, u)]
    for e in (e1, e2):
        for k in range(nphi):
            phi = 2.0 * np.pi * k / nphi
            off = w0 * np.cos(phi) + theta_d * z_rel * np.sin(phi)
            slope = theta_d * np.sin(phi)
            d = u + slope * e
            rays.append((rel + off * e, d / np.linalg.norm(d)))
    return rays


def emit_release(L, i: int, pos: np.ndarray, d: np.ndarray):
    tag = f"relg{i}"
    L.append(f'    model.component("comp1").physics("gop")'
             f'.create("{tag}", "ReleaseGrid", -1);')
    L.append(f'    model.component("comp1").physics("gop").feature("{tag}")'
             f'.set("x0", new double[]{{{f(pos[0])}, {f(pos[1])}, '
             f'{f(pos[2])}}});')
    L.append(f'    model.component("comp1").physics("gop").feature("{tag}")'
             f'.set("L0", new String[]{{"{f(d[0])}", "{f(d[1])}", '
             f'"{f(d[2])}"}});')
    for pn, pv in (("RayDirectionVector", "Expression"),
                   ("RadialDistribution", "UniformRadiusIntervals"),
                   ("Rc", "0"), ("Ncr", "1"), ("Nphi", "1"), ("qr0", "0"),
                   ("Nw", "1"), ("lambda0Nval", "1"), ("nuNval", "1")):
        L.append(f'    try {{ model.component("comp1").physics("gop")'
                 f'.feature("{tag}").set("{pn}", "{pv}"); }} '
                 f'catch (Exception e) {{ }}')


def header(cls: str):
    L = []
    L.append("import com.comsol.model.*;")
    L.append("import com.comsol.model.util.*;")
    L.append("")
    L.append(f"public class {cls} {{")
    L.append("  public static void main(String[] args) { run(); }")
    L.append("  public static Model run() {")
    L.append('    Model model = ModelUtil.create("Model");')
    L.append('    model.component().create("comp1", true);')
    L.append('    model.component("comp1").geom().create("geom1", 3);')
    L.append('    model.component("comp1").geom("geom1").lengthUnit("mm");')
    return L


def footer(L, out_txt: str, dt_ns: float, n_steps: int):
    L.append('    model.study().create("std1");')
    L.append('    model.study("std1").create("rtrac", "RayTracing");')
    L.append(f'    model.study("std1").feature("rtrac")'
             f'.set("tlist", "range(0,{f(dt_ns)},{f(n_steps * dt_ns)})");')
    L.append('    model.study("std1").run();')
    L.append('    model.result().dataset().create("rayd", "Ray");')
    L.append('    model.result().export().create("exp1", "Data");')
    L.append('    model.result().export("exp1").set("data", "rayd");')
    L.append('    model.result().export("exp1").set("expr", '
             'new String[]{"qx", "qy", "qz"});')
    L.append(f'    model.result().export("exp1")'
             f'.set("filename", "{out_txt}");')
    L.append('    model.result().export("exp1").set("fullprec", true);')
    L.append('    model.result().export("exp1").run();')
    L.append(f'    System.out.println("EXPORTED: {out_txt}");')
    L.append("    return model;")
    L.append("  }")
    L.append("}")
    return L


def gen_freespace(out_dir: str, dt_ns: float, nphi: int) -> str:
    w0, M2, lam, Lz = FS["w0"], FS["M2"], FS["lam"], FS["Lz"]
    theta_d = M2 * lam / (np.pi * w0)
    cls = "freespace_beam"
    L = header(cls)
    L.append('    model.component("comp1").geom("geom1")'
             '.create("blk1", "Block");')
    L.append(f'    model.component("comp1").geom("geom1").feature("blk1")'
             f'.set("size", new String[]{{"8", "8", "{f(Lz)}"}});')
    L.append(f'    model.component("comp1").geom("geom1").feature("blk1")'
             f'.set("pos", new String[]{{"-4", "-4", "0"}});')
    L.append('    model.component("comp1").geom("geom1").run();')
    L.append('    model.component("comp1").mesh().create("mesh1", "geom1");')
    L.append('    model.component("comp1").mesh("mesh1").autoMeshSize(4);')
    L.append('    model.component("comp1").mesh("mesh1").run();')
    L.append('    model.component("comp1").physics()'
             '.create("gop", "GeometricalOptics", "geom1");')
    L.append('    try { model.component("comp1").physics("gop")'
             '.feature("mp1").set("n_mat", "userdef"); } '
             'catch (Exception e) { }')
    L.append('    try { model.component("comp1").physics("gop")'
             '.feature("mp1").set("n", "1"); } catch (Exception e) { }')
    rel = np.array([0.0, 0.0, 0.5])          # waist at z=0.5, inside block
    u = np.array([0.0, 0.0, 1.0])
    for i, (p, d) in enumerate(bundle(rel, u, w0, theta_d, 0.0, nphi),
                               start=1):
        emit_release(L, i, p, d)
    t_end = (Lz + 5.0) / C_MM_NS
    n_steps = int(np.ceil(t_end / dt_ns))
    out_txt = os.path.join(out_dir, "freespace_beam_ray.txt").replace(
        "\\", "/")
    footer(L, out_txt, dt_ns, n_steps)
    path = os.path.join(out_dir, f"{cls}.java")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"wrote {path}  (w0={w0} mm, M2={M2}, theta_d={theta_d*1e3:.4f} "
          f"mrad, {1 + 2 * nphi} rays, {n_steps} steps)")
    return path


def gen_design(design: str, out_dir: str, dt_ns: float, nphi: int) -> str:
    geom = pd.read_csv(os.path.join(_HERE, "designs", "comsol",
                                    f"comsol_geom_{design}.csv"))
    mirrors = geom[geom["item"].str.startswith("mirror_")]
    with open(os.path.join(_HERE, "designs", SPECS[design]),
              "r", encoding="utf-8") as fh:
        spec = json.load(fh)
    n_exit = int(spec["metrics"]["n_exit"])
    opl_mm = float(spec["metrics"]["opl_m"]) * 1000.0
    cfg = _Cfg(**spec["cfg"])
    cfg.n_passes = n_exit + 1
    res = _sim(cfg)
    pattern = np.asarray(res.spot_pattern[: res.bounces])
    s0, s1 = pattern[0], pattern[1]
    u01 = (s1 - s0) / np.linalg.norm(s1 - s0)
    rel = s0 + 3.0 * u01

    w0 = float(cfg.w0)
    M2 = float(getattr(cfg, "M2", 1.0))
    lam = float(cfg.wavelength)
    theta_d = M2 * lam / (np.pi * w0)
    z_rel = 3.0 - float(getattr(cfg, "input_waist_offset", 0.0))

    cls = f"m_{design}_beam"
    L = header(cls)
    ps_bnd_tags = []
    for _, m in mirrors.iterrows():
        k = int(str(m["item"]).split("_")[1])
        c = np.array([m.x_mm, m.y_mm, m.z_mm])
        n = np.array([m.nx, m.ny, m.nz]); n /= np.linalg.norm(n)
        sag = np.array([m.sagx, m.sagy, m.sagz]); sag /= np.linalg.norm(sag)
        e1 = np.cross(sag, n); e1 /= np.linalg.norm(e1)
        e2 = sag
        R = float(m.roc_mm)
        a = float(m.aperture_r_mm)
        S = c + R * n
        exprs = []
        for i in range(3):
            exprs.append(
                f"{f(S[i])}-({f(n[i])})*sqrt({f(R)}^2-s1^2-s2^2)"
                f"+({f(e1[i])})*s1+({f(e2[i])})*s2")
        tag = f"ps{k}"
        L.append(f'    model.component("comp1").geom("geom1")'
                 f'.create("{tag}", "ParametricSurface");')
        for pname, pval in (("parmin1", f(-a)), ("parmax1", f(a)),
                            ("parmin2", f(-a)), ("parmax2", f(a))):
            L.append(f'    model.component("comp1").geom("geom1")'
                     f'.feature("{tag}").set("{pname}", "{pval}");')
        L.append(f'    model.component("comp1").geom("geom1")'
                 f'.feature("{tag}").set("coord", new String[]{{'
                 f'"{exprs[0]}", "{exprs[1]}", "{exprs[2]}"}});')
        L.append(f'    model.component("comp1").geom("geom1")'
                 f'.feature("{tag}").set("rtol", "1e-7");')
        L.append(f'    model.component("comp1").geom("geom1")'
                 f'.feature("{tag}").set("selresult", true);')
        L.append(f'    model.component("comp1").geom("geom1")'
                 f'.feature("{tag}").set("selresultshow", "bnd");')
        ps_bnd_tags.append(f"geom1_{tag}_bnd")
    r_env = 0.0
    z_max = 0.0
    for _, m in mirrors.iterrows():
        c = np.array([m.x_mm, m.y_mm, m.z_mm])
        r_env = max(r_env, float(np.hypot(c[0], c[1])) +
                    float(m.aperture_r_mm))
        z_max = max(z_max, abs(c[2]) + float(m.aperture_r_mm))
    r_env += 6.0
    z_half = z_max + 6.0
    L.append('    model.component("comp1").geom("geom1")'
             '.create("cyl1", "Cylinder");')
    L.append(f'    model.component("comp1").geom("geom1").feature("cyl1")'
             f'.set("r", "{f(r_env)}");')
    L.append(f'    model.component("comp1").geom("geom1").feature("cyl1")'
             f'.set("h", "{f(2 * z_half)}");')
    L.append(f'    model.component("comp1").geom("geom1").feature("cyl1")'
             f'.set("pos", new String[]{{"0", "0", "{f(-z_half)}"}});')
    L.append('    model.component("comp1").geom("geom1").run();')
    inp = ", ".join(f'"{t}"' for t in ps_bnd_tags)
    L.append('    model.component("comp1").selection()'
             '.create("selmir", "Union");')
    L.append('    model.component("comp1").selection("selmir")'
             '.set("entitydim", 2);')
    L.append(f'    model.component("comp1").selection("selmir")'
             f'.set("input", new String[]{{{inp}}});')
    L.append('    model.component("comp1").mesh().create("mesh1", "geom1");')
    L.append('    model.component("comp1").mesh("mesh1").autoMeshSize(3);')
    L.append('    model.component("comp1").mesh("mesh1").run();')
    L.append('    model.component("comp1").physics()'
             '.create("gop", "GeometricalOptics", "geom1");')
    L.append('    try { model.component("comp1").physics("gop")'
             '.feature("mp1").set("n_mat", "userdef"); } '
             'catch (Exception e) { }')
    L.append('    try { model.component("comp1").physics("gop")'
             '.feature("mp1").set("n", "1"); } catch (Exception e) { }')
    L.append('    model.component("comp1").physics("gop")'
             '.create("wall1", "Wall", 2);')
    L.append('    model.component("comp1").physics("gop")'
             '.feature("wall1").selection().named("selmir");')
    L.append('    model.component("comp1").physics("gop")'
             '.feature("wall1").set("WallCondition", "SpecularReflection");')
    L.append('    System.out.println("WALL boundaries: " + '
             'model.component("comp1").physics("gop").feature("wall1")'
             '.selection().entities().length);')
    for i, (p, d) in enumerate(bundle(rel, u01, w0, theta_d, z_rel, nphi),
                               start=1):
        emit_release(L, i, p, d)
    t_end_ns = (opl_mm + 60.0) / C_MM_NS
    n_steps = int(np.ceil(t_end_ns / dt_ns))
    out_txt = os.path.join(out_dir, f"{design}_beam_ray.txt").replace(
        "\\", "/")
    footer(L, out_txt, dt_ns, n_steps)
    path = os.path.join(out_dir, f"{cls}.java")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"wrote {path}  (w0={w0} mm, M2={M2}, theta_d={theta_d*1e3:.4f} "
          f"mrad, z_rel={z_rel:.2f} mm from waist, {1 + 2 * nphi} rays, "
          f"{n_steps} steps)")
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", required=True,
                    choices=["freespace"] + sorted(SPECS))
    ap.add_argument("--out-dir", default=os.path.join(
        _HERE, "designs", "comsol", "java"))
    ap.add_argument("--dt-ns", type=float, default=None)
    ap.add_argument("--nphi", type=int, default=8)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    if args.design == "freespace":
        gen_freespace(args.out_dir, args.dt_ns or 0.01, args.nphi)
    else:
        gen_design(args.design, args.out_dir, args.dt_ns or 0.02, args.nphi)
    return 0


if __name__ == "__main__":
    sys.exit(main())
