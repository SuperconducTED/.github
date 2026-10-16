# 2026-10-15: superconducted-brand-identity

> Status: **PLAN; round 3 candidates saved, team choosing.** Written before any kit code, as
> the engineering convention requires. Sections marked *(planned)* are rewritten as the record
> once the kit is built. So far `brand/` holds only the four candidates
> (`brand/candidates/`, with their own guide) and the shared VectorCraft tools.

## Problem / Motivation

SuperconducTED has no logo. The organisation profile uses an animated Bloch-sphere header and
shields.io badges, but there is no mark, no wordmark and no file set a member can drop into a
slide, a poster, a paper or a repository's social preview. The owner's rule for the identity:
**branding is story first**, as with the CASSANDRA Collective's mark, where every element
carries one sentence of its myth.

## The story (owner, 2026-10-15)

The project's real origin, in the owner's choice of words: Qiskit's `NoiseModel.from_backend`
froze a machine that keeps moving.

> Qiskit can describe an IBM quantum computer in one line, `NoiseModel.from_backend`. It reads
> the machine's latest calibration and freezes it into one noise model. The machine does not
> stay frozen: its chip hangs at the bottom of a dilution refrigerator, about a hundredth of a
> degree above absolute zero, and its noise still drifts from one calibration to the next.
> SuperconducTED keeps every calibration and answers with the range the machine actually moves
> through: not one crisp number, but an interval that brackets the real hardware.

What a stranger must read from the mark with no label (owner's pick): **real quantum hardware**,
**noise that drifts**, **ranges, not single numbers**.

Elements the owner chose to carry (2026-10-15): the dilution-refrigerator chandelier, a
calibration dial or ring, the drifting chip, and interval brackets.

## History of this decision

| Round | What was shown | Owner's verdict |
| --- | --- | --- |
| Earlier session, 2026-10-15 | Sigmoid transition band, junction T, Tc resistor T, cold flame | "Pretty generic"; branding must be story first. |
| 1 | Story "Simulate, then hedge" (Leiden 1911 "Kwik nagenoeg nul" with David Deutsch's universal quantum computer): an = bending into an approximately-equal sign, in three variants and two palettes | "None of it really explains the project." The real push was IBM and Qiskit; restart from idea, colour, story and logo. |
| 2 | Story above; three flat marks (chandelier with pendulum and gauge; calibration ring with a drifted chip; chip with a drift trail in brackets) and six palettes | "Oversimplicity is the problem": the owner set aside his own brief's simplicity principle and asked for depth, detail and a unique style, "something that should be marvelous". Palette deferred. |
| 3 | Four styles drawn in parallel, all four elements in each: engraved seal, technical cutaway, radial astrolabe, isometric illustration | 2026-10-16: "I loved all of them." The owner is asking the team to choose; all four are saved in `brand/candidates/` with their build scripts. |

**The owner's override, recorded.** His original requirements list both "simplicity" and
"legible from a favicon to a billboard, reproducible in one colour". On 2026-10-15 he overrode
the first. The plan keeps the second by building a responsive system: a detailed hero for 128 px
and up, a redrawn small mark for 16 to 32 px, and depth carried by line work and stroke weight
rather than gradients, so single-colour reproduction still holds.

## Plan

1. **Round 3 sheet (done 2026-10-16).** One finished-quality candidate per style, each with a
   hero rendered at 1024 px, a solid-black version, a small companion mark at 32 and 16 px, a
   lockup, and notes that map each element to the story. Drawn in VectorCraft in two neutral
   tones; the palette is chosen afterwards with the owner. Saved in `brand/candidates/` with a
   guide for the team (`brand/candidates/README.md`). Verified: every candidate rebuilds from
   that layout; all 12 SVGs come out byte-identical and all 20 PNGs pixel-identical (their
   bytes differ only in VectorCraft's embedded timestamp).
   **Found while saving:** VectorCraft 0.10 reports a successful export but writes no file
   when the full path is 260 characters or longer. Two builds read an export back, and in a
   deep scratch folder (265 and 267 characters) they failed; in the repository the longest
   such path is 121 characters. `brand/tools/vcdriver.py` now has `fresh_export`, which refuses
   such a path up front, removes any old file and waits for the new one, so the failure is
   loud instead of a silent read of a stale file.
2. **Build script** `brand/tools/build_brand.py`: every number of the chosen mark, the lockups
   and the palette lives in this one file; it drives VectorCraft's headless engine through
   `brand/tools/vcdriver.py` and regenerates every asset.
3. **Check script** `brand/tools/check_brand.py`: every expected file exists; every SVG has a
   title and a viewBox, no live text, no images or external references, and only its variant's
   colours; every PNG has its pixel size and transparency where required; every palette pair
   meets its WCAG target (`brand/tools/wcag.py`). Exits non-zero on any failure.
4. **Deliverables:** the hero mark, the small mark, a horizontal lockup (primary), a compact
   horizontal, a stacked lockup; on-light, on-dark, solid black and solid white variants; SVG
   (text as outlines), transparent PNG at 1x/2x/4x, PDF, EPS, compressed `.vectorcraft`
   sources; favicon SVG and 16/32/48 PNG, app icons 180/192/512, avatar 500/1024, a 1280x640
   social card; guide images (construction, clear space, palette, brand board).
5. **Guide** `brand/README.md`: story, element meanings, construction, lockups, clear space,
   minimum sizes, palette, typography, files, don'ts, sources.
6. **Licence** `brand/LICENSE-BRAND.md`: CC BY 4.0 (owner decision) plus a note that the name
   and mark identify the project and imply no endorsement by IBM, by the Qiskit project, by TED
   or TED University, or by anyone else.
7. **Pull request** on `SuperconducTED/.github`; nothing merges without the owner.

## What changed *(planned)*

| File | One-sentence description |
| --- | --- |
| `brand/tools/build_brand.py` | Draws every asset in VectorCraft from the numbers in the file. |
| `brand/tools/check_brand.py` | Verifies files, SVG hygiene, PNG sizes and palette contrast. |
| `brand/tools/vcdriver.py` | Minimal stdio MCP client for VectorCraft's headless engine (from the CASSANDRA kit). |
| `brand/tools/wcag.py` | WCAG 2.x relative luminance and contrast ratio (from the CASSANDRA kit). |
| `brand/tools/install_fonts.py` | Installs the chosen open-licence fonts into VectorCraft. |
| `brand/README.md` | The brand guide. |
| `brand/LICENSE-BRAND.md` | CC BY 4.0 and the no-endorsement note. |
| `brand/{svg,png,pdf,eps,web,guide,source}/` | Generated assets. |

## Mathematical / Statistical details *(planned)*

- **Geometry.** Written once the mark is chosen: every radius, angle, hatch spacing and stroke
  weight as a fraction of the mark's size.
- **Contrast.** WCAG 2.x: channel linearisation c_lin = c/12.92 if c ≤ 0.04045 else
  ((c + 0.055)/1.055)^2.4; L = 0.2126 R + 0.7152 G + 0.0722 B; ratio = (L1 + 0.05)/(L2 + 0.05).
  Targets: 4.5:1 for text, 3:1 for graphics.

## Design decisions *(planned)*

- **Why not IBM's or Qiskit's own symbols.** The story credits IBM and Qiskit in prose; the mark
  borrows nothing of theirs (no eight-bar stripes, no Qiskit logo, no IBM blue or Qiskit purple,
  no processor names). The dilution-refrigerator chandelier is the field's shared image, not a
  company's.
- **Distinct from CASSANDRA.** Different shape language, palette and type (no Source Serif 4).

## Verification *(planned)*

```bash
python brand/tools/build_brand.py
python brand/tools/check_brand.py
```

Plus a visual pass of the brand board and the 16 px favicon checked by eye.

## Related docs

- CASSANDRA Collective brand kit, the pattern this follows: `Cassandra-Collective/.github/brand`.
- Organisation profile: `profile/README.md` in this repository.
- Engine rationale: `superconducted-noise-engine/README.md`, "Why this exists".

## As of 2026-10-16

The four candidates were committed and pushed as `37403c2`. The owner then widened the work to
the whole branding operation (foundation, visual system, digital applications); that plan is in
[`2026-10-16-superconducted-brand-system.md`](2026-10-16-superconducted-brand-system.md). The
sections above are kept as written.
