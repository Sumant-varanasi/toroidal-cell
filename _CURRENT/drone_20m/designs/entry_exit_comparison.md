# Entry/exit through a holed mirror vs entry from the side

*(Analysis for Dr. Benoy's question, 2026-07-08: "You mentioned holed
mirrors for entry and exit, compare this with entry and exit from sides.")*

## The one-line answer

In a chord-skip ring the coupling hole is a **transverse-selective
aperture**: the beam pattern revisits the entrance mirror's azimuth every
N chords but at a *different point on the mirror face* each time (that is
the k-spot constellation), and only the k-th, designed visit falls on the
hole. A side slot (gap between mirrors, scraper edge, or a removed
mirror) selects only by **azimuth** — it cannot tell the k visits apart —
so the beam escapes at its *first* return, capping the cell at N chords.
The hole is therefore worth a factor of exactly **k = spots per mirror
(9–19×)** in optical path for the same ring.

## Why a side-entry beam cannot join the pattern

Every chord of the re-entrant pattern terminates on a mirror at both ends
(that is what a reflection sequence means), so the outward extension of
any pattern chord is blocked by a mirror substrate. An external beam can
only be introduced by *opening* the pattern somewhere:

* **Hole in mirror 0** — opens one point of the constellation. The beam
  enters along the true chord direction, all closure/AOI conditions are
  preserved, intermediate visits land beside the hole (verified: hole
  clearance ≥ 0.35–4.2 mm at the 5th percentile across the build
  Monte-Carlo) and the k-th visit exits through the same hole at 2×AOI
  from the input axis.
* **Side slot / removed mirror / scraper** — opens a whole azimuth. The
  beam enters correctly and follows the same chords, but when j·s ≡ 0
  (mod N) — after exactly N chords, since gcd(s, N) = 1 — it arrives at
  the open azimuth and leaves, regardless of where on the face it would
  have landed. n_side = N chords, always.

## The numbers, per robust design (exact-trace values)

| design | N | k (spots/mirror) | hole OPL | side-slot OPL (N·L) | hole gain | physical gap between mirror edges |
|---|---|---|---|---|---|---|
| 29.0 m Ø183 (CM254-750) | 12 | 17 | **28.99 m** | 1.71 m | **17.0×** | 12.7 mm |
| 24.8 m Ø180 (CM254-200) | 16 | 11 | **24.77 m** | 2.25 m | **11.0×** | 2.6 mm |
| 20.7 m Ø141 (CM254-500) | 12 | 17 | **20.66 m** | 1.22 m | **17.0×** | 1.7 mm |
| 20.4 m Ø180 (CM254-150) | 16 | 9 | **20.38 m** | 2.26 m | **9.0×** | 2.8 mm |
| 16.6 m Ø160 (CM254-150) | 13 | 11 | **16.60 m** | 1.51 m | **11.0×** | 4.3 mm |
| 14.9 m Ø133 (CM254-150) | 10 | 19 | **14.85 m** | 0.78 m | **19.0×** | 4.5 mm |
| 13.6 m Ø143 (CM254-250) | 12 | 11 | **13.64 m** | 1.24 m | **11.0×** | 2.3 mm |

The "physical gap" column shows a side aperture *is* geometrically
available (1.7–12.7 mm between substrate edges) — the objection is not
mechanical, it is that using it forfeits the dense pattern. A side-entry
version of the Ø180 ring would deliver 2.3 m instead of 20.4 m.

## Where side entry IS the right choice

Side/gap coupling is exactly what single-orbit ring cells use (star-
polygon toroidal cells with one pass per mirror azimuth): with k = 1
there is nothing for a hole to select, and skipping the drilled mirror
saves a custom part. Our architecture's entire advantage is k > 1, so it
inherits the hole requirement. The commercial segmented-ring cells sit in
between: their patterns revisit each azimuth a few times and they couple
through a small opening in the mirror surface for the same reason we do.

## Engineering notes on the holed mirror

* **One custom part.** Only mirror 0 is modified: a 2.6 mm bore in a
  catalog CM254 substrate (drill/ultrasonic from the back face,
  countersink the rear to a cone so only a ~0.5 mm land of coated surface
  is removed at the edge). All other N−1 mirrors are stock.
* **No transmission penalty.** The injection is mode-matched (w at the
  hole 0.32–0.48 mm vs the 1.3 mm hole radius), so hole transmission is
  ~100 % and T = R^(chords−1) exactly.
* **Entry = exit = one window.** The exit beam re-images through the same
  hole (round-trip ABCD ≈ identity) at 2×AOI from the input axis — one
  wedged window and one detector pickoff behind mirror 0 serve both,
  which is also the lowest-leak-count gas envelope. A side-entry cell
  needs a window in the curved wall plus a separate exit port.
* **Hole-edge scatter.** The dangerous mechanism is an intermediate spot
  grazing the bore edge; that is an explicit design check (hole clearance
  ≥ beam edge + build-walk budget) and is Monte-Carlo verified per
  design, so edge scatter is bounded by the far Gaussian tail
  (< e⁻⁸ ≈ 3×10⁻⁴ of a pass at worst-case walk).
