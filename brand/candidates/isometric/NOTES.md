# SuperconducTED round 3: the isometric illustration candidate

## Stranger's caption

A cryogenic machine hangs over a measuring dial; its chip has wandered off the dial's centre
mark, and a pair of square brackets frames the whole range it wandered through.

## How the four elements carry the story

* **Chandelier:** the real machine, a tapering stack of cold plates with rods and coax.
* **Dial:** its centre, on the chandelier's axis, is where the frozen snapshot says the chip is.
* **Chip:** off that centre and twisted, at the end of a trail of every calibration kept.
* **Brackets:** [ and ] on the dial bound the whole trail and the chip: the interval reported.

Detail:

1. **Chandelier (real hardware):** six plates that narrow toward the bottom (top flange, four
   intermediate stages, mixing-chamber plate), joined by support rods, with eight coaxial lines
   S-bending and looping down through every stage, an attenuator on each plate, a pulse-tube
   cold head, a helical heat exchanger running between the still pot and the mixing-chamber pot,
   and a breadboard of tapped holes on the coldest plate. No stage names, no temperatures.
2. **Calibration dial (the frozen snapshot):** below the coldest plate hangs a dial: a flat
   face inside a raised bezel graduated every 3 degrees (bolder every 15, full-width at the four
   cardinal points). Its centre sits on the chandelier's axis, drawn as a dashed plumb line, and
   is marked by a small aim ring: that is where the one calibration Qiskit froze says the chip
   is. A dashed ghost of the chip sits square on it.
3. **Drifting chip (noise that drifts):** the real chip package (a die with a 2 x 2 qubit
   lattice, couplers and bond wires, three connectors with coax from the mixing-chamber plate)
   has moved off the aim point and twisted 24 degrees. A trail of dots, one per kept
   calibration, wanders from the ghost to the chip: the machine did not jump, it drifted.
4. **Interval brackets (ranges, not single numbers):** an extruded [ and ] stand on the dial
   face, turned 20 degrees toward the viewer, with a tinted range zone between them whose front
   edge is finely graduated. The zone holds the ghost, the whole trail and the chip: the range
   the engine reports brackets the real hardware.

## Construction

* One orthographic camera for everything: azimuth 0, elevation 22 degrees, so every circle is an
  ellipse of axis ratio sin 22 = 0.375. The model is built in 3D in `build.py` and projected; the
  chip and the brackets are rotated in plan so they show three faces.
* Painter's order: dial stage first, then the space under the coldest plate, then plate by plate
  upward; inside each gap, rods, coax, attenuators, pots and the helix are sorted far to near by
  camera depth. Prisms (the brackets) paint side faces far to near, then the front cap.
* Depth is flat facets only: top faces in paper, faces turned left in the light tint, faces
  turned right in the shade tint, the chip package one step darker, the bracket fronts in full
  ink. No gradients, shadows or transparency anywhere.
* The drift trail is a Brownian bridge through seven waypoints: on each leg, Gaussian steps of
  standard deviation 0.014 world units are summed into a walk w(i), i = 0..7, and the bridge
  w(i) minus (i / 7) w(7) is added to the straight leg, so the noise is exactly zero at every
  waypoint. The seed is fixed (11), so the drawing is reproducible.
* One-colour files are real knockouts, not white paint: the art is painted in black and white,
  every stroke is outlined, VectorCraft's pathfinder merge keeps only the topmost colour of each
  visible region, the white regions are deleted, and the result is re-exported. `build.py`
  asserts that only one fill colour remains (`#000000` in hero-black.svg, `#1A1D24` in
  small.svg), with no strokes and no opacity.

## Palette (two neutrals, tints mixed per RGB channel)

| Role | Paper ground | Dark ground (inverted ladder) | One colour |
|---|---|---|---|
| ground, top faces | `#F2EEE6` | `#1A1D24` | white / transparent |
| light facet | `#C7C4BF` (20 % ink) | `#45474B` (80 % ink) | white / transparent |
| shade facet | `#7B7B7B` (55 % ink) | `#91908F` (45 % ink) | hatching, 1 px lines |
| ink: lines, bracket fronts, die | `#1A1D24` | `#F2EEE6` | `#000000` |

On the dark ground the tone ladder is inverted (t becomes 1 minus t), which keeps the contrast
order: what is darkest on paper becomes brightest on ink, so the brackets and the chip still lead.

## The three stroke weights (at the 1024 px hero, 209.6 px per world unit)

| Weight | Width | Used for |
|---|---|---|
| W1 | 4.4 px | silhouettes of the big parts: plates, bezel, chip package, central port, cardinal ticks |
| W2 | 2.2 px | internal edges, small parts (rods, attenuators, ports), bracket faces, major ticks, the snapshot ghost |
| W3 | 1.05 px | detail: minor ticks, bolts, bond wires, the drift trail, guide circle, hatching in the one-colour version |

Two cased lines sit outside the ladder on purpose: coax (4.4 px ink casing, 1.8 px light core)
and the heat-exchanger tube (3.4 px casing, 1.3 px core); the casing is what makes a tube read
as a tube.

## The passage worth zooming into

The dial stage: the twisted chip package with its die, qubit crosses, couplers and twelve bond
wires; the dashed snapshot ghost on the aim ring; the dotted calibration trail looping out toward
the left bracket and back to the chip; the graduated front edge of the range zone; the bezel's
foreshortened ticks, crowded at the back and open at the sides. A second passage is the helical
heat exchanger threading the bore of the cold plate down to the mixing-chamber pot.

## Files

| File | What it is |
|---|---|
| `build.py` | the whole drawing: geometry, painter, VectorCraft emission, exports (`python -I build.py`; `quick` for review renders) |
| `hero.svg`, `hero-1024.png` | the hero on paper, tinted |
| `hero-black.svg` | one colour, solid `#000000` on transparent, knockouts as real holes |
| `hero-white-on-black.png` | one colour reversed |
| `hero-dark.png`, `hero-128.png` | review renders: the tinted hero on ink, and the hero at 128 px |
| `small.svg`, `small-32.png`, `small-16.png` | the favicon companion (ink with knockouts; PNGs on paper) |
| `sheet.png` | presentation sheet, 2000 x 1300 |
| `_work/` | intermediates, review crops and the patch history of the loop |

## Quality loop (what each render showed and what changed)

1. First render: a credible chandelier, but at 128 px only "a stack" survived; brackets thin,
   chip tiny, index tab a crude black block, empty bottom gap, helix hidden behind plates.
2. Stronger taper, tighter bottom gap, bigger and darker chip and brackets, heat exchanger moved
   off-axis to the visible front-left, eight coax lines. The chip still overhung the ring edge.
3. Wider dial band and bigger chip: the brackets became pillars, but at 22 degrees the front of a
   ring is a sliver, so chip, ghosts and index piled up on the bottom edge.
4. Switched the dial to its centre reading: aim point at the dial centre on the chandelier's axis,
   chip displaced across the face, brackets on the face turned toward the viewer. The story now
   has room. Small mark redrawn with knockout halos (the first version fused into a trophy shape).
5. Range bar replaced by a tinted, graduated zone; richer top flange; fixed a layering bug that
   hid the aim point under the zone.
6. Drift trail of calibration dots (Brownian bridge), crosshair removed to declutter, coax service
   loops, one-colour pipeline shared by hero and small mark, lockup refit, a stray ring speck in
   the favicon removed.

## What I would improve with more time

* Make the drift louder at mid sizes: a larger dial (or a smaller chip) so the offset is half a
  chip width more, and a heavier first and last trail dot.
* Give the 64 px and 128 px uses their own simplified hero (fewer coax, no bolts, thicker W3),
  the way the favicon has its own redraw, instead of scaling the 1024 px drawing.
* Vary the coax rhythm between stages (today every plate shows the same row of attenuators) and
  add the radiation-shield flanges at the plate rims for more physical credibility.
* Optimise the SVGs: hero.svg is about 440 KB and hero-black.svg about 670 KB, because every
  curve is a sampled polyline. Fitting cubic Beziers would cut them by roughly an order of
  magnitude.
* Tune the favicon on a real pixel grid at 16 px (today it is drawn on a 16-unit grid but with
  half-unit coordinates, so some edges anti-alias).

## Honest self-assessment

* It works best large: at 300 px and up it is a detailed, believable machine with a clear
  [ chip ] story at its foot, and the one-colour engraving version is arguably the strongest
  artwork in the set.
* It fails at small hero sizes: at 128 px the chandelier reads as a tiered column and the [ ]
  survive, but the chip, the ghost and the trail vanish; at 64 px it is a grey column. The
  favicon carries the small sizes alone, and at 16 px even the favicon is mostly "[ block ]".
* The drift is the quietest of the four ideas: the offset is modest and its best evidence (ghost
  and trail) is fine line work.
* The composition is tall and narrow (about 0.56 wide to 1 high), so it fills a square poorly,
  and the dial with two upright brackets can be misread as a stand or a gate before it is read
  as an interval.
* The grey tints are neutral by brief; until the palette arrives the tinted hero looks more like
  a technical manual than a brand, which is a fair criticism of the style itself.
