# The mark API: one function per candidate

Every candidate folder (`engraved/`, `cutaway/`, `radial/`, `isometric/`) exposes the same small
interface in a `mark.py`, so that one generator (`brand/tools/build_brand.py`) can draw any
candidate, in any palette, into any layout: lockups, avatar, favicons, social cards, banners.

## Contract

```python
# brand/candidates/<style>/mark.py
ROLES = ("ink", "paper", "accent", "tint-light", "tint-shade")

def box(variant="hero") -> tuple[float, float, float, float]:
    """The art's bounding box (x0, y0, x1, y1) inside the unit square, so layouts can align
    the visible art rather than the square. The unit square is what draw_mark scales."""

def draw_mark(vc, x, y, size, colours, variant="hero", mono=False) -> list[int]:
    """Draw the mark into VectorCraft's ACTIVE document, its unit square mapped to the square
    with top-left (x, y) and side `size` (points, y down). Returns the ids of what it drew.

    colours: {"ink": "#rrggbb", "paper": "#rrggbb", "accent": "#rrggbb", optional
              "tint-light", "tint-shade"}. Missing tints are mixed from ink and paper:
              t(a) = (1 - a) * paper + a * ink per sRGB channel, a = 0.20 and 0.55 by default.
    variant:  "hero" (the detailed mark, 128 px and up) or "small" (the favicon redraw,
              16 to 32 px).
    mono:     True draws the one-colour version in colours["ink"] only, with real knock-outs
              (no paper-coloured shapes), for solid black and solid white use.
    Side effects: adds objects to the active document; draws no background unless a design
    needs paper-coloured shapes inside the art (then it uses colours["paper"]).
    """
```

## The colour rule

- **`accent` is the range, and only the range:** the interval brackets `[ ]` and whatever
  marks the reported interval on the dial (an inked arc, a range zone, a dimension line that
  spans the interval). Nothing else wears the accent.
- **`ink` is the machine and the measurement:** the refrigerator, the dial, the chip, its
  trail and ghosts, and all line work.
- **`paper`** only where a design paints the ground colour inside the art.
- **Tints** only where a design shades with them (the isometric facets).

This turns the story's two halves into the identity's colour logic: the machine in ink, the
engine's answer in the accent.

## Acceptance for each candidate

1. `build.py` draws its deliverables through `draw_mark`, and rebuilding reproduces the
   committed `hero.svg`, `hero-black.svg` and `small.svg` byte for byte and every committed PNG
   pixel for pixel (with the neutral colours ink `#1A1D24`, paper `#F2EEE6`, accent = ink).
2. With a distinct accent, only the range elements change colour: render the hero twice
   (accent = ink, accent = a test colour) and confirm that every pixel that differs belongs to
   the brackets or the range marking.
3. `mono=True` output paints in a single colour (fills and any strokes alike), with no opacity
   and no paper-coloured shapes. Strokes are allowed when they are that one colour: line-work
   designs (the cutaway, the engraving) are drawn with them, and converting them to fills would
   change the committed files. *(Amended 2026-10-16; the first wording said "no strokes".)*
5. Optional: a design with a hand-hinted 16 px drawing exposes it as `variant="small16"` and
   lists it in a module-level `VARIANTS` tuple; the generator then uses it for every 16 px file.
4. Works from the repository's own folder; nothing outside the candidate's folder changes.
