# 2026-10-16: professional-profile

Status: **plan, written before the change**; the result is appended as an as-of section.

## Problem / Motivation

Mert, 2026-10-16: the organisation profile "needs to be professional". The page GitHub shows at
github.com/SuperconducTED (`profile/README.md`) was 273 lines against the 27 of
`Cassandra-Collective/.github`'s profile, and:

- it decorated with 16 shield badges, a pinned-repository card (github-readme-stats), a
  star-history chart and a wave footer (capsule-render), all from third-party services, and "❯"
  glyphs in every heading;
- it stated retired or wrong facts: a "≥ 630 snapshot" training floor (NC-012 has been at least
  1,170 since 2026-09-09), polling "at HH:05 every hour" (the target is :37, NC-008), a phase
  roadmap and FAQ written before cycle 2, and PyTorch and scikit-fuzzy badges;
- it duplicated the website and the engine README at length.

## Decisions (Mert, 2026-10-16)

| Question | Answer |
| --- | --- |
| Shape | CASSANDRA-style and short: the logo, the tagline, one paragraph, a projects table, "How we work", links. No badges, stats cards or third-party widgets. |
| Header | The stacked lockup, switching between its on-light and on-dark versions with the visitor's GitHub theme, centred, 280 px wide (its minimum is 225 px). |
| The two explainer diagrams | Dropped from the profile; `fuzzy-noise.svg` and `it2.svg` stay in the repository. |

## What will change (planned)

| File | Change |
| --- | --- |
| `profile/README.md` | Rewritten from the beginning to the shape above. |
| `README.md` | The repository map's row for the root SVGs says the profile no longer loads them. |
| `docs/implementations/2026-10-16-professional-profile.md` | This record. |

## Implementation approach

- Images load by relative path from `profile/` (`../brand/svg/...`), as CASSANDRA's profile does,
  so the page follows the brand files in this repository with no raw URLs.
- Every statement is checkable: the projects' one-liners match their repository descriptions
  (set and read back on 2026-10-16), and "How we work" names only practices the repositories
  enforce (the ADR ledger, the numerical-claims register, per-change records, aims stated as
  aims). The page states no figures, so it needs no register rows.

## Mathematical / Statistical details

N/A: prose and layout only.

## Design decisions

- **No status badges or live counters**: they depend on external services, go stale silently and
  add nothing a visitor can act on; the engine's README carries its CI badge.
- **The org-level paragraph says what and why, not how**: the method and its equations live on the
  website and in the engine README, linked from the projects table.

## Verification (planned)

- The rewritten profile renders on GitHub (blob view on the branch, then the organisation page
  after merging), with the lockup switching between light and dark themes.
- Every link resolves; no em dashes.

## Related docs

- `2026-10-16-apply-brand-to-org-profile.md` (the previous restyle, which listed the stale facts)
- `2026-10-16-organisation-home.md`
- `Cassandra-Collective/.github` `profile/README.md` (the model)

## As of 2026-10-16, later: rendered and checked

`profile/README.md` is 33 lines. On GitHub's blob view of the branch it renders with the stacked
lockup in both themes (the on-dark file under a dark GitHub theme), the tagline, the paragraph,
the three-row projects table, "How we work" and the footer links; all 34 relative links in the
changed files resolve and none contains an em dash. The organisation page itself shows the new
profile once this branch is merged into `main`.
