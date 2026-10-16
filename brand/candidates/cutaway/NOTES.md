# SuperconducTED round 3: technical cutaway

One candidate mark in the style of a mechanical engineering drawing: a side elevation of a
dilution-refrigerator chandelier whose lowest stage turns into a graduated magnifier dial, all
on one shared centre line. Everything is drawn by `build.py` in VectorCraft from pure-Python
geometry; rerun it to regenerate every file (about 1.5 s).

## Stranger's caption

A quantum computer's refrigerator drawn like a blueprint: at its cold bottom a dial shows the
chip has drifted off its calibrated centre, and bold brackets mark the range it moves within.

## The four elements and the story

1. **Chandelier**: a sectioned side elevation of the fridge, six plates tapering downward (top
   flange, then five colder stages, no names or temperatures drawn), joined by rods, crossed by
   a still pumping line, a pulse-tube cold head with two heat stations, a still pot, a helical
   continuous heat exchanger, three step heat exchangers, a mixing-chamber pot with its phase
   boundary, a four-line coax loom swaying between stages with clamps under every plate, and
   two output lines with an amplifier and two circulators; a cold finger carries it all down
   to the dial. It says "real hardware, hung in a cryostat, coldest at the bottom".
2. **Calibration dial**: the magnifier ring under the coldest plate, a solid band with a fine
   baseline, 3 degree graduations, 15 degree major ticks and a knurled bezel. Its index
   triangle and its dash-dot crosshair sit on the fridge's own centre line, and a drafting
   datum symbol (centre-of-mass circle, two quadrants solid) marks the crossing: that point is
   where the frozen calibration, the one `NoiseModel.from_backend` snapshot, says the chip is.
3. **Drifting chip**: the solid chip (a 3 x 3 lattice of cross-shaped qubits knocked out of the
   die) sits clearly right of the datum; an earlier position is drawn in phantom line, the
   drafting convention for the alternate positions of a moving part, joined to it by a dashed
   drift path with an arrowhead; a numeral-free dimension line measures the drift from the
   datum.
4. **Interval brackets**: bold solid [ ] that enclose every position, past and present, with a
   numeral-free dimension line spanning them. The snapshot point sits inside the interval but
   not at its centre: the range is what the machine actually moves through, not a symmetric
   error bar around the frozen value.

## Stroke weights (hero design space 1000 units = 1024 px)

| Role | Weight | At 1024 px | Used for |
|---|---|---|---|
| Heavy | 7.0 units | 7.2 px | plate sections (butt caps, round joins) |
| Medium | 3.4 units | 3.5 px | rods, tubes, coax and output lines, pots, 15 degree ticks |
| Fine | 1.4 units | 1.4 px | 45 degree section hatching, centre lines, phantom and hidden lines, dimension lines, minor ticks, knurl |

Solid fills sit above the strokes: the dial band (10 units), the brackets (12 units), the
chip, clamps, bolts, index, arrowheads, datum quadrants. Line types follow drafting practice:
section hatching alternates direction between adjacent parts and is globally registered;
centre lines are long-short; phantom lines long-short-short; hidden lines (the back half of
the helix) short dashes.

## The passage worth zooming into

The bottom of the stack and the dial interior: the helix whose front turns are solid and back
turns hidden-dashed, the hatched step heat exchangers, the sectioned mixing-chamber pot with
its phase boundary, the circulators with their ferrite discs, and inside the dial the knocked
out qubit lattice, the datum symbol, the phantom chip with its centre mark and the dashed
drift path. The plates also reward a look: each bore stops the section exactly at the tube
wall, so the hatch breaks where the pumping line, the pulse tube and every cable pass through.

## Small companion mark

`small.svg` is a separate bold redraw on a 32-unit grid with every edge on a whole unit:
a 3-unit dial band, the snapshot index on the axis, the chip 4 units right of it, and bold
brackets 0.8 units or more clear of the band. Because a 32-grid master halves to half-pixel
edges, `small-16.png` comes from a hinted 16-grid variant, `small-16.svg` (1-pixel brackets,
3-pixel chip, symmetric layout). The hero is not usable below about 96 px; switch to the
small mark there.

## Files

`build.py` (all numbers), `hero.svg`, `hero-1024.png`, `hero-black.svg`, `hero-white-on-black.png`,
`small.svg`, `small-32.png`, `small-16.svg`, `small-16.png` (rendered from `small-16.svg`, not
from `small.svg`), `sheet.png` (2000 x 1540). `check-*.png` are my own inspection renders
(hero at 128 and 64 px, and nearest-neighbour enlargements made by `upscale.py`).

Verified on the exported files, not on the in-memory geometry:

- `hero-black.svg` paints only `#000000` and `none`, with no background, opacity, gradient,
  filter, image or text element (grep).
- Every knockout survives export: `check_svg.py` parses the filled paths of `hero-black.svg`,
  `small.svg` and `small-16.svg` and evaluates the nonzero winding rule at 24 probe points
  (nine qubit holes, the guard-ring gap, chip body and rim, dial interior and band, both datum
  quadrant states, the small marks' rings, chips and brackets); all 24 match.
- Every SVG `<title>` is "SuperconducTED", the only word in any mark file; no en or em dash in
  any file in this folder.

## What I would improve with more time

- Thin the middle of the stack: the pumping line, still pot, helix, step exchangers, mixing
  pot and circulators crowd one narrow band; a second pass would move the circulators lower
  and give the helix more height.
- Draw the coax as true semi-rigid runs (straight lengths with tight radiused bends) instead
  of smooth sways, which still read slightly organic next to the ruled geometry.
- Add the radiation shields as phantom cans around the lower stages, which would deepen the
  cutaway reading, once a way is found to keep them from fighting the dial.
- Test the hero at 96 to 160 px against real UI contexts and set a formal switch-over size.

## Honest self-assessment

- Strength: the story is told by one continuous centre line, from the cryostat axis through the
  index to the datum, and the drift is the only thing that breaks the symmetry, so the eye
  lands on it; every element uses a real drafting convention, which gives craft and a style
  no stock icon set ships.
- Weakness: it is an emblem-illustration more than a logo; at 64 px it is a grey silhouette,
  the dial can still read as a watch or pocket-watch face to some viewers, and the
  chandelier's resemblance to the real thing depends on having seen fridge photos.
- Risk at small sizes: the favicon is a ring with marks inside it, which is the family most
  likely to be confused with CASSANDRA's ring-and-dashes mark at 16 px; the square chip and
  square brackets are the differentiators and should be kept bold in any revision.
