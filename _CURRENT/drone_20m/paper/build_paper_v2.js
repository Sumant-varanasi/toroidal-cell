/* Build the TMPC drone-cell paper — REVISION v2 (post-review).
   Incorporates Dr. Benoy's review items: IRcell/literature comparison with
   overlap factor and OD-noise analysis, tri-gas operation (CH4/NH3/H2),
   disc-volume comparison, window selection, holed-mirror vs side entry,
   manufacturing / construction tolerance, author list.
   Run:  node build_paper_v2.js  ->  TMPC_drone_paper_v2.docx            */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, BorderStyle, WidthType, ShadingType, TabStopType,
  Footer, PageNumber,
} = require(require("child_process").execSync("npm root -g").toString().trim() + "/docx");

const FIG = path.resolve(__dirname, "..", "designs", "figures");
const OUT = path.join(__dirname, "TMPC_drone_paper_v2.docx");

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

// Title
body.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 160 },
  children: [R("Computational Design and Tolerance-Tiered Optimization of Chord-Skip Toroidal Multipass Cells for Airborne Methane Spectroscopy", { bold: true, size: 30 })],
}));

// Authors (per supervisor's instruction)
body.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 60 },
  children: [
    R("Sumant Varanasi", { size: 22 }), R("1,†", { size: 16, superScript: true }),
    R(", Thomas Benoy", { size: 22 }), R("2,†,*", { size: 16, superScript: true }),
    R(", Rob Lennox", { size: 22 }), R("3", { size: 16, superScript: true }),
    R(", Evgeny Rebrov", { size: 22 }), R("2", { size: 16, superScript: true }),
  ],
}));
body.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 40 },
  children: [R("1 Indian Institute of Technology Delhi – Abu Dhabi, Abu Dhabi, United Arab Emirates   2 University of Warwick, Coventry, United Kingdom   3 Eblana Photonics, Dublin, Ireland", { size: 18 })],
}));
body.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 240 },
  children: [R("† These authors contributed equally.   * Corresponding author.", { size: 18 })],
}));

// Abstract
body.push(H1("Abstract"));
body.push(P("Toroidal multipass cells fold long absorption paths into compact, mechanically robust volumes, but demonstrated designs reach at most ~10 m of optical path in the 100–200 mm diameter class — 15.1 m commercially — and rely on custom diamond-turned optics. We present a tolerance-tiered family of ring-geometry multipass cells built exclusively from catalogue 25.4 mm (and 12.7 mm) concave mirrors, verified by exact three-dimensional ray tracing with astigmatic Gaussian propagation, independently cross-validated to sub-micrometre agreement, and qualified by Monte-Carlo analysis with per-trial physical criteria. Three principles enable the result: a chord-skip ring geometry whose near-diameter chords deliver up to 146 mm of path per reflection at 7–13° incidence; an engineered dual-plane re-entrance condition tuned by the machined ring radius (≈1.2 rad of accumulated transverse phase per millimetre); and mode-matched injection through a single 1.3 mm coupling hole that renders hole losses negligible, so transmission equals R to the power (n−1). The verified passive-build ceiling of the architecture is 29.0 m at 76.6 % transmission (R = 0.999) in a Ø183 mm envelope — established as a boundary by three independent search campaigns — with 20.4 m robust at standard laboratory tolerances and 20.7 m in Ø141 mm at flight grade. Because the cavity eigenmode's Rayleigh range is wavelength-independent, designs port across gas lines by a √λ rescaling of the launch waist: the menu is re-verified at the NH3 line at 1512.2 nm (all designs robust) and at the H2 (1-0) S(1) quadrupole line at 2121.8 nm (six designs robust), and a walk-hardened 25.7 m design is Monte-Carlo robust at all three wavelengths. We further introduce a graded spot-overlap criterion — the worst Gaussian pair coupling over every mirror, 10⁻⁵–10⁻¹⁵ in power across the menu (−34 to −148 dB field) — which quantifies fringe immunity where the literature offers only a binary rule, and matters doubly for H2 because chord-scale parasitic etalons have free spectral ranges that coincide with the Dicke-narrowed line width. A half-inch-mirror family extends the menu to leak-sniffer scale (verified 9.1 m in Ø129 mm at 90.8 %, 75 mL sample volume; nominal 19.3 m in Ø93 mm at 37 mL, 4× the best commercial path-to-volume ratio); a two-inch family yields a tri-gas-robust 19.0 m cell at 86.0 % from only eight mirrors whose full path completes in every Monte-Carlo trial at every manufacturing grade including desktop polymer printing (4.5× the published printed-cell record, one alignment session required); and two-SKU rings that alternate catalogue curvatures unlock re-entrance conditions no single curvature can close, extending the verified nominal ceiling to 51.7 m in Ø180 mm. Tolerance is treated as a design input throughout, structured as the three-tier chain a build actually experiences: construction error as a capture-range check (recoverable by the one-time alignment), alignment residual, and post-alignment operational drift, which dominates deployment. Executing that chain gives every design an input-drift capture envelope (0.37–1.14 mm, 3.0–18.8 mrad — exceeding the summed drone-mount demand by 2.2–16× in position and 5.5–94× in angle), 5000-trial composed-drift Monte-Carlo yields against a 99.9 % drone criterion (met outright, 5000/5000, by the tri-gas flagship, the sparse 15.3 m and the two-inch 19.0 m designs on an aluminium-flexure mount), and a quantified low-cost route: a hybrid printed-shell/aluminium-cartridge build that saves 33–46 % of structure mass while plastic never defines an optical datum, carried best by the two-inch design at 95.0 % yield. Manufacturing-process-mapped Monte-Carlo shows which designs survive standard CNC, hybrid printed/machined and polymer-printed builds with no adjustment at all; wedged sapphire and fused-silica windows are selected for drone robustness; and polarization, vibration-to-signal and thermal budgets are quantified. The complete design set, machining-level specifications and CAD accompany the paper."));

// 1 Introduction
body.push(H1("1. Introduction"));
body.push(P("Tunable diode laser absorption spectroscopy (TDLAS) needs tens of metres of absorption path for trace-gas sensitivity, while drone deployment restricts the sensor head to roughly a 19 cm envelope and about a kilogram of payload. Three gases motivate this work: methane at 1653.7 nm (2ν3 R(3) triplet) for emission surveys, ammonia at 1512.2 nm (ν1+ν3) for agricultural and industrial monitoring, and molecular hydrogen at 2121.8 nm — the (1-0) S(1) electric-quadrupole line, five orders of magnitude weaker than the other two [23–25] — for leak detection in the emerging hydrogen economy, where percent-of-LEL sensitivity is operationally useful. Multipass cells reconcile path and packaging by folding the beam between mirrors. The classical two-mirror Herriott cell [11–13] achieves this with re-entrant elliptical patterns; its densest variants reach 54.6 m in a 12 cm-base astigmatic-type cell [9] and 26.4 m in a 12 cm dense-pattern cell [10], at the cost of custom mirror pairs and critical two-mirror alignment. Ring-geometry (toroidal/circular) cells trade some packing density for one-piece mechanical robustness: demonstrated paths are 2.2–4.1 m in the monolithic toroidal cell of Tuzson et al. [1, 2], >12 m in a 145 mm circular paraboloid [3], 10 m at <200 g in the segmented cell of Graf et al. [4] — the design basis of the commercial IRcell family [16], whose largest variant folds 15.1 m into a Ø194 mm disc — and 10 m (30 m theoretical) from multi-layer patterns on a 100 mm ring [7]; mask-based fringe suppression [5], double-row geometries [6], and cryogenic toroidal cavities [8] extend the family. Across this literature, demonstrated toroidal-class paths in drone-compatible envelopes cluster at or below ~10 m (15.1 m commercially), and every design relies on custom optics."));
body.push(P("This work asks a deliberately constrained question: how much verified optical path can a ring cell deliver inside a 190 mm envelope using only catalogue mirrors — Thorlabs CM254-series 25.4 mm concave mirrors (16 focal lengths, ≈US$74 each) and, for a low-volume variant, CM127-series 12.7 mm mirrors — with 9–16 mirrors, a single coupling hole, and a fibre-coupled DFB source? The chord-skip parameter is the entry point: near-diameter chords at near-normal incidence multiply the path per bounce. Our contributions are: (1) the chord-skip parametrisation with an engineered — rather than searched-for — re-entrance condition, tuned by the machined ring radius against catalogue-locked curvatures; (2) a graded, exactly computed spot-overlap criterion that turns the literature's binary 'spots must not overlap' rule [5, 7, 13, 22] into a quantitative fringe-immunity figure evaluated over every mirror; (3) mode-matched single-hole coupling that renders the hole lossless and, we show, is worth a factor equal to the spots-per-mirror count k = 9–19 relative to side coupling; (4) wavelength portability by construction, verified by Monte-Carlo re-qualification of the entire menu at the NH3 and H2 lines; (5) a tolerance-tiered design menu in which every design carries a Monte-Carlo robustness verdict at a stated build grade, and — new in this revision — a manufacturing-process-mapped construction-tolerance analysis, comparison with the commercial state of the art including gas volume and noise mechanisms, a two-SKU generalisation of the ring, and quantified polarization and vibration budgets. Machining-level specifications, STEP/STL CAD and the full simulation platform accompany every design."));

// 2 Architecture & theory
body.push(H1("2. Cell architecture and design principles"));
body.push(H2("2.1 Chord-skip ring geometry"));
body.push(P([R("N identical concave mirrors of curvature radius "), I("R"), R(" and clear-aperture radius 11.4 mm (5.7 mm for the half-inch family) face inward from a ring of radius "), I("R"), sub("ring"), R(", one every 360°/"), I("N"), R(". A beam injected through a hole in mirror M0 advances by "), I("s"), R(" mirrors per reflection (the chord skip, gcd("), I("N"), R(", "), I("s"), R(") = 1). Each chord length and the (identical) incidence angle on every mirror follow")]));
body.push(EQ([I("L"), R(" = 2 "), I("R"), sub("ring"), R(" sin(π"), I("s"), R("/"), I("N"), R("),   "), I("θ"), sub("i"), R(" = π/2 − π"), I("s"), R("/"), I("N"), R(".")]));
body.push(P([R("For "), I("s"), R(" ≈ "), I("N"), R("/2 the chords approach the ring diameter while "), I("θ"), sub("i"), R(" falls to 6–13°: a 74 mm-radius ring yields 146 mm of path per reflection — the geometric core of the result. The assembly envelope is 2("), I("R"), sub("ring"), R(" + 18 mm), the allowance covering substrate and housing wall (13 mm for the half-inch family).")]));
body.push(H2("2.2 Re-entrance: dual-plane phase closure"));
body.push(P([R("In the paraxial unit cell (one chord plus one mirror) the transverse ray oscillation advances per bounce by a phase "), I("θ"), R(" in each principal plane, split by the off-axis astigmatism:")]));
body.push(EQ([R("cos "), I("θ"), sub("t"), R(" = 1 − "), I("L"), R("/("), I("R"), R(" cos "), I("θ"), sub("i"), R("),   cos "), I("θ"), sub("s"), R(" = 1 − "), I("L"), R(" cos "), I("θ"), sub("i"), R(" /"), I("R"), R(",")]));
body.push(P([R("with per-plane stability requiring |cos "), I("θ"), R("| ≤ 1. The beam exits through the entrance hole after "), I("n"), R(" = "), I("kN"), R(" reflections when both accumulated phases return to their launch value; zero-crossing launches close at phase 0 or π, giving four closure-mode combinations per geometry:")]));
body.push(EQ([I("n θ"), sub("t,s"), R(" ≡ 0 or π  (mod 2π),   "), I("n"), R(" = "), I("kN"), R(".")]));
body.push(P([R("The single machinable parameter "), I("R"), sub("ring"), R(" moves both accumulated phases along a nearly fixed direction, at ≈1.2 rad per millimetre for the designs below, so a candidate is closable only if its signed phase residuals lie near that line; the residual is absorbed by the launch amplitudes through their weak aberration-mediated phase pull. Re-entrance thus becomes an engineered property: the ring is machined to the radius that closes the pattern for the delivered mirror lot, and the verified designs re-cross the hole centre to within 10⁻⁶–10⁻⁴ mm.")]));
body.push(H2("2.3 Constellation rule and the graded spot-overlap criterion"));
body.push(P([R("At closure the "), I("n"), R(" spots sample a Lissajous curve at the phase-snapped rates "), I("θ′"), R(" of Eq. (3); spot "), I("j"), R(" lands on mirror ("), I("js"), R(") mod "), I("N"), R(" at face coordinates")]));
body.push(EQ([I("u"), sub("j"), R(" = "), I("A"), sub("t"), R(" sin("), I("j θ′"), sub("t"), R("),   "), I("v"), sub("j"), R(" = "), I("A"), sub("s"), R(" {sin, cos}("), I("j θ′"), sub("s"), R(").")]));
body.push(P([R("Three exact geometric rules follow: the spots-per-mirror count "), I("k"), R(" must be odd (for even "), I("k"), R(" the tangential π-slot coincides with a sagittal near-return and a spot lands in the coupling hole); gcd("), I("M"), R(", "), I("k"), R(") = 1 in both planes with "), I("M"), R(" = round("), I("nθ"), R("/2π); and — decisive in practice — every mirror carries the same "), I("k"), R("-point pattern at a different phase origin along the curve, so the worst spot pair must be evaluated over all "), I("N"), R(" mirrors, not only the launch mirror, which overestimates usable separation by up to 3×.")]));
body.push(P([R("Because the dominant intra-cell fringe mechanism is scatter at one mirror spot coupling into the beam direction of a nearby spot [13, 20, 22], we quantify what the literature states only as a binary rule. For two Gaussian spots of radii "), I("w"), sub("i"), R(", "), I("w"), sub("j"), R(" separated by "), I("d"), R(" on a mirror, the field-amplitude coupling is")]));
body.push(EQ([I("η"), R(" = [2"), I("w"), sub("i"), I("w"), sub("j"), R("/("), I("w"), sub("i"), sup("2"), R(" + "), I("w"), sub("j"), sup("2"), R(")] · exp[−"), I("d"), sup("2"), R("/("), I("w"), sub("i"), sup("2"), R(" + "), I("w"), sub("j"), sup("2"), R(")],")]));
body.push(P([R("and the design metric is the maximum "), I("η"), R(" over every same-mirror pair of the full pattern. Every clearance is additionally padded by the expected build-error spot walk of the target build grade (§6), and self-crowding patterns are rejected before ray tracing. Spot-overlap fringes, the dominant practical noise source in this cell class [5, 7, 20], are thereby excluded by construction and by margin, not only by topology.")]));
body.push(H2("2.4 Mode-matched single-hole coupling"));
body.push(P([R("The cell eigenmode has a mirror-plane 1/e² radius per plane of")]));
body.push(EQ([I("w"), sub("m"), sup("2"), R(" = "), I("M"), sup("2"), I("λL"), R(" / (π sin "), I("θ"), R("),")]));
body.push(P([R("≈ 0.3–0.45 mm here. A 1.3 mm waist placed at the hole is badly mismatched to it; the beam then breathes to ~3× its injected size, spots overlap, and the hole clips 13.5 % of the power at entry and again at exit. Instead, the injection optics place the in-cell waist (0.20–0.33 mm) near mid-chord: the beam rides the eigenmode at 0.21–0.42 mm for the entire path, the radius at the hole is ~0.3–0.37 mm, and the 1.3 mm hole transmits ≈100 % both ways. Cell transmission is then exactly")]));
body.push(EQ([I("T"), R("("), I("R"), R(") = "), I("T"), sub("h"), sup("2"), R(" "), I("R"), sup("n−1"), R(" ≈ "), I("R"), sup("n−1"), R(",")]));
body.push(P([R("with "), I("T"), sub("h"), R(" ≈ 1 the hole transmission. At closure the round-trip ABCD map is the identity, so the exit beam reproduces the injected Gaussian and leaves through the same hole, separated from the input axis by 2"), I("θ"), sub("i"), R(" (22.5–22.7° for "), I("N"), R(" = 16), placing laser and detector side by side behind M0 with no beamsplitter.")]));
body.push(H2("2.5 Injection chain: source and collimator selection"));
body.push(P("The mode-matched launch is a finite-conjugate imaging task — relay the source mode to a 0.20–0.33 mm waist roughly 45–120 mm past the coupling hole — and the collimator choice follows from it. The baseline chain is a fibre-pigtailed DFB: the fibre mode (radius ≈ 5.5 µm) is imaged by a short-focal aspheric lens of the standard collimation-package type [14] operated slightly defocused, at magnification ≈ 60×. For the standard-build design an f ≈ 2 mm asphere places the 0.33 mm waist ≈ 120 mm from the lens — the exact conjugates, computed by the q-parameter design, are listed on each specification sheet — so a single catalogue lens in an adjustable FC/APC collimator body performs collimation and mode matching in one element, and its focus adjustment is the fine trim used during alignment. An attractive alternative first stage is a reflective (off-axis-paraboloid) fibre collimator: being achromatic and figure-stable it removes lens focal drift from the thermal budget of §6 and serves all three gas lines with one part. Direct free-space collimation of a TO-can device is the most compact option but is quantitatively limited: the best residual divergence of a collimated TO60 package is ≈0.8° full angle (≈7 mrad half-angle), whereas the cell eigenmode accepts λ/(πw₀) ≈ 1.6–2.6 mrad — a ≈4× mismatch, equivalent to an M² well beyond the verified 1.3 budget, costing ≥80 % of the light and destroying the spot-size guarantees. TO-can sources are therefore suitable only with additional spatial filtering (or for much shorter cells); the fibre-coupled variant is the design baseline."));
body.push(H2("2.6 Wavelength portability"));
body.push(P([R("The re-entrance closure, chord geometry, path length and throughput are properties of ray geometry and are wavelength-independent. The Gaussian mode also ports by construction: the cavity eigen-"), I("q"), R(" satisfies "), I("q"), R(" = ("), I("Aq"), R(" + "), I("B"), R(")/("), I("Cq"), R(" + "), I("D"), R("), whose solution fixes the Rayleigh range from the ABCD matrix alone, so every spot radius scales as")]));
body.push(EQ([I("w"), R("(λ₂) = "), I("w"), R("(λ₁) · ("), I("λ"), sub("2"), R("/"), I("λ"), sub("1"), R(")"), sup("1/2"), R(",   with unchanged waist positions.")]));
body.push(P("Re-qualifying a design at a new gas line therefore means rescaling the launch waist by √(λ₂/λ₁) — one turn of the collimator focus ring — and re-running the full check matrix and Monte-Carlo. Moving from 1653.7 nm to the H2 line at 2121.8 nm grows every spot by 13.3 % and is the qualifying case; the NH3 line at 1512.2 nm shrinks spots by 4.4 % and only adds margin. Protected-gold mirrors cover all three lines with one coating."));
body.push(H2("2.7 Two-SKU rings: a second closure knob"));
body.push(P([R("With even "), I("N"), R(" and odd "), I("s"), R(", the beam alternates between two mirror populations on every bounce, so a ring assembled from two catalogue curvatures ("), I("f"), sub("A"), R(", "), I("f"), sub("B"), R(" per plane) is a legal re-entrant system whose transverse phase advance per two bounces follows the alternating unit cell")]));
body.push(EQ([R("cos "), I("θ"), sub("2"), R(" = ½ tr[ "), I("M"), R("("), I("f"), sub("B"), R(") "), I("P"), R("("), I("L"), R(") "), I("M"), R("("), I("f"), sub("A"), R(") "), I("P"), R("("), I("L"), R(") ],")]));
body.push(P([R("which reduces exactly to cos 2"), I("θ"), R("₁ of Eq. (2) for "), I("f"), sub("A"), R(" = "), I("f"), sub("B"), R(". Closure at "), I("n"), R(" = "), I("kN"), R(" requires ("), I("n"), R("/2)"), I("θ"), sub("2"), R(" ≡ 0 (mod π) in both planes. The mixture ratio is a second closure knob: (N, s, k) combinations that no single catalogue curvature can close may close for a pair — §4.6 verifies one such design at 51.7 m.")]));

body.push(H2("2.8 The tolerance chain: construction, alignment, and operational drift"));
body.push(P("Mechanical error enters a multipass cell three times, and the three entries must be budgeted separately because they have different remedies. Construction tolerance — the as-built position and tilt error of every mirror seat — is largely recoverable by the one-time alignment every build performs, so its primary role is a capture-range check: the alignment chain must be able to steer the as-built pattern back to nominal. Alignment tolerance is the residual left after that session; it is set by adjuster resolution, feedback quality and operator skill, not by machining. Operational drift is the post-alignment motion under thermal expansion, vibration, pressure loading and thermal cycling — the error that cannot be aligned away and therefore dominates field and drone deployment. The in-use error vector is"));
body.push(EQ([I("T"), R(" = "), I("R"), sub("align"), R(" + "), I("D"), sub("op"), R(",   "), I("P"), sub("xy"), R(" = ("), I("dx"), sup("2"), R(" + "), I("dy"), sup("2"), R(")"), sup("1/2"), R(",   "), I("Θ"), sub("xy"), R(" = ("), I("dθ"), sub("x"), sup("2"), R(" + "), I("dθ"), sub("y"), sup("2"), R(")"), sup("1/2"), R(",")]));
body.push(P([R("with position and angle drift reported separately and combined only when checking physical clearance. The acceptance criterion for the whole chain is operational: under any input spot-position or input-angle drift inside the budget, the beam must still exit the coupling hole with positive clearance. We quantify each design's tolerance to that drift as its "), I("capture envelope"), R(" — the largest launch offset and launch tilt, per axis and sign, for which the full path completes, every intermediate pass clears the hole, and the exit spot still leaves wholly inside the hole rim (§6.3). A design is drone-qualified when its capture envelope contains the summed alignment-residual and operational-drift demand of the chosen mount architecture, and when Monte-Carlo sampling inside that demand box passes at product yield (>99.9 %).")]));

// 3 Methods
body.push(H1("3. Numerical methods"));
body.push(P("Designs were generated and verified with our open simulation platform: an exact 3-D ray tracer on toroidal/spherical surfaces (analytic normals, Newton-iterated intersections, per-bounce aperture tests), astigmatic Gaussian propagation via per-plane complex-q ABCD transfer with the actual per-bounce incidence angles, per-bounce mirror curvature (required for two-SKU rings) and an M² factor, loss budget, per-plane stability, and spot diagnostics. The search runs in two stages: Stage A enumerates the catalogue space (16 curvatures × N = 9–16 × coprime skips × a fine ring-radius grid × odd k up to 45) against packing, envelope, stability, closure-residual and constellation criteria, with all clearances sized for the expected build-error walk; Stage B ray-traces survivors, sweeps the ring radius in 20 µm steps to locate the ~20 µm-wide closure valley, and polishes six launch/geometry parameters by Nelder-Mead. The same harness runs at any wavelength and mirror family through environment parameters; two-SKU candidates use an analytic alternating-cell prescreen on a 2 µm ring-radius grid (the closure acceptance windows are ~5 µm wide and alias under coarser sampling) followed by the same exact refinement. A design is accepted only if the final trace passes all eight physical checks (exit through the hole at the designed bounce, no early hole leakage, aperture clearance, worst-pair spot separation over all mirrors, per-plane stability, packing, envelope, path-length floor). The tracer was cross-validated against the independent open-source ray tracer Optiland [15]: over 64 bounces the two agree to 0.000 µm RMS in spot position — for the methane-line designs and equally for the tri-gas design traced at 2121.8 nm."));
body.push(P("Robustness is a Monte-Carlo verdict, not a nominal margin: 100–400 trials per design with independent per-mirror perturbations at a stated build grade, and per-trial physical criteria — the full path completes, spots never merge (the simulator's own minimum-separation and overlap flags), intermediate spots keep clearing the coupling hole, and the exit still leaves the 1.3 mm hole with no realignment. Manufacturing processes are mapped onto the same machinery (§6.4) by converting published process capabilities into tolerance grades (seat flatness over the 25.4 mm pocket → mirror tilt σ; positional accuracy → decentre; radial accuracy → ring radius), so 'will the cell survive construction tolerance' is answered by the same exact-trace Monte-Carlo as alignment tolerance."));

body.push(...fig("drone_20m_cell3d_paper.png",
  "Exact traced beam path of the 20.4 m standard-build design: 16 catalogue mirrors on a 72.155 mm ring, 144 chords, coloured by bounce order; the input beam (green) enters through the 1.3 mm hole in M0 and the closed pattern exits through the same hole.", 580));

// 4 Results
body.push(H1("4. Results"));
body.push(H2("4.1 The tolerance-tiered design menu"));
body.push(...tbl(
  "Tolerance-tiered design menu (1-inch family). Every row passes the full check matrix in the exact ray trace; the robustness tier is a 100-trial Monte-Carlo verdict at the stated build grade with per-trial physical criteria. Transmission T = R^(chords−1) exactly (hole losses ≈ 0), quoted at the project mirrors' R = 0.999. Gases column: verified Monte-Carlo-robust wavelengths (C = CH4 1653.7 nm, A = NH3 1512.2 nm, H = H2 2121.8 nm).",
  ["design", "mirrors", "chords", "OPL [m]", "T @0.999", "envelope [mm]", "robust at", "gases"],
  [
    ["mixed two-SKU (§4.6)", "6+6 × CM254-250/375", "372", "51.66", "69.0 %", "180", "active align.", "C, A"],
    ["geometric ceiling", "14 × CM254-100 (R 200)", "322", "38.60", "72.5 %", "169", "active align.", "C, A"],
    ["flight max OPL", "12 × CM254-750 (R 1500)", "204", "28.99", "76.6 %", "183", "flight build", "C, A"],
    ["tri-gas flagship", "16 × CM254-200 (R 400)", "176", "25.72", "83.9 %", "185", "flight build", "C, A, H"],
    ["long", "16 × CM254-200 (R 400)", "176", "24.77", "83.9 %", "180", "flight build", "C, A"],
    ["H2-optimised", "16 × CM254-200 (R 400)", "176", "23.83", "83.9 %", "174", "flight build", "C, A, H"],
    ["flight compact", "12 × CM254-500 (R 1000)", "204", "20.66", "81.6 %", "141", "flight build", "C, A, H"],
    ["two-inch long", "8 × CM508-150 (R 300)", "152", "19.04", "86.0 %", "182", "flight build", "C, A, H"],
    ["standard-build corner", "16 × CM254-150 (R 300)", "144", "20.38", "86.7 %", "180", "standard build", "C, A, H"],
    ["balanced", "13 × CM254-150 (R 300)", "143", "16.60", "86.8 %", "160", "flight build", "C, A, H"],
    ["sparse high-T", "16 × CM254-100 (R 200)", "112", "15.30", "89.5 %", "175", "flight build", "C, A, H"],
    ["small", "10 × CM254-150 (R 300)", "190", "14.85", "82.8 %", "133", "flight build", "C, A, H"],
    ["small max-T", "12 × CM254-250 (R 500)", "132", "13.64", "87.7 %", "143", "flight build", "C, A, H"],
    ["two-inch high-T", "7 × CM508-500 (R 1000)", "105", "11.61", "90.1 %", "187", "flight build", "C, A, H"],
  ],
  [1620, 2080, 660, 760, 800, 950, 1150, 850]));
body.push(...fig("menu_pareto.png",
  "The verified design menu as an envelope–path map (marker colour = transmission at R = 0.999). The Pareto frontier is populated entirely by catalogue-mirror designs; the dashed line marks the ~10 m demonstrated record of published toroidal cells in this size class.", 540));
body.push(H2("4.2 The passive-build boundary"));
body.push(P("The mirrors used in this project provide R = 0.999, so the photon budget admits ~700 reflections before transmission falls below 50 % and the real limit is spot-pattern geometry under build error. The tier boundaries are therefore the key quantitative result, and we established them as boundaries: three independent search campaigns with build-walk clearance demands of 0.55, 0.6 and 0.8 mm converge on the same frontier. At standard laboratory tolerances (kinematic mounts, 0.5 mrad tilt class) the ceiling is 20.4 m: denser constellations lose spot identity as relative spot motion of 0.3–0.5 mm collapses their separation margins. At flight-grade tolerances (glued/welded, 0.1 mrad — the construction class a vibrating airframe requires regardless) the ceiling is 29.0 m. Between 29 and 38.6 m, closures exist and complete 100 % of Monte-Carlo paths, but their 209–322-chord patterns walk into each other (the 38.6 m design's 5th-percentile worst-pair separation falls to 0.23 mm at flight grade against a ~0.57 mm pair width); because pattern walk grows roughly as the square root of the chord count, the standard-tolerance ceiling sits near 145 chords on the 11.4 mm aperture and the flight ceiling near 210. Beyond the passive boundary, the verified route is closed-loop trim (§6.6): the 38.6 m uniform and 51.7 m two-SKU designs are exact-trace feasible and complete their paths at flight tolerances, requiring active recovery only of the coherent pattern walk — approximately 1–3 mm — with two catalogue actuators. Downward, the smallest robust 1-inch envelope is Ø133 mm; below ~Ø113 mm, nine 25.4 mm mirrors no longer pack (the half-inch family of §4.5 continues the menu to Ø93)."));
body.push(H2("4.3 Representative designs"));
body.push(P("The 20.38 m standard-build design (16 × CM254-150, R_ring = 72.155 mm, Ø180) enters at 11.25° incidence, completes 144 chords of mean 141.5 mm, deposits 9 spots per mirror with a worst pair 3.5 beam radii apart, and re-crosses the hole plane within 6 nm of the entrance point; all intermediate M0 visits clear the hole by ≥1.46 mm beyond the local beam radius. Mode matching sets a 0.326 mm waist 102 mm past the hole (0.365 mm at the hole; hole transmission 100.0 %); transmission is R¹⁴³ = 86.7 %, so a 10 mW DFB delivers ≈8.7 mW to the detector. The tri-gas flagship (16 × CM254-200 on a 74.507 mm ring, Ø185) delivers 25.72 m over 176 chords at 83.9 %: its walk-hardened constellation (worst pair 5.4 beam radii; separation margin 1.10 mm; hole margin 0.86 mm) is what carries Monte-Carlo robustness at all three gas lines. The H2-optimised variant of the same family closes on a 2.7 mm smaller ring (23.83 m, Ø174) with margins sized at 2121.8 nm, and was Optiland-cross-validated at that wavelength to 0.000 µm RMS."));
body.push(...fig("drone_26m_cell3d_paper.png",
  "The tri-gas flagship: 176 chords (25.72 m) between sixteen CM254-200 mirrors on a 74.507 mm ring. Its walk-hardened spot constellation is Monte-Carlo robust as-built at the CH4, NH3 and H2 lines — the tri-gas ceiling of the architecture, confirmed independently by a search run natively at 2121.8 nm.", 580));
body.push(...fig("drone_20m_constellations_paper.png",
  "Per-mirror spot constellations of the standard-build design (ray-traced): each of the 16 mirrors carries the same 9-point pattern at a different phase origin; the worst pair over all mirrors is the verified fringe-safety quantity. M0 additionally shows the entrance/exit hole.", 560));
body.push(...fig("drone_20m_beam_evolution.png",
  "Tangential and sagittal 1/e² beam radii at each bounce under mode-matched injection: the beam rides the cell eigenmode at 0.21–0.42 mm for all 144 chords, an order of magnitude below the 11.4 mm clear aperture.", 520));
body.push(...fig("drone_20m_experiment_paper.png",
  "As-built rendering: mirrors in a one-piece machined ring; laser collimator, mode-matching lens and detector all mount behind M0, the exit beam leaving at twice the incidence angle from the injection axis.", 560));
body.push(...fig("throughput_vs_R.png",
  "Coating choice sets the photon budget: with the coupling hole rendered lossless by mode matching, transmission follows Eq. (6) for every design. Vertical guides mark conservative catalogue gold, typical protected gold, and enhanced/dielectric coatings.", 520));

body.push(H2("4.4 Tri-gas operation: NH3 and H2"));
body.push(P("Following Eq. (7), the entire menu was re-qualified at 1512.2 nm and 2121.8 nm: the launch waist was rescaled, the full check matrix re-run, and the Monte-Carlo verdict re-issued at each design's build grade. At the NH3 line every design remains robust as-built. At the H2 line — spots 13.3 % larger — six designs remain robust, including both 20 m-class cells and the 25.72 m flagship; the 29.0 m and 24.8 m designs lose their separation margins, so the tri-gas ceiling is 25.72 m (Fig. 8). One hardware build therefore serves all three gases: the gold mirrors and the cell are common, and each gas channel swaps the DFB source, the detector and (for H2) the window coating."));
body.push(...fig("trigas_matrix.png",
  "Monte-Carlo robustness (as-built, flight grade) of the menu at the three gas lines. Spot sizes scale as √λ, so the H2 line at 2121.8 nm is the qualifying case; the walk-hardened designs carry their margins across all three wavelengths.", 480));
body.push(...fig("drone_24m_h2_cell3d_paper.png",
  "The H2-optimised design traced at 2121.8 nm (176 chords, 23.83 m, Ø174): the same mirror family as the flagship re-closed on a smaller ring with H2-sized margins; 400-trial flight-grade Monte-Carlo completes 176/176 chords in every trial.", 560));
body.push(...tbl(
  "Line data (HITRAN2020 [25]) and projected detection limits. Peak absorbance is base-e at 296 K, 1 atm; detection limits are 1σ for the 20.4 m standard-build cell at two noise-equivalent-absorbance (NEA) levels. Note the 1653.7 nm methane feature is the 2ν3 R(3) triplet (R(4) lies at 1651.0 nm).",
  ["gas / line", "λ [nm]", "S [cm/molec]", "abs. per ppm·m", "LOD @ NEA 10⁻⁴", "LOD @ NEA 10⁻⁶"],
  [
    ["CH4 2ν3 R(3) triplet", "1653.73", "3.16×10⁻²¹", "3.8×10⁻⁵", "129 ppb", "1.3 ppb"],
    ["NH3 ν1+ν3 multiplet", "1512.24", "2.26×10⁻²¹ (5.5×10⁻²¹ blended)", "5.3×10⁻⁵", "92 ppb", "0.9 ppb"],
    ["H2 (1-0) S(1) quadrupole", "2121.83", "3.19×10⁻²⁶", "1.6–2.9×10⁻⁹", "0.17–0.31 %v", "17–31 ppm"],
  ],
  [2350, 900, 1850, 1450, 1400, 1400]));
body.push(P("The H2 row deserves its honest reading: the quadrupole line is ~10⁵ weaker than the others, and the best published direct-absorption result is 12 ppmv at 1 s over 11.4 m at NEA ≈ 3×10⁻⁷ [24]; with 20–26 m and a 10⁻⁴ fringe-limited floor the cell delivers 0.15–0.3 %v — already ≈5 % of the lower explosive limit, an operationally useful leak alarm — and tens of ppm with wavelength-modulation spectroscopy at 10⁻⁶ [23]. The line is also sub-Doppler at 1 atm (Dicke-narrowed to ≈0.026–0.04 cm⁻¹ FWHM [23]), which couples directly to the cell design: a parasitic etalon between two mirrors one chord apart has a free spectral range 1/(2L) = 0.034–0.064 cm⁻¹ across the menu — squarely on the H2 line width, where it distorts the line shape rather than the baseline and cannot be fitted out. Chord-scale parasites must therefore be suppressed at the source, which is precisely what the graded overlap criterion of Eq. (5) does (worst-pair power coupling 10⁻⁵–10⁻¹⁵ across the menu, before multiplying by the mirror scatter fraction); window etalons (FSR ≈ 1 cm⁻¹) and full-pattern parasites (FSR < 0.001 cm⁻¹) land far from the line and behave as fittable baseline. Sources and detectors are catalogue items for all three channels (fibre-coupled DFBs at 1512/1654 nm; 2122 nm DFBs from at least two vendors; standard InGaAs below 1.7 µm, extended-InGaAs with a short-focal collection lens for H2)."));

body.push(H2("4.5 The low-volume half-inch family"));
body.push(P("Because 'toroidal cells are low-volume cells' is their core application claim, the same search machinery was run on the catalogue half-inch family (CM127-series, 5.7 mm clear-aperture radius, ≈US$50) over Ø90–130 mm envelopes. Spot radii do not shrink with the mirror — Eq. (5)'s w is set by chord length and curvature — so the halved aperture crowds patterns roughly four times harder and the robust designs are all sparse (k = 5–7). The verified menu: 7.54 m in Ø122 mm with 40 mL of beam-limited sample volume (189 m/L, the best verified path-to-volume ratio in this work); and, with a 0.8 mm coupling hole and correspondingly smaller collimator — the project-standard 1.3 mm hole occupies a third of the half-inch aperture and is the binding constraint — 9.11 m in Ø129 mm at 90.8 % transmission and 75 mL, robust as-built at flight grade (99.0 % completion over 400 trials). The nominal showcase is 19.31 m in a Ø93 mm disc at 37 mL — a path-to-volume ratio of 518 m/L, four times the best commercial figure — at active-alignment tier. Pumped gas exchange is 1–9 s at 0.5–2 SLM; run as an open flow-through ring the cell clears in ~25 ms of flight at 5 m/s."));
body.push(...tbl(
  "Low-volume half-inch menu against the commercial small cell (IRcell-S4 values from the manufacturer datasheet [16]).",
  ["cell", "OPL", "envelope", "gas volume", "path/volume", "T", "tier"],
  [
    ["IRcell-S4 (commercial)", "4.03 m", "Ø106×32", "31 mL", "130 m/L", "n.p.", "product"],
    ["this work, Ø122", "7.54 m", "Ø122×18", "40 mL", "189 m/L", "≥55 %*", "flight build"],
    ["this work, mini (0.8 mm hole)", "9.11 m", "Ø129×18", "75 mL", "121 m/L", "90.8 %", "flight build"],
    ["this work, showcase", "19.31 m", "Ø93×19", "37 mL", "518 m/L", "64.7 %", "active align."],
  ],
  [2560, 900, 1100, 1050, 1100, 800, 1300]));
body.push(P("(*the as-searched launch of the Ø122 design carries an exit-truncation loss; a mode-matched relaunch recovers most of the R^(n−1) = 92 % geometric value.)"));

body.push(H2("4.6 A verified two-SKU design"));
body.push(P("Applying the alternating-cell prescreen of Eq. (9) to nine catalogue curvature pairs on N ∈ {12, 14, 16} produced dozens of exact closures (exit miss 0.000–0.01 mm with positive hole clearance) at nominal paths of 30–69 m — far beyond the uniform ceiling — of which several, including the four longest, exist for neither constituent curvature alone. Spot crowding on the 1-inch aperture eliminates all but one after separation-aware re-optimisation: alternating six CM254-250 with six CM254-375 mirrors on a 71.928 mm ring closes a k = 31 pattern of 372 chords for 51.66 m in a Ø180 envelope at 69.0 % transmission (exit miss 2.3 µm; hole clearance +2.46 mm; worst-pair separation +0.03 mm). The uniform counterfactual was checked explicitly: neither ROC 500 nor ROC 750 closes k = 31 anywhere in the ring-radius window. With its hair-thin separation margin this is an active-alignment design for the CH4/NH3 lines, and on 1-inch apertures it is a singular feasible point rather than a family; its significance is architectural — the two-SKU degree of freedom extends the verified nominal ceiling of the catalogue-parts architecture by 34 %, and larger apertures or margin-aware mixed search are the identified route to making such designs robust."));
body.push(...tbl(
  "The verified two-SKU design.",
  ["parameter", "value"],
  [
    ["ring", "N = 12, skip 5, R_ring = 71.928 mm, envelope Ø180"],
    ["mirrors", "alternating CM254-250-M01 (R 500) / CM254-375-M01 (R 750), 6 + 6"],
    ["pattern", "k = 31 spots per mirror, 372 chords, OPL 51.66 m"],
    ["transmission", "69.0 % at R = 0.999 (T = R³⁷¹)"],
    ["checks", "exit miss 2.3 µm; hole clearance +2.46 mm; worst-pair separation +0.03 mm"],
    ["closure counterfactual", "k = 31 does not close for either curvature alone (analytic scan, ±2 mm window)"],
  ],
  [2300, 6700]));

body.push(H2("4.7 The two-inch variant and the printability boundary"));
body.push(P("Under the same Ø190 envelope, 50.8 mm CM508-series mirrors pack only at N = 7–8, and two designs are Monte-Carlo robust as-built at flight grade and at all three gas lines: 19.04 m at 86.0 % from eight mirrors (Ø182; hole clearance 3.4 mm, aperture margin 10.3 mm) and 11.61 m at 90.1 % from seven (Ø187). The 19 m design is the most practical cell in the menu on a parts basis — eight pockets to machine and ≈US$1.1k of optics for drone_20m-class performance — and its doubled aperture converts directly into build robustness: it is the only design whose full 152-chord path completes in 100 % of Monte-Carlo trials at every manufacturing grade mapped in §6.4, desktop FDM included. The honest qualifier is that at printed grades the spot bookkeeping still degrades (occasional pair merging; the exit needs the standard one-time trim), so a printed build is a '19 m that reliably folds, one alignment required' demonstrator — against a published printed-multipass record of 4.2 m — while the flight instrument remains CNC aluminium. In the other direction the two-inch family does not extend the OPL ceiling inside this envelope: beating 29 m at N = 7–8 requires k ≥ 21 patterns at transverse amplitudes where the paraxial prescreen no longer locates the micrometre-wide closure valleys; larger apertures win outright only when the envelope itself is relaxed."));

// 5 Comparison
body.push(H1("5. Comparison with published and commercial cells"));
body.push(H2("5.1 Path, volume and architecture"));
body.push(P("The closest commercial comparator is the IRcell family [16], both generations of which descend from the Empa lineage: the original IRcell is a true toroid — one continuous diamond-turned gold ring whose concentric geometry is optically unstable, so beam components superpose and a patented absorption mask truncates the beam at every reflection to suppress fringes [3, 5] — while the second-generation IRcell-S implements the segmented circular cell of Graf et al. [4] with 65 individually curved confocal segments, one spot per segment, and no mask. Table 5 places this work against the family and the published record. In headline terms: the largest commercial cell folds 15.12 m into a Ø194 mm disc with 128 mL of sample volume; our flagship folds 25.72 m into Ø185 (and 20.66 m into Ø141) using catalogue mirrors, at a verified 83.9 % transmission where no laser-coupled commercial figure is published. The honest downside is sealed sample volume: near-diameter chords sweep the whole disc, so our beam-limited chambers hold 117–331 mL against the IRcell-S's 31–128 mL. Per litre, the menu spans 70–189 m/L — at parity with the published toroidal family (70–132 m/L) — while carrying two to five times the absolute path, and the half-inch showcase reaches 518 m/L. For drone leak detection, low volume serves response time, and there the architecture's open-ring option (slotted lids, as the commercial cell also offers) gives millisecond exchange in flight."));
body.push(...fig("volume_pvr_comparison.png",
  "Optical path against gas sample volume for this work (stars; beam-limited chamber volumes) and the published/commercial circular and toroidal cells (grey; manufacturer and literature values). Diagonal guides are constant path-to-volume ratio.", 560));
body.push(...tbl(
  "Position against published and commercial compact multipass cells (demonstrated/datasheet values).",
  ["cell", "envelope", "OPL", "volume", "optics", "notes"],
  [
    ["Tuzson 2013 toroid [1]", "Ø~100 mm", "2.2–4.1 m", "40 mL", "monolithic diamond-turned", "unstable; needs mask [5]"],
    ["Graf 2018 segmented [4]", "Ø~155 mm", "9.89 m", "140 mL", "65 diamond-turned segments", "<200 g; basis of IRcell-S"],
    ["IRcell-S15 (commercial) [16]", "Ø194 mm", "15.12 m", "128 mL", "custom monolith", "fringe spec <2×10⁻⁴ rms"],
    ["Chang 2020 multi-layer [7]", "Ø~100 mm", "10 m (30 m theory)", "94 mL", "ring surface + mask", "fringe <0.5 % with mask"],
    ["Dong 2016 Herriott [9]", "12 cm base", "54.6 m", "—", "2 custom spherical", "densest; critical alignment"],
    ["this work, flight compact", "Ø141 mm", "20.66 m", "200 mL", "12 × catalogue", "robust as-built, tri-gas"],
    ["this work, tri-gas flagship", "Ø185 mm", "25.72 m", "247 mL", "16 × catalogue", "robust at all three lines"],
    ["this work, flight max", "Ø183 mm", "28.99 m", "331 mL", "12 × catalogue", "robust as-built (CH4/NH3)"],
    ["this work, two-SKU", "Ø180 mm", "51.66 m", "~310 mL", "6+6 × catalogue", "active tier; nominal ceiling"],
  ],
  [2150, 1000, 1100, 850, 1900, 2360]));
body.push(H2("5.2 Overlap factor and the optical-density noise budget"));
body.push(P("Whether a dense pattern buys noise is the decisive question for any multipass cell, and we answer it mechanism by mechanism rather than by assertion. The dominant intra-cell fringe source in this cell class is scatter at one mirror spot coupling into the beam direction of a nearby spot: the mechanism is stated explicitly in the astigmatic-Herriott literature [13, 22], and was measured directly at JPL, where the dominant fringe of a flight Herriott cell was traced to 'scattering between neighboring spots in the circulation pattern' [20]. 'Overlap factor' is not a standardised multipass figure of merit, so we report the graded quantity of Eq. (5) computed exactly over every same-mirror pair of every design (Fig. 11): worst pairs sit 2.8–5.8 beam radii apart, i.e. field couplings of −34 to −148 dB before multiplying by the gold scatter fraction (Å-class roughness contributes ~10⁻⁵ per bounce). Our beams do not overlap — and unlike the binary rule, the margin is a number that survives Monte-Carlo build error. For reference, the original toroidal IRcell superposes beam components by construction (its absorption mask exists for that reason), and the segmented IRcell-S sizes its facets at ≈3.45 beam radii — comparable to our worst designs and below our hardened ones. Beam crossings in the cell volume (thousands per pattern, at 0.2–60°) exchange no energy in a linear medium and produce fringe periods of 2.4–9.5 µm at the detector-relevant angles — hundreds of periods across any detector, integrating to zero. The remaining fringe channels are engineered: the coupling hole keeps ≥2× the beam diameter clear (the hole-clipping criterion of [13]); windows are wedged and tilted (§6.5); and diamond-turning tool-mark scatter — the residual fringe source identified on the segmented cell [4] — is absent from polished catalogue substrates. On this budget the expected noise floor is in the class of the segmented cell (NEA ≈ 2×10⁻⁵ short-term; 5.8×10⁻⁶ absorption noise demonstrated on a drone [19]) and clearly below masked toroids; we state it as an expectation with mechanisms and margins, and leave the measured floor to the build."));
body.push(...fig("overlap_coupling.png",
  "The graded spot-overlap criterion: every same-mirror spot pair of every menu design (dots) and each design's worst pair (stars) against the equal-width Gaussian coupling curve of Eq. (5). All designs sit at or beyond the segment-edge margin of the commercial segmented cell; continuous-fold toroids occupy the shaded region by construction, which is why they require absorption masks.", 560));
body.push(H2("5.3 Coupling through a holed mirror versus side entry"));
body.push(P("Ring cells in the literature couple through openings in the mirror ring [4, 16]; a fair question is why this work drills a catalogue mirror instead. The answer is a factor the architecture cannot otherwise access: in a chord-skip ring the pattern revisits the entrance mirror's azimuth every N chords but at a different transverse point each time — that is the k-spot constellation — so the coupling aperture must select by transverse position, which only a hole in the mirror face does. A side slot (gap between mirrors, scraper edge, or an opening in the ring) selects only by azimuth: the beam escapes at its first azimuthal return, capping the cell at N chords regardless of pattern. Side entry would deliver 2.3 m from the Ø180 ring that delivers 20.4–25.7 m through the hole — the hole is worth exactly k = 9–19×. The physical gaps between our mirror edges (1.7–12.7 mm) would admit a beam without any drilling; the objection is optical, not mechanical. Single-orbit ring cells with k = 1 are the converse case: nothing exists for a hole to select, so side coupling is correct there — the commercial segmented cell couples through two 5 mm ring apertures for exactly that reason. Practically, one drilled mirror (a 2.6 mm bore, countersunk from the rear) is the only custom part in the assembly; entrance and exit share it, so one wedged window and one detector serve the sealed cell, and intermediate visits clear the bore by Monte-Carlo-verified margins, bounding edge scatter below the e⁻⁸ Gaussian tail."));

// 6 Engineering
body.push(H1("6. Tolerance and engineering analysis"));
body.push(H2("6.1 Monte-Carlo robustness"));
body.push(P("Each design was subjected to Monte-Carlo trials with independent per-mirror perturbations at two build grades — research (tilt σ = 0.5 mrad per axis; decentre σ = 50 µm lateral, 100 µm axial; curvature σ = 1 mm; ring radius σ = 0.1 mm; launch σ = 50 µm and 0.5 mrad) and flight (0.1 mrad; 20/30 µm; 0.5 mm; 30 µm; 20 µm and 0.1 mrad). Table 6 reports 400-trial statistics for the round's headline designs; no trial of any tiered design clips or loses the beam at its stated grade. One-at-a-time sensitivity identifies the dominant error source per design — mirror-pocket tilt for long-curvature designs, ring radius and curvature error for compact short-curvature ones — and the one-piece machined ring, whose pocket angles are cut in a single CNC operation, targets precisely that term. Demanding build-walk-sized clearances during the search itself measurably hardens the surviving designs; it is why the flagship carries its margins across all three gas lines. These are as-built verdicts at a stated grade; §6.3 extends them to the full tolerance chain of §2.8 — capture envelopes, composed alignment-plus-drift Monte-Carlo at product yield, and coherent worst-case sweeps — and §6.4 to manufacturing processes."));
body.push(...tbl(
  "400-trial Monte-Carlo at flight-grade tolerances (as-built; no realignment).",
  ["metric", "tri-gas 25.7 m", "H2-opt. 23.8 m (at 2122 nm)", "sparse 15.3 m", "mini 9.1 m (½″)"],
  [
    ["full-path completion", "400/400", "400/400", "400/400", "396/400"],
    ["spot-walk p95 [mm]", "0.36", "0.45", "0.37", "0.53"],
    ["min separation p05 [mm]", "1.23", "—", "1.29", "0.54"],
    ["hole clearance p05 [mm]", "0.49", "—", "1.22", "0.35"],
    ["exit drift p95 [mrad]", "2.8", "3.6", "4.3", "15.3"],
  ],
  [2100, 1750, 2100, 1550, 1560]));
body.push(...fig("mc_hist.png",
  "Monte-Carlo distributions for the standard-build design at research-grade tolerances (400 trials): traversal count is invariant at 144; OPL and exit drift remain within operational bounds in every trial.", 540));
body.push(H2("6.2 Systematic errors: compensation rather than tolerance"));
body.push(P("Catalogue mirrors carry a ±1 % focal-length tolerance, typically biased across a delivered lot; re-optimising only the ring radius restores the complete check matrix across the entire band with a strictly linear trim. Temperature acts through the same mechanism (aluminium scales R_ring by 23.6 ppm/K against an essentially fixed glass curvature), so a small ring heater doubles as the closure fine-adjustment actuator — and as an anti-condensation measure in flight. All tiered designs pass every check to M² = 1.3, beyond typical fibre-coupled DFB sources."));
body.push(...tbl(
  "Systematic-error compensation and robustness (launch frozen; full check matrix must re-pass).",
  ["design", "ROC ±1 % → ring trim", "thermal window (Al)", "thermal window (invar)", "M² tested"],
  [
    ["standard 20.4 m", "±0.72 mm (linear)", "±26 K", "≥±30 K", "1.3 pass"],
    ["tri-gas 25.7 m", "±0.75 mm (linear)", "±18 K", "≥±30 K", "1.3 pass"],
    ["long 24.8 m", "±0.72 mm (linear)", "±20 K", "≥±30 K", "1.3 pass"],
    ["compact 20.7 m", "±0.62 mm (linear)", "±8 K", "≥±30 K", "1.3 pass"],
    ["mini 9.1 m (½″)", "±0.52 mm (linear)", "±30 K", "≥±30 K", "1.3 pass"],
  ],
  [1700, 2300, 1800, 1900, 1660]));
body.push(H2("6.3 Capture envelopes and drone yield under the composed drift model"));
body.push(P("The acceptance criterion of §2.8 was executed for every menu design by per-axis bisection: the largest launch position offset and launch tilt, each sign, for which the full path still completes, every intermediate pass clears the hole, and the exit leaves wholly inside the hole rim. The resulting capture envelopes (Table 8, Fig. 13) span 0.37–1.14 mm in position and 3.0–18.8 mrad in angle. Two structural facts emerge. First, angle capture exceeds the drone demand by one to two orders of magnitude in every design: launch tilt deforms the re-entrant Lissajous pattern slowly, while position drift translates it toward the hole rim roughly one-to-one, so position capture — which tracks each design's exit-hole clearance, as the acceptance model predicts — is always the binding axis. Second, even the smallest envelope in the menu contains the summed alignment-residual and operational-drift demand of both drone mount architectures with at least 2.2× position and 5.5× angle margin: as-built error inside the capture box is recoverable by one alignment session, and post-alignment drone drift never walks the exit out of the hole."));
body.push(...tbl(
  "Input-drift capture envelopes per design (bisection to the exit-clearance boundary), against the summed alignment-residual + drone operational-drift demand of two mount architectures: aluminium isostatic flexure (easy-regime residual 0.02 mm / 0.05 mrad + drift 0.05 mm / 0.15 mrad) and hybrid plastic body + aluminium mirror cartridge (medium residual 0.05 / 0.15 + drift 0.12 / 0.40).",
  ["design", "P_cap [mm]", "Θ_cap [mrad]", "margin vs flexure (pos/ang)", "margin vs hybrid (pos/ang)"],
  [
    ["tri-gas 25.7 m", "0.50", "10.1", "7.1× / 51×", "2.9× / 18×"],
    ["27 m (Ø160)", "1.06", "14.2", "15× / 71×", "6.2× / 26×"],
    ["H2-opt. 23.8 m", "0.41", "6.0", "5.9× / 30×", "2.4× / 11×"],
    ["sparse 15.3 m", "1.03", "18.8", "15× / 94×", "6.1× / 34×"],
    ["mini 9.1 m (½″, 0.8 mm hole)", "0.51", "8.0", "7.2× / 40×", "3.0× / 15×"],
    ["two-inch 19.0 m", "1.14", "13.2", "16× / 66×", "6.7× / 24×"],
    ["ceiling 29.0 m", "0.47", "3.0", "6.8× / 15×", "2.8× / 5.5×"],
    ["compact 20.7 m", "0.41", "4.2", "5.9× / 21×", "2.4× / 7.6×"],
    ["standard-tier 22.3 m", "0.37", "6.5", "5.2× / 32×", "2.2× / 12×"],
  ],
  [2350, 1150, 1300, 2280, 2280]));
body.push(...fig("capture_envelope.png",
  "Input-drift capture envelopes per design against the summed alignment-residual + drone operational-drift demand of the aluminium-flexure and hybrid plastic-body mount architectures. Left: launch-position capture (the binding axis, tracking exit-hole clearance). Right: launch-angle capture on a log scale — one to two orders above demand in every design.", 620));
body.push(P("Whether a design also survives sustained deployment inside those envelopes is a yield question, and product yield cannot be resolved by 400 trials: demonstrating 99.9 % at 95 % confidence requires essentially zero failures in 5000. Each design was therefore run through a 5000-trial Monte-Carlo per mount architecture, sampling uniformly inside the composed demand box — alignment residual plus operational drift applied independently per mirror (position and tilt, all axes) and to the launch chain — with per-trial criteria of full completion, no early hole leakage, whole-beam exit through the hole, and no physical spot overlap (Table 9). On the aluminium-flexure architecture, three designs pass the product criterion outright with 5000/5000 completions — the tri-gas flagship, the sparse 15.3 m and the two-inch 19.0 m — while the H2-optimised, half-inch mini and compact designs sit at 99.3–99.7 % (field grade), and the two boundary designs (the 29.0 m ceiling and the walk-tight 22.3 m) confirm their boundary character at 92–96 %. On the hybrid plastic-body architecture the ranking is the same but shifted down — 95.0 % for the two-inch, ~90 % for the sparse and flagship, 37–70 % for dense or boundary patterns — which converts the low-cost question from opinion to number: the hybrid build is a research-grade option carried best by the sparse two-inch design, and reaching product grade in plastic requires either the carbon-filled shell's smaller drift or a relaxed-clearance design generation."));
body.push(...tbl(
  "5000-trial composed-drift Monte-Carlo yield per mount architecture (uniform sampling inside the alignment-residual + drone operational-drift envelope; LB = 95 % Wilson lower bound). Drone product criterion: LB ≥ 99.9 %.",
  ["design", "Al flexure yield (LB) [%]", "verdict", "hybrid plastic yield (LB) [%]"],
  [
    ["tri-gas 25.7 m", "100.00 (99.92)", "drone product", "89.7 (88.8)"],
    ["27 m (Ø160)", "98.66 (98.30)", "research", "69.6 (68.3)"],
    ["H2-opt. 23.8 m", "99.60 (99.38)", "field", "64.6 (63.3)"],
    ["sparse 15.3 m", "100.00 (99.92)", "drone product", "90.4 (89.6)"],
    ["mini 9.1 m (½″)", "99.72 (99.53)", "field", "64.8 (63.5)"],
    ["two-inch 19.0 m", "100.00 (99.92)", "drone product", "95.0 (94.3)"],
    ["ceiling 29.0 m", "95.86 (95.27)", "boundary", "37.4 (36.0)"],
    ["compact 20.7 m", "99.28 (99.01)", "field", "63.6 (62.2)"],
    ["standard-tier 22.3 m", "92.48 (91.72)", "boundary", "53.3 (51.9)"],
  ],
  [2200, 2300, 1500, 2400]));
body.push(...fig("drone_yield_mc5000.png",
  "5000-trial composed-drift Monte-Carlo drone yield, plotted as trial failure rate (100 − yield) on a log scale so the product criterion is legible (lower is better). The dashed line is the 99.9 % drone criterion; the tri-gas 25.7 m, sparse 15.3 m and two-inch 19.0 m designs clear it with zero failures in 5000 trials on the aluminium-flexure mount (✓). The hybrid plastic-body architecture (right bars) is a research-grade option, best carried by the two-inch design.", 600));
body.push(P("Worst-case single-degree-of-freedom sweeps (every mirror displaced coherently to +max, then −max, per axis — the conservative extreme of the same drift envelopes) pass on eight of ten mirror axes for every menu design. The recurring exception is instructive rather than damning: coherent radial displacement of all mirrors is not a tolerance draw but a uniform ring-radius change — the thermal breathing mode, which accumulates ≈1.2 rad of re-entrance phase per millimetre and is governed by the machined trim law and the thermal windows of Table 7 (±8–30 K in aluminium), not by the random-drift budget. A drift source that is common-mode radial is a temperature signal, and the ring heater is its actuator."));

body.push(H2("6.4 Construction tolerance: what actually builds this cell"));
body.push(P("Construction tolerance plays three distinct roles in the chain of §2.8, and this section reports all three so the claims are not conflated. As-built survival — the Monte-Carlo verdicts below, with no adjustment of any kind — is the strictest reading and deliberately understates what a real build achieves, because the coherent component of construction error (the pattern translation and walk that dominate at loose grades) is exactly what the one-time ring trim and launch alignment recover; our menus carry that distinction as the robust versus robust-after-trim tiers. What alignment cannot recover is the incoherent component (spot merging, aperture clipping, early hole leakage), which is why dense patterns need precision machining regardless of adjustment; and what neither machining nor alignment removes is post-alignment operational drift, which §6.3 budgets separately. With that structure stated: manufacturing processes were mapped onto the Monte-Carlo machinery by converting published process capabilities into tolerance grades — seat flatness over the 25.4 mm pocket into mirror tilt σ (CNC precision 0.1 mrad; CNC standard 0.5; printed body with machined seats 0.3; industrial SLA 1.5; MJF/SLS 2.5; FDM 4.0), positional accuracy into decentre, radial accuracy into ring radius — and running the exact-trace Monte-Carlo per process (Fig. 15). The verdict is structured: dense 204-chord designs survive only precision-CNC aluminium; the sparse-pattern designs (144 chords, and especially the 112-chord 15.3 m design with 7 spots per mirror) complete 100 % of paths even on standard CNC and on a printed body with machined seats, failing only the no-realignment exit criterion by ~20 µm of pattern walk — recovered by the one-time ring trim every build performs. A fully polymer-printed cell fails three independent ways: as-printed accuracy (best industrial SLA holds ±0.27 mm on a 180 mm part against the ±0.1 mm ring budget, and no printed surface holds 2.5–12.7 µm seat flatness), in-service stability (PA12's CTE shrinks the thermal closure window to ±2–6 K and its 0.2–0.3 % moisture swelling walks the ring radius ~100 µm with the weather), and dynamics (printed lids resonate at 330–670 Hz, inside the 60–700 Hz rotor band, where aluminium lids sit at 1.2–2.0 kHz). The resolution is architectural, not material: a hybrid build in which a printed polymer shell (with integral base) carries a machined aluminium mirror-cartridge ring on three dowels, so plastic never defines an optical datum and the O-ring stays a seal. Generated directly from the design rows (CAD volumes, Table 10), the hybrid saves 33–46 % of structure mass — 435 g versus 817 g for the compact Ø141 cell, 1.06 kg versus 1.75 kg for the two-inch Ø182 — while the only machined part shrinks from the full housing to a simple annulus, and 6 mm printed lids keep their fundamental mode at or above 475 Hz (683 Hz in carbon-filled PA12 on the largest lid). The residual question for the hybrid is not construction but operational drift — its plastic shell moves more with temperature and vibration than a monolithic ring — and §6.3 quantifies exactly that with the composed-vector Monte-Carlo: the sparse two-inch design is the natural carrier of the low-cost architecture. The economics then land where they should: printing buys the shell, enclosure, window bezels and ducting for tens of dollars; the cartridge is a $100–200 machining job; and the flight-proven precedent for this cell class remains monolithic CNC aluminium on vibration dampers [19] for instruments where the last factor of margin matters."));
body.push(...fig("construction_tolerance.png",
  "Construction tolerance as a Monte-Carlo verdict: 100-trial exact-trace completion per manufacturing process (columns: three designs spanning sparse to dense patterns; colour: survives as-built / completes but needs the standard one-time trim / fails). Sparse patterns extend the cheap-build envelope; dense patterns require precision CNC.", 620));
body.push(...tbl(
  "Structure mass and lid fundamental mode from the generated CAD volumes: all-aluminium versus hybrid printed-shell + aluminium mirror-cartridge builds (metal lids 4 mm, plastic lids 6 mm; mirrors and coupling optics add 164–536 g depending on family).",
  ["design", "all-Al [g] (lid f₁)", "hybrid PA12 [g] (lid f₁)", "hybrid PA12-CF [g] (lid f₁)", "saving"],
  [
    ["compact 20.7 m (Ø141)", "817 (2.03 kHz)", "435 (803 Hz)", "446 (1.14 kHz)", "45–47 %"],
    ["flight max 29.0 m (Ø183)", "1270 (1.20 kHz)", "688 (475 Hz)", "705 (674 Hz)", "44–46 %"],
    ["mini 9.1 m (Ø129, ½″)", "497 (2.41 kHz)", "263 (955 Hz)", "270 (1.35 kHz)", "46 %"],
    ["two-inch 19.0 m (Ø182)", "1751 (1.22 kHz)", "1056 (483 Hz)", "1076 (685 Hz)", "39–40 %"],
  ],
  [2250, 1800, 1900, 2000, 950]));
body.push(H2("6.5 Cell windows"));
body.push(P("The sealed cell needs one wedged window behind M0. Calcium fluoride, the default infrared window, is mechanically the wrong material for an airframe: sapphire exceeds it roughly tenfold in hardness, twelve- to nineteen-fold in rupture strength and four- to six-fold in fracture toughness, with UV fused silica intermediate. Two catalogue parts cover the three gas lines: a Ø12.7 mm wedged UV-fused-silica window with 1050–1700 nm antireflection coating for the NH3 and CH4 channels, and a Ø12.7 mm wedged sapphire window with 1.65–3.0 µm coating for the CH4 and H2 channels (standard fused silica is excluded at 2.1 µm by its OH absorption; sapphire is ordered c-cut so the mounting tilt introduces no birefringence structure). The 30 arcmin wedge walks the back-surface ghost off the mode by ≈30× the beam divergence within 50 mm, a 3–5° mount tilt removes the front-surface reflection from the collimator axis, and any residual etalon has a free spectral range of ≈1 cm⁻¹ — an order of magnitude wider than the absorption features, i.e. fittable baseline curvature rather than line-shaped noise; measured precedent for wedged-versus-plane windows in a 1650 nm methane cell is ≈23× fringe suppression [26]. Both beams (entry and exit, 22.6° apart) pass one Ø12.7 mm window ~10 mm behind the mirror; an FKM O-ring seals it (ammonia-compatible), captured by a printed bezel."));
body.push(H2("6.6 CAD, build plan and the active tier"));
body.push(P("Because the optical datums live in the design row, the housing CAD is generated from it: a parametric script emits STEP (for Fusion 360 / FEA) and STL models — ring body with mirror pockets on the exact ring radius, the M0 beam cone at the design incidence angle, window boss, gas ports and bolt circle — for five housings from Ø129 to Ø183, plus hybrid printed-shell/aluminium-cartridge variants of the compact and two-inch designs (Fig. 16). The assembly procedure is: measure the delivered mirror curvatures; machine the ring to the interpolated radius from the linear trim law (Table 7); bond or screw the mirrors (bonded optics qualify to 20–40 g shock, an order of magnitude above the ~1.5–3 g, 60–700 Hz multirotor environment); align once with the collimator focus ring and launch adjuster; and isolate the whole cell from the airframe on rubber dampers — rigid inside, damped outside, the configuration validated in drone flight by [19]. For the active-alignment tier the same parts close a control loop: the Monte-Carlo shows these designs complete their paths even at flight tolerances and need recovery only of the coherent pattern walk (~1–3 mm), for which the ring heater is the slow actuator (1.2–1.7 µm of ring radius per kelvin, millikelvin-limited resolution), a ±5 mrad launch piezo the fast one, and a quadrant detector behind the coupling hole the error signal — roughly US$400–700 of additional hardware buys the step from 29 to 38.6 m (uniform) or 51.7 m (two-SKU)."));
body.push(...fig("cad_tmpc_20m.png",
  "Parametric housing CAD generated from the verified design row (exploded: lid, mirror ring with pockets and window boss, base). STEP models import directly into Fusion 360 for modal and static analysis; STL models serve print quoting for the enclosure parts.", 520));
body.push(H2("6.7 Operational physics: polarization, vibration, and remaining effects"));
body.push(P("Polarization. Over 98–372 gold reflections the s/p Fresnel differences accumulate, and the sagittal launch tips the incidence plane slightly bounce to bounce. Jones-matrix accumulation along the exact traced geometry (complex-index Fresnel coefficients [27]) shows the cell is a strong retarder for arbitrary input — a 45° linear launch exits 6–39° elliptical with design-specific azimuth rotation — but possesses a clean eigenaxis: light launched linearly polarized along the sagittal (vertical) axis exits 96.3–99.9 % pure in every menu design. The design rules are to key the polarization-maintaining fibre to the sagittal axis and to place no polarization-analysing element after the cell; the high-incidence skip-3 family additionally diattenuates (up to 6.4× s/p in bare-gold worst case), one more reason the near-diameter low-incidence family is the right architecture. Vibration. With the cell rigid inside and damped outside, the coupling of the 1.5–3 g, 60–700 Hz rotor environment into the spectra is bounded link by link: elastic seat tilt in the monolithic ring is 0.01–0.1 µrad per g (three orders below the flight tilt budget), ring-radius modulation is nanometric, aluminium lid modes sit above the excitation band, and the residual paths are launch-chain pointing (1–10 µrad per g against a 100 µrad budget) and exit-spot motion on the detector, which an f ≤ 25 mm collection lens absorbs. Aero-optic index fluctuations from rotor wash enter at δOPL ≈ 2.6 µm at 20 m — slow baseline, invisible to wavelength modulation. Remaining effects carry stated bounds: gravity sag of the ring <0.5 µm; catalogue λ/10 figure error enters as curvature error already Monte-Carloed; Å-class polish roughness sets the ~10⁻⁵-per-bounce scatter reservoir whose interference the overlap criterion suppresses; the sample's refractive index shifts OPL by a fixed 2.7×10⁻⁴; contamination in open-flow operation is self-monitored, since T = R^(n−1) makes the cell its own reflectometer (a 10⁻⁴ per-mirror reflectivity change reads as ≈2 % transmission change at 204 chords); and the ring heater doubles as the anti-dew measure within the thermal windows of Table 7."));

// 7 Discussion
body.push(H1("7. Discussion"));
body.push(P("Within the toroidal class the verified paths double to triple the demonstrated state of the art at comparable diameter — 29.0 m robust as-built against a 9.9 m demonstrated record and a 15.1 m commercial maximum — using catalogue optics and a single machined part, with the tri-gas flagship carrying 25.7 m across three gas lines spanning 1.5–2.1 µm on one build. The passive-build boundary itself is a result: three independent search campaigns at different clearance demands converge on 20.4 m (standard tolerances), 29.0 m (flight grade) and ~145/~210 chords as the respective pattern-walk ceilings on the 11.4 mm aperture, so further path inside this envelope demonstrably requires either active alignment (38.6 m uniform, 51.7 m two-SKU, both exact-trace verified with a costed two-actuator loop) or larger apertures. Drone qualification is likewise structural rather than asserted: the tolerance chain separates what machining must hold (the incoherent construction component), what one alignment session recovers (the coherent component, bounded by capture envelopes 2.2–16× the mount demand), and what the deployment must survive (composed residual-plus-drift sampling at >99.9 % yield) — and the same analysis quantifies the cost of the low-mass hybrid build as a yield number rather than a caveat. Against the dense-pattern Herriott records [9, 10], the ring architecture concedes packing density but eliminates the custom mirror pair, the critical two-mirror alignment, and — quantified here for the first time via the graded overlap criterion — carries its fringe immunity as a Monte-Carlo-guarded margin rather than a topology argument. Three limitations bound the claims. First, the results are simulation-verified: the verification chain (exact tracing, independent cross-validation at two wavelengths, per-trial physical Monte-Carlo criteria, systematic-error compensation laws, process-mapped construction tolerance) is designed to de-risk the build, and machining-level specifications plus CAD accompany each design, but the measured fringe floor and throughput await the first assembly. Second, coating reflectivity enters parametrically; all transmissions rescale by Eq. (6), and the polarization audit's absolute splits (computed with bare-gold constants) scale down ~20× for an R = 0.999 enhanced coating while its eigenaxis conclusion is coating-independent. Third, the two-SKU result is a singular feasible point on 1-inch apertures, and we executed the two natural continuations to their verdicts: a separation-aware mixed search produces nominal designs with real separation margins (30.5 m at +0.33 mm), but a dedicated Monte-Carlo composing the alternating-curvature baseline with flight-grade errors shows they buy that separation at the aperture edge and clip under 0.25 mm of curvature error; and on two-inch apertures — headroom up to 14.7 mm — the worst pairs remain negative, isolating the root cause as constellation degeneracy: the mixed prescreen checks closure only, whereas robust patterns additionally require the near-degenerate-phase-pair screen that the uniform search applies analytically. Porting that screen to the alternating-cell phase structure is the single identified blocker between the mixed family and build robustness."));

// 8 Conclusion
body.push(H1("8. Conclusion"));
body.push(P("Chord-skip ring geometry, engineered dual-plane re-entrance tuned by the machined ring radius, a graded and Monte-Carlo-guarded spot-overlap criterion, and mode-matched single-hole coupling together turn catalogue mirrors into a tolerance-tiered family of multipass cells: 20.4 m at standard laboratory tolerances, 29.0 m at flight grade, 25.7 m robust at the methane, ammonia and hydrogen lines on a single build, 19.0 m tri-gas-robust from only eight two-inch mirrors (completing at every manufacturing grade including polymer printing), 9.1 m at 90.8 % in a Ø129 mm half-inch cell with 75 mL of sample volume, and — with a costed two-actuator loop — 38.6 m uniform or 51.7 m with a two-SKU ring, all inside drone-compatible envelopes on ≈1 kg payloads. Every design carries an eight-item exact-trace check matrix, an independent cross-validation, a Monte-Carlo verdict at a stated build grade, an input-drift capture envelope with its drone-demand margin, a composed-drift yield against the 99.9 % product criterion, systematic-error compensation laws, and generated CAD in both all-aluminium and hybrid printed-shell/aluminium-cartridge builds. Next steps: fabricate the tri-gas flagship and the standard-build design, measure transmission, fringe floor and polarization against the budgets quantified here, and fly the integrated three-channel sensor."));

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
  "Thorlabs Inc., CM254-/CM127-series concave mirrors, fibre and TO-can collimation packages, and WW-series wedged windows, product documentation (2026).",
  "H. Kramer, Optiland: open-source sequential ray tracing in Python, github.com/HarrisonKramer/optiland.",
  "IRsweep AG (Sensirion), IRcell, IRcell-S4 and IRcell-S15 datasheets (2016–2021).",
  "R. Ghorbani and F. M. Schmidt, “ICL-based TDLAS sensor for real-time breath gas analysis of carbon monoxide isotopes,” Opt. Express 25(11), 12743–12752 (2017).",
  "R. Ghorbani and F. M. Schmidt, “Real-time breath gas analysis of CO and CO2 using an EC-QCL,” Appl. Phys. B 123, 144 (2017).",
  "B. Tuzson, M. Graf, J. Ravelid, P. Scheidegger, A. Kupferschmid, H. Looser, R. P. Morales, and L. Emmenegger, “A compact QCL spectrometer for mobile, high-precision methane sensing aboard drones,” Atmos. Meas. Tech. 13, 4715–4726 (2020).",
  "C. R. Webster et al., “Tunable laser spectrometers for planetary science,” Appl. Opt. 60(7), 1958–1970 (2021).",
  "P. Werle, R. Mücke, and F. Slemr, “The limits of signal averaging in atmospheric trace-gas monitoring by tunable diode-laser absorption spectroscopy (TDLAS),” Appl. Phys. B 57, 131–139 (1993).",
  "J. B. McManus, M. S. Zahniser, and D. D. Nelson, “Dual quantum cascade laser trace gas instrument with astigmatic Herriott cell at high pass number,” Appl. Opt. 50(4), A74–A85 (2011).",
  "V. Avetisov, O. Bjoroey, J. Wang, P. Geiser, and K. G. Paulsen, “Hydrogen sensor based on tunable diode laser absorption spectroscopy,” Sensors 19(23), 5313 (2019).",
  "J. Westberg, V. Avetisov, Y. Chen, V. Bjoroy, and P. Geiser, “Direct TDLAS measurements of molecular hydrogen at 2.1 µm and 2.4 µm,” Opt. Express 33(5), 11409–11419 (2025).",
  "I. E. Gordon et al., “The HITRAN2020 molecular spectroscopic database,” J. Quant. Spectrosc. Radiat. Transf. 277, 107949 (2022).",
  "D. Masiyano, J. Hodgkinson, and R. P. Tatam, “Gas cells for tunable diode laser absorption spectroscopy employing optically diffuse surfaces,” Appl. Phys. B 90, 279–288 (2008), and D. Masiyano, PhD thesis, Cranfield University (2009).",
  "S. Babar and J. H. Weaver, “Optical constants of Cu, Ag, and Au revisited,” Appl. Opt. 54(3), 477–481 (2015).",
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
      page: { margin: { top: 1080, bottom: 1080, left: 1180, right: 1180 } },
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
  console.log(`wrote ${OUT}  (${(b.length / 1024 / 1024).toFixed(1)} MB, ` +
              `${figN} figures, ${tabN} tables, ${eqN} equations, ${refs.length} references)`);
});
