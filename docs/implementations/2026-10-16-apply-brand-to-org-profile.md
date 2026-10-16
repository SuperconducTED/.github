# 2026-10-16: apply-brand-to-org-profile

> Status: **on branch `brand/apply-identity-to-profile`, pull request pending; the settings
> steps below are not applied.** Applies the
> identity chosen on 2026-10-16 (technical cutaway mark, Cryostat palette, tagline "Noise as a
> range, not a number.") to the organisation profile in this repository. The organisation
> settings and social previews are prepared below as manual steps for the owner; nothing in
> them has been applied.

## Problem / Motivation

The organisation profile (`profile/README.md`, rendered on github.com/SuperconducTED) still
wore the pre-brand look: an animated Bloch-sphere banner and two diagrams in a purple, cyan and
night palette (`#7f5af0`, `#06b6d4`, `#0b0d17`, `#1e1b4b`), glows and gradients, badges in the
same purple, and copy that states the research aim ("an interval that brackets real
hardware") as if it were a result. The brand guide (`brand/README.md` on PR #1) retires that
palette, bans gradients and glows, and gives the accent colour one meaning: the range. The
brand foundation (`brand/FOUNDATION.md` section 2) requires "aims to bracket", never
"brackets", until the results phase reports.

The repository's own `README.md` (an older copy of the profile) also pointed its banner and
diagram at `./assets/header.svg` and `./assets/fuzzy-noise.svg`, which have never existed on
`main`, so both images were broken on the repository page.

## Plan

1. Branch from `origin/main`, not from the brand branch, so this pull request does not depend
   on PR #1 and either can merge first.
2. Replace `header.svg` with a byte copy of the kit's `brand/kit/web/profile-header.svg`
   (same 1280 x 340 size), keeping the raw URL the README already loads; give it alt text that
   says what the banner says.
3. Redraw `fuzzy-noise.svg` and `it2.svg` in the Cryostat dark roles, accent on the range only.
4. Recolour every retired-palette use in both READMEs (badges, the mermaid pipeline, the pinned
   repository card, the footer wave) to ink and light.
5. Fix only voice in the copy (dashes, claims stated as aims); list stale facts for the owner.
6. Write the settings and social-preview steps for the owner, with measured file sizes.

## What changed

| File | Change |
| --- | --- |
| `header.svg` | Replaced by a byte copy of `brand/kit/web/profile-header.svg` from commit 06f1959 (git blob `243bfeb1dddb65b541c339e665ed01b1c01cd77e`, sha256 `18b411d4d005393d4aa2b3043ca4e9f871aa6b33789c274710d4a351b6bdb4db`); static, letters as outlines. |
| `fuzzy-noise.svg` | Redrawn in the Cryostat dark roles: footprint of uncertainty and the interval band in the accent, crisp value, sampled models, measured point and type in ink; glows and gradient removed; kickers in sentence case; "brackets" stated as the aim. |
| `it2.svg` | Redrawn the same way: the Type-1 curve in ink, the IT2 band (FOU, UMF, LMF, plateau, membership interval) in the accent; captions moved apart so the signature no longer overlaps them. |
| `profile/README.md` | New banner alt text; badges, mermaid classes, pinned card and footer recoloured; four sentences reworded from result to aim; stale asset paths in the header comment corrected. |
| `README.md` | Same restyle and voice edits; the two broken `./assets/` image paths now load the raw URLs from `main`. Its other content is unchanged (see the stale list). |
| `docs/implementations/2026-10-16-apply-brand-to-org-profile.md` | This record. |

## Implementation approach

**The banner is a copy, not a reference.** Both READMEs load
`https://raw.githubusercontent.com/SuperconducTED/.github/main/header.svg`. Pointing them at
`brand/kit/web/profile-header.svg` instead would show a broken image until PR #1 merges and
would make the two pull requests order-dependent. Copying the file keeps the URL and works in
either merge order; the cost is that `header.svg` is a deployed copy, so after any rebuild of
the kit's banner it must be copied again (the profile README's header comment says so). The
blob hash above is how to check that the copy still matches.

**The diagrams use the brand's own role colours, not new ones.** Every colour is one of the
dark chart roles that `brand/figures/build_styles.py` derives from `palettes.py` and records in
`brand/figures/roles.json`:

| Role (roles.json, Cryostat, dark) | Hex | Used for |
| --- | --- | --- |
| ground | `#0A1B24` | Card background; the ring around the measured point |
| text / ink | `#EEF3F5` | All headings and labels, the crisp value, the Type-1 curve, sampled models, the measured point, arrows |
| text_secondary | `#9CA5AA` | Kickers, subtitles, captions, tick labels |
| axis | `#5A676D` | Axes and their end ticks |
| grid | `#25353D` | Panel frames (decoration) |
| band_fill | `#18404B` | The footprint of uncertainty and the interval band |
| accent / band_edge | `#4FD6E6` | The range only: the FOU edges (UMF, LMF), the plateau of the peak, the membership interval at the sample x, the interval's bounds |

The colour rule decides each element: if it is the engine's answer or a range of values, it
wears the accent; the machine, the measurement, the type and all other line work wear ink. The
Type-1 triangle loses its fill, so the only filled shapes left are ranges. The interval's two
bound markers are drawn as the mark's square brackets (`[` and `]`), echoing the logo. No text
is set in the accent. The SMIL animations (pulsing samples, the measured point drifting inside
the interval) are kept; the guide bans gradients, shadows, glows and textures, not motion.

**Typography follows the guide's roles.** Panel headings are Space Grotesk Medium; labels,
kickers and captions are Space Mono, and kickers keep normal casing, so the old all-capitals
strips (including "SUPERCONDUCTED", which the naming rules allow only inside a drawn mark) are
now sentence case with light tracking. The text is live, with system fallbacks
(`ui-monospace`, Menlo, Consolas; `ui-sans-serif`, Segoe UI): viewers without the brand fonts
see the fallback faces. The kit's own files carry their letters as outlines, which these hand
edited diagrams do not.

**README colours.** The retired family (`7f5af0`, `06b6d4`, `0b0d17`, `1e1b4b`) is replaced
everywhere it appears: badges become ink (`0A1B24`) or, on the two-part activity badges, ink
label and light (`EEF3F5`) value; the pinned repository card gets ink ground, light title and
icon, secondary text (its `tokyonight` theme would otherwise colour the text teal, close to the
accent); the footer wave is one flat ink instead of a gradient. In the mermaid pipeline the
input and stages are ink and the output node, the interval prediction, is the one node in the
accent. Third-party colours (Qiskit `6929C4`, IBM `052FAD`, NumPy, SciPy, PyTorch, pytest,
GitHub Actions, Python) stay, because they credit those projects in their own colours, and so
do the status colours (amber, green, blue, slate) on the status, licence and roadmap badges,
because the brand defines no status colours; both are listed for the owner below.

**Edits are scripted with exact before-counts.** The README edits ran from one script that
asserts how many times each old string occurs in each file before replacing anything and writes
nothing if any count differs; it caught one overlap on its first run (`title_color=06b6d4&`
also matched the badge pattern) and wrote nothing. Line endings are preserved.

## Mathematical / statistical details

**Band fill.** `brand/figures/roles.json` defines the band as a solid tint of the accent over
the ground, per sRGB channel and rounded to 8 bits:

    t = (1 - a) * ground + a * accent,  a = 0.20

With ground `#0A1B24` = (10, 27, 36) and accent `#4FD6E6` = (79, 214, 230):
(0.8 * 10 + 0.2 * 79, 0.8 * 27 + 0.2 * 214, 0.8 * 36 + 0.2 * 230) = (23.8, 64.4, 74.8),
rounded (24, 64, 75) = `#18404B`, the value roles.json records.

**Contrast** (WCAG 2.x relative-luminance ratio, computed with `brand/tools/wcag.py`):

| Pair | Ratio | Target |
| --- | --- | --- |
| text `#EEF3F5` on ground | 15.71 | 4.5 (text) |
| secondary `#9CA5AA` on ground | 7.01 | 7.0 (roles.json `secondary_text_target`) |
| accent `#4FD6E6` on ground | 10.12 | 3.0 (graphics) |
| axis `#5A676D` on ground | 3.01 | 3.0 (`axis_target`) |
| text on band fill | 10.02 | 4.5 |
| accent on band fill | 6.45 | 3.0 (`edge_on_band`) |
| frame `#25353D` on ground | 1.39 | none: decoration, like the grid role |
| white badge text on ink `#0A1B24` | 17.57 | 4.5 |
| shields' dark text `#333` on light `#EEF3F5` | 11.30 | 4.5 |

The ink badges sit at 1.08:1 against GitHub's dark page (`#0d1117`): their outline nearly
disappears in dark mode, though their text stays readable. This is the cost of keeping the
badges in the palette.

## Design decisions

- **Branch from `main` and copy the banner** rather than stack on PR #1 and reference the kit
  path: independent merge order and an unchanged image URL, at the cost of one deployed copy
  (above).
- **Dark diagrams only.** The diagrams stay dark cards in both GitHub themes, as before and as
  the banner is; a `<picture>` pair with light versions (accent `#0A6C7C`) is possible but
  doubles the files to maintain.
- **UMF and LMF in the accent, not ink.** They are the band's bounds, the same role as `p_lo`
  and `p_hi`, and the chart style edges its band in the accent. This makes the IT2 panel read
  as a range against the ink Type-1 curve, which is the diagram's point.
- **Live text, not outlines or embedded fonts.** Outlining needs the VectorCraft pipeline and
  makes the diagrams hard to edit by hand; embedding subsetted Space Mono and Space Grotesk as
  data URIs would make every viewer see the brand faces but needs fontTools and adds a
  base64 block to each file. Left as an option for the owner.
- **Voice, not facts.** Four sentences and one alt text that stated the aim as a result now say
  "aim to bracket", "the aim is", "aims to bracket" and "is designed to absorb"; the diagram's
  "real IBM ∈ [p_lo, p_hi]" gains an "aim:" prefix. Dated or stale facts are listed below for
  the owner, not changed.

## Voice audit and stale content, for the owner

Checked against `brand/FOUNDATION.md` and the engine at `origin/main` fec055c. Byte scan: no
U+2013 or U+2014 in any file this change touches.

**Reworded (voice only):** the abstract's "predictions that bracket real hardware", "The win is
that the real IBM datapoint lives inside the interval", "That extra richness is exactly why the
interval prediction ... brackets real hardware", the FAQ's "The fuzzy envelope absorbs the
per-snapshot accuracy gap", and the fuzzy-noise alt text. In `README.md`, the same sentences
where they occur.

**Stale or unsupported, left for the owner** (profile/README.md unless noted):

1. **The ANFIS floor is `≥ 630` in five places** (roadmap Phase 1, Now shipping, the glossary's
   ANFIS row, the FAQ's "What's the ≥ 630 number?", and `README.md`). The engine's register
   row NC-012 reads `≥ 1170` since 2026-09-09, counted in distinct device states, not snapshot
   files.
2. **"floor projected for mid-July 2026"** (roadmap Phase 1 and Now shipping) is a past date.
3. **Roadmap state.** Phase 2 "in design" and Phase 3 "Whitepaper ... planned" predate the ANFIS
   core merging (engine PR #114, 2026-10-15), and the profile's phase numbers no longer match
   the engine's (its phase 3 is "Results from ANFIS", tracked on the `phase-3-dashboard`
   branch).
4. **Polling cadence.** "fires at HH:05 every hour" and "targeting ~24 snapshots/day": the
   workflow now has four entries per hour (:07, :22, :37, :52) plus a daily sweep at 04:41,
   and its header records that IBM republishes about every 1.26 h (NC-030).
5. **Backfill cap.** "capped at 30 days via `SUPERCONDUCTED_HISTORICAL_MAX_DAYS`" matches the
   poller's default, but the workflow comment records reads verified to at least 60 days; worth
   a look before it is restated.
6. **Field notes** stop at the 2026-05-25 audit; nothing since (for example the ANFIS core,
   engine PR #114, merged 2026-10-15).
7. **Stack badges for PyTorch and scikit-fuzzy:** neither is in `requirements.txt`,
   `requirements-dev.txt` or `pyproject.toml`, and nothing under `src/` imports them.
8. **Unsourced comparative claims:** "Crisp calibration-based noise models match real hardware
   tightly on the snapshot ... and degrade silently" (abstract) and "The literature reports
   excellent fidelity on the snapshot it was tuned on, then degrades silently" (Why fuzzy, why
   now) need a citation or softening; "We close the gap with" (abstract) could read as a
   result.
9. **Text and diagram disagree** on the illustrative IT2 numbers: the text says
   `μ(T1 = 142 µs) = 0.85` and `∈ [0.55, 0.85]`; the diagram shows `μ = 0.53` and
   `∈ [0.4, 0.9]` at about 130 µs.
10. **`README.md` is an older divergent draft** of the profile ("Manifesto" heading, the
    `0.686%` Bautra et al. 2026 benchmark bar, a four-hourly cadence, "ANFIS training
    prerequisite", no IT2 section). Options: make it identical to `profile/README.md`, or
    replace it with a short repository README that points at the profile and the brand guide.
11. **Remaining non-palette colours:** the status badges (amber `f59e0b`, green `10b981`, blue
    `3b82f6`, slate `64748b`), the activity badges for open issues (amber) and open PRs
    (green), and the third-party stack badges. Kept on purpose (above); say if they should go
    to ink too. The footer wave could also be removed rather than recoloured.

Correct as written: Python 3.11 and 3.12 (CI matrix), MIT licence, five contributors plus the
faculty advisor (`docs/team.md`), every linked engine document exists, and the
`calibration-data` layout (`snapshots/YYYY-MM/...`).

## Manual steps for the owner (not applied)

GitHub accepts these only through its web settings, and they are the owner's to make. Files
are in a checkout of `brand/superconducted-identity` (PR #1), under `brand/kit/web/`; sizes
measured 2026-10-16.

**A. Organisation profile** (needs an organisation owner): open
`https://github.com/organizations/SuperconducTED/settings/profile` (or: your profile picture,
**Organizations**, SuperconducTED, **Settings**). The field names below are GitHub's usual
labels; the page was not opened signed in while writing this.

1. **Organization display name:** `SuperconducTED`
2. **Description:** `Student research at TED University: interval-valued noise models for IBM's superconducting quantum computers, built on Qiskit Aer.` (130 characters; GitHub allows 160)
3. **Location:** `Ankara, Türkiye`
4. **URL:** leave blank (FOUNDATION.md section 9: no placeholder site).
5. Click **Update profile**.
6. **Profile picture:** under the current picture, click **Upload new picture**, choose
   `avatar-1024.png` (1024 x 1024, 60,901 bytes; GitHub's limit is 1 MB), keep the crop at the
   full square, and confirm.

**B. Social previews** (one per repository; each needs admin on that repository): open the
repository, **Settings** (gear tab), **General**, scroll to **Social preview**, click **Edit**,
then **Upload an image...**. GitHub asks for PNG, JPG or GIF under 1 MB, at least 640 x 320,
1280 x 640 recommended; all three cards are 1280 x 640.

| Repository | File | Size | Note |
| --- | --- | --- | --- |
| `.github` | `social-card.png` (the tagline card) | 45,650 bytes | GitHub has no organisation-level social preview; this card stands in for the organisation where this repository is linked. |
| `superconducted-noise-engine` | `social-card-noise-engine.png` | 52,295 bytes | |
| `superconducted-codesign` | `social-card-codesign.png` | 51,603 bytes | **Private:** GitHub accepts a social preview on a private repository only if one was uploaded before, and this one has none, so it cannot be set until the repository is public. |

**C. Check afterwards:** `gh repo list SuperconducTED --json name,usesCustomOpenGraphImage`
shows `true` for each repository whose preview was set (all `false` on 2026-10-16), and
`gh api orgs/SuperconducTED --jq '{name,description,location}'` shows the profile fields (all
`null` on 2026-10-16).

## Verification

Run from the repository root of this branch.

1. **The banner is the kit's file:** `git hash-object header.svg` prints
   `243bfeb1dddb65b541c339e665ed01b1c01cd77e`, the blob of
   `brand/kit/web/profile-header.svg` at 06f1959 (`git rev-parse
   06f1959:brand/kit/web/profile-header.svg` in a clone that has PR #1's branch).
2. **Colours and the colour rule:** every hex in the two diagrams (comments excluded) is one of
   the seven roles above; `#4FD6E6` and `#18404B` appear only on elements whose XML comment
   names a range (6 in `fuzzy-noise.svg`, 7 in `it2.svg`) and never on text; no
   `linearGradient`, `filter` or `feGaussianBlur`; no `7f5af0`, `06b6d4`, `0b0d17`, `1e1b4b`
   left in either README. The check script used while building caught each of six planted
   defects: the accent on a label, the accent on an arrow, an off-palette colour, a glow
   filter, an en dash and a retired colour in a README.
3. **Rendering:** each SVG renders as an `<img>` in Chromium (headless Edge) on both GitHub
   grounds (`#ffffff`, `#0d1117`) at the README column width; after pushing, open
   `https://github.com/SuperconducTED/.github/blob/brand/apply-identity-to-profile/fuzzy-noise.svg`
   and the same for `it2.svg` and `header.svg`, and the branch's `profile/README.md` blob view,
   which renders the mermaid pipeline (GitHub draws mermaid in the browser and falls back to a
   code block on a syntax error) and the badge rows. That README view still loads `main`'s
   images (absolute URLs), so the README itself shows the new art only after merge: check
   `https://github.com/SuperconducTED` then (GitHub's image proxy may serve the old
   `header.svg` for a few minutes).
4. **External images:** every shields.io, github-readme-stats and capsule-render URL in
   `profile/README.md` returns HTTP 200 with the new colours (checked 2026-10-16;
   star-history answers 301 to a lowercased URL, unchanged by this work).

## Related docs

- `brand/README.md` (the brand guide: colour rule, typography, don'ts) and
  `brand/FOUNDATION.md` (voice, claims as aims, section 9 profile drafts), both on PR #1.
- `brand/figures/roles.json` (the role colours used here), on PR #1.
- `docs/implementations/2026-10-15-superconducted-brand-identity.md` and
  `2026-10-16-superconducted-brand-system.md`, on PR #1.
- GitHub docs: "Customizing your repository's social media preview" and "Customizing your
  organization's profile".
