# SuperconducTED logo, round 3: shared brief for the four style agents

## The project

SuperconducTED is a student research organisation (TED University, Ankara). Its flagship,
`superconducted-noise-engine`, is a fuzzy-logic noise engine for Qiskit Aer quantum-computer
emulators. Qiskit Aer's `NoiseModel` takes crisp numbers (T1, T2, gate error, readout error)
from ONE calibration of an IBM superconducting quantum computer, but the real machine drifts
between calibrations. The engine ingests every calibration snapshot and answers with an
interval (a range) that brackets the real hardware, instead of one crisp number.

## The story the mark must tell (approved by the owner)

> Qiskit can describe an IBM quantum computer in one line, `NoiseModel.from_backend`. It reads
> the machine's latest calibration and freezes it into one noise model. The machine does not
> stay frozen: its chip hangs at the bottom of a dilution refrigerator, about a hundredth of a
> degree above absolute zero, and its noise still drifts from one calibration to the next.
> SuperconducTED keeps every calibration and answers with the range the machine actually moves
> through: not one crisp number, but an interval that brackets the real hardware.

A stranger looking at the mark with no label should come away with: **real quantum hardware**,
**noise that drifts**, **ranges, not single numbers**.

## Elements the owner chose (ALL FOUR must appear and each must carry its meaning)

1. **The chandelier**: the dilution refrigerator, the hanging stack of plates that gets colder
   toward the bottom; the chip is mounted at the lowest, coldest plate. Typical commercial
   fridges have a room-temperature top flange, then plates for roughly 50 K, 4 K, the still,
   the cold plate and the mixing chamber (about 10 to 15 mK), joined by support rods, with
   coaxial cables running down through the stages (in photos they curve and loop between
   plates). Draw a believable, detailed chandelier, not generic tiers. Do NOT write any stage
   names or temperatures into the artwork.
2. **The calibration dial / ring**: a graduated ring with tick marks; its centre or index mark
   is where the frozen calibration (the snapshot) says the machine is.
3. **The drifting chip**: the qubit chip, visibly moved off that aim point (an offset, a trail
   of earlier positions, or similar). It must still sit inside the range.
4. **Interval brackets**: the [ ] of an interval, marking the range the engine reports. They
   must bracket the drifting chip / reading.

## The owner's verdict on earlier rounds (why this round exists)

- Round 1 (an "=" bending into "≈", three variants): "none of it really explains the project".
- Round 2 (three flat icons: a chandelier with a pendulum, a crosshair ring with a chip, a chip
  in brackets): "oversimplicity is the problem ... no logo should resemble the same graphic
  concepts others use ... overlook the simplicity concept and create more depth and detail ...
  something that should be marvelous".
- So: depth, detail, craft, a unique style that stands out. Nothing a stock-icon set ships.

## Hard constraints (the owner's production requirements still apply)

- **Single-colour reproducible.** No gradients, no drop shadows, no transparency effects, no
  raster textures. Depth comes from line work: hatching, stroke-weight hierarchy, solid vs
  outline, negative space, facets in flat tints. The mark must still read in solid black on
  white and solid white on black.
- **Responsive system.** A detailed hero for 128 px and up AND a redrawn small companion mark
  for 16 to 32 px (favicon), clearly from the same family (not a scaled-down hero).
- **At least three distinct stroke weights**, and at least one passage a viewer would want to
  zoom into.
- **Colours for now: two neutral tones only** (the palette is deliberately deferred):
  ink `#1A1D24`, paper `#F2EEE6`. Also show solid black `#000000` on white and solid white on
  black.
- **Text:** only "SUPERCONDUCTED" (any casing; the brand writes it SuperconducTED) and,
  optionally, "NOISE ENGINE". No other words, numbers, dates or labels. No em dashes or en
  dashes anywhere (in artwork or notes); use commas, colons, middle dots.
- **Trademarks:** no IBM logo or its eight-bar stripes, no Qiskit logo, no IBM blue `#0F62FE`,
  no Qiskit purple `#6929C4`, no IBM processor or bird names (Heron, Eagle, ...), no TED or
  TED University emblem, no people's names.
- **Keep it distinct from the CASSANDRA Collective brand** (a ring with three forecast dashes,
  night + bronze + gold, Source Serif 4 + Inter): do not use Source Serif 4.
- **Fonts available in VectorCraft:** Space Grotesk (Regular, Medium, Bold; installed for this
  project), Inter, Source Sans 3, Roboto, JetBrains Mono. Do not use IBM Plex (reads as IBM).
  Convert text to outlines before exporting SVG (`type.createOutlines`).

## Tools (Windows; use these exact paths)

- Python: `C:\Users\senso\AppData\Local\Programs\Python\Python312\python.exe` (run with `-I`;
  add the tools folder to `sys.path` inside your script). No PIL/numpy; standard library only.
- VectorCraft 0.10 headless engine via the MCP client
  `...\scratchpad\tools\vcdriver.py` (class `VC(root)`; `vc.tool(name, **args)` calls MCP tools
  such as `draw_path`, `draw_shape`, `add_text`, `export`; `vc.cmd(id, **params)` runs any engine
  command such as `file.new`, `select.set`, `stroke.set`, `object.path.outlineStroke`,
  `object.pathfinder.unite`, `object.pathfinder.intersect`, `type.createOutlines`,
  `text.setStyle`, `object.group`, `file.close`). `root` confines every file the engine reads
  or writes, so pass your own output folder.
- Geometry helpers you may import or copy (do NOT edit the shared file):
  `...\scratchpad\tools\sc_marks.py` (`capsule`, `circle`, `ring`, `rrect`, `chip`,
  `arc_band`) and `place(d, x, y, s)` in `...\scratchpad\tools\sheet2.py` (scales unit-box path
  data). The round-2 marks in `sc_marks.py` are the REJECTED simple versions; go far beyond them.
- VectorCraft gotchas: coordinates are y-down from the artboard's top-left; new shapes get a
  1 pt black stroke unless you pass `stroke="none"`; stroke weight is `strokeWidth`; caps and
  joins via `vc.cmd("stroke.set", cap="round", join="round")` on the selection; new objects
  become the selection; `object.setBounds` positions from the centre unless `reference=0`;
  `export` to .png is transparent unless you draw a background; `export(..., scale=s)` sets
  pixels per point; one document per deliverable (`file.new` then `file.close`).
- Hatching: the simplest robust route is analytic clipping in Python (compute line segments
  clipped to circles, rectangles or polygons yourself), drawn as thin filled capsules or
  stroked lines. `object.pathfinder.intersect` also works on a selection (back to front).
- You can LOOK at your own renders with the Read tool on the PNG. Do it after every render.

## Required outputs (in your own folder only)

- `build.py`: the script that draws everything (all numbers in it).
- `hero.svg` and `hero-1024.png` (the detailed primary mark on paper, 1024 px square).
- `hero-black.svg` (solid black on transparent) and `hero-white-on-black.png`.
- `small.svg`, `small-32.png`, `small-16.png` (the favicon companion).
- `sheet.png`: one presentation sheet, about 2000 px wide: the hero LARGE (at least 900 px),
  the hero on a dark ink ground, solid black, the hero at 128 and 64 px, the small mark at 32
  and 16 px, and a lockup with the word SuperconducTED.
- `NOTES.md`: the stranger's caption (one line); how each of the four elements maps to the
  story (one line each); the three stroke weights; the passage worth zooming into; what you
  would improve with more time; an honest self-assessment, including where it fails.

## Quality loop (mandatory)

Render, look at the PNG, critique it as a senior brand designer would (does it read as a
chandelier? is the chip clearly drifted yet inside the brackets? is the detail beautiful or
just busy? does it survive at 128 px? does the small mark read at 16 px?), fix, and repeat at
least three times before you stop. Keep the files you end with; delete nothing outside your
folder and touch no git repository.
