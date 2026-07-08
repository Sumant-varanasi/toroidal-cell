# TMPC vs the IRsweep IRcell and published compact multipass cells

*(Answers Dr. Benoy's review points, 2026-07-08: "compare against the IRSweep
gas cell... what is the downside? Compare overlap factor... Are your beams
overlapping? Will the OD noise be worse? Compare with other works also...
compare the volume of the disc.")*

All "ours" numbers below are exact-trace values from `cell_metrics.py`
([cell_metrics.csv](cell_metrics.csv)); literature numbers carry their source.

## 1. What the IRcell actually is

Two generations, both from the Empa lineage (IRsweep AG, acquired by
Sensirion 2021):

* **Original IRcell / IRcell-4M** (2016): a *toroidal* cell in the strict
  sense — one continuous diamond-turned gold ring mirror (Tuzson et al.,
  Opt. Lett. 38, 257, 2013). The concentric geometry is optically
  **unstable**: beam components superpose, so a patented Teflon
  **absorption mask** truncates the beam at every reflection to kill
  fringes (Mangold et al., JOSA A 33, 913, 2016). 3.49 m path, 38 mL,
  Ø100 × 30 mm; alignment tolerance ±0.002° horizontal.
* **IRcell-S4 / S15** (2020): the segmented circular MPC of Graf,
  Emmenegger & Tuzson, Opt. Lett. 43, 2434 (2018) — 65 individually
  curved confocal mirror segments in a monolithic ring (Rs = 2Rc). This
  made the cavity **stable**: exactly one spot per segment, no overlap,
  no mask. S4: 4.03 m / 31 mL / Ø106 mm. S15: 15.12 m / 128 mL / Ø194 mm.
  Fringe spec < 2.0×10⁻⁴ rms at 4.3 µm (all variants). Entry/exit: two
  separate 5 mm apertures in the ring.

The professor's "3× improvement" framing is right against the S4/original
(4 m class) and ~35 % against the top-end S15 — in a *smaller* envelope.

## 2. Head-to-head table

| cell | architecture | OPL | envelope | gas volume | PVR | entry/exit | fringe/noise (as published) |
|---|---|---|---|---|---|---|---|
| IRcell-4M (2016) | monolithic toroid + Teflon mask | 3.49–3.99 m | Ø100×30 | 38 mL | 92 m/L | one 4 mm hole, in/out 28° apart | spec <2×10⁻⁴ rms; users measured 0.42 ‰ rms fringes, 6.5–8.5×10⁻⁸ cm⁻¹ Hz^-1/2 (Ghorbani & Schmidt 2017) |
| IRcell-S4 (2020) | 65 confocal segments | 4.03 m | Ø106×32 | 31 mL | 130 m/L | two 5 mm apertures | spec <2×10⁻⁴ rms |
| **IRcell-S15** (2020) | 65 confocal segments | **15.12 m** | Ø194×32 | 128 mL | 118 m/L | two 5 mm apertures | spec <2×10⁻⁴ rms |
| Graf 2018 prototype | segmented ring, CNC Al + Ni-P + Au | 9.89 m | ~Ø155 ring, 198 g | 140 mL | 70 m/L | apertures at segments 0+33 | NEA 2×10⁻⁵ (1σ) short-term; 2.64×10⁻⁴ (2σ) at 1 s compact |
| Tuzson 2020 drone version | same SC-MPC, damped | 10 m | 2.1 kg instrument | 140 mL | 70 m/L | apertures | absorption noise 5.8×10⁻⁶ → 1.1 ppb CH₄ @ 1 s |
| Chang 2020 multi-layer toroid | toroid + absorption mask | 8.3 / 10 m | Ø~100 class | 63 / 94 mL | 106–132 m/L | side coupling + mask | "fringe effect < 0.5 %" with mask |
| Empa NO₂ (Mangold-type, AMT 2018) | circular paraboloid + mask | 12.2 m | Ø145 | — | — | off-axis + 4 mm mask holes | 0.23 ppb @ 1 Hz but baseline re-zeroed every 18–20 min |
| **ours, drone_20m** | 16 discrete CM254 gold mirrors, chord-skip k=9 | **20.38 m** | Ø180×~31 | 290–500 mL | 70 m/L (min chamber) | one 2.6 mm hole in mirror 0 | worst spot-pair power overlap 5.8×10⁻⁶ (§3) |
| **ours, drone_14cm** | 12 mirrors, k=17 | **20.66 m** | **Ø141**×~29 | 200–264 mL | 103 m/L (min chamber) | one 2.6 mm hole | worst pair 1.7×10⁻⁵ power |
| **ours, drone_29m** | 12 mirrors, k=17 | **28.99 m** | Ø183 | 331–520 mL | 88 m/L (min) | one 2.6 mm hole | worst pair 4.2×10⁻⁴ power |

Sources: IRcell datasheets (laser2000.co.uk mirror of IRsweep S15 sheet;
archive.org S4/4M sheets); Graf 2018 Opt. Lett. 43, 2434 (note: page 2434,
not 2665); Tuzson AMT 13, 4715 (2020); Chang Opt. Lett. 45, 5897 (2020);
Ghorbani & Schmidt Opt. Express 25, 12743 (2017) + Appl. Phys. B 123:144.

**Where we win:** path per envelope (20.4 m vs 15.1 m in a smaller disc;
20.7 m in Ø141 where nothing published exceeds ~10 m), verified throughput
(86.7 % at R=0.999; IRcell publishes no laser-coupled figure, only ~60 %
broadband FTIR coupling), catalog mirrors instead of diamond-turned
monolith, and a smaller total open aperture (one Ø2.6 mm hole = 5.3 mm²
vs two Ø5 mm = 39 mm²).

**Where the IRcell wins (the honest downsides):** (a) sealed sample volume
— 31–128 mL vs our 200–330 mL minimum chamber: their disc is hollow only
where the beam lives, ours must enclose near-diameter chords crossing the
full disc; (b) coupling tolerance — their collimated-input apertures accept
±0.5–0.75°, our mode-matched hole wants flight-grade build or one
alignment session (that is exactly the tolerance-tier structure of our
menu); (c) product maturity — theirs is a shipping commercial part with a
measured fringe spec, ours is a verified design.

## 3. "Overlap factor" and whether our beams overlap

"Overlap factor" is not a standardized multipass figure of merit (it is a
hollow-core-fiber term); the two quantities actually used in the MPC
literature are the **binary spot-non-overlap rule** and the
**path-to-volume ratio**. We therefore report a graded version of the
first — which the literature never quantifies — and the second in §4.

**Spot-overlap suppression.** The fringe mechanism is scatter at one
mirror spot coupling into the beam direction of a nearby spot (Aerodyne
patent US8531659; measured by JPL: the dominant fringe in a Herriott cell
came from "scattering between neighboring spots", Webster et al., Appl.
Opt. 60, 1958, 2021). For two Gaussian spots of radii wᵢ, wⱼ separated by
d on a mirror, the field-amplitude coupling is
η = (2wᵢwⱼ/(wᵢ²+wⱼ²))·exp(−d²/(wᵢ²+wⱼ²)) (power η²). Exact-trace values
over **every spot pair on every mirror**:

| design | worst pair d | d/w̄ | field coupling η | power η² | pairs with η²>10⁻⁴ |
|---|---|---|---|---|---|
| drone_29m (29.0 m) | 1.24 mm | 2.79 | 2.1×10⁻² (−34 dB) | 4.2×10⁻⁴ | 2 of 15 259 |
| drone_25m (24.8 m) | 1.24 mm | 3.84 | 6.3×10⁻⁴ (−64 dB) | 4.0×10⁻⁷ | 0 |
| drone_14cm (20.7 m) | 1.47 mm | 3.31 | 4.1×10⁻³ (−48 dB) | 1.7×10⁻⁵ | 0 |
| **drone_20m (20.4 m)** | 1.54 mm | 3.55 | 2.4×10⁻³ (−52 dB) | 5.8×10⁻⁶ | 0 |
| 16.6 m / Ø160 | 1.27 mm | 3.54 | 2.0×10⁻³ (−54 dB) | 4.0×10⁻⁶ | 0 |
| 14.9 m / Ø133 | 0.93 mm | 3.38 | 3.3×10⁻³ (−50 dB) | 1.1×10⁻⁵ | 0 |
| 13.6 m / Ø143 | 1.54 mm | 4.59 | 2.6×10⁻⁵ (−92 dB) | 6.8×10⁻¹⁰ | 0 |

So: **no, the beams do not overlap** — the worst pair in the headline
design sits 3.6 beam radii apart, a −52 dB field-coupling margin *before*
multiplying by the gold-mirror scatter fraction (10⁻³–10⁻⁴ for catalog
gold) and the R^Δn propagation factor. The same quantity for the original
IRcell is effectively 0 dB (continuous beam superposition — that is why it
needs the absorption mask); for the IRcell-S it is set by segment-edge
clipping rather than spot spacing (their segments are sized x₀ = 2C·w with
C = 6.9, i.e. edge at 3.45w — comparable margin to ours, consistent with
both designs claiming mask-free operation). The Monte-Carlo tolerance runs
keep the p05 worst-pair separation ≥ the touching limit at the stated
build grades, so the margin survives construction error.

**Beam crossings in the volume** (the other "overlap"): our chords cross
1 000–15 000 times per pattern at 0.2–1.2° minimum / ~20–60° typical
angles. Crossing beams exchange no energy in a linear gas; interference
at the crossing exists locally but the fringe period λ/(2 sin(θ/2)) is
2.4–9.5 µm at the typical angles — hundreds of periods across any
detector, integrating to zero (sinc-envelope visibility). Only fields
that *co-propagate to the detector* matter: mirror-spot scatter (bounded
above), window surfaces (wedged — see window study), and hole-edge
clipping. Our hole keeps ≥ 2× the beam diameter clear (w(hole) = 0.32–0.48
mm in a 1.3 mm-radius hole), which is the explicit McManus criterion for
fringe-free coupling (patent US7307716), and intermediate-spot hole
clearance ≥ 0.35–4.2 mm at MC p05 keeps the far Gaussian tail (< e⁻⁸) as
the only edge illumination.

## 4. Will the OD noise be worse? (prediction, mechanism by mechanism)

| mechanism | IRcell(-4M) | IRcell-S | ours |
|---|---|---|---|
| spot/beam superposition on mirror | continuous (mask required) | none (1 spot/segment, edge at ~3.45w) | none (worst pair ≥ 2.8–4.6 w̄, −34…−92 dB) |
| coupling aperture | 4 mm hole, in/out 28° | two 5 mm apertures | one 2.6 mm hole, ≥2× beam dia, clearance MC-verified |
| surface micro-structure scatter | diamond-turning tool marks (7.9 µm period — Graf traced residual fringes to exactly this) | same fabrication | polished catalog mirrors, λ/10, no periodic structure |
| windows | tilted CaF₂ | tilted options | 30-arcmin wedged + 3–5° mount (23× measured fringe suppression for wedged vs plane, Masiyano; ~30× Brewster-spoiler benchmark) |
| mask edges | Teflon mask in beam | none | none |

Expected outcome: our fringe floor should sit in the same class as the
segmented cell — NEA ~2×10⁻⁵ (1σ) short-term, the drone-flown version of
which measured 5.8×10⁻⁶ absorption noise — and clearly below the masked
toroids (< 0.5 % *with* mask). Two caveats to state in the paper: (1) we
have 9–19 spots per mirror vs their 1 per segment, so we rely on the
*enforced graded margin* rather than topology — this is the novel,
quantified design rule (d/w ≥ 3.3 worst case, MC-guarded); (2) our
per-mirror reflection count is higher and R=0.999 gold scatter must be
included in the stray-light budget; the −34 dB worst design (29 m) is the
one to watch, and its two warm pairs are between bounces 100+ apart, so
their interference term is further suppressed by R^Δn/2 ≈ 0.95 and by the
√T path attenuation. For H₂ at 2121.8 nm the line is sub-Doppler
(HWHM ≈ 0.013–0.02 cm⁻¹), so etalons with FSR near the linewidth — OPDs
of tens of cm, i.e. chord-scale parasites — are the dangerous ones; the
spot-separation margin is therefore *more* valuable for the H₂ channel,
and the wedged window (OPD mm-scale, FSR ~0.5–1 cm⁻¹) stays benign.

Bottom line for the professor: **beams do not overlap; the OD-noise
mechanisms that forced masks and baseline cycling on the toroidal family
are absent by construction and by enforced margin; the realistic
prediction is IRcell-S-class NEA (10⁻⁵ decade) with 3–5× more path in the
same or smaller disc.** The claim to print is the conservative one:
"comparable to or better than the 2×10⁻⁵ demonstrated for the segmented
circular cell, without absorption masks" — a measured number must wait
for the build.

## 5. Volume of the disc (the honest comparison)

Two volumes matter, and we should quote both:

* **V_min** — chamber just tall enough for the beam envelope (+3w +1 mm
  machining): 117–331 mL across the menu (20.4 m design: 290 mL; Ø141
  design: 200 mL; 13.6 m: 127 mL).
* **V_full** — simple lid-and-ring build enclosing the 1″ mirrors: 224–520 mL.

Path-to-volume: 70–127 m/L (V_min). The IRcell-S4/S15 sit at 118–130 m/L,
the Graf prototype at 70 m/L, Chang's masked toroids at 106–132 m/L. So
per litre we are **at parity with the published toroidal family**
(70–127 vs 70–132 m/L) while carrying 2–5× their absolute path; the
S4-class sealed volume itself is unreachable for a chord-skip disc because
near-diameter chords sweep the whole disc area — that is the geometric
price of the k-fold path gain, and the paper should say so plainly.

Compensating factors worth stating: (a) drone leak-detection wants fast
gas exchange — at 1 SLM the 200–290 mL chamber turns over in 12–17 s, and
the cell runs open/flow-through exactly as IRsweep advertises for the
IRcell-S ("without top and bottom lids"); a mesh-walled or slotted-lid
variant makes the TMPC a zero-exchange-time open-path cell with the same
optics; (b) height: our chamber is 29–31 mm tall like theirs (32 mm);
(c) if sealed-volume-per-path is the mission driver, the compact Ø141
design (103 m/L) is the right pick from our menu, not the Ø180.

## 6. One-line summary table for the paper

| metric | IRcell-S15 (best commercial) | TMPC drone_20m | TMPC drone_14cm |
|---|---|---|---|
| OPL | 15.12 m | **20.38 m (+35 %)** | 20.66 m |
| envelope | Ø194 × 32 mm | **Ø180 × 31 mm** | **Ø141 × 29 mm** |
| gas volume | 128 mL | 290 mL (min chamber) | 200 mL |
| PVR | 118 m/L | 70 m/L | 103 m/L |
| throughput | not published (~60 % broadband FTIR) | **86.7 % verified** | 81.6 % |
| fringe strategy | 1 spot/segment (custom diamond-turned monolith) | enforced d/w ≥ 3.3 margin (catalog mirrors) | same (d/w ≥ 3.3) |
| coupling | two 5 mm apertures | one 2.6 mm hole | one 2.6 mm hole |
| mirrors | custom monolith | **catalog CM254 + one drilled** | catalog + one drilled |
