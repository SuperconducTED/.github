# SuperconducTED round 3 · Engraved emblem / seal

## The stranger's caption

An engraved seal of a cryogenic quantum machine: its chip has swung off the dial's mark, and heavy brackets catch the whole range it moves through.

## How the four elements carry the story

- **Chandelier (real quantum hardware).** Six plates, from the room-temperature top flange down to the mixing-chamber plate, narrowing slightly as they get colder, joined by four posts per stage (two in front with hex nuts, two behind). Coax bundles change character stage by stage: a dog-leg jog, a row of staggered attenuators, a sideways service bow, a straight run and an S-bend. The central column runs from the pumping line and its clamped flange to the still pot, a heat-exchanger coil and the mixing-chamber pot. The whole stack hangs from the seal's own inner ring by two threaded rods and the pumping line. No stage names or temperatures appear anywhere.
- **Calibration dial (the frozen snapshot).** The seal's inner ring is the instrument's graduated scale: ticks every 2°, mid ticks every 10°, major ticks every 30°. A solid index triangle at six o'clock marks where the frozen calibration says the chip is, and a dashed plumb line joins it to the chip's pivot under the lowest plate.
- **Drifting chip (noise that drifts).** The solid chip, a sample holder with screws, bond wires and a dark die with four cross-shaped qubits and a feedline knocked out, hangs 20° off the plumb line. The dashed outline on the line is the snapshot's position, with an aim point. Dotted outlines are earlier positions. A small arc scale under the swing keeps one tick for every recorded position.
- **Interval brackets (ranges, not single numbers).** Two heavy engraved [ ] with a paper inline enclose every position, including the present one. The same interval is inked on the dial as a solid arc between bracket-shaped ends, so the range reads on the instrument's own scale. It is deliberately not centred on the index, because the real range is not centred on the snapshot.

## Stroke weights (model units; the hero renders at 1.024 px per unit)

| Role | Weight | Used for |
|---|---|---|
| Hair | 0.85 | hatching, face tone, interior ruling, guilloche, bolt rings, bond wires |
| Fine | 1.3 | minor ticks, fine rules, cables, ghost outlines, secondary contours |
| Medium | 2.2 | primary contours of plates, pots and tubes, mid ticks |
| Bold | 3.2 | shadow-side contours, band lower edges, bold dial rule, major ticks, the hanger rod |
| Heavy | 8.0 | outer seal ring |

The brackets, index, chip die, dial interval and lettering are solid fills, a sixth level above the strokes. The field ruling is 0.95 on a pitch of exactly 4 px at 1024. That pitch divides the pixel grid at 512, 256, 128 and 64 px, so the field renders as a flat tone instead of moiré bands; every hero placement on the sheet uses one of those sizes.

## The passage worth zooming into

The bracket window: the swung holder with its corner screws, bond wires and knocked-out qubits. Behind it sit the dotted ghosts, the dashed snapshot with its aim point, and the tick record of positions on the small arc. A close second is the heat-exchanger stage, where the coil's front turns cross in front of its tube and the back turns pass behind it, all inside a cross-hatched dark interior, with paper halos around every post and cable.

## Construction notes

- `build.py` draws everything. All geometry is computed in Python on a 1000 unit box: analytic clipping against convex polygons and ellipses produces the halos, knock-outs and occlusion. There are no paper-coloured overlays: every light passage is a real gap, so `hero-black.svg` and the white-on-black version are honest single-colour reductions.
- Lettering is Space Grotesk Bold, outlined in VectorCraft (`type.createOutlines`). Each glyph is then rotated rigidly onto the baseline circle, with tracking solved so that SUPERCONDUCTED spans 146°. NOISE ENGINE uses the same tracking and spans about 105°. Ornaments between the words are drawn stars of tick marks with dot trails, not font characters.
- No gradients, shadows, opacity, raster textures or live text in any SVG (checked with grep). Colours are ink `#1A1D24` and paper `#F2EEE6`, plus `#000000` and `#FFFFFF` for the solid versions.
- The small mark is a separate drawing on a 32 grid: seal ring, hanger rod, solid holder with a pocket, brackets in the same bar-and-serif shape, and the index triangle. Its chip sits 3 units right of the axis and 1.5 units clear of the right bracket. `small.svg` also carries a paper-coloured disc behind the ring, filling the seal's interior, so the favicon stays legible on dark browser tabs. On an ink ground (as on the sheet) the mark is drawn in paper with no disc.
- `work/` holds inspection helpers (`render2x.py`, `crop.py`, `montage.py`, `pnglib.py`) and the crops I looked at. None of them are needed to build.

## What I would improve with more time

- Swelling lines. A real burin line thickens and thins along its length. Outlining each hatch stroke into a variable-width fill would allow tone to change along a line, and would allow a radial vignette in the field. My stepped vignette left rings of overlapping round caps at 512 px, so I removed it.
- A purpose-built lettering. Space Grotesk Bold is legible at 128 px, but it reads as a modern badge next to the engraving. Engraved inline capitals drawn for the seal would unify the voice.
- More tone on the lit half of each plate band, and cast shadows of the posts on the faces.
- A tuned 128 px cut of the hero, with heavier ticks and no field ruling, so the mid size does not depend on how a rasterizer treats hairlines.
- Outline every stroke to fills for production files. `hero.svg` uses stroked paths with round caps, 3,338 polylines in 18 stroke groups (counted in the exported file).

## Honest self-assessment

- **Where it works.** At 1024 px it reads as a believable dilution refrigerator, not generic tiers. The dark stage interiors make the lit hardware stand forward, and the story is legible in one pass down the axis: machine, pivot, chip off the plumb line, brackets, index on the dial. At 128 px the stack becomes light plates over dark stages, and the chip window with its brackets stays clear.
- **Where it fails.**
  - Below 128 px the engraving collapses. At 64 px the field renders nearly black in VectorCraft, because hairlines appear to be clamped to a minimum width; a browser may render it lighter. The hero is a 128 px and up mark, and the small mark carries everything below.
  - The swinging chip is a liberty. The real chip is rigidly mounted, and what drifts is its noise, not its position.
  - The ghost positions and the tick record are faint at 1024 px and invisible at 512 px and below, so the "trail" reading rests on the solid chip's offset alone at small sizes.
  - The small mark is simple by necessity. At 16 px the hanger rod and index triangle barely survive, and the chip reads as a dark square with a light dot. Its family tie to the hero rests on the ring, the bracket shape and the offset chip.
  - The lettering's weight competes with the fine engraving. Some viewers will see a badge before they see an engraving.
