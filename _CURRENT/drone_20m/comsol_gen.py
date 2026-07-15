"""Generate COMSOL 6.4 Java-API models from the shipped geometry CSVs.

Implements the mirror-only validation protocol in actual COMSOL: each
mirror becomes an analytic parametric spherical-cap surface, all caps
get a specular Wall, one chief ray is released just inside the cavity on
the exact launch line, and a Ray-Tracing study traces to just past the
design exit bounce. Ray coordinates are exported on a fine time grid;
`comsol_extract.py` reconstructs the bounce vertices (exact line-line
intersections of the straight chord segments) and scores them against
the platform's exact trace.

Usage (from _CURRENT/):
    ../.venv/Scripts/python.exe drone_20m/comsol_gen.py --design D190_19m_2inch
Then compile+run with comsolcompile/comsolbatch (see comsol_run.ps1).
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
C_MM_NS = 299.792458          # speed of light [mm/ns]

SPECS = {
    "D190_26m_trigas": "design_spec_D190_26m.json",
    "D160_27m": "design_spec_D160_27m.json",
    "D180_24m_H2": "design_spec_D180_24m_H2.json",
    "D180_15m_sparse": "design_spec_D180_15m_sparse.json",
    "D130_9m_halfinch": "design_spec_D130_9m_halfinch.json",
    "D190_19m_2inch": "design_spec_D190_19m_2inch.json",
    "D190_29m_max": "design_D190_29m.json",
    "D150_14cm_flight": "design_D150_14cm.json",
    "D180_22m": "design_D180_22m.json",
}


def f(x: float) -> str:
    return f"{x:.12g}"


def gen(design: str, out_dir: str, dt_ns: float = 0.02,
        with_image: bool = False) -> str:
    geom = pd.read_csv(os.path.join(_HERE, "designs", "comsol",
                                    f"comsol_geom_{design}.csv"))
    mirrors = geom[geom["item"].str.startswith("mirror_")]
    launch = geom[geom["item"] == "launch_ray"].iloc[0]
    ps_bnd_tags = []

    with open(os.path.join(_HERE, "designs", SPECS[design]),
              "r", encoding="utf-8") as fh:
        spec = json.load(fh)
    n_exit = int(spec["metrics"]["n_exit"])
    opl_mm = float(spec["metrics"]["opl_m"]) * 1000.0

    # Release from the first real mirror spot heading to the second, using
    # the platform's own traced spot pattern — unambiguous direction into
    # the cavity (the hole-entrance ray is reconstructed only up to a sign
    # in the CSV, which is not robust for COMSOL).
    cfg = _Cfg(**spec["cfg"])
    cfg.n_passes = n_exit + 1
    res = _sim(cfg)
    pattern = np.asarray(res.spot_pattern[: res.bounces])
    s0, s1 = pattern[0], pattern[1]
    u01 = (s1 - s0) / np.linalg.norm(s1 - s0)
    rel = s0 + 3.0 * u01                        # 3 mm off M(s0) toward M(s1)
    d = u01

    # trace long enough for n_exit bounces plus half a chord
    t_end_ns = (opl_mm + 60.0) / C_MM_NS
    n_steps = int(np.ceil(t_end_ns / dt_ns))

    cls = f"m_{design}"
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

    for _, m in mirrors.iterrows():
        k = int(str(m["item"]).split("_")[1])
        c = np.array([m.x_mm, m.y_mm, m.z_mm])
        n = np.array([m.nx, m.ny, m.nz]); n /= np.linalg.norm(n)
        sag = np.array([m.sagx, m.sagy, m.sagz]); sag /= np.linalg.norm(sag)
        e1 = np.cross(sag, n); e1 /= np.linalg.norm(e1)
        e2 = sag
        R = float(m.roc_mm)
        a = float(m.aperture_r_mm)
        S = c + R * n                          # centre of curvature
        # square patch (no pole singularity, meshes cleanly):
        # P(s1,s2) = S - n*sqrt(R^2-s1^2-s2^2) + e1*s1 + e2*s2
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
    # enclosing air domain: without a meshed domain the GOP interface has
    # no selection and wall features never fire (rays sail straight through)
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

    # union selection of just the mirror-cap boundaries (so the specular
    # wall lands on mirrors only, not the enclosing cylinder)
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
    L.append('    try {')
    L.append('      model.component("comp1").physics("gop")'
             '.feature("mp1").set("n", "1");')
    L.append('      System.out.println("MEDIUM n=1 set");')
    L.append('    } catch (Exception e) {')
    L.append('      System.out.println("mp1 missing; gop features: " + '
             'String.join(",", model.component("comp1").physics("gop")'
             '.feature().tags()));')
    L.append('    }')
    L.append('    model.component("comp1").physics("gop")'
             '.create("wall1", "Wall", 2);')
    L.append('    model.component("comp1").physics("gop")'
             '.feature("wall1").selection().named("selmir");')
    L.append('    model.component("comp1").physics("gop")'
             '.feature("wall1").set("WallCondition", "SpecularReflection");')
    L.append('    System.out.println("WALL boundaries: " + '
             'model.component("comp1").physics("gop").feature("wall1")'
             '.selection().entities().length);')

    L.append('    model.component("comp1").physics("gop")'
             '.create("relg1", "ReleaseGrid", -1);')
    qx, qy, qz = f(rel[0]), f(rel[1]), f(rel[2])
    dx, dy, dz = f(d[0]), f(d[1]), f(d[2])
    L.append(f'    model.component("comp1").physics("gop").feature("relg1")'
             f'.set("x0", new double[]{{{qx}, {qy}, {qz}}});')
    L.append(f'    model.component("comp1").physics("gop").feature("relg1")'
             f'.set("L0", new String[]{{"{dx}", "{dy}", "{dz}"}});')
    # collapse the release grid to a single chief ray
    for pn, pv in (("RayDirectionVector", "Expression"),
                   ("RadialDistribution", "UniformRadiusIntervals"),
                   ("Rc", "0"), ("Ncr", "1"), ("Nphi", "1"), ("qr0", "0"),
                   ("Nw", "1"), ("lambda0Nval", "1"), ("nuNval", "1")):
        L.append(f'    try {{ model.component("comp1").physics("gop")'
                 f'.feature("relg1").set("{pn}", "{pv}"); }} '
                 f'catch (Exception e) {{ }}')

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
    out_txt = os.path.join(out_dir, f"{design}_ray.txt").replace("\\", "/")
    L.append(f'    model.result().export("exp1")'
             f'.set("filename", "{out_txt}");')
    L.append('    model.result().export("exp1").set("fullprec", true);')
    L.append('    model.result().export("exp1").run();')
    L.append(f'    System.out.println("EXPORTED: {out_txt}");')

    if with_image:
        png = os.path.join(out_dir, f"{design}_comsol.png").replace("\\", "/")
        L.append('    model.result().create("pg1", "PlotGroup3D");')
        L.append('    model.result("pg1").set("data", "rayd");')
        L.append('    model.result("pg1").create("rtraj1", "RayTrajectories");')
        L.append('    try { model.result("pg1").feature("rtraj1")'
                 '.set("linetype", "tube"); } catch (Exception e) { }')
        L.append('    try { model.result("pg1").feature("rtraj1")'
                 '.set("tuberadiusexpr", "0.4[mm]"); } catch (Exception e) { }')
        L.append('    model.result("pg1").run();')
        # top-down camera (ring lies in z = 0) + white background
        L.append('    try {')
        L.append('      model.result("pg1").set("view", "view1");')
        L.append(f'      model.view("view1").camera()'
                 f'.set("target", new double[]{{0, 0, 0}});')
        L.append(f'      model.view("view1").camera()'
                 f'.set("position", new double[]{{0, 0, {f(3.2 * r_env)}}});')
        L.append('      model.view("view1").camera()'
                 '.set("up", new double[]{0, 1, 0});')
        L.append('      model.view("view1").set("showgrid", "off");')
        L.append('      model.view("view1").set("showaxisorientation", "off");')
        L.append('    } catch (Exception e) { '
                 'System.out.println("view set failed: " + e.getMessage()); }')
        L.append('    model.result().export().create("img1", "Image3D");')
        L.append('    model.result().export("img1").set("plotgroup", "pg1");')
        L.append('    model.result().export("img1").set("sourceobject", "pg1");')
        L.append(f'    model.result().export("img1")'
                 f'.set("pngfilename", "{png}");')
        L.append('    try { model.result().export("img1")'
                 '.set("size", "manual"); '
                 'model.result().export("img1").set("unit", "px"); '
                 'model.result().export("img1").set("width", "1600"); '
                 'model.result().export("img1").set("height", "1200"); '
                 'model.result().export("img1").set("resolution", "96"); } '
                 'catch (Exception e) { }')
        L.append('    try { model.result().export("img1")'
                 '.set("background", "color"); '
                 'model.result().export("img1").set("bgcolor", "white"); } '
                 'catch (Exception e) { }')
        L.append('    model.result().export("img1").run();')
        L.append(f'    System.out.println("IMAGE: {png}");')

    L.append("    return model;")
    L.append("  }")
    L.append("}")

    java = os.path.join(out_dir, f"{cls}.java")
    with open(java, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"wrote {java}  (release at {rel.round(4)}, "
          f"{n_steps} steps x {dt_ns} ns, n_exit={n_exit})")
    return java


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", default="D190_19m_2inch",
                    choices=sorted(SPECS))
    ap.add_argument("--out-dir", default=os.path.join(
        _HERE, "designs", "comsol", "java"))
    ap.add_argument("--dt-ns", type=float, default=0.02)
    ap.add_argument("--image", action="store_true",
                    help="also export a COMSOL ray-trajectory PNG")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    gen(args.design, args.out_dir, args.dt_ns, with_image=args.image)
    return 0


if __name__ == "__main__":
    sys.exit(main())
