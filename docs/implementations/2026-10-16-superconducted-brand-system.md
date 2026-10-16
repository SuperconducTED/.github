# 2026-10-16: superconducted-brand-system

> Status: **DONE for everything that does not wait on a choice** (record below the plan, in
> "What changed" and "Verification results"). Open: the team's mark pick, then the owner's
> palette and tagline picks, then the final kit in `brand/kit/`. The plan sections are kept as
> written before the work; the record is added after them.

## Problem / Motivation

The four logo candidates (`brand/candidates/`, committed as `37403c2`) are only one part of an
identity. On 2026-10-16 the owner asked for "all the things that need to be done for the whole
branding operation" while the team chooses a mark. Today the organisation has no palette, no
type rules, no written positioning, no shared chart style (the engine's docs hold 66 chart
images and the code has no styling at all), a blank GitHub organisation profile (no display
name, description, location or website; the default avatar) and a profile banner from before
the brand existed.

## Owner decisions (2026-10-16)

| Question | Decision |
| --- | --- |
| Scope | A. brand foundation, B. visual system, C. digital applications. **Not now:** D. print and presentation (slides, poster, LaTeX, stickers). |
| Palette | Prepare options now; the owner picks after the team picks the mark. |
| Typefaces | Space Grotesk + Space Mono: one family, since Space Grotesk is "a proportional sans-serif typeface variant based on" Colophon Foundry's Space Mono (Space Grotesk's README). Both SIL OFL 1.1, both installed in VectorCraft from their official repositories with the owner's permission. |
| Language | English brand (tagline, guide, cards); team messages stay Turkish with a collapsed English summary. |

## The split that shapes the plan

The mark is not chosen and the palette waits for it, so the work divides in two:

- **Independent of the mark: build now and finish.** Foundation text, palette options, the
  type system, the chart style, the licence, the kit tooling and its checks.
- **Dependent on the mark: build as a generator, render for all four candidates as decision
  aids, finalize only for the winner.** Lockups, avatar, favicons, app icons, profile banner,
  social cards, README header, brand board.

## Plan

### W0. Shared ground (first, by the lead)
- `brand/tools/palettes.py`: the single source of truth for the palette options, each with
  roles (ink, paper, accent on light, accent on dark, optional machine tint), a one-line
  reason tied to the story, and WCAG ratios computed by `wcag.py`. Six options, carried over
  from round 2 and kept clear of IBM blue `#0F62FE`, Qiskit purple `#6929C4` and the CASSANDRA
  Collective's night, bronze and gold.
- `brand/tools/install_fonts.py`: installs both families (done; tested on a fresh install of
  Space Mono and on the already-installed path).

### W1. A colour-role API for each candidate (four agents in parallel, one folder each)
Each `brand/candidates/<style>/` gains `mark.py` with
`draw_mark(vc, x, y, size, colours, variant="hero" | "small", mono=False)`, drawing into the
active VectorCraft document. Roles: `ink` (the machine and its line work), `paper` (only where
a design paints the ground colour), `accent` (**the range**: the interval brackets and the
range marking on the dial; nothing else), plus `tint-light` and `tint-shade` where a design
uses tints (derived from ink and paper when not given). Acceptance, per candidate:
- with `accent = ink` and the neutral colours, the output reproduces today's `hero.svg` and
  `small.svg` exactly (byte-identical SVG export);
- with a distinct accent, only the range elements change colour (checked by a pixel mask);
- `mono=True` gives the one-colour version with real knock-outs.
This lets one generator apply any palette to any mark, and turns the story's two halves
(machine and range) into the colour logic of the identity.

### W2. Chart style (one agent)
`brand/figures/`: a generator that writes one matplotlib style file per palette option (the
chosen one later becomes `superconducted.mplstyle`) with named colours for the three things
this project draws: the **interval band** (the engine's answer), the **crisp line** (the
single-snapshot prediction) and the **measured points** (the hardware), plus a categorical
sequence for per-qubit series and Space Grotesk / Space Mono as fonts. Demo figures per palette,
with clearly labelled illustrative data. Verified against real matplotlib in a throwaway
environment (needs the owner's permission for the download). Adoption inside the engine is a
follow-up pull request there, not part of this branch.

### W3. Brand foundation (the lead)
`brand/FOUNDATION.md`, drafted only from what the repositories already say (the engine
README's "Why this exists", the profile abstract, `docs/team.md`), new text marked as draft:
the story; a one-line descriptor; a positioning paragraph; the tagline shortlist (1. "Noise as
a range, not a number." 2. "The machine drifts. We give the range." 3. "Every calibration, not
just the last."), for the owner to pick; a short and a long boilerplate; naming rules
(SuperconducTED, its flagship's name, the TED footnote); voice and tone; drafts for the
organisation profile fields. **Applying the profile fields is a settings change: only on the
owner's word.**

### W4. The generator and the decision aids (after W1)
`brand/tools/build_brand.py --mark <style> --palette <name> --out <folder>` produces the full
kit: horizontal (primary), stacked and icon lockups; on-light, on-dark, black and white
variants; SVG with outlined text, transparent PNG at 1x/2x/4x, PDF, EPS, compressed sources;
avatar 500/1024; favicon SVG and 16/32/48 PNG; app icons 180/192/512; the profile banner
(`header.svg`); social cards 1280x640 for the organisation, the noise engine and the co-design
repository; a README header; a brand board. `brand/tools/check_brand.py` verifies files, SVG
hygiene (title, viewBox, no live text, no images, only the variant's colours), PNG sizes and
transparency, and palette contrast; it exits non-zero on any failure.
Decision aids, committed for the team: `brand/decision/in-use-<style>.png` (each mark as
avatar, favicon in a browser tab, README header, social card, chart) and
`brand/decision/palettes.png` (six palettes on all four marks). The final kit is generated
once the mark and palette are chosen; until then the generator is tested end to end in a
scratch folder.

### W5. Licence, guide, record (the lead)
`brand/LICENSE-BRAND.md` (CC BY 4.0 for the brand files, owner decision; scripts under the
repository's licence) with a note that the name and mark identify the project and imply no
endorsement by IBM, by the Qiskit project, by TED (Türk Eğitim Derneği) or TED University, or
by anyone else. `brand/README.md`: the guide, including the table below. This record, then a
commit and push only on the owner's word.

## How the deliverables answer the original brief

| Brief section | Deliverable |
| --- | --- |
| 1. Scalability and versatility | Hero plus a redrawn small mark; favicons 16/32/48; one-colour black and white versions; minimum sizes in the guide; `check_brand.py` |
| 2. Strategic alignment and rationale | `FOUNDATION.md` (story, positioning, voice); the guide's "why each element" section |
| 3. Colour and accessibility | `palettes.py`: 3 to 4 core colours per option, hex, RGB, CMYK, WCAG ratios from `wcag.py`; chart colours for the band, line and points |
| 4. Typography | Space Grotesk + Space Mono with roles, weights and sizes; installer |
| 5. Structural layout and lockups | Horizontal (primary), stacked, icon; clear space; minimum sizes |
| 6. File and production readiness | SVG, PNG (transparent), PDF, EPS, sources; favicon markup; a note on prompting AI tools for clean vector art |

## Mathematical / Statistical details *(planned)*

- **Contrast.** WCAG 2.x as implemented in `brand/tools/wcag.py`: c_lin = c/12.92 if
  c ≤ 0.04045 else ((c + 0.055)/1.055)^2.4; L = 0.2126 R + 0.7152 G + 0.0722 B;
  ratio = (L1 + 0.05)/(L2 + 0.05). Targets: 4.5:1 for text, 3:1 for graphics.
- **Tints.** Where a design or a chart needs a tint, it is a per-channel mix in sRGB:
  t(c) = (1 − a)·paper + a·ink for coverage a in [0, 1].
- **Chart band (set in W2, 2026-10-16).** The band is a solid tint, not an opacity:
  t = (1 − a)·ground + a·accent per sRGB channel, with coverage **a = 0.20** for every palette,
  light and dark. Measured, not picked: the floor (0.19 light, 0.16 dark) is the smallest value
  at which the fill differs from the ground by ΔE ≥ 8 for normal vision and both simulated
  colour-vision deficiencies (Machado 2009) in all six palettes; the ceiling (0.23 light, 0.44
  dark) is where ink and text on the band would fall below 4.5:1 or the accent edge below 3:1
  on the fill. 0.20 is the floor rounded up to the next 0.05. Worst cases at 0.20: ink on the
  band 4.72:1, accent edge on the band 3.65:1, band edge on the ground 4.82:1
  (`brand/figures/check_styles.py`).
- **Series colours (W2).** Per palette, hues within 30 degrees of the accent are excluded (the
  accent means the range); each slot clears 3:1 on its ground and stays at least ΔE 15 (normal)
  and 8 (simulated deficiency) from the accent, the ink and its neighbours. Result: six series
  colours for Cryostat, Phosphor, Figure and Monochrome, five for Copper stage, four for Heat
  leak; three or four are safe for all-pairs use (scatter plots, small multiples).

## Design decisions *(planned)*

- **Accent means "range", and nothing else.** One colour rule, taken from the story, makes the
  identity explain itself: whatever is the engine's answer (brackets, intervals, chart bands)
  wears the accent; the machine wears ink.
- **Generator over hand-made files.** Four candidates times six palettes is 24 combinations; a
  generator renders any of them, and the final kit comes from the same code the team saw.
- **Print and presentation deferred** by the owner; the generator's layout code is written so
  slides and a poster can be added later without touching the mark API.

## Verification *(planned)*

- Each candidate: `python -I brand/candidates/<style>/build.py` still reproduces its committed
  SVGs byte for byte; the role API's regression and pixel-mask checks pass.
- `python -I brand/tools/build_brand.py --mark <style> --palette <name> --out <scratch>` for
  every mark, then `python -I brand/tools/check_brand.py <scratch>`.
- The chart styles load in matplotlib and render the demo figures.
- Everything runs from a short folder (VectorCraft 0.10 writes no file at 260+ path characters).

## What changed (record, 2026-10-16)

| File | One-sentence description |
| --- | --- |
| `brand/README.md` | The brand guide: idea, colour rule, palette options, type, lockups, charts, applications, files, don'ts, rebuilding, the brief map. |
| `brand/FOUNDATION.md` | Story, descriptor, positioning, audiences, character, tagline shortlist, boilerplates, naming rules, voice, org-profile drafts. |
| `brand/LICENSE-BRAND.md` | CC BY 4.0 for the brand files; MIT proposed for the scripts; no-endorsement and fonts notes. |
| `brand/.gitignore` | Ignores Python bytecode caches. |
| `brand/tools/palettes.py` | The six palette options by role, with WCAG checks. |
| `brand/tools/build_brand.py` | Builds the full kit for any mark and palette, and the team's decision aids. |
| `brand/tools/check_brand.py` | Verifies a built kit against its manifest. |
| `brand/tools/install_fonts.py` | Installs Space Grotesk and Space Mono into VectorCraft (now both families). |
| `brand/tools/vcdriver.py` | Unchanged since `37403c2`. |
| `brand/candidates/MARK_API.md` | The interface every candidate implements (amended: one-colour strokes allowed; optional `small16`). |
| `brand/candidates/<style>/mark.py`, `check_api.py` | Each candidate's drawing interface and its acceptance tests (four agents, one folder each). |
| `brand/candidates/<style>/build.py`, `NOTES.md` | Rebuilt on top of `mark.py`; notes gain a colour-roles section. |
| `brand/candidates/README.md` | Gains "See them in use" and the mark-API note. |
| `brand/figures/` | Chart styles (12 files), `roles.json`, helper module, demos, generator and checks (one agent). |
| `brand/decision/` | `in-use-<style>.png` for each candidate and `palettes.png`. |
| `docs/implementations/2026-10-15-superconducted-brand-identity.md` | One appended "As of 2026-10-16" pointer. |

## Verification results (2026-10-16)

The candidate figures below come from each candidate's `check_api.py`; the lead re-ran all four
after the agents finished (sequentially, 18 s, 16 s, 191 s and 28 s) and every figure
reproduced exactly, all four exiting 0.

- **Every candidate keeps its committed files.** Rebuilt with the neutral colours through the
  new interface, each reproduces its committed SVGs byte for byte (engraved 3/3, cutaway 4/4,
  radial 3/3, isometric 3/3) and its PNGs pixel for pixel (5/5 each); rebuilt PNGs whose bytes
  differed only by VectorCraft's timestamp were restored to the committed bytes after a pixel
  comparison.
- **The accent lands only on the range.** Rendering each hero with accent `#D9480F` against
  accent = ink, every changed pixel lies on the range elements: engraved 8,517 of 8,517,
  cutaway 5,628 of 5,628, radial 23,214 of 23,214, isometric 14,242 of 14,242, with 0 strays;
  each check was shown to fail on a planted leak.
- **The generator.** Every candidate builds a complete kit (180 files: lockups in four colour
  variants, SVG, PNG, PDF, EPS, sources, web set, guide images) and `check_brand.py` reports 0
  problems for all four in neutral colours and for engraved/Cryostat, cutaway/Heat leak and
  isometric/Phosphor. The checker caught each of seven planted defects (live text, an
  off-palette colour, a second colour in a one-colour file, a missing PDF, a wrong-size
  favicon, wrong opacity at corners, a painted background).
- **Charts.** `brand/figures/check_styles.py`: 46 of 46 checks in an independent run (59 of 59
  in the designer's run with the optional palette validator and strict demo comparison).
- **Palettes.** `brand/tools/palettes.py`: all contrast targets met.
- **Text.** No em or en dashes in any new or changed text file.

## Decisions made during the work

- **VectorCraft's path limit.** 0.10 reports a successful export but writes nothing at 260 or
  more path characters (measured); read-backs go through `fresh_export`, and the guide says to
  build from a short folder.
- **Shaded accents.** The isometric brackets shade with mixes of the accent; the mark reports
  them through `colours_used()`, and the checker allows exactly those.
- **Hinted small marks.** Cutaway and radial carry hand-hinted 16 px drawings (`small16`); the
  generator draws favicons edge to edge so the 32-unit and 16-unit grids land on whole pixels.
- **One-time setup.** The engraved mark outlines its lettering in a temporary document; the
  generator lets it do that before opening any document of its own.
- **Transparency check.** A transparent file must have at least a quarter of its border clear:
  art may touch an edge (the isometric bracket does), a painted background may not.
- **Name casing.** Card kickers read "SuperconducTED"; capitals stay inside drawn marks.
- **Series colours.** A palette's accent limits its chart series (Heat leak four, Copper stage
  five, the rest six), which is now an input to the owner's palette choice.

## Open, and follow-ups outside this branch

- The team picks the mark; the owner then picks the palette and the tagline, and confirms the
  scripts' licence; then `build_brand.py` writes the final kit into `brand/kit/`.
- Applying the organisation profile fields and avatar, replacing `header.svg`, and restyling the
  profile's two diagrams and badges: after the picks, and only on the owner's word.
- Uploading social previews: by hand in each repository's settings (GitHub has no API).
- Adopting the chart style in the engine's scripts: a pull request in that repository.
- Print and presentation (slides, poster, LaTeX, stickers): deferred by the owner.

## Related docs

- `docs/implementations/2026-10-15-superconducted-brand-identity.md`: the story and the history
  of rounds 1 to 3.
- `brand/candidates/README.md`: the four candidates and the team's choice.
- CASSANDRA Collective brand kit (`Cassandra-Collective/.github/brand`): the pattern this follows.

## As of 2026-10-16, later: the choices are made and the kit is built

- **The team chose the technical cutaway** (the owner's words: "team feedback is in the second
  logo is the way to go"). The owner then chose the **Cryostat** palette (he added that it suits
  a project about emulation), the tagline **"Noise as a range, not a number."**, and **MIT** for
  the scripts. A decision sheet of the cutaway in all six palettes, each kit built and checked
  (180 files, 0 problems each), informed the palette choice.
- **The official kit** is in `brand/kit/`: `build_brand.py --out brand/kit` (defaults now
  `palettes.MARK = "cutaway"`, `palettes.CHOSEN = "cryostat"`), 180 files, `check_brand.py`
  0 problems. The organisation's social card carries the tagline.
- **Fixed on the way:** the palette guide printed CMYK as 0 or 1, because VectorCraft's
  `color.convert` answers in fractions; it now shows percentages and flags the two colours
  outside VectorCraft's "Generic CMYK (SWOP-like)" gamut (`#0A1B24`, colour difference 3.5;
  `#4FD6E6`, 7.7) for proofing.
- **Charts:** `brand/figures/styles/superconducted.mplstyle` (and `-dark`) are now written as
  copies of the Cryostat styles, and the helper's `use()` defaults to Cryostat; `check_styles.py`
  still passes 46 of 46.
- **Guide:** `brand/README.md` now documents the chosen identity: construction, minimum sizes
  derived from the geometry (hero 128 px, brackets 1.6 px wide there), CMYK with gamut notes,
  the tagline, and the kit's files. `FOUNDATION.md` records the tagline, `LICENSE-BRAND.md`
  the MIT text (identical to the engine's licence).
- **Still only on the owner's word:** the organisation profile fields and avatar, replacing the
  profile banner and its two diagrams and badges, and uploading the social previews.

## As of 2026-10-16, after PR #1 merged: the mathematics of the mark

The owner asked what was still missing and narrowed it to the brand itself. Compared with the
CASSANDRA Collective's guide, the brand lacked a construction drawing, an answer to the brief's
five opening principles, a Projects section and a Notes section. The owner then set the bar:
"Construction drawing should be very detailed. Because we did not generate an AI slop, this is
real work, so people should know and learn the mathematics behind the logo."

- **`brand/CONSTRUCTION.md`** (new): the mathematics of the mark in plain notation, every value
  computed from `brand/candidates/cutaway/mark.py`: the design space and scale, line weights and
  arc-length dash patterns (and the 34-unit phase that centres a centre line's short dash on a
  crossing), 45 degree section hatching on a globally registered grid (c = k * 6 * sqrt(2)), the
  six plates, support rods, the coax loom as cubic Beziers with a sine fan, the helical heat
  exchanger as an orthographic helix whose cos(theta) sign picks solid or hidden, the dial (117 of
  120 graduations, 129 of 180 knurl marks), the chip's winding-number lattice, the drift Bezier,
  the interval equations, the small marks' pixel grids, minimum sizes from line widths, and the
  colour, tint, chart-band and lockup formulas.
- **Five construction sheets** in `brand/kit/guide/construction-{1..5}-*.{svg,png}`, drawn by the
  new `brand/tools/construction_sheets.py` (one agent) from the mark's constants, its
  `construction()` data and the geometry `hero_art()` emits; the build stops if `mark.py`
  changes in a way the sheets do not understand. `mark.py` gains `construction()` (no change to
  the drawing: `check_api.py` still reports 4/4 SVGs byte-identical and 5/5 PNGs
  pixel-identical).
- **A correction.** The brand guide and the cutaway's notes said the frozen snapshot sits off
  the interval's centre. The geometry says the two chip positions are 60 units either side of
  the datum, so the interval (384 to 616) is centred on it. Both texts now say so, marked as a
  correction; changing the mark to make the interval lopsided is left to the owner.
- **Guide additions:** "How the mark meets the brief" (the five principles), "Projects", and
  "Notes" (the TED name and TED University's corporate identity guide, the TED Conferences word
  mark registered in 2010 and renewed in 2019, the parked .com and .org domains), plus links to
  `CONSTRUCTION.md` and the sheets.
- **Kit:** rebuilt; `check_brand.py` reports 190 files, 0 problems. The only new files are the
  ten sheet files and the manifest records for them. Every other regenerated file differed from
  the committed one only by VectorCraft's embedded timestamps (PNG, PDF, EPS, sources) or by line
  endings (SVG, JSON), and was restored. The sheets' SVGs are large (about 12.6 MB together,
  outlined text); the kit grew from 11 MB to 24 MB.

## As of 2026-10-16, later: the kit moved up to `brand/`

The kit's folders are now `brand/eps`, `brand/guide`, `brand/pdf`, `brand/png`, `brand/source`,
`brand/svg`, `brand/web` and `brand/manifest.json` (the layout of `Cassandra-Collective/.github`);
the chosen mark's source moved from `brand/candidates/cutaway/` to `brand/mark/`, and the other
candidates and the decision sheets to `brand/history/`. All moves are renames with unchanged blob
ids. The `brand/kit/...` and `brand/candidates/...` paths in the sections above describe the tree
as it was; see `2026-10-16-organisation-home.md`.
