# What "active alignment" actually requires (Tier-3 actuation spec)

The active-alignment tier holds the architecture's showcase numbers —
38.6 m/Ø169, 26.7 m/Ø157, 22.0 m/Ø155 (1″) and 19.3 m/Ø93/37 mL (½″) —
but "needs active alignment" is only a useful statement with numbers
attached. From the 400-trial Monte-Carlo runs (`results_tol_27m`,
`results_tol_24m_h2`) and the tier menus:

## The gap to close

At the flight build (0.1 mrad class) the Tier-3 designs complete their
full path in ≥ 90–100 % of trials — the pattern survives; what fails is
the *passive* spot bookkeeping: pattern walk p95 of 0.8–3.7 mm against
hole clearances of ±0.5 mm and pair separations of 0.03–0.36 mm. The
actuators must therefore recover ~1–3 mm of coherent pattern walk, not
re-create the pattern.

## Sensitivity ordering (drone_27m 400-trial, exit-drift metric)

| error source | contribution at 1σ | note |
|---|---|---|
| mirror ROC (σ 0.5 mm) | ~200 mrad-class dominant term | measure-and-trim at assembly (0.75 mm ring trim per 1 % ROC — linear law) |
| ring radius (σ 30 µm) | ~6.7 | the in-situ fine knob |
| mirror axial decenter | ~1.5 | machining |
| mirror lateral decenter | ~0.8 | machining |
| launch tilt/position | ~0.1–0.2 | the fast knob |

The ordering says: (1) ROC error is absorbed **once**, at assembly, by
machining the ring to the measured-ROC trim table (all designs show the
linear law, 0.52–0.75 mm per 1 %); (2) residual drift in operation is a
*ring-radius-equivalent* effect at the µm scale plus launch pointing.

## The actuator set (all catalog parts)

1. **Ring thermal trim** — gain α·R_ring = 1.2–1.7 µm/K (Al). A ±10 K
   foil-heater loop = ±12–17 µm of ring radius at millikelvin-limited
   resolution ≪ 1 µm: covers the entire post-assembly closure residual
   for every Tier-3 design. Time constant minutes — the slow loop.
2. **Launch tip/tilt piezo** — exit-drift p95 at flight grade is
   3–15 mrad across the menu; a ±5 mrad piezo tip/tilt with sub-50 µrad
   resolution (any catalog piezo mount) closes pointing in real time —
   the fast loop.
3. **Error signal** — the exit beam itself: a quadrant/position detector
   behind the mirror-0 hole reads walk directly; maximize transmitted
   power + center the quad. No in-cell sensor, no extra optical port.

This is a two-loop controller on two catalog actuators — the same
actuator set the standard build already carries as the one-time trim
(heater + adjustable launch); Tier-3 just runs it closed-loop. The cost
delta over a passive cell is the piezo mount and a quad detector
(~$400–700), which buys +50 % path (25.7 → 38.6 m) in a smaller disc, or
the Ø93/37 mL PVR showcase.

*Caveats: the MC treats the drone vibration spectrum only through the
0.1 mrad flight tolerance class; the closed-loop bandwidth needed against
rotor-band (60–700 Hz) excitation of the *launch* path is set by the
damped-mount transmissibility and should come out of the Fusion-360
modal study on the shipped STEP models.*
