# 2026-10-16 · Repository presence: descriptions, topics, social previews and the settings behind the community files

| | |
|---|---|
| Repository | `SuperconducTED/.github`, plus the settings of every repository in the organisation |
| Branch | `docs/community-health` |
| Status | Planned. Every setting below is approved by the owner (2026-10-16); none is applied yet. Each "As of" section appended later records what was applied and read back |

Prose style: no em or en dashes.

## Problem / Motivation

Measured on 2026-10-16 (`gh api repos/SuperconducTED/<repo>`):

| Repository | Visibility | Description | Homepage | Topics | Discussions | Private vulnerability reporting |
|---|---|---|---|---|---|---|
| superconducted-noise-engine | public | none | none | none | on (Q&A answerable, 0 discussions) | off |
| `.github` | public | none | none | none | off | off |
| superconducted-codesign | private | "Requirements and design record for the SuperconducTED co-design tool (SRS v0.2, pre-scope-freeze draft)" | none | none | off | not offered (private) |

So the flagship showed no description or topics in search, on the organisation page or in link previews, and every link to it unfurled with GitHub's generic image although the brand kit (pull request #1) ships a social card for it. The community files in this branch also depend on two settings: `SECURITY.md` prefers private vulnerability reporting, and the default "Ask a question" link and `SUPPORT.md` point at this repository's Q&A.

## What Changed

| File | Description |
|---|---|
| `docs/implementations/2026-10-16-repository-presence.md` | This record: the approved settings, descriptions and topics, the pending homepages, and which social card goes on which repository. |

Nothing else in the tree. Repository settings live outside it; the engine's README header is a separate engine pull request (below).

## Implementation Approach

### 1. Settings the owner approved on 2026-10-16

| Setting | Repositories | Command | Read back with |
|---|---|---|---|
| Private vulnerability reporting on | superconducted-noise-engine, `.github` | `gh api -X PUT repos/SuperconducTED/<repo>/private-vulnerability-reporting` | `gh api repos/SuperconducTED/<repo>/private-vulnerability-reporting` gives `"enabled": true` |
| Discussions on | `.github` | `gh repo edit SuperconducTED/.github --enable-discussions` | `gh api repos/SuperconducTED/.github --jq .has_discussions` gives `true`; GraphQL `discussionCategories` lists Q&A with `isAnswerable: true` |

Not approved, so unchanged: Discussions for superconducted-codesign. Its questions go through the default Question form.

The owner approved these "once the .github pull request merges", and on 2026-10-16 confirmed right after the merge rather than right before it. For the minutes in between, the merged `SECURITY.md` names a report form, and the default `config.yml` and `SUPPORT.md` link a Q&A page, that do not exist yet; they are flipped immediately after the merge and read back.

### 2. Descriptions and topics (approved by the owner on 2026-10-16, to apply when this branch merges); homepages pending

Descriptions follow the Collective's pattern: what the project is, in one sentence a stranger understands, with its status. Topics favour names other repositories already use, so the project shows up on those topic pages; the counts are `gh api "search/repositories?q=topic:<name>"` on 2026-10-16.

**superconducted-noise-engine**

- Description (208 characters): "Fuzzy-logic noise engine for Qiskit Aer: turns IBM calibration snapshots into an ensemble of noise models, aiming for interval predictions that track real hardware across calibration cycles. Research preview."
- Homepage: blank, pending the organisation's website decision (see Design Decisions).
- Topics (13): `quantum-computing` (6,346 repositories), `qiskit` (1,928), `qiskit-aer` (61), `ibm-quantum` (216), `superconducting-qubits` (70), `quantum-noise` (32), `noise-model` (12), `fuzzy-logic` (1,280), `takagi-sugeno-kang` (8), `anfis` (75), `uncertainty-quantification` (1,552), `calibration` (2,539), `python`.
- Left out: `type-2-fuzzy` and `interval-type-2-fuzzy` (0 repositories each), `noise-modeling` (14, a near-duplicate of `noise-model`).

**`.github`**

- Description (179 characters): "SuperconducTED's organisation profile, its brand (the cutaway mark, the Cryostat palette and the scripts that build them) and the community health files every repository inherits."
- Homepage: blank, pending the organisation's website decision (see Design Decisions).
- Topics (5): `brand-guidelines`, `brand-identity` (168), `design-system`, `logo` (the Collective's four), and `community-health` (624).

**superconducted-codesign** (private, so only members see any of this)

- Description: unchanged; it already says what the repository is, and its social card repeats it.
- Homepage: none.
- Topics (4): `requirements` (832), `software-requirements-specification` (12), `co-design` (45), `quantum-computing`.

Apply, after the merge, with `gh repo edit SuperconducTED/<repo> --description "..." --add-topic <a>,<b>,...` (no `--homepage` until the website is chosen), then read back with `gh api repos/SuperconducTED/<repo> --jq '{description,homepage,topics}'`.

### 3. Social previews (the owner uploads by hand)

GitHub has no API for the social preview; it is set in each repository's **Settings, General, Social preview, Edit, Upload an image**. GitHub asks for a PNG, JPG or GIF under 1 MB, at least 640 by 320 pixels, 1280 by 640 recommended.

| Repository | Upload this file from `brand/kit/web/` | What the card says | Size |
|---|---|---|---|
| superconducted-noise-engine | `social-card-noise-engine.png` | "Noise engine", with the engine's one-line description | 1280 x 640, 52,295 bytes |
| `.github` | `social-card.png` | "SuperconducTED", with the tagline "Noise as a range, not a number." | 1280 x 640, 45,650 bytes |
| superconducted-codesign | `social-card-codesign.png` | "Co-design", with "Requirements and design record for the SuperconducTED co-design tool." | 1280 x 640, 51,603 bytes |

The organisation itself has no social preview setting; its avatar and profile fields belong to the session applying the brand to the organisation profile.

### 4. The engine pull request (owner's choice, 2026-10-16)

A separate pull request in superconducted-noise-engine, opened after this branch merges, with:

- the brand README header, `brand/kit/web/readme-header-noise-engine.svg`, at the top of the engine's `README.md`, loaded from this repository's `main` by absolute URL (it shows a broken image until pull request #1 is merged, which is why the engine pull request comes second);
- a thin `CONTRIBUTING.md` that points at the engine's own conventions (module ownership in `docs/team.md`, the decision ledger, the numerical claims register, the pull request template's hard constraints) and defers the general parts to the organisation's guide;
- `.github/ISSUE_TEMPLATE/config.yml` with contact links to the engine's Q&A, the security policy and the code of conduct, blank issues left on;
- a Question form, `.github/ISSUE_TEMPLATE/question.yml`, labelled `question`.

The engine's `bug.md`, `feature.md` and pull request template stay unchanged. That pull request carries its own implementation record under the engine's rules.

## Mathematical / Statistical Details

None.

## Design Decisions

| Decision | Alternatives | Why | Who |
|---|---|---|---|
| One card per repository, as the kit provides | The organisation card everywhere | The kit was built that way; the Collective did the same | Brand kit, pull request #1 |
| The organisation card (with the tagline) on `.github` | No card there | `.github` is the organisation's home; its card is the one with the tagline | Engineering; the owner reviews it at upload |
| Homepage left blank on every repository until the organisation's website is chosen | The organisation page (first drafted, and approved earlier the same day); `docs/architecture.md` | The owner is choosing a website (`superconducted.dev` or `superconducted.io` under evaluation) and asked for blank homepages until then. `superconducted.com` and `superconducted.org` are registered to someone else (since 2025-07-18) and are never used as a homepage or in any link | Owner, 2026-10-16, relayed by the lead session |
| Topics chosen from names other repositories use | Coining exact names for interval type-2 fuzzy logic | A topic nobody else uses leads nowhere | Engineering; approved by the owner, 2026-10-16 |
| Settings applied only on the owner's word, then read back | Applying them without asking | They are public-facing and outside the tree | Owner's standing rule |

## Verification

Before any change: the measurements in the first table (`gh api repos/SuperconducTED/<repo>`, `.../private-vulnerability-reporting`, GraphQL `discussionCategories`), the topic counts above, and the card files' sizes and dimensions (`file`, `ls -l`).

After each change, the read-back command in its row, and `gh api repos/SuperconducTED/<repo>/community/profile --jq .health_percentage` for all three repositories, recorded in an appended "As of" section.

**Not tested:** how the cards look as link previews on other sites, which depends on the upload.

## Related Docs

- [`2026-10-16-community-health-files.md`](2026-10-16-community-health-files.md), [`2026-10-16-licence.md`](2026-10-16-licence.md)
- [`brand/README.md`](../../brand/README.md), "Digital applications"
- The pattern this follows: `Cassandra-Collective/.github`, `docs/implementations/2026-10-14-project-cards-and-org-move.md` and `2026-10-15-discussions-qa.md`
