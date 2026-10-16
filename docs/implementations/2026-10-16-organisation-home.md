# 2026-10-16: organisation-home

Status: **plan, written before the changes it describes.** Results are recorded in an as-of
section appended at the end; the plan rows are not edited afterwards.

## Problem / Motivation

Mert, 2026-10-16: the brand's `eps`, `guide`, `pdf`, `png`, `source`, `svg` and `web` folders are
"missing", and SuperconducTED needs "a proper branding just like CASSANDRA", READMEs written
"from the beginning properly", and "all the steps for a proper open source organisation".

Measured the same day against `Cassandra-Collective/.github` and its flagship:

| Area | CASSANDRA | SuperconducTED before this change |
| --- | --- | --- |
| Brand layout | `brand/eps`, `brand/guide`, `brand/pdf`, `brand/png`, `brand/source`, `brand/svg`, `brand/web` | the same folders one level down, in `brand/kit/` |
| `.github` root `README.md` | a map of the repository | a 251-line copy of the organisation profile page |
| Community health files and licence | CoC, CONTRIBUTING, SECURITY, SUPPORT, issue forms, PR template, LICENSE, NOTICE (health 87%) | none on `main` (health 25%); prepared on the unpushed branch `docs/community-health` |
| Organisation profile | name and description | all fields empty |
| Repository presence | every repository has a description and topics | none |
| Flagship | branded README, CONTRIBUTING, CITATION.cff | none of these; README states the retired "at least 630 records" floor (NC-012 has been 1,170 since 2026-09-09) and "five contributors" (health 37%) |

## Decisions (Mert, 2026-10-16, this session)

| Question | Answer |
| --- | --- |
| Kit layout | Move the seven folders up to `brand/`, exactly like CASSANDRA. |
| Candidates and decision sheets | Move to `brand/history/` (three candidates, the brief, the mark API, the comparison, the in-use and palette sheets). |
| The chosen mark's source | Its own folder, `brand/mark/` (the cutaway's `mark.py`, `check_api.py`, `build.py`, `NOTES.md` and renders). |
| READMEs to rewrite from the beginning | The `.github` root README (a repository map), the brand guide (restructured to CASSANDRA's section order), and the engine README. |
| Organisation profile | Name "SuperconducTED"; description "Student research at TED University: honest noise models for superconducting quantum computers."; URL `https://superconducted.github.io/`; location "Ankara, Türkiye"; no public email. **Applied and read back before this plan was written.** |
| The private co-design repository | Naming it in public files is fine; the morning's "never name it" rule is dropped. |
| Engine CITATION.cff authors | Mert Efe Şensoy, Burak Öztekin, Baha Jarad, Bengisu Cıvdı and Dr. Fırat Akba. |
| Website repository | Description "Source of superconducted.github.io, the SuperconducTED website: Hugo, English and Turkish, deployed by GitHub Actions.", homepage the site, topics `hugo`, `github-pages`, `website`, `quantum-computing`. |

Already approved earlier the same day (recorded in `2026-10-16-repository-presence.md` and
`2026-10-16-community-health-files.md` on this branch) and not re-asked: the community files and
licence, private vulnerability reporting on the engine and `.github`, Discussions on `.github`, and
the descriptions and topics of the engine, `.github` and the co-design repository, all applied
right after this repository's pull request merges.

## What will change (planned)

This pull request (`SuperconducTED/.github`, branch `docs/organisation-home`):

| Path | Change |
| --- | --- |
| `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`, `.github/ISSUE_TEMPLATE/*`, `.github/pull_request_template.md`, `LICENSE`, `NOTICE`, `brand/LICENSE-BRAND.md`, three records and `_TEMPLATE.md` | The six commits of `docs/community-health`, rebased unchanged onto `main` (`68e40e7`). |
| `brand/kit/{eps,guide,pdf,png,source,svg,web}/`, `brand/kit/manifest.json` | Renamed to `brand/{eps,...}/` and `brand/manifest.json`. Pure renames: no file is rebuilt. |
| `brand/candidates/cutaway/` | Renamed to `brand/mark/`; its two scripts' path to `brand/tools` shortened by one level. |
| `brand/candidates/{engraved,isometric,radial}/`, `BRIEF.md`, `MARK_API.md`, `README.md`, `compare.py`, `compare.png`, `.gitignore` | Renamed to `brand/history/candidates/`; their scripts' paths to `brand/tools` lengthened by one level. |
| `brand/decision/` | Renamed to `brand/history/decision/`. |
| `brand/tools/build_brand.py` | Finds the chosen mark in `brand/mark/`, the others in `brand/history/candidates/`, writes decision sheets to `brand/history/decision/`; rebuild instructions name the new kit location. |
| `brand/README.md` | Rewritten from the beginning in CASSANDRA's section order, with every link to the new paths. |
| `brand/CONSTRUCTION.md` | Links and commands point to `mark/` and `guide/`; no other change. |
| `README.md` (root) | Rewritten from the beginning as a map of the repository, replacing the stray copy of the profile page. |
| `profile/README.md` | Only the HTML comment's path to the header's source (`brand/web/profile-header.svg`). |
| `docs/implementations/2026-10-16-organisation-home.md` | This record. |
| `docs/implementations/2026-10-16-superconducted-brand-system.md`, `2026-10-16-repository-presence.md` | One appended as-of section each (the kit moved; homepages are no longer blank). |

Then, in order:

1. **Settings, right after the merge**, each read back: private vulnerability reporting on the
   engine and `.github`; Discussions on `.github`; descriptions and topics on all four
   repositories; community health percentages recorded.
2. **Engine pull request** (needs a teammate's approval): README rewritten from the beginning with
   the brand header loaded from `.github`'s `brand/web/`; `CITATION.cff`; the prepared community
   files (`CONTRIBUTING.md`, issue chooser `config.yml`, Question form) from `docs/community-files`.
   It goes second because its header image loads from this repository's `main`.
3. **Website pull request**: `scripts/sync_brand.py` and `NOTICE` updated to the new paths
   (`data/brand.yaml` stays valid: it is pinned to `c70c9a9`), bundled with switching on the three
   pending facts once engine PR #116 merges.

## Implementation approach

- **Renames, not rebuilds.** PNG, PDF, EPS and `.vectorcraft` files embed timestamps and SVG and
  JSON line endings change under `core.autocrlf`, so rebuilding would rewrite almost every file.
  Every move is `git mv`, proven afterwards by `git diff -M100% --stat` (renames only) and by
  identical blob ids in `git ls-tree` before and after.
- **The kit becomes `brand/` itself.** `check_brand.py` takes a kit folder and reads
  `<folder>/manifest.json`; with the manifest at `brand/manifest.json`, `check_brand.py brand`
  checks the kit with no code change. `build_brand.py` never deletes its output folder, but it is
  run into a short scratch folder (VectorCraft writes nothing at 260+ path characters) and the
  seven folders and the manifest are copied into `brand/`.
- **Paths.** Scripts locate `brand/tools` relative to their own folder; each moved script's
  number of `..` steps changes to match its new depth. No other code changes.

## Mathematical / Statistical details

N/A: purely structural (renames, paths and prose).

## Design decisions

- **`brand/mark/` rather than `brand/history/candidates/cutaway/`**: the chosen mark's geometry is
  a live input of every build and the subject of `CONSTRUCTION.md`; filing it under "history"
  would point readers learning the mathematics at a folder that says it is past. Mert's choice.
- **One pull request for the community files and the restructure**: the new root README describes
  both the community files and the moved brand folders, so it must land with them; the renames
  collapse to a short diff.
- **Dated records keep their old `brand/kit/` links** (append-only rule); the brand-system record
  gets one as-of line saying where the files went.

## Verification (planned)

- `git diff -M100% --stat origin/main` lists the kit, mark, history and decision files as renames
  only; `git ls-tree -r` blob ids for every moved file equal their ids on `main`.
- `python -I brand/tools/check_brand.py brand`: 190 files checked, 0 problems.
- The chosen mark imports from `brand/mark/` through `build_brand.py`'s loader and
  `mark.construction()` returns the values CONSTRUCTION.md cites; `brand/mark/check_api.py` runs.
- Every relative link in `README.md`, `brand/README.md` and `brand/CONSTRUCTION.md` resolves to a
  file in the tree (a link checker run over the three files); no em dashes in any changed file.
- On GitHub after the push: the brand guide and the root README render with their images.

## Related docs

- `2026-10-16-community-health-files.md`, `2026-10-16-licence.md`,
  `2026-10-16-repository-presence.md` (this branch)
- `2026-10-16-superconducted-brand-system.md` (the kit, built under `brand/kit/`)
- `Cassandra-Collective/.github` `README.md` and `brand/README.md` (the model)
