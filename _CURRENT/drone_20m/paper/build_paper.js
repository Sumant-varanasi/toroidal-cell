/* Build the TMPC drone-cell draft paper (docx).
   Run:  node build_paper.js   ->  TMPC_drone_paper_draft_v1.docx        */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, LevelFormat, BorderStyle, WidthType, ShadingType, PageBreak,
  Footer, PageNumber,
} = require(require("child_process").execSync("npm root -g").toString().trim() + "/docx");

const FIG = path.resolve(__dirname, "..", "designs", "figures");
const OUT = path.join(__dirname, "TMPC_drone_paper_draft_v1.docx");

// ---------- helpers ----------------------------------------------------
const FONT = "Times New Roman";
const SZ = 22;                       // 11 pt body

function R(text, opts = {}) {
  return new TextRun({ text, font: FONT, size: SZ, ...opts });
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

// ---------- content -----------------------------------------------------
const body = [];

// Title block
body.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 160 },
  children: [R("Twenty-metre optical paths in sub-19 cm rings: chord-skip toroidal multipass cells built from catalogue mirrors for drone-borne methane sensing", { bold: true, size: 30 })],
}));
body.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 60 },
  children: [R("Sumant Varanasi", { size: 22 }), R("1", { size: 22, superScript: true }),
             R(", [co-author names — Naman Rindani, Padmanabh Mishra — confirm list and order]", { size: 22, color: "B00000" }),
             R("1", { size: 22, superScript: true }),
             R(", and Thomas Benoy", { size: 22 }), R("2,*", { size: 22, superScript: true })],
}));
body.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 40 },
  children: [R("1", { size: 20, superScript: true }),
             R("Indian Institute of Technology Delhi – Abu Dhabi, UAE", { size: 20 })],
}));
body.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 40 },
  children: [R("2", { size: 20, superScript: true }),
             R("Aston Institute of Photonic Technologies, Aston University, Birmingham, UK", { size: 20 })],
}));
body.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 200 },
  children: [R("*t.benoy@aston.ac.uk", { size: 20, italics: true })],
}));

// Abstract
body.push(H1("Abstract"));
body.push(P("Toroidal multipass cells (TMPCs) fold long absorption paths into compact, mechanically robust volumes, but published designs demonstrate at most ~10 m of optical path in the 100–200 mm diameter class and typically require custom diamond-turned optics. We present a family of ring-geometry multipass cells that reach a verified 20.4–24.8 m optical path length within a 180 mm assembly envelope — and 20.6 m within 159 mm — using only 13–16 catalogue 25.4 mm protected-gold spherical mirrors (≈US$1000 of optics). Three design principles enable this: (i) a chord-skip ring geometry whose near-diameter chords deliver up to 143 mm of path per reflection at 7–13° incidence; (ii) an engineered dual-plane re-entrance condition in which the machined ring radius acts as the closure-tuning parameter (≈1.2 rad of accumulated Gouy-type transverse phase per millimetre), with a number-theoretic constellation rule that guarantees fringe-safe spot separation on every mirror; and (iii) mode-matched injection through a single 1.3 mm coupling hole, which makes hole losses negligible so that cell transmission equals R^(n−1) exactly in mirror reflectivity R. Designs are verified with an exact three-dimensional ray tracer including astigmatic Gaussian-beam propagation, cross-validated against an independent ray tracer to sub-micrometre agreement, and toleranced by Monte-Carlo analysis: at research-grade build tolerances the headline 20.4 m design completes all 144 traversals in 100 % of trials, and the ±1 % catalogue tolerance on mirror focal length is absorbed by a linear 0.72 mm-per-percent trim of the ring radius. A thermal analysis shows ±26 K of drift immunity on a plain aluminium ring. The results place a 1654 nm methane-sensing path of >20 m on a sub-kilogram, drone-compatible optical head assembled from catalogue parts."));
body.push(P([R("Keywords: ", { bold: true }), R("multipass cell; toroidal cell; laser absorption spectroscopy; TDLAS; methane detection; unmanned aerial vehicle; Herriott cell")]));

// 1 Introduction
body.push(H1("1. Introduction"));
body.push(P("Tunable diode laser absorption spectroscopy (TDLAS) of the methane 2ν3 band near 1654 nm requires tens of metres of absorption path for sub-ppm sensitivity, while drone deployment restricts the sensor head to roughly a 19 cm envelope and a few hundred grams of optics. Multipass cells reconcile these demands by folding the path between mirrors. The classical two-mirror Herriott cell [11–13] achieves this with re-entrant elliptical spot patterns, and its densest variants reach exceptional path-to-volume ratios (54.6 m in a 17 cm astigmatic cell [9]; 26.4 m in a 12 cm dense-pattern cell [10]), at the cost of custom mirror pairs and sub-milliradian two-mirror alignment."));
body.push(P("Ring-geometry (toroidal/circular) cells trade some packing density for one-piece mechanical robustness: the mirror is a single machined annulus, or a ring of discrete segments, and the beam pattern is set by the injection angle. Tuzson et al. demonstrated the monolithic toroidal concept at 2.2–4.1 m [1] following the versatile multipass geometry of Manninen et al. [2]; Mangold et al. extended it to a circular paraboloid at >12 m in a 145 mm cell [3]; Graf et al. produced a segmented, interference-free circular cell of 10 m at <200 g [4] and studied mask-based fringe suppression with coherent field simulations [5]; Chang et al. demonstrated 10 m (30 m theoretical) from multi-layer patterns on a 100 mm ring surface [7]; and cryogenic toroidal cavities for particle-physics spectroscopy have recently exceeded 15 m [8]. Double-row circular cells reach 74.7 m but at 250 mm diameter [6]. Across this literature, demonstrated toroidal-class paths in drone-compatible envelopes cluster at or below ~10 m, and every design relies on custom or diamond-turned optics."));
body.push(P("This work asks a deliberately constrained question: how much verified optical path can a ring cell deliver inside a 190 mm envelope using only catalogue spherical mirrors — specifically Thorlabs CM254-series 25.4 mm protected-gold concave mirrors (16 focal lengths, ≈US$74 each) — with 8–16 mirrors, a single 1.3 mm coupling hole, and a 1.3 mm collimated input beam? Our contributions are: (1) a chord-skip parametrisation of the ring geometry, in which the beam advances s ≈ N/2 mirrors per reflection, giving near-diameter chords at near-normal incidence — this single parameter is what separates the present designs from fixed star-polygon toroidal cells; (2) an engineered, rather than searched-for, re-entrance condition: dual-plane transverse phase closure tuned by the machined ring radius against the catalogue-locked radii of curvature, together with an exact constellation criterion (odd spots-per-mirror k with unit-fraction phase steps evaluated over the full n-point pattern on every mirror) that guarantees minimum spot separations and hole clearance before any ray is traced; (3) mode-matched single-hole coupling that renders the coupling hole lossless; and (4) a fully verified design menu — 13.6 m in a 143 mm envelope to 24.8 m in 180 mm — each design passing an eight-item physical check matrix in an exact 3-D ray trace, cross-validated against an independent tracer, and toleranced by Monte-Carlo analysis with codified compensation rules for catalogue radius-of-curvature error and temperature."));

// 2 Architecture & theory
body.push(H1("2. Cell architecture and design principles"));
body.push(H2("2.1 Chord-skip ring geometry"));
body.push(P("N identical concave mirrors of radius of curvature R and clear-aperture radius 11.4 mm face inward from a ring of radius R_ring, one every 360°/N. A beam injected through a hole in mirror M0 advances by s mirrors per reflection (the chord skip, gcd(N, s) = 1). Each chord has length L = 2 R_ring sin(πs/N) and the angle of incidence on every mirror is θ_i = π/2 − πs/N. For s ≈ N/2 the chords approach the ring diameter while θ_i falls to 6–13°, so a 72 mm-radius ring yields 140+ mm of path per reflection with near-normal incidence — the geometric core of the result. The assembly envelope is 2(R_ring + 18 mm), the allowance covering the mirror substrate and a machined aluminium wall."));
body.push(H2("2.2 Re-entrance: dual-plane phase closure"));
body.push(P("In the paraxial unit cell (one chord of length L plus one mirror), the transverse ray oscillation advances by a phase θ per bounce, cos θ_t = 1 − L/(R cos θ_i) in the tangential plane and cos θ_s = 1 − L cos θ_i /R in the sagittal plane (the off-axis astigmatic split). The beam exits through the entrance hole after n = kN reflections when both accumulated phases return to their launch value. Launching the tangential plane at a zero crossing (hole at the pattern centre in u) closes at phase 0 or π; the sagittal plane closes at 0 (height-offset launch) or 0/π (vertical-tilt launch), giving four closure-mode combinations per geometry. Because the single machinable parameter R_ring moves both accumulated phases along a nearly fixed direction (slope cos²θ_i, ≈1.2 rad of accumulated phase per millimetre of ring radius for the designs below), a candidate is closable only if its signed phase residuals lie near that line; the residual left after the ring-radius sweep is absorbed by the launch amplitudes through their weak aberration-mediated phase pull. This turns re-entrance from a found coincidence into an engineered property, with the ring radius machined to the value that closes the pattern for the delivered mirror lot."));
body.push(H2("2.3 Constellation number theory: fringe-safe spot patterns"));
body.push(P("At closure, the n = kN spots lie on a Lissajous curve sampled at unit-fraction phase steps: with M_t = round(nθ_t/2π), the per-revisit tangential step on any one mirror is 2πM_t/k. Three exact geometric rules follow. First, k must be odd: for even k the tangential π-slot coincides with a sagittal near-return and an intermediate spot lands in the coupling hole (the star-polygon parity rule). Second, gcd(M, k) = 1 in both planes, or the k spots per mirror collapse onto k/gcd clusters. Third — decisive in practice — every mirror carries the same k-point pattern at a different phase origin along the Lissajous (mirror q is first struck at bounce j_q, so its pattern starts at phase j_q θ), and the worst spot pair must be evaluated over all N mirrors; evaluating only the launch mirror overestimates the usable separation by up to a factor of three. The minimum pair distance d_min (in units of the pattern amplitude) and the pattern extent are computed exactly for each candidate (M_t, M_s, k, mode) combination, sizing the required amplitude A = (2w + margin)/d_min and rejecting self-crowding patterns before ray tracing. Spot-overlap fringes — the dominant practical noise source in this cell class [5, 7] — are thereby excluded by construction: every design below keeps every spot pair on every mirror at least the sum of the local 1/e² radii plus 0.36–0.42 mm apart."));
body.push(H2("2.4 Mode-matched single-hole coupling"));
body.push(P("A 1.3 mm waist placed at the hole is badly mismatched to the cell eigenmode (whose mirror-plane radius is w_m = √(M²λL/π sin θ) ≈ 0.3–0.45 mm here); the beam then breathes to ~3× its injected size, spots overlap, and the hole clips 13.5 % of the power at entry and again at exit. Instead, a small lens focuses the 1.3 mm collimated input so that the in-cell waist (0.20–0.33 mm in the designs below) sits near mid-chord: the beam rides the eigenmode at 0.21–0.42 mm for the entire path, the beam radius at the hole is ~0.3–0.37 mm, and the 1.3 mm hole transmits ≈100 % in both directions. Cell transmission is then exactly T(R) = R^(n−1), with any coating reflectivity substitutable; at closure the round-trip ABCD map is the identity, so the exit beam reproduces the injected Gaussian and leaves through the same hole, angularly separated from the input by 2θ_i (22.5° for the N = 16 designs), placing laser and detector side by side behind M0 without a beamsplitter."));

// 3 Methods
body.push(H1("3. Numerical methods"));
body.push(P("Designs were generated and verified with an open simulation platform comprising an exact 3-D ray tracer on toroidal/spherical surfaces (analytic normals, Newton-iterated intersections, per-bounce hard-aperture tests), astigmatic Gaussian propagation via per-plane complex-q ABCD transfer with the actual per-bounce incidence angles and an M² beam-quality factor, a loss-budget model, per-plane stability, and spot-pattern diagnostics. A two-stage search was used. Stage A enumerates the full catalogue space — 16 CM254 radii of curvature × N = 8–16 × all coprime chord skips × a 0.05–0.25 mm ring-radius grid × odd k — and retains candidates passing mirror packing, envelope, per-plane stability, dual-plane closure residuals, and the exact constellation criterion of §2.3. Stage B ray-traces the survivors: launch parameters are seeded from the analytic amplitudes, the ring radius is swept ±1.5 mm in 20 µm steps to locate the closure valley (whose width is ~20 µm), and a six-parameter Nelder-Mead polish (ring radius, launch height, two launch tilts, waist size, waist position) minimises the exit miss with soft margin penalties, the objective evaluated at the designed exit bounce to keep the landscape continuous. A design is accepted only if the final honest trace passes all eight checks of Table 2. The tracer was cross-validated against the independent open-source sequential ray tracer Optiland [15]: over 64 bounces of the headline design the two agree to 0.000 µm RMS in spot position, 0.01° in incidence angle, and 0.8 µm in chord length."));

// Fig 1 cell3d
body.push(...fig("drone_20m_cell3d.png",
  "Exact traced beam path of the headline design (drone_20m): 16 catalogue gold mirrors on a 72.155 mm ring, 144 chords (20.38 m), coloured by bounce order; the input beam (green) enters through the 1.3 mm hole in M0 and the closed pattern exits through the same hole.", 580));

// 4 Results
body.push(H1("4. Results"));
body.push(H2("4.1 Verified design menu"));
body.push(...tbl(
  "Verified design menu. Every row passes the full check matrix in the exact ray trace. T is optical transmission at R = 0.985; T(R) = R^(chords−1) exactly (hole losses ≈ 0). Envelope = 2(R_ring + 18 mm).",
  ["design", "mirrors", "R_ring [mm]", "chords", "OPL [m]", "T @0.985", "envelope × height [mm]"],
  [
    ["max OPL", "16 × CM254-200 (R 400)", "71.758", "176", "24.77", "7.1 %", "180 × 22"],
    ["headline 20 m", "16 × CM254-150 (R 300)", "72.155", "144", "20.38", "11.5 %", "180 × 16"],
    ["mid", "12 × CM254-075 (R 150)", "67.489", "156", "20.34", "9.6 %", "171 × 22"],
    ["compact 20 m", "13 × CM254-050 (R 100)", "61.519", "169", "20.64", "7.9 %", "159 × 18"],
    ["compact max-T", "13 × CM254-150 (R 300)", "62.087", "143", "16.60", "11.7 %", "160 × 20"],
    ["small", "12 × CM254-250 (R 500)", "53.486", "132", "13.64", "13.8 %", "143 × 16"],
  ],
  [1500, 2400, 1200, 900, 900, 1000, 1460]));
body.push(P("The verified boundary of the approach under these constraints is a 141 mm envelope (13.4 m); the best near-miss outside it — 18.0 m in 140 mm — fails only by an intermediate spot grazing the coupling hole by 0.56 mm, and re-slotting the hole within the constellation (a tangential launch offset) is an open lever. Below 105 mm, 8 × 25.4 mm mirrors no longer pack on the ring."));

body.push(H2("4.2 The headline design"));
body.push(P("The 20.38 m design uses sixteen CM254-150-M01 mirrors (R = 300 mm) on a ring machined to R_ring = 72.155 mm (envelope 180 mm, inner height 16 mm, enclosed volume 0.26 L, optics ≈790 g with housing). The beam enters at 11.25° mean incidence, completes 144 chords of mean 141.5 mm, deposits 9 spots on each mirror with a worst-pair separation of 0.99 mm against summed beam radii of ~0.64 mm, keeps 4.9 mm of aperture margin, and re-crosses the hole plane within 6 nm of the entrance point at the designed bounce. Mode matching sets a 0.326 mm waist 102 mm past the hole (beam radius at the hole 0.365 mm; hole transmission 100.0 %). All intermediate visits to M0 clear the hole by at least 1.46 mm beyond the local beam radius. Transmission is R^143: 11.5 % at R = 0.985, 10.0 % at 0.984, 1.3 % at the conservative 0.97. With a 10 mW distributed-feedback laser, 1.0–1.2 mW reaches the detector at the design coating — four orders of magnitude above the noise-equivalent power of an InGaAs photodiode in a kilohertz detection bandwidth."));

body.push(...fig("drone_20m_constellations.png",
  "Per-mirror spot constellations of the headline design (ray-traced): each of the 16 mirrors carries the same 9-point Lissajous at a different phase origin; the worst pair over all mirrors — not just the launch mirror — is the verified fringe-safety quantity. M0 additionally shows the entrance/exit hole.", 560));
body.push(...fig("drone_20m_beam_evolution.png",
  "Tangential and sagittal 1/e² beam radii at each bounce of the headline design under mode-matched injection: the beam rides the cell eigenmode at 0.21–0.42 mm for all 144 chords, an order of magnitude below the 11.4 mm clear aperture.", 520));
body.push(...fig("drone_20m_experiment.png",
  "As-built rendering of the headline design: sixteen 25.4 mm gold mirrors in a one-piece machined ring, the traced beam threading the cell; laser collimator, mode-matching lens and detector all mount behind M0, the exit beam leaving 22.5° from the injection axis.", 560));

// 5 Tolerances
body.push(H1("5. Tolerance and engineering analysis"));
body.push(H2("5.1 Monte-Carlo build tolerances"));
body.push(P("Each design was subjected to 300–400 Monte-Carlo trials with independent per-mirror perturbations at research-grade magnitudes (tilt σ = 0.5 mrad per axis; decentre σ = 50 µm lateral, 100 µm axial; radius-of-curvature σ = 1 mm; ring radius σ = 0.1 mm; launch σ = 50 µm and 0.5 mrad). No trial in any design clipped or lost the beam; all completed the full traversal count."));
body.push(...tbl(
  "Monte-Carlo results (research-grade tolerances; mean ± σ, p95 in brackets).",
  ["metric", "drone_20m", "drone_25m", "drone_16cm"],
  [
    ["trials clipping / losing beam", "0/400", "0/300", "0/300"],
    ["OPL [m]", "20.35 ± 0.03", "24.74 ± 0.03", "20.61 ± 0.03"],
    ["transmission @0.985", "11.5 ± 1.7 %", "7.1 ± 1.3 %", "7.9 ± 1.4 %"],
    ["exit pointing drift [mrad]", "4.2 ± 2.6 (9.4)", "5.0 ± 3.3 (11.2)", "38 ± 23 (89)"],
    ["spot-pattern walk p95 [mm]", "0.89", "1.43", "2.95"],
    ["hole clearance available [mm]", "1.46", "3.40", "1.65"],
  ],
  [2600, 1800, 1800, 1800]));
body.push(P("The two long-radius designs are robust as-machined: the pattern walk stays well inside the hole clearance and the exit beam moves ~0.2–0.3 mm on a detector 50 mm behind M0. The compact R = 100 mm design is an order of magnitude more sensitive — its strong per-bounce focusing converts radius errors into phase errors — and requires roughly 2× tighter machining or use of its thermal trim during first alignment. One-at-a-time sensitivity analysis identifies the dominant error source per design: mirror-pocket tilt for the R ≥ 300 mm designs (3.3 mrad of exit drift per 0.5 mrad tilt σ, versus a negligible radius-of-curvature contribution), and ring radius / radius-of-curvature for the R = 100 mm design (20 and 28 mrad per σ respectively, with tilt negligible at 0.7). The one-piece machined ring, in which all pocket angles are cut in a single CNC operation, targets precisely the dominant term."));

body.push(...fig("mc_hist.png",
  "Monte-Carlo distributions for the headline design at research-grade tolerances (400 trials): traversal count is invariant at 144; OPL, transmission, and exit drift remain within operational bounds in every trial.", 560));
body.push(...fig("sensitivity.png",
  "One-at-a-time sensitivity of exit-pointing drift for the headline design: per-mirror tilt dominates, followed by ring radius and lateral decentre; radius-of-curvature error is negligible for the R = 300 mm mirrors.", 520));

body.push(H2("5.2 Systematic errors: catalogue ROC and temperature"));
body.push(P("Catalogue mirrors carry a ±1 % focal-length tolerance, and a delivered lot is typically biased collectively. Re-optimising only the ring radius (launch untouched) restores the complete check matrix across the entire ±1 % band for all three designs, with a strictly linear trim rule: 0.72 mm of ring radius per percent of radius-of-curvature error for the two 180 mm designs, 0.62 mm for the compact design (worst residual exit miss 0.12 mm, transmission preserved within its Monte-Carlo band). The assembly procedure is therefore: measure the delivered radii of curvature, machine the ring to the interpolated radius, and walk in the final micrometres with the temperature trim. Temperature acts through the same mechanism — an aluminium ring scales R_ring by 23.6 ppm/K while the glass mirror curvature is essentially fixed — so thermal drift detunes closure predictably. With the launch frozen at the alignment temperature, the headline design passes every check over ±26 K on plain aluminium (±20 K for the 24.8 m design; ±8 K for the compact design), and an invar ring holds ≥±30 K for all three; conversely a small ring heater doubles as the closure fine-adjustment actuator. Beam-quality robustness was verified separately: all designs pass every check up to M² = 1.3, beyond typical fibre-coupled DFB sources."));
body.push(...tbl(
  "Systematic-error compensation and robustness.",
  ["design", "ROC ±1 % → ring trim", "thermal window (Al)", "thermal window (invar)", "M² limit tested"],
  [
    ["drone_20m", "±0.72 mm (linear)", "±26 K", "≥±30 K", "1.3 (pass)"],
    ["drone_25m", "±0.72 mm (linear)", "±20 K", "≥±30 K", "1.3 (pass)"],
    ["drone_16cm", "±0.62 mm (linear)", "±8 K", "≥±30 K", "1.3 (pass)"],
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
    ["Dong 2016 [9]", "170×65×55 mm", "54.6 m", "2 custom spherical", "densest compact cell; critical alignment"],
    ["this work, compact", "159 mm", "20.6 m", "13 × catalogue $74", "all checks verified"],
    ["this work, headline", "180 mm", "20.4 m", "16 × catalogue $74", "11.5 % T at R = 0.985"],
    ["this work, max OPL", "180 mm", "24.8 m", "16 × catalogue $74", "7.1 % T at R = 0.985"],
  ],
  [2100, 1500, 1500, 2200, 2060]));
body.push(P("Within the toroidal/ring class the verified paths roughly double the demonstrated state of the art at comparable diameter, and do so with catalogue optics and a single machined part. The astigmatic-Herriott record of Dong et al. [9] remains denser, but requires custom mirror figures and alignment tolerances that a one-piece ring eliminates; the present cells trade ~2.5× in path density for catalogue procurement, single-operation machining, and tilt-dominated (rather than figure-dominated) error budgets. For drone-borne methane sensing at 1654 nm, 20.4 m at 11.5 % transmission delivers ~1 mW to the detector from a 10 mW DFB — SNR-limited by fringe suppression rather than photon budget, which is why the constellation-level fringe-safety guarantee, rather than mask-based suppression after the fact [5], is the design-level contribution. The complete optical head (mirrors, ring, injection optics) is estimated below 1 kg with a 0.26 L sampling volume, compatible with sub-second gas exchange under modest flow."));
body.push(P("Three limitations bound the claims. First, all results are simulation-verified, not yet experimentally demonstrated; the verification chain (exact tracing, independent cross-validation, Monte-Carlo tolerancing, and systematic-error compensation rules) is designed to de-risk the build, and the as-built specification tables (mirror placements, lens focus, launch tilts, detector pickoff) accompany each design. Second, mirror reflectivity enters as an external parameter; we quote T(R) = R^(n−1) exactly so that measured coating data replace the assumed 0.985 directly. Third, surface-figure error and scatter are not modelled; at 9 spots per mirror and ≥0.99 mm separations the designs are tolerant of localised defects, but wavefront error accumulation over ~150 reflections merits measurement on the assembled cell."));

// 7 Conclusion
body.push(H1("7. Conclusion"));
body.push(P("Chord-skip ring geometry, engineered dual-plane re-entrance tuned by the machined ring radius, exact constellation number theory, and mode-matched single-hole coupling together turn catalogue 1-inch gold mirrors into verified 20–25 m multipass cells inside drone-compatible 143–180 mm envelopes. The designs pass an eight-item physical check matrix in exact ray tracing, survive research-grade Monte-Carlo build tolerances with zero geometric failures, absorb the full catalogue radius-of-curvature tolerance through a linear ring-radius trim, and hold alignment over ±26 K on a plain aluminium ring. The immediate next steps are fabrication of the headline design, cavity transmission and fringe-floor measurement against the simulated budgets, and integration with a 1654 nm DFB source for airborne methane sensing."));

// Acknowledgements + data
body.push(H1("Acknowledgements"));
body.push(P("[Draft placeholder — funding, internship programme (IIT Delhi–Abu Dhabi / Aston University joint internship), supervision acknowledgements. Per the project brief, intellectual property resides with Aston University.]"));
body.push(H1("Data and code availability"));
body.push(P("The simulation platform (exact toroidal ray tracer, astigmatic Gaussian propagation, tolerance engine), the design-search harness, all verified design specifications, and the scripts reproducing every figure and table are available at github.com/Sumant-varanasi/toroidal-cell (directory _CURRENT/, presets drone_20m, drone_25m, drone_16cm)."));

// References
body.push(H1("References"));
const refs = [
  "B. Tuzson, M. Mangold, H. Looser, A. Manninen, and L. Emmenegger, “Compact multipass optical cell for laser spectroscopy,” Opt. Lett. 38(3), 257–259 (2013).",
  "A. Manninen, B. Tuzson, H. Looser, Y. Bonetti, and L. Emmenegger, “Versatile multipass cell for laser spectroscopic trace gas analysis,” Appl. Phys. B 109, 461–466 (2012).",
  "M. Mangold, B. Tuzson, M. Hundt, J. Jágerská, H. Looser, and L. Emmenegger, “Circular paraboloid reflection cell for laser spectroscopic trace gas analysis,” J. Opt. Soc. Am. A 33(5), 913–919 (2016).",
  "M. Graf, L. Emmenegger, and B. Tuzson, “Compact, circular, and optically stable multipass cell for mobile laser absorption spectroscopy,” Opt. Lett. 43(11), 2434–2437 (2018).",
  "M. Graf et al., coherent-field modelling and absorption-mask fringe suppression in toroidal multipass cells (2017). [verify citation details]",
  "K. Sun et al., double-row circular multipass cell reaching 74.7 m (2018). [verify citation details]",
  "J. Chang et al., “Multi-layer beam patterns from a single toroidal ring surface,” Opt. Lett. 45 (2020). [verify citation details]",
  "Y. Kilinc et al. (CREMA collaboration), cryogenic toroidal multipass cavities at 6.8 µm with >15 m path (2026). [verify citation details]",
  "L. Dong et al., ultra-compact dense-spot-pattern multipass cell, 54.6 m in 220 mL (2016). [verify citation details]",
  "K. Liu et al., dense-pattern multipass cell, 26.4 m (2015). [verify citation details]",
  "D. R. Herriott, H. Kogelnik, and R. Kompfner, “Off-axis paths in spherical mirror interferometers,” Appl. Opt. 3(4), 523–526 (1964).",
  "D. R. Herriott and H. J. Schulte, “Folded optical delay lines,” Appl. Opt. 4(8), 883–889 (1965).",
  "J. B. McManus, P. L. Kebabian, and M. S. Zahniser, “Astigmatic mirror multipass absorption cells for long-path-length spectroscopy,” Appl. Opt. 34(18), 3336–3348 (1995).",
  "Thorlabs Inc., CM254-xxx-M01 protected-gold concave mirror series, product datasheets (2026).",
  "H. Kramer, Optiland: open-source sequential ray tracing in Python, github.com/HarrisonKramer/optiland.",
];
refs.forEach((t, i) => body.push(new Paragraph({
  spacing: { after: 80 },
  indent: { left: 480, hanging: 480 },
  children: [R(`[${i + 1}] `, { size: 20 }), R(t, { size: 20 })],
})));

// note to authors
body.push(new Paragraph({ children: [new PageBreak()] }));
body.push(H1("Note to authors (delete before submission)"));
body.push(P("This is an auto-generated draft from the verified simulation results of 2 July 2026. To update: (1) confirm the author list, order, and affiliations; (2) complete the [verify citation details] references from the WP1 literature package; (3) replace the assumed R = 0.985 with the measured coating reflectivity via T(R) = R^(chords−1); (4) add experimental sections when the headline cell is assembled. Every number in the text is traceable to _CURRENT/drone_20m/designs/ (specs, CSVs, investigations.md); figures regenerate with drone_20m/make_figures.py, and this document with drone_20m/paper/build_paper.js."));

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
  console.log("wrote", OUT, b.length, "bytes");
});
