# SuperconducTED brand guide

> **Status, 2026-10-16: the system is built; two choices are open.** The team is choosing one of
> four marks ([`candidates/`](candidates/)), then the owner picks one of six palettes. Everything
> else is here and ready: the story and voice, the colour rule, type, lockups, chart style, the
> generator that produces every file, and its checks. Once both choices are made, one command
> writes the final kit into `kit/` and this guide gains the mark's construction and measured
> minimum sizes.

## The idea

Qiskit can describe an IBM quantum computer in one line, `NoiseModel.from_backend`, by freezing
its latest calibration. The machine does not stay frozen: its noise drifts from one calibration
to the next. SuperconducTED keeps every calibration and answers with the range the machine
moves through, not one crisp number. The full story, positioning, tagline shortlist,
boilerplate, naming rules and voice are in [`FOUNDATION.md`](FOUNDATION.md).

Every candidate mark draws the same four things: the dilution-refrigerator chandelier (the real
machine), a calibration dial (where the frozen snapshot says the machine is), the drifting chip
(where it actually is) and interval brackets (the engine's answer).

## The one colour rule

**The accent colour means the range, and nothing else.** Brackets, intervals on the dial, the
band on a chart: whatever is the engine's answer wears the accent. The machine, the
measurement, the type and all line work wear ink. So the colours explain the project on their
own, and a reader of a chart knows at a glance which shape is our answer.

## Colour

Six options, chosen after the mark (owner decision 2026-10-16). The single source of truth is
[`tools/palettes.py`](tools/palettes.py); run it to print every ratio. Values below are its
output on 2026-10-16 (WCAG 2.x contrast).

| Option | Ground, dark | Ground, light | Ink on light | Accent on light | Accent on dark | Why |
| --- | --- | --- | --- | --- | --- | --- |
| Cryostat | `#0A1B24` | `#EEF3F5` | `#0A1B24` | `#0A6C7C` (5.44:1) | `#4FD6E6` (10.12:1) | The cold of the dilution refrigerator. |
| Heat leak | `#0B1622` | `#F1F4F7` | `#1F5F86` (6.26:1) | `#B8461B` (4.84:1) | `#FF8A4C` (7.80:1) | Cold machine, warm noise. |
| Copper stage | `#15171A` | `#F5F3EF` | `#15171A` | `#9C4E1C` (5.38:1) | `#E39256` (7.28:1) | The refrigerator's copper plates; close in feel to CASSANDRA's terracotta. |
| Phosphor | `#0B1410` | `#EEF3EF` | `#0B1410` | `#0B7446` (5.19:1) | `#5BF0A0` (12.85:1) | The oscilloscope trace that shows a signal drifting. |
| Figure | `#16191D` | `#FFFFFF` | `#16191D` | `#1F77B4` (4.82:1) | `#6FB1E3` (7.62:1) | Matplotlib's default blue, the colour of most Python plots. |
| Monochrome | `#111214` | `#F7F7F5` | `#111214` | `#5F6368` (5.64:1) | `#9AA0A6` (7.10:1) | No colour to lean on. |

Targets: type on its ground at least 4.5:1, marks and accents at least 3:1. Every option meets
both, and every accent also clears 4.5:1, so it may carry text. All options stay clear of IBM blue
`#0F62FE`, Qiskit purple `#6929C4` and the CASSANDRA Collective's night, bronze and gold. The
kit's palette guide adds RGB and approximate CMYK values (VectorCraft's conversion) for the
chosen option. See every option on every mark in [`decision/palettes.png`](decision/palettes.png).

**One-colour use.** Every mark has a true one-colour version (solid black, solid white) with
real knock-outs. Use it on photographs, busy grounds, engraving, embroidery and anything printed
in one ink. The mark never depends on colour to be recognised.

## Typography

Two families, one lineage: Space Grotesk is "a proportional sans-serif typeface variant based
on" Colophon Foundry's Space Mono (Space Grotesk's own README), so the pair reads as one voice.

| Typeface | Role | Setting | Licence and source |
| --- | --- | --- | --- |
| **Space Grotesk** | The wordmark, headings, running text | Wordmark and headings Medium; text Regular; never wider tracking than the default for the wordmark | SIL OFL 1.1, `github.com/floriankarsten/space-grotesk` |
| **Space Mono** | Code, data labels, kickers, small technical captions | Regular; kickers keep normal casing (the name stays SuperconducTED), +60 tracking | SIL OFL 1.1, `github.com/google/fonts` (`ofl/spacemono`) |

Install both into VectorCraft with
`python -I brand/tools/install_fonts.py <folder with the TTFs>`. Logo files carry their letters
as outlines and need no fonts; never retype the wordmark, use the files.

## Lockups

Proportions, in units of the visible mark height H (Hs for the small mark), from the constants in
[`tools/build_brand.py`](tools/build_brand.py):

| Lockup | Use it for | Layout |
| --- | --- | --- |
| **Horizontal** (primary) | Headers, documents, the website, banners | Hero mark, then the wordmark 0.20 H to its right, capitals 0.22 H tall, centred on the mark's centre line |
| **Stacked** | Square and portrait spaces | Hero mark, then the wordmark 0.16 H below it, capitals 0.15 H tall, both centred on one axis |
| **Compact** | Navigation bars and anything 24 to 64 px tall | Small mark, then the wordmark 0.30 Hs to its right, capitals 0.42 Hs tall |
| **Mark alone** | Avatars, app icons, stickers | Hero at 128 px and up; the small mark below that |

**Clear space:** keep X = 0.25 H free of other text and graphics on every side.
**Minimum sizes:** measured on the chosen mark once it is picked (the detailed heroes need about
128 px; below that, every candidate switches to its redrawn small mark).

## Charts

The project's figures share one style: the **interval band** in the accent (a solid tint at
coverage 0.20, edged in the accent), the **crisp line** for a single-snapshot prediction (ink,
dashed), and the **measured points** in ink, plus a categorical sequence for per-qubit series.
Style files, a small helper module and demo figures for every palette are in
[`figures/`](figures/); `python -I brand/figures/check_styles.py` validates them.

A palette's accent also limits its series colours, since no series may look like the range:
Cryostat, Phosphor, Figure and Monochrome give six, Copper stage five, Heat leak four. Adopting
the style in the engine's own scripts is a follow-up pull request in that repository.

![Chart style in every palette](figures/demo/all-palettes.png)

## Digital applications

Generated for the chosen mark and palette by `tools/build_brand.py` (until then, see each
candidate in use in [`decision/`](decision/)):

| File | Size | Use |
| --- | --- | --- |
| `web/avatar-500.png`, `-1024.png` | 500, 1024 px | GitHub organisation avatar and other profile pictures |
| `web/favicon.svg`, `favicon-16/32/48.png` | 16 to 48 px | Browser tabs (the small mark on a tile, so the icon keeps one shape) |
| `web/app-icon-180/192/512.png` | 180 to 512 px | Home-screen and app icons |
| `web/profile-header.svg`, `.png` | 1280 x 340 | The organisation profile banner (same size as today's `header.svg`) |
| `web/social-card*.png` | 1280 x 640 | Social previews: the organisation, the noise engine, the co-design repository |
| `web/readme-header-noise-engine.svg`, `.png` | 1280 x 320 | The top of the engine's README |

```html
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/app-icon-180.png">
```

VectorCraft writes no `.ico`; if one is ever needed, combine `favicon-16/32/48.png` with any icon
tool. A social preview is uploaded by hand in each repository's Settings, General, Social
preview (GitHub has no API for it).

## Files and formats

| Folder (in a built kit) | Contents | Use for |
| --- | --- | --- |
| `svg/` | Every mark and lockup in every colour variant, text as outlines | Web, slides, anything that takes SVG; scales without limit |
| `png/` | The same with transparent backgrounds, marks at 128 to 1024 px, small marks at 16 to 64 px, lockups at 1x, 2x and 4x | Tools that do not take SVG; use @2x on dense screens |
| `pdf/`, `eps/` | Marks and lockups, one per file | Print shops, LaTeX, older sign-making workflows |
| `web/` | Avatar, favicons, app icons, banner, cards, README header | The organisation's online presence |
| `guide/` | Palette with hex, RGB, CMYK and ratios; clear space; brand board | This guide |
| `source/` | The compressed `.vectorcraft` document behind each file | Editing in VectorCraft |

Colour variants: `on-light` (for light grounds), `on-dark` (for dark grounds), `black` and
`white` (one colour).

**If you generate ideas with AI tools,** ask explicitly for clean vector art, flat colour, no
gradients, no shadows and a solid background, then redraw the result here. Never ship an AI
raster as part of the identity.

## Don't

- Don't give the accent to anything but a range.
- Don't recolour outside the chosen palette, or add gradients, shadows, glows or textures.
- Don't use the hero below about 128 px; use the small mark.
- Don't stretch, skew, rotate or rearrange any part of a mark or lockup.
- Don't retype the wordmark or set it in another typeface.
- Don't use the TED or TED University emblem or colours with it, or imply endorsement by IBM, the
  Qiskit project, TED or TED University.
- Don't place the colour versions on busy photographs; use solid black or white there.

## Rebuilding

Needs VectorCraft 0.10 or later, Python 3.10 or later (standard library only) and the two
typefaces installed. Keep the checkout path short: VectorCraft 0.10 writes no file at 260 or
more path characters. From the repository root:

```bash
python -I brand/tools/palettes.py
python -I brand/tools/build_brand.py --mark <engraved|cutaway|radial|isometric> --palette <option> --out brand/kit
python -I brand/tools/check_brand.py brand/kit
python -I brand/tools/build_brand.py --decision --scratch <short scratch folder>
```

SVG output is byte-identical from run to run. PNG output is identical pixel for pixel but not
byte for byte, because VectorCraft stamps each PNG with its creation time; so a rebuild shows
every PNG as changed in git even when nothing visible changed. Commit a regenerated PNG only
when its pixels changed: compare the decoded pixels first (`png_read` in
`tools/check_brand.py` decodes a PNG with the standard library) and restore the committed file
when they match.

## How this answers the brief

| Brief section | Where it is answered |
| --- | --- |
| 1. Scalability and versatility | Hero plus redrawn small mark; one-colour versions; favicons; minimum sizes; `check_brand.py` |
| 2. Strategic alignment and rationale | [`FOUNDATION.md`](FOUNDATION.md); "The idea" and the colour rule above; each candidate's notes |
| 3. Colour and accessibility | Six options with hex values and WCAG ratios; the chosen one also with RGB and CMYK |
| 4. Typography | Space Grotesk and Space Mono, roles and settings above |
| 5. Structural layout and lockups | Horizontal (primary), stacked, compact, mark alone; clear space |
| 6. File and production readiness | SVG, PNG, PDF, EPS and sources; favicon markup; the AI-tools note |

## Licence

The brand files are CC BY 4.0; see [`LICENSE-BRAND.md`](LICENSE-BRAND.md), which also covers
the scripts (MIT, proposed), the fonts and the no-endorsement note. The plan and history are in
[`../docs/implementations/`](../docs/implementations/) (2026-10-15 and 2026-10-16).
