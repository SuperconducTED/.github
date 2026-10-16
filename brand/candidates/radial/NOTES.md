# SuperconducTED, round 3: RADIAL ORNAMENT / ASTROLABE

## The stranger's caption

An engraved precision dial ringed by bolted plates, rods and cables, so some kind of serious hardware; a chip has wandered off the dial's mark, and a bracketed arc on the dial shows the whole range it moves through.

(Written as what the mark says unaided. The intended reading, a dilution refrigerator seen from below, is not something a stranger will name; see the self-assessment.)

## How the four elements carry the story

1. **Chandelier.** We look straight up the dilution refrigerator: the bolted top flange is the outermost, heaviest ring, then four plates that go from solid and bolted (warm) to open hairlines (cold), support rods seen end-on as hollow radial tubes in every gap, and three coax bundles running down through every stage (slack bows, feedthroughs, beads, attenuators, one service loop each), all over radial hatching that converges on the axis like a shaft seen from below.
2. **Calibration dial.** The coldest plate (the mixing chamber, where the chip is mounted) has its rim engraved as a graduated dial in three tiers (2, 10 and 30 degrees); the solid index at twelve o'clock and the reticle under it are where the frozen snapshot says the machine is.
3. **Drifting chip.** The packaged chip sits on that coldest plate 45 degrees clockwise off the index, reached by a wandering path of three earlier positions whose beads grow toward the present.
4. **Interval brackets.** Between a `[` and a `]` bent onto the dial, the dial turns solid and its graduations open as windows: that arc is the range the engine reports, and the index, the whole trail and the chip all lie inside it.

## Stroke weights (units of the 1000-unit hero box; 1 unit = 1 px at 1000 px)

| Tier | Weight | Where |
|---|---|---|
| Heavy | 12 (glyph strokes), up to 34 and 52 as solid bands | the bracket glyphs; the flange (34) and the interval band (52) are solid masses |
| Medium | 3.4 to 8 | dial rims (8 and 3.5), 10-degree ticks (3.4), plate edges, the rods (8 to 13 wide) |
| Fine | 1.1 to 2.2 | gap hatching (1.1), coax (2.0), 2-degree ticks (1.7), the trail (1.1 thickening to 2.6), the dashed track (1.4) |

## The passage worth zooming into

The coax bundle at half past seven (lower left), between the flange and the dial: three cables leave the flange through ringed feedthroughs, one of them throws a service loop, they pass the two solid plates through more feedthroughs, take a bead on each open plate, bow slack across every hatched gap in channels cut clear of the hatching, pass the hollow support rods, and land on the dial through attenuator blocks. The chip is the second one: package, four pins a side, a die window, the die, and a cross for the qubit.

## The small companion

- `small.svg` (32-unit grid): the dial ring; the interval from twelve to three o'clock swelling into a heavy band; an upright `[` at the top and a `]` lying on its side at the right (both radial, as on the hero, and axis-aligned so they land on whole pixels); the chip two units off centre toward the band.
- `small-16.png` is hand-hinted pixel art of the same drawing (`PIX16` in `build.py`), because the vector rendered at 16 px blurs to grey. This is the usual favicon practice, but it means the 16 px file is not literally `small.svg` scaled.
- The hero's interval runs from 18 degrees before to 68 degrees after the index; the small mark's runs from 0 to 90 degrees. That is a deliberate hinting choice, not a different meaning.

## Quality loop log

1. Outer graduated dial with a centre-pivoted alidade: read as a **watch face** (hand plus pivot), chip and trail tiny in an empty middle, coax S-bends looked like springs. Rebuilt.
2. Moved the dial to the coldest plate around the chip, removed the hand, made the bolted flange the frame: clock reading gone, chip now next to its brackets. Still: empty spoked face (compass), faint trail, small chip.
3. Bigger chip and orbit, dashed track instead of spokes, hexagonal boss, bolder reticle and index. Outer zone a flat, monotone stack of rings with no depth.
4. Radial hatching in the gaps (converging, so it reads as looking up a shaft), rods and coax cut clear of it. It hid the hatched plate P2; coax bows alternated and looked tangled; the trail broke into stubs at its halos.
5. P2 made solid, coax bows all one way, trail beads without the line. First full sheet: at 128 px the outer rings drowned the dial, and the small mark read as a power or pie-chart icon.
6. Enlarged the dial and face, compressed the plates, chip 78 units: the meaning now carries at 128 px. Small-mark lab: curved brackets turned into "Z" flags at 32 px and vanished at 16 px.
7. Hand-hinted 16 px pixel art with axis-aligned bracket glyphs; matching 32-unit vector. Tried a mirror-symmetric variant: it read as a robot head or padlock, rejected.
8. Trail re-spaced into a clean wander (reticle, three growing beads, a path thickening toward the chip).
9. Removed a face ring that pushed a target reading; 16 px slots on the sheet placed on whole pixels.
10. Smoothed the small mark's band (corner knockouts had made a staircase) and lightened the hatching (pitch 7 to 8 units) so the bracketed arc leads at 128 px.

## What I would improve with more time

- A third size between the two marks (48 to 96 px): at 64 px the hero is a grey textured disc and the small mark is too sparse to take its place.
- Give the hero's chandelier a silhouette cue (for example, the coax bundles longer and bolder, or a faint second, offset ring set implying the plates hang one under another) so it reads as hardware hanging above you, not only as a ring instrument.
- Tune the lower half of the face, which is calm but generic (boss, screws, dashed track).
- Fit the `]` of the small mark so it reads as a bracket before it reads as a cup.
- Print tests: the 1.1-unit hatching needs checking at real print sizes and on a dark ground, where it fills in first.

## Honest self-assessment

- **Where it works.** The bracketed arc on the coldest plate is the strongest idea: the graduations open as windows inside a solid band held by `[` and `]`, and the index, the trail and the chip all sit inside it, so "a range, not a number" is literal. The line-weight hierarchy (solid warm plates outside, hairlines toward the cold centre) gives real depth with one colour, and the mark survives solid black and paper on ink unchanged because every knockout is a true hole.
- **Where it fails.** Seen from directly below, the chandelier does not read as a chandelier to a stranger: it reads as a precision instrument, a lens or a turbine, and the hardware reading rests on the bolts, rods and cables, not on the silhouette. A graduated ring with a central boss still carries some watch or compass association. The coax bundles, the most fridge-specific detail, are small at hero size.
- **Small sizes.** At 128 px the hero carries on four masses (flange ring, bracketed arc, chip, dial face) and the fine work becomes texture. At 64 px it is a grey disc. The 16 px favicon reads as a ring with a heavy bracketed arc and a chip, but the sideways `]` is the weakest glyph in the system.

## Files

| File | What it is |
|---|---|
| `build.py` | Everything, all numbers in it. `python -I build.py` builds look renders and all deliverables (about 2.5 minutes). |
| `hero.svg`, `hero-1024.png` | Hero, ink `#1A1D24` on paper `#F2EEE6` (one compound path plus the paper square). |
| `hero-black.svg` | Hero, solid black on transparent (one compound path). |
| `hero-white-on-black.png` | Hero, solid white on black. |
| `small.svg`, `small-32.png`, `small-16.png` | Small companion: 32-unit vector, its 32 px render, the hand-hinted 16 px pixel art. |
| `sheet.png` | 2000 x 1130 px, exported at scale 1: hero at 1000 px, on ink, solid black on white, true-pixel ladders (hero 128 and 64, small 32 and 16) on paper and on ink, the small mark magnified, the lockup. |
| `_work/` | Quality-loop renders (`loopN-*`), zoom crops, the SVG round-trip renders (`rt-*.png`) and magnified favicons (`mag-*.png`), plus the patch scripts used between loops. |

Checks run: every shipped SVG re-opened in VectorCraft and re-rendered (`_work/rt-*.png`); each SVG holds one ink path and no text, gradient, opacity or filter; text appears only on the raster sheet's lockup (Space Grotesk Medium); no em or en dashes in this file or in `build.py`.
