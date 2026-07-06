/* Build the TMPC drone-cell paper — FINAL DRAFT.
   Run:  node build_paper.js  ->  TMPC_drone_paper_final_draft.docx      */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, BorderStyle, WidthType, ShadingType, TabStopType,
  Footer, PageNumber,
} = require(require("child_process").execSync("npm root -g").toString().trim() + "/docx");

const FIG = path.resolve(__dirname, "..", "designs", "figures");
const OUT = path.join(__dirname, "TMPC_drone_paper_final_draft.docx");

// ---------- helpers ----------------------------------------------------
const FONT = "Times New Roman";
const SZ = 22;                       // 11 pt body

function R(text, opts = {}) {
  return new TextRun({ text, font: FONT, size: SZ, ...opts });
}
function I(text, opts = {}) {           // italic (math) run
  return R(text, { italics: true, ...opts });
}
function P(children, opts = {}) {
  if (typeof children === "string") children = [R(children)];
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 120, line: 276 },
    children, ...opts,
  });
}
function H1(text) {
  return new Paragraph({
    spacing: { before: 280, after: 160 },
    children: [R(text, { bold: true, size: 24 })],
  });
}
function H2(text) {
  return new Paragraph({
    spacing: { before: 220, after: 120 },
    children: [R(text, { bold: true, italics: true, size: 22 })],
  });
}
let eqN = 0;
function EQ(runs) {
  eqN += 1;
  return new Paragraph({
    spacing: { before: 100, after: 140 },
    tabStops: [{ type: TabStopType.CENTER, position: 4680 },
               { type: TabStopType.RIGHT, position: 9360 }],
    children: [R("\t"), ...runs, R(`\t(${eqN})`)],
  });
}
function pngSize(p) {
  const b = fs.readFileSync(p);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
let figN = 0;
function fig(file, caption, widthPx = 560) {
  const p = path.join(FIG, file);
  const { w, h } = pngSize(p);
  figN += 1;
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 160, after: 60 },
      children: [new ImageRun({
        type: "png", data: fs.readFileSync(p),
        transformation: { width: widthPx, height: Math.round(widthPx * h / w) },
        altText: { title: `Figure ${figN}`, description: caption, name: `fig${figN}` },
      })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [R(`Fig. ${figN}. `, { bold: true, size: 20 }),
                 R(caption, { size: 20 })],
    }),
  ];
}
let tabN = 0;
const bd = { style: BorderStyle.SINGLE, size: 2, color: "888888" };
const borders = { top: bd, bottom: bd, left: bd, right: bd };
function cell(text, width, opts = {}) {
  return new TableCell({
    borders, width: { size: width, type: WidthType.DXA },
    shading: opts.head ? { fill: "E8EEF4", type: ShadingType.CLEAR } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({
      alignment: opts.center ? AlignmentType.CENTER : AlignmentType.LEFT,
      children: [R(text, { size: 18, bold: !!opts.head })],
    })],
  });
}
function tbl(caption, header, rows, widths) {
  tabN += 1;
  const total = widths.reduce((a, b) => a + b, 0);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { before: 200, after: 80 },
      children: [R(`Table ${tabN}. `, { bold: true, size: 20 }),
                 R(caption, { size: 20 })],
    }),
    new Table({
      width: { size: total, type: WidthType.DXA },
      columnWidths: widths,
      rows: [
        new TableRow({ children: header.map((t, i) => cell(t, widths[i], { head: true, center: true })) }),
        ...rows.map(r => new TableRow({
          children: r.map((t, i) => cell(t, widths[i], { center: i > 0 })),
        })),
      ],
    }),
    new Paragraph({ spacing: { after: 160 }, children: [] }),
  ];
}
const sub = t => I(t, { subScript: true });
const sup = t => I(t, { superScript: true });

// ---------- content -----------------------------------------------------
const body = [];

// Title (no banner, no author block)
body.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 240 },
  children: [R("Chord-skip toroidal multipass cells from catalogue mirrors: tolerance-tiered 20–29 m optical paths for drone-borne methane sensing", { bold: true, size: 30 })],
}));

// Abstract
body.push(H1("Abstract"));
body.push(P("Toroidal multipass cells fold long absorption paths into compact, mechanically robust volumes, but published designs demonstrate at most ~10 m of optical path in the 100–200 mm diameter class and typically require custom diamond-turned optics. We present a family of ring-geometry multipass cells that reach a verified 20.4–29.0 m optical path length within a 183 mm assembly envelope — and 20.7 m within 141 mm — using 12–16 catalogue 25.4 mm concave mirrors (≈US$1000 of optics) and a sub-kilogram optical head. Three design principles enable this: (i) a chord-skip ring geometry whose near-diameter chords deliver up to 143 mm of path per reflection at 7–13° incidence; (ii) an engineered dual-plane re-entrance condition in which the machined ring radius acts as the closure-tuning parameter (≈1.2 rad of accumulated transverse phase per millimetre), with a number-theoretic constellation rule that guarantees fringe-safe spot separation on every mirror; and (iii) mode-matched injection through a single 1.3 mm coupling hole, which makes hole losses negligible so that cell transmission equals R to the power (n−1) in mirror reflectivity R — 86.7 % for the headline 20.4 m design at R = 0.999. Designs are verified with an exact three-dimensional ray tracer including astigmatic Gaussian-beam propagation, cross-validated against an independent ray tracer to sub-micrometre agreement, and toleranced by Monte-Carlo analysis: at research-grade build tolerances the headline design completes all 144 traversals in 100 % of trials, the ±1 % catalogue tolerance on mirror focal length is absorbed by a linear 0.72 mm-per-percent trim of the ring radius, and a plain aluminium ring holds alignment over ±26 K. Because the mirrors provide R = 0.999, the photon budget admits ~700 reflections and the true limit is spot-pattern geometry under build error; a tolerance-tiered menu results, with every tier verified by per-trial physical criteria (path completion, spot merging, hole leakage, unassisted exit): 20.4 m at 86.7 % is robust at standard laboratory build tolerances; 29.0 m at 76.6 % (Ø183 mm), 24.8 m at 83.9 %, and 20.7 m at 81.6 % in a Ø141 mm envelope are robust at flight-grade (0.1 mrad) build tolerances — the glued/welded construction class a vibrating airframe requires regardless; and the geometric ceiling — 38.6 m in Ø169 mm at 72.5 % — is reachable only with active alignment."));

// 1 Introduction
body.push(H1("1. Introduction"));
body.push(P("Tunable diode laser absorption spectroscopy (TDLAS) of the methane 2ν3 band near 1654 nm requires tens of metres of absorption path for sub-ppm sensitivity, while drone deployment restricts the sensor head to roughly a 19 cm envelope and about a kilogram of payload. Multipass cells reconcile these demands by folding the path between mirrors. The classical two-mirror Herriott cell [11–13] achieves this with re-entrant elliptical patterns; its densest variants reach 54.6 m in a 12 cm-base astigmatic-type cell [9] and 26.4 m in a 12 cm dense-pattern cell [10], at the cost of custom mirror pairs and critical two-mirror alignment. Ring-geometry (toroidal/circular) cells trade some packing density for one-piece mechanical robustness: demonstrated paths are 2.2–4.1 m in the monolithic toroidal cell of Tuzson et al. [1, 2], >12 m in a 145 mm circular paraboloid [3], 10 m at <200 g in the segmented cell of Graf et al. [4], and 10 m (30 m theoretical) from multi-layer patterns on a 100 mm ring [7]; mask-based fringe suppression [5], double-row geometries at larger diameter [6], and cryogenic toroidal cavities for particle-physics spectroscopy [8] extend the family. Across this literature, demonstrated toroidal-class paths in drone-compatible envelopes cluster at or below ~10 m, and every design relies on custom optics."));
body.push(P("This work asks a deliberately constrained question: how much verified optical path can a ring cell deliver inside a 190 mm envelope using only catalogue mirrors — Thorlabs CM254-series 25.4 mm concave mirrors (16 focal lengths, ≈US$74 each) — with 9–16 mirrors, a single 1.3 mm coupling hole, and a 1.3 mm collimated input? The chord-skip parameter is the entry point: in our early design-space exploration, moving from adjacent-mirror propagation to a skip of s = 4 on a 9-mirror ring raised the path length by 67 % while cutting the incidence angle from 67.5° to 10°, and a companion catalogue study showed 12.7 mm mirrors saturate near 12 m — fixing the present 25.4 mm design space. Our contributions are: (1) the chord-skip parametrisation itself, with s ≈ N/2 giving near-diameter chords at near-normal incidence; (2) an engineered — rather than searched-for — re-entrance condition, tuned by the machined ring radius against catalogue-locked curvatures, with an exact constellation criterion guaranteeing fringe-safe spot patterns before any ray is traced; (3) mode-matched single-hole coupling that renders the hole lossless; and (4) a tolerance-tiered design menu (13.6–38.6 m), in which every design passes an eight-item physical check matrix in exact ray tracing, is cross-validated independently, and carries a Monte-Carlo robustness verdict at a stated build grade, together with machining-level build specifications and a drone mass budget."));

// 2 Architecture & theory
body.push(H1("2. Cell architecture and design principles"));
body.push(H2("2.1 Chord-skip ring geometry"));
body.push(P([R("N identical concave mirrors of curvature radius "), I("R"), R(" and clear-aperture radius 11.4 mm face inward from a ring of radius "), I("R"), sub("ring"), R(", one every 360°/"), I("N"), R(". A beam injected through a hole in mirror M0 advances by "), I("s"), R(" mirrors per reflection (the chord skip, gcd("), I("N"), R(", "), I("s"), R(") = 1). Each chord length and the (identical) incidence angle on every mirror follow")]));
body.push(EQ([I("L"), R(" = 2 "), I("R"), sub("ring"), R(" sin(π"), I("s"), R("/"), I("N"), R("),   "), I("θ"), sub("i"), R(" = π/2 − π"), I("s"), R("/"), I("N"), R(".")]));
body.push(P([R("For "), I("s"), R(" ≈ "), I("N"), R("/2 the chords approach the ring diameter while "), I("θ"), sub("i"), R(" falls to 6–13°: a 72 mm-radius ring yields 140+ mm of path per reflection — the geometric core of the result. The assembly envelope is 2("), I("R"), sub("ring"), R(" + 18 mm), the allowance covering substrate and housing wall.")]));
body.push(H2("2.2 Re-entrance: dual-plane phase closure"));
body.push(P([R("In the paraxial unit cell (one chord plus one mirror) the transverse ray oscillation advances per bounce by a phase "), I("θ"), R(" in each principal plane, split by the off-axis astigmatism:")]));
body.push(EQ([R("cos "), I("θ"), sub("t"), R(" = 1 − "), I("L"), R("/("), I("R"), R(" cos "), I("θ"), sub("i"), R("),   cos "), I("θ"), sub("s"), R(" = 1 − "), I("L"), R(" cos "), I("θ"), sub("i"), R(" /"), I("R"), R(",")]));
body.push(P([R("with per-plane stability requiring |cos "), I("θ"), R("| ≤ 1. The beam exits through the entrance hole after "), I("n"), R(" = "), I("kN"), R(" reflections when both accumulated phases return to their launch value; zero-crossing launches close at phase 0 or π, giving four closure-mode combinations per geometry:")]));
body.push(EQ([I("n θ"), sub("t,s"), R(" ≡ 0 or π  (mod 2π),   "), I("n"), R(" = "), I("kN"), R(".")]));
body.push(P([R("The single machinable parameter "), I("R"), sub("ring"), R(" moves both accumulated phases along a nearly fixed direction, at ≈1.2 rad per millimetre for the designs below, so a candidate is closable only if its signed phase residuals lie near that line; the residual is absorbed by the launch amplitudes through their weak aberration-mediated phase pull. Re-entrance thus becomes an engineered property: the ring is machined to the radius that closes the pattern for the delivered mirror lot, and the verified designs re-cross the hole centre to within 10⁻⁶–10⁻⁴ mm.")]));
body.push(H2("2.3 Constellation rule: fringe-safe spot patterns"));
body.push(P([R("At closure the "), I("n"), R(" spots sample a Lissajous curve at the phase-snapped rates "), I("θ′"), R(" of Eq. (3); spot "), I("j"), R(" lands on mirror ("), I("js"), R(") mod "), I("N"), R(" at face coordinates")]));
body.push(EQ([I("u"), sub("j"), R(" = "), I("A"), sub("t"), R(" sin("), I("j θ′"), sub("t"), R("),   "), I("v"), sub("j"), R(" = "), I("A"), sub("s"), R(" {sin, cos}("), I("j θ′"), sub("s"), R(").")]));
body.push(P([R("Three exact geometric rules follow: the spots-per-mirror count "), I("k"), R(" must be odd (for even "), I("k"), R(" the tangential π-slot coincides with a sagittal near-return and a spot lands in the coupling hole); gcd("), I("M"), R(", "), I("k"), R(") = 1 in both planes with "), I("M"), R(" = round("), I("nθ"), R("/2π) (otherwise the "), I("k"), R(" spots per mirror collapse into clusters); and — decisive in practice — every mirror carries the same "), I("k"), R("-point pattern at a different phase origin along the curve, so the worst spot pair must be evaluated over all "), I("N"), R(" mirrors, not only the launch mirror, which overestimates usable separation by up to 3×. The minimum pair distance and pattern extent are computed exactly per candidate from Eq. (4), sizing the required amplitude — with every clearance additionally padded by the expected build-error spot walk of the target build grade (§5) — and rejecting self-crowding patterns before ray tracing. Spot-overlap fringes, the dominant practical noise source in this cell class [5, 7], are thereby excluded by construction.")]));
body.push(H2("2.4 Mode-matched single-hole coupling"));
body.push(P([R("The cell eigenmode has a mirror-plane 1/e² radius per plane of")]));
body.push(EQ([I("w"), sub("m"), sup("2"), R(" = "), I("M"), sup("2"), I("λL"), R(" / (π sin "), I("θ"), R("),")]));
body.push(P([R("≈ 0.3–0.45 mm here. A 1.3 mm waist placed at the hole is badly mismatched to it; the beam then breathes to ~3× its injected size, spots overlap, and the hole clips 13.5 % of the power at entry and again at exit. Instead, the injection optics place the in-cell waist (0.20–0.33 mm) near mid-chord: the beam rides the eigenmode at 0.21–0.42 mm for the entire path, the radius at the hole is ~0.3–0.37 mm, and the 1.3 mm hole transmits ≈100 % both ways. Cell transmission is then exactly")]));
body.push(EQ([I("T"), R("("), I("R"), R(") = "), I("T"), sub("h"), sup("2"), R(" "), I("R"), sup("n−1"), R(" ≈ "), I("R"), sup("n−1"), R(",")]));
body.push(P([R("with "), I("T"), sub("h"), R(" ≈ 1 the hole transmission. At closure the round-trip ABCD map is the identity, so the exit beam reproduces the injected Gaussian and leaves through the same hole, separated from the input axis by 2"), I("θ"), sub("i"), R(" (22.5° for "), I("N"), R(" = 16), placing laser and detector side by side behind M0 with no beamsplitter.")]));
body.push(H2("2.5 Injection chain: source and collimator selection"));
body.push(P("The mode-matched launch is a finite-conjugate imaging task — relay the source mode to a 0.20–0.33 mm waist roughly 45–120 mm past the coupling hole — and the collimator choice follows from it. The baseline chain is a fibre-pigtailed 1654 nm DFB: the fibre mode (radius ≈ 5.5 µm) is imaged by a short-focal aspheric lens of the standard collimation-package type [14] operated slightly defocused, at magnification ≈ 60×. For the headline design an f ≈ 2 mm asphere places the 0.33 mm waist ≈ 120 mm from the lens — the exact conjugates, computed by the q-parameter design, are listed on each specification sheet — so a single catalogue lens in an adjustable FC/APC collimator body performs collimation and mode matching in one element, and its focus adjustment is the fine trim used during alignment. An attractive alternative first stage is a reflective (off-axis-paraboloid) fibre collimator: being achromatic and figure-stable it removes lens focal drift from the thermal budget of §5, complementing the ±26 K window of the aluminium ring. Direct free-space collimation of a TO-can device is the most compact option but is quantitatively limited: the best residual divergence of a collimated TO60 package is ≈0.8° full angle (≈7 mrad half-angle), whereas the cell eigenmode accepts λ/(πw₀) ≈ 1.6–2.6 mrad — a ≈4× mismatch, equivalent to an M² well beyond the verified 1.3 budget, costing ≥80 % of the light and destroying the spot-size guarantees. TO-can sources are therefore suitable only with additional spatial filtering (or for much shorter cells); the fibre-coupled variant is the design baseline."));

// 3 Methods
body.push(H1("3. Numerical methods"));
body.push(P("Designs were generated and verified with our open simulation platform: an exact 3-D ray tracer on toroidal/spherical surfaces (analytic normals, Newton-iterated intersections, per-bounce aperture tests), astigmatic Gaussian propagation via per-plane complex-q ABCD transfer with the actual per-bounce incidence angles and an M² factor, loss budget, per-plane stability, and spot diagnostics; earlier iterations of the platform added Sobol design-space sampling and machine-learning surrogates used in the exploratory phase. The search runs in two stages: Stage A enumerates the catalogue space (16 curvatures × N = 9–16 × coprime skips × a fine ring-radius grid × odd k up to 45) against packing, envelope, stability, closure-residual and constellation criteria, with all clearances sized for the expected build-error walk; Stage B ray-traces survivors at a design-basis M² = 1.1, sweeps the ring radius in 20 µm steps to locate the ~20 µm-wide closure valley, and polishes six launch/geometry parameters by Nelder-Mead. A design is accepted only if the final trace passes all eight checks of Table 3. The tracer was cross-validated against the independent open-source ray tracer Optiland [15]: over 64 bounces of the headline design the two agree to 0.000 µm RMS in spot position, 0.01° in incidence angle, and 0.8 µm in chord length."));

// Fig 1 cell3d
body.push(...fig("drone_20m_cell3d_paper.png",
  "Exact traced beam path of the headline design: 16 catalogue mirrors on a 72.155 mm ring, 144 chords (20.38 m), coloured by bounce order; the input beam (green) enters through the 1.3 mm hole in M0 and the closed pattern exits through the same hole.", 580));

// 4 Results
body.push(H1("4. Results"));
body.push(H2("4.1 The tolerance-tiered design menu"));
body.push(...tbl(
  "Tolerance-tiered design menu. Every row passes the full check matrix in the exact ray trace; the robustness tier is a 100-trial Monte-Carlo verdict at the stated build grade (§5). Transmission T = R^(chords−1) exactly (hole losses ≈ 0), quoted at the project mirrors' R = 0.999. Envelope = 2(R_ring + 18 mm).",
  ["design", "mirrors", "chords", "OPL [m]", "T @0.999", "env. × height [mm]", "robust at"],
  [
    ["geometric ceiling", "14 × CM254-100 (R 200)", "322", "38.60", "72.5 %", "169 × 24", "active align."],
    ["flight max OPL", "12 × CM254-750 (R 1500)", "204", "28.99", "76.6 %", "183 × 23", "flight build"],
    ["long", "16 × CM254-200 (R 400)", "176", "24.77", "83.9 %", "180 × 22", "flight build"],
    ["mid", "14 × CM254-100 (R 200)", "182", "22.25", "83.4 %", "172 × 26", "active align."],
    ["flight compact", "12 × CM254-500 (R 1000)", "204", "20.66", "81.6 %", "141 × 27", "flight build"],
    ["headline 20 m", "16 × CM254-150 (R 300)", "144", "20.38", "86.7 %", "180 × 16", "standard build"],
    ["balanced", "13 × CM254-150 (R 300)", "143", "16.60", "86.8 %", "160 × 20", "flight build"],
    ["small", "10 × CM254-150 (R 300)", "190", "14.85", "82.8 %", "133 × 19", "flight build"],
    ["small max-T", "12 × CM254-250 (R 500)", "132", "13.64", "87.7 %", "143 × 16", "flight build"],
  ],
  [1550, 2300, 750, 850, 950, 1500, 1460]));
body.push(...fig("menu_pareto.png",
  "The verified design menu as an envelope–path map (marker colour = transmission at R = 0.999). The Pareto frontier is populated entirely by catalogue-mirror designs; the dashed line marks the ~10 m demonstrated record of published toroidal cells in this size class.", 540));
body.push(P("The mirrors used in this project provide R = 0.999 at 1654 nm, so the photon budget admits ~700 reflections before transmission falls below 50 % and the real limit becomes spot-pattern geometry under build error. Table 1 therefore reports each design's robustness tier, determined by a 100-trial Monte-Carlo at the stated build grade with per-trial physical criteria (full path completion, no spot merging by the simulator's own minimum-separation metric, positive hole clearance, and an exit that still leaves the 1.3 mm hole with no realignment): 'standard build' = kinematic-mount laboratory tolerances (0.5 mrad tilt class); 'flight build' = glued/welded precision tolerances (0.1 mrad class — the vibration spec a drone cell needs anyway); 'active alignment' = nominally feasible but requiring in-situ trim (ring temperature + launch adjuster). (Transmission for any other coating follows from Eq. (6), Fig. 7 — e.g. a protected-gold build at R = 0.985 would transmit 6–14 %.) The tier boundaries, established by exhaustive search (0.1 mm ring-radius grid, up to 720 bounces, k ≤ 45 spots per mirror, clearances sized to the expected build-error spot walk), are themselves the key observation. At standard tolerances the dense long-path constellations lose spot identity — relative spot motion of 0.3–0.5 mm collapses their separation margins (the 38.6 m design's 5th-percentile minimum separation falls to 0.06 mm) — while at flight grade the 176–204-chord designs hold every margin with ≥99 % path completion. Because pattern walk grows roughly with the square root of the chord count, the standard-tolerance ceiling sits near 145 chords on the 11.4 mm clear aperture. Downward, the smallest robust envelope is 133 mm (14.9 m); below ~113 mm, nine 25.4 mm mirrors no longer pack. The architecture's map is therefore 20.4 m per standard build, 29.0 m per precision build, and 38.6 m per active alignment; larger-aperture mirrors are the identified route past all three."));

body.push(...fig("drone_25m_cell3d_paper.png",
  "The 176-chord long design (24.77 m in the same 180 mm envelope, 11 spots per mirror). At R = 0.999 the 32 additional reflections relative to the headline design cost only 2.8 % of signal, which is why the long-path corners are preferred when the build grade allows them.", 580));

body.push(H2("4.2 The headline design"));
body.push(P("The 20.38 m design uses sixteen CM254-150 mirrors (R = 300 mm) on a ring machined to R_ring = 72.155 mm (envelope 180 mm, inner height 16 mm, sampled volume 0.26 L). The beam enters at 11.25° mean incidence, completes 144 chords of mean 141.5 mm, deposits 9 spots on each mirror with a worst-pair separation of 0.99 mm against summed beam radii of ~0.64 mm, keeps 4.9 mm of aperture margin, and re-crosses the hole plane within 6 nm of the entrance point at the designed bounce; all eight intermediate visits to M0 clear the hole by at least 1.46 mm beyond the local beam radius. Mode matching sets a 0.326 mm waist 102 mm past the hole (radius at the hole 0.365 mm; hole transmission 100.0 %). Transmission is R¹⁴³ = 86.7 % at R = 0.999: a 10 mW DFB source delivers ≈8.7 mW to the detector, so the photon budget is not the limiting factor at any realistic coating."));

body.push(...fig("drone_20m_constellations_paper.png",
  "Per-mirror spot constellations of the headline design (ray-traced): each of the 16 mirrors carries the same 9-point pattern at a different phase origin; the worst pair over all mirrors is the verified fringe-safety quantity. M0 additionally shows the entrance/exit hole.", 560));
body.push(...fig("drone_20m_beam_evolution.png",
  "Tangential and sagittal 1/e² beam radii at each bounce under mode-matched injection: the beam rides the cell eigenmode at 0.21–0.42 mm for all 144 chords, an order of magnitude below the 11.4 mm clear aperture.", 520));
body.push(...fig("drone_20m_experiment_paper.png",
  "As-built rendering of the headline design: sixteen 25.4 mm mirrors in a one-piece machined ring; laser collimator, mode-matching lens and detector all mount behind M0, the exit beam leaving 22.5° from the injection axis.", 560));
body.push(...fig("throughput_vs_R.png",
  "Coating choice sets the photon budget: with the coupling hole rendered lossless by mode matching, transmission follows Eq. (6) for every design. Vertical guides mark conservative catalogue gold, typical protected gold, and enhanced/dielectric coatings.", 520));

// 4.3 drone budget
body.push(H2("4.3 Drone integration: mass and power budget"));
body.push(P("Table 2 gives a CAD-level mass estimate for the complete airborne sensor head. Mirror substrates are 25.4 mm × 6.35 mm glass (≈8 g each); the one-piece aluminium ring (14 mm radial section, pocketed) and two 1.5 mm lids dominate the optical-head mass and admit ~30 % lightweighting by skeletonising; injection optics comprise the fibre collimator, mode-matching lens and InGaAs photodiode on a common plate behind M0. With a compact DFB driver/DAQ stack the full payload is ≈1.0–1.2 kg, within the payload class of standard commercial multirotor platforms, and the 0.26 L sampled volume exchanges in well under a second at modest flow. Power is dominated by the laser TEC and electronics at a few watts; the cell itself is passive."));
body.push(...tbl(
  "Mass budget (CAD-level estimates, headline vs compact design).",
  ["item", "drone_20m (Ø180)", "drone_14cm (Ø141)"],
  [
    ["mirror substrates", "16 × 8 g = 128 g", "12 × 8 g = 96 g"],
    ["Al ring (pocketed) + lids", "≈ 450–600 g", "≈ 380–500 g"],
    ["injection optics + detector plate", "≈ 80 g", "≈ 80 g"],
    ["optical head subtotal", "≈ 0.66–0.81 kg", "≈ 0.56–0.68 kg"],
    ["DFB laser + driver + DAQ", "≈ 0.30–0.40 kg", "≈ 0.30–0.40 kg"],
    ["total payload", "≈ 1.0–1.2 kg", "≈ 0.9–1.1 kg"],
  ],
  [3200, 3100, 3060]));

// 5 Tolerances
body.push(H1("5. Tolerance and engineering analysis"));
body.push(P("Each design was subjected to Monte-Carlo trials with independent per-mirror perturbations at two build grades — research (tilt σ = 0.5 mrad per axis; decentre σ = 50 µm lateral, 100 µm axial; curvature σ = 1 mm; ring radius σ = 0.1 mm; launch σ = 50 µm and 0.5 mrad) and flight (0.1 mrad; 20/30 µm; 0.5 mm; 30 µm; 20 µm and 0.1 mrad). No trial of any tiered design clipped or lost the beam at its stated grade, and geometric quantities in Table 3 are coating-independent. One-at-a-time sensitivity identifies the dominant error source per design: mirror-pocket tilt for the R ≥ 300 mm designs (3.3 mrad of exit drift per 0.5 mrad tilt σ, curvature error negligible), and ring radius / curvature for compact short-ROC designs (tilt negligible). The one-piece machined ring, whose pocket angles are cut in a single CNC operation, targets precisely the dominant term. Demanding build-walk-sized clearances during the search itself measurably hardens the surviving designs — the headline design's worst-case Monte-Carlo spot separation grows 30 % — turning tolerance from a post-hoc filter into a design input."));
body.push(...tbl(
  "Monte-Carlo results at research-grade tolerances (mean ± σ; p95 in brackets).",
  ["metric", "drone_20m", "drone_25m", "drone_16cm"],
  [
    ["trials clipping / losing beam", "0/400", "0/300", "0/300"],
    ["OPL [m]", "20.35 ± 0.03", "24.74 ± 0.03", "20.61 ± 0.03"],
    ["exit pointing drift [mrad]", "4.2 ± 2.6 (9.4)", "5.0 ± 3.3 (11.2)", "38 ± 23 (89)"],
    ["spot-pattern walk p95 [mm]", "0.89", "1.43", "2.95"],
    ["hole clearance available [mm]", "1.46", "3.40", "1.65"],
  ],
  [2600, 1800, 1800, 1800]));
body.push(...fig("mc_hist.png",
  "Monte-Carlo distributions for the headline design at research-grade tolerances (400 trials): traversal count is invariant at 144; OPL and exit drift remain within operational bounds in every trial.", 560));
body.push(P("Systematic errors are compensated rather than tolerated. Catalogue mirrors carry a ±1 % focal-length tolerance, typically biased across a delivered lot; re-optimising only the ring radius restores the complete check matrix across the entire band with a strictly linear trim — 0.72 mm per percent of curvature error for the 180 mm designs, 0.62 mm for the compact one. The assembly rule is therefore: measure the delivered curvatures, machine the ring to the interpolated radius, walk in the final micrometres with the temperature trim. Temperature acts through the same mechanism (aluminium scales R_ring by 23.6 ppm/K against an essentially fixed glass curvature): with the launch frozen, the headline design passes every check over ±26 K on plain aluminium (±20 K for the 24.8 m design, ±8 K for short-ROC compact designs), an invar ring holds ≥±30 K for all, and a small ring heater doubles as the closure fine-adjustment actuator. All tiered designs also pass every check up to M² = 1.3, beyond typical fibre-coupled DFB sources."));
body.push(...tbl(
  "Systematic-error compensation and robustness.",
  ["design", "ROC ±1 % → ring trim", "thermal window (Al)", "thermal window (invar)", "M² tested"],
  [
    ["drone_20m", "±0.72 mm (linear)", "±26 K", "≥±30 K", "1.3 pass"],
    ["drone_25m", "±0.72 mm (linear)", "±20 K", "≥±30 K", "1.3 pass"],
    ["drone_16cm", "±0.62 mm (linear)", "±8 K", "≥±30 K", "1.3 pass"],
  ],
  [1700, 2300, 1800, 1900, 1660]));

// 6 Discussion
body.push(H1("6. Discussion"));
body.push(...tbl(
  "Position against published compact multipass cells (demonstrated values unless noted).",
  ["cell", "diameter", "OPL", "optics", "notes"],
  [
    ["Tuzson 2013 [1]", "~100 mm", "4.1 m", "monolithic diamond-turned", "first monolithic toroidal"],
    ["Graf 2018 [4]", "<200 g", "10 m", "segmented diamond-turned", "interference-free"],
    ["Chang 2020 [7]", "100 mm", "10 m (30 m theory)", "ring surface", "multi-layer patterns"],
    ["Dong 2016 [9]", "12 cm base", "54.6 m", "2 custom spherical", "densest; critical alignment"],
    ["this work, flight compact", "141 mm", "20.7 m", "12 × catalogue $74", "81.6 % T @0.999"],
    ["this work, headline", "180 mm", "20.4 m", "16 × catalogue $74", "86.7 % T @0.999"],
    ["this work, flight max", "183 mm", "29.0 m", "12 × catalogue $74", "76.6 % T @0.999"],
  ],
  [2100, 1500, 1500, 2200, 2060]));
body.push(P("Within the toroidal class the verified paths roughly double-to-triple the demonstrated state of the art at comparable diameter, using catalogue optics and a single machined part; the dense-pattern Herriott records [9, 10] remain denser but at custom-optics and alignment cost the one-piece ring eliminates. Three limitations bound the claims: the results are simulation-verified rather than experimentally demonstrated (the verification chain — exact tracing, independent cross-validation, Monte-Carlo tolerancing at stated build grades, systematic-error compensation — is designed to de-risk the build, and machining-level specification sheets accompany each design); coating reflectivity enters as an external parameter, quoted parametrically throughout; and surface-figure error and scatter are not yet modelled, meriting measurement on the assembled cell."));

// 7 Conclusion
body.push(H1("7. Conclusion"));
body.push(P("Chord-skip ring geometry, engineered dual-plane re-entrance tuned by the machined ring radius, an exact constellation criterion with build-walk-sized clearances, and mode-matched single-hole coupling together turn catalogue 1-inch mirrors into verified, tolerance-tiered 20–29 m multipass cells inside drone-compatible 133–183 mm envelopes, transmitting ~77–88 % at R = 0.999 on a ≈1 kg payload. Next steps: fabricate the headline design, measure transmission and fringe floor against the simulated budgets, and integrate a 1654 nm DFB source for airborne methane sensing."));

// References
body.push(H1("References"));
const refs = [
  "B. Tuzson, M. Mangold, H. Looser, A. Manninen, and L. Emmenegger, “Compact multipass optical cell for laser spectroscopy,” Opt. Lett. 38(3), 257–259 (2013).",
  "A. Manninen, B. Tuzson, H. Looser, Y. Bonetti, and L. Emmenegger, “Versatile multipass cell for laser spectroscopic trace gas analysis,” Appl. Phys. B 109, 461–466 (2012).",
  "M. Mangold, B. Tuzson, M. Hundt, J. Jágerská, H. Looser, and L. Emmenegger, “Circular paraboloid reflection cell for laser spectroscopic trace gas analysis,” J. Opt. Soc. Am. A 33(5), 913–919 (2016).",
  "M. Graf, L. Emmenegger, and B. Tuzson, “Compact, circular, and optically stable multipass cell for mobile laser absorption spectroscopy,” Opt. Lett. 43(11), 2434–2437 (2018).",
  "M. Graf et al., “Beam folding analysis and optimization of mask-enhanced toroidal multipass cells,” Opt. Lett. 42(16), 3137–3140 (2017).",
  "Z. Yang, Y. Guo, X. Ming, and L. Sun, “Generalized optical design of the double-row circular multi-pass cell,” Sensors 18(8), 2680 (2018).",
  "H. Chang, S. Feng, X. Qiu, H. Meng, G. Guo, et al., “Implementation of the toroidal absorption cell with multi-layer patterns by a single ring surface,” Opt. Lett. 45(21), 5897–5900 (2020).",
  "P. Amaro et al. (CREMA Collaboration), “Laser excitation of the 1S hyperfine transition in muonic hydrogen,” arXiv:2112.00138 (2021), and toroidal multipass-cavity development therein.",
  "L. Dong, C. Li, N. P. Sanchez, A. K. Gluszek, R. J. Griffin, and F. K. Tittel, “Compact CH4 sensor system based on a continuous-wave, low power consumption, room temperature interband cascade laser,” Appl. Phys. Lett. 108, 011106 (2016).",
  "K. Liu et al., “Highly sensitive detection of methane by near-infrared laser absorption spectroscopy using a compact dense-pattern multipass cell,” Sens. Actuators B: Chem. 220, 1000–1005 (2015).",
  "D. R. Herriott, H. Kogelnik, and R. Kompfner, “Off-axis paths in spherical mirror interferometers,” Appl. Opt. 3(4), 523–526 (1964).",
  "D. R. Herriott and H. J. Schulte, “Folded optical delay lines,” Appl. Opt. 4(8), 883–889 (1965).",
  "J. B. McManus, P. L. Kebabian, and M. S. Zahniser, “Astigmatic mirror multipass absorption cells for long-path-length spectroscopy,” Appl. Opt. 34(18), 3336–3348 (1995).",
  "Thorlabs Inc., CM254-xxx-M01 concave mirror series and fibre/TO-can collimation packages, product documentation (2026).",
  "H. Kramer, Optiland: open-source sequential ray tracing in Python, github.com/HarrisonKramer/optiland.",
];
refs.forEach((t, i) => body.push(new Paragraph({
  spacing: { after: 80 },
  indent: { left: 480, hanging: 480 },
  children: [R(`[${i + 1}] `, { size: 20 }), R(t, { size: 20 })],
})));

// ---------- document ----------------------------------------------------
const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: SZ } } } },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ font: FONT, size: 18, children: [PageNumber.CURRENT] })],
        })],
      }),
    },
    children: body,
  }],
});

Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(OUT, b);
  console.log("wrote", OUT, b.length, "bytes,", eqN, "equations,",
              figN, "figures,", tabN, "tables");
});
