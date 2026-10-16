# 2026-10-16 · Organisation-wide community health files

| | |
|---|---|
| Repository | `SuperconducTED/.github` |
| Branch | `docs/community-health`, based on `brand/superconducted-identity` (pull request #1) at `06f1959` |
| Status | Implemented and checked on 2026-10-16 by static checks (Python 3.12.10 with PyYAML 6.0.3, git 2.53, gh 2.92, Windows 11); how GitHub renders the defaults can only be seen after merge |

Prose style: no em or en dashes.

## Problem / Motivation

On 2026-10-16 GitHub's community profile (`gh api repos/SuperconducTED/<repo>/community/profile`) scored the organisation's repositories at:

| Repository | Visibility | Score | Has of its own |
|---|---|---|---|
| superconducted-noise-engine | public | 37% | README, LICENSE (MIT), pull request template, two legacy Markdown issue templates (`bug.md`, `feature.md`) |
| `.github` | public | 25% | README |
| superconducted-codesign | private | 28% | README |

No repository had a code of conduct, a contributing guide, a security policy or a support guide. A person who found a security problem in the engine (for example a committed IBM Quantum token, or a scheduled workflow an outside pull request could abuse) had no published private route to report it, and private vulnerability reporting was off on both public repositories. Nobody was told what conduct is expected or where to ask a question.

The owner's sister organisation, the Cassandra Collective, closed the same gap on 2026-10-14 by making its `.github` repository the home of organisation-wide defaults (`Cassandra-Collective/.github`, `docs/implementations/2026-10-14-community-health-files.md`); every one of its repositories now scores 87%. The owner asked for the same here, adapted to SuperconducTED, after the brand (pull request #1) landed.

## What Changed

| File | Description |
|---|---|
| `CODE_OF_CONDUCT.md` | The Contributor Covenant 2.1 with the enforcement contact sensoymertefe@gmail.com: a byte-for-byte copy of the Cassandra Collective's file. |
| `SECURITY.md` | The organisation-wide security policy: report privately through GitHub's private vulnerability reporting (public repositories) or by email, what to include, what to expect, scope with the engine's own risks named; a repository's own policy takes precedence. |
| `SUPPORT.md` | Where to ask questions (each repository's Discussions, Q&A category), what to include (Qiskit and Aer versions, the backend and snapshot), what not to post (tokens, `.env`), and that there is no paid support. |
| `CONTRIBUTING.md` | The organisation's general guide: the projects, the shared values (evidence, sourced numbers, written decisions, docs with code), how to start, the issue-first flow, and the rules specific to this repository. A project's own guide and conventions take precedence. |
| `.github/ISSUE_TEMPLATE/bug-report.yml` | Default issue form for a bug report, labelled `bug`. |
| `.github/ISSUE_TEMPLATE/feature-or-improvement.yml` | Default issue form for a feature or improvement, labelled `enhancement`. |
| `.github/ISSUE_TEMPLATE/question.yml` | Default issue form for a question that should be tracked as an issue, labelled `question`. |
| `.github/ISSUE_TEMPLATE/config.yml` | Template chooser: blank issues off; contact links to this repository's Q&A, the security policy and the code of conduct. |
| `.github/pull_request_template.md` | Default pull request template: what changes, the issue it closes, evidence, docs updated, checklist. |
| `docs/implementations/_TEMPLATE.md` | The implementation-document template, copied unchanged from the Cassandra Collective (it is generic). `CONTRIBUTING.md` and the owner's standing rules cite it, and this repository had none. |
| `README.md` | One block appended at the end: a "Community health files" table and a "Licence" section. Nothing above it changes, because a parallel session is restyling the rest of the file. |
| `docs/implementations/2026-10-16-community-health-files.md` | This document. |

The licence files (`LICENSE`, `NOTICE`, the legal code in `brand/LICENSE-BRAND.md`) are in the same branch and have their own record, [`2026-10-16-licence.md`](2026-10-16-licence.md). Descriptions, topics, social previews and the settings this change depends on are in [`2026-10-16-repository-presence.md`](2026-10-16-repository-presence.md).

## Implementation Approach

**How GitHub uses these files.** GitHub's documentation, "Creating a default community health file", says (as the Cassandra Collective's record quotes it on 2026-10-14):

- default community health files go in a **public** repository named `.github` owned by the organisation;
- GitHub uses a default file for every repository in the organisation that has no file of that type of its own, whatever that repository's visibility;
- issue templates and their `config.yml` must be stored in `.github/ISSUE_TEMPLATE`;
- the other supported files may be in the root, the `.github` folder or the `docs` folder;
- if a repository has valid issue templates or an issue template `config.yml` of its own, **none** of the default issue templates are used there: the replacement is all or nothing for the folder, file by file for everything else;
- a label set by an issue template must exist in the repository where the template is used, or it is not applied.

**Which defaults each repository will show,** file by file, once this branch merges:

| Repository | Code of conduct | Contributing | Security | Support | Issue forms and `config.yml` | Pull request template |
|---|---|---|---|---|---|---|
| superconducted-noise-engine | default | default | default | default | **its own** (`bug.md`, `feature.md`) | **its own** |
| superconducted-codesign | default | default | default | default | default | default |
| `.github` | these files | these files | these files | these files | these files | these files |

The engine is the case that matters most:

- Its own `.github/ISSUE_TEMPLATE/` (two legacy Markdown templates, no `config.yml`) means none of the default forms and no default contact links appear on its new-issue page, and blank issues stay possible there. The owner decided on 2026-10-16 to add, in a separate engine pull request, a `config.yml` (contact links to its Q&A, the security policy and the code of conduct; blank issues stay on) and a Question form; `bug.md` and `feature.md` stay unchanged.
- It has no `CONTRIBUTING.md`, so the default guide would be shown there. That is why the default guide names the engine's own conventions (module ownership in `docs/team.md`, the decision ledger, the numerical claims register) by absolute URL, and why the owner chose a thin engine `CONTRIBUTING.md` in the same engine pull request, which then takes precedence.
- Its own pull request template (hard-constraint review, CI gates, owner sign-off) keeps overriding the default.

**Placement.** As in the Cassandra Collective: the four Markdown policies at the root (what a reader browsing this repository sees first, and short absolute URLs for the other files to link to), the issue forms and `config.yml` in `.github/ISSUE_TEMPLATE/` (the only accepted location), and the pull request template in `.github/`.

**Links.** Every link in a default file is an absolute URL, because GitHub shows a default file in the context of another repository, where a relative link would resolve against the wrong one.

**What was adapted from the Cassandra Collective, and why:**

- **Code of conduct:** copied byte for byte. It never names an organisation ("community leaders", "our community"), is plain ASCII and has no em or en dashes, so it reads correctly here; the owner chose the same enforcement contact.
- **Security policy:** private vulnerability reporting is offered only for the public repositories, because GitHub offers it only there (`gh api repos/SuperconducTED/superconducted-codesign/private-vulnerability-reporting` answers 404 for the private repository); email is the route for everything else. The scope names this organisation's real risks: an IBM Quantum token committed to a repository, a scheduled workflow whose secrets an outside pull request could reach, unsafe loading of calibration snapshots or stored datasets. Prediction quality (how well an interval brackets hardware) is out of scope as a research finding, the counterpart of the Collective's "what a model writes".
- **Support guide:** the version fields name the engine's libraries (`qiskit`, `qiskit-aer`, `numpy`, `scipy`) instead of GPUs. It does not claim every repository has a Question form or that blank issues are off everywhere, because neither will be true of the engine until its own pull request merges, and blank issues stay on there by the owner's choice.
- **Contributing guide:** the values are this organisation's own practices, each linked to where it is practised (the numerical claims register, the decision ledger). The review step names the engine's module owners. Neither the guide nor the support guide names the private repository: a public file would otherwise publish its name, and the defaults apply to it anyway.
- **Forms:** the same three forms and element schema; examples and hints changed to this domain (backend and snapshot, Qiskit versions, IBM Quantum token). The Question form now says that Discussions is usually the better place, since it exists from the start here.
- **Pull request template:** one checklist line added, "Every new number in a document has a source", from the engine's numerical claims rule; the secrets line names IBM Quantum tokens and `.env`.

## Mathematical / Statistical Details

None. This is a documentation and configuration change.

## Design Decisions

| Decision | Alternatives | Why | Who |
|---|---|---|---|
| Shared files as organisation defaults in this repository | A full copy in every repository | One place to change the shared policy; the Collective's pattern | Owner, 2026-10-16 (the brief) |
| Enforcement and security contact sensoymertefe@gmail.com | A new role address; a university address | Already public in the Collective's code of conduct | Owner, 2026-10-16 |
| Private vulnerability reporting as the preferred route on the public repositories | Email only | Keeps the report, the fix and the advisory in one place. It is off today; the owner approved turning it on for the engine and `.github` | Owner, 2026-10-16 (enabling); engineering (preferring it) |
| `blank_issues_enabled: false` in the default `config.yml` | `true` | The owner's final choice for the Collective (2026-10-14), so every issue arrives through a form with its label. It applies only where the defaults apply (`.github`, codesign); the Question form keeps a route for questions | Engineering, following the owner's precedent; stated for review |
| The default "Ask a question" link points at this repository's Q&A | The engine's Q&A | Matches the Collective, and the defaults are shown in `.github` and codesign, not in the engine. It needs Discussions on for `.github`, which the owner approved | Owner, 2026-10-16 (Discussions); engineering (link) |
| Not naming superconducted-codesign in public files | Listing it with the others | The defaults apply to it without being named; naming it would publish a private repository's name | Engineering, stated for review |
| Engine conventions linked from the default guide, not restated | Restating ownership and ADR rules | One source of truth; the engine's files keep evolving | Engineering |
| The README change is one block appended at the end | A rewrite like the Collective's | A parallel session is restyling `README.md` and `profile/README.md`; an appended block merges cleanly with that work | Engineering, coordinated with that session |
| Response times stated as aims ("a few days"), with exams and holidays named | A fixed service level | A student group cannot promise one | Engineering |
| Labels `bug`, `enhancement`, `question` only | Adding area or priority labels | They exist in all three repositories today (`gh label list`), so the forms work wherever they are shown | Engineering |

## Verification

1. **State before the change,** read through the GitHub API on 2026-10-16:
   - the community profile scores and files (table under Problem / Motivation);
   - private vulnerability reporting: `enabled: false` on `.github` and the engine, 404 on codesign;
   - Discussions: on for the engine only, with the six default categories and Q&A answerable (GraphQL `discussionCategories`), 0 discussions; off for `.github` and codesign;
   - labels: `bug`, `enhancement` and `question` exist in all three repositories (`gh label list`);
   - the engine's `.github/ISSUE_TEMPLATE/` holds `bug.md` and `feature.md` and no `config.yml` (`gh api repos/SuperconducTED/superconducted-noise-engine/contents/.github/ISSUE_TEMPLATE`);
   - open issues across the organisation labelled `good first issue`: 0; `help wanted`: 0 (search API). The guide's two search links therefore show empty lists today, and say what to do then.
2. **Code of conduct is an exact copy.** `git hash-object CODE_OF_CONDUCT.md` gives `4860e75b35034fa7b88d3b78e3de8068c7289514`, the blob of `CODE_OF_CONDUCT.md` on `Cassandra-Collective/.github` `origin/main`. `grep -i -E 'cassandra|ephesus|collective'` finds nothing in it.
3. **Issue forms are valid.** A validator kept outside the repository (`validate_forms.py`, PyYAML 6.0.3) loads each file with `yaml.safe_load` and checks it against GitHub's documented form schema: required `name`, `description` and non-empty `body`; unique form names; element types and their allowed attributes and validations; `id` pattern and uniqueness; markdown elements with a `value` and no `id`; dropdown and checkbox options; boolean `required`; labels a subset of {`bug`, `enhancement`, `question`}; no `type`, `projects` or `assignees`; `config.yml` with a boolean `blank_issues_enabled` and contact links with exactly `name`, `url` (https) and `about`.

   Result: `OK: 4 files, every check passed (bug-report.yml 7 fields, feature-or-improvement.yml 6 fields, question.yml 3 fields)`.

   The validator was checked against faults: on mutated copies it caught 9 of 9 injected faults (a missing `description`, an invalid element type, an `id` with a space, a duplicate form name, a misspelt `label` key, a string `blank_issues_enabled`, a contact link without `about`, a label not in the repository, a string `required`).
4. **No em or en dashes.** A byte-level search (`LC_ALL=C grep` for U+2013 and U+2014) finds 0 in every new file and in the lines added to `README.md` and `brand/LICENSE-BRAND.md`; the same search finds 2 in the engine's `.github/ISSUE_TEMPLATE/feature.md`, showing that it detects them.
5. **Links.** Every distinct absolute URL in the new files and in the added lines was fetched signed out with `curl` on 2026-10-16:
   - 14 answer 200, including the engine's Q&A, the four engine documents the guides link to, both organisation-wide label searches and the Creative Commons legal code.
   - 8 answer 404 today and **resolve only after merge**: this repository's `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`, `docs/implementations/_TEMPLATE.md`, `brand/README.md` and `brand/tools/build_brand.py` on `main` (the last two arrive with pull request #1), and `.github/discussions/categories/q-a`, which exists only once Discussions is on for this repository.
   - 2 redirect to GitHub's sign-in page, as expected: the two `security/advisories/new` forms need an account (and the form itself only once private vulnerability reporting is on).
   - 4 redirect permanently, all inside the copied Contributor Covenant text (three contributor-covenant.org pages and `mozilla/diversity`, now `mozilla/inclusion`); left as they are, to keep the copy exact.
   - 1 is not a link: the `<repository>` placeholder in `SECURITY.md`, inside a code span.
6. **Line endings.** The new files are committed with LF (`git ls-files --eol`), none with a byte order mark.

**Not tested:**
- How GitHub displays the defaults (the template chooser, the forms, the "contributing guidelines" link, the repository tabs). GitHub reads defaults only from the default branch, so this can be observed only after merge. Expected afterwards: the community profile of `.github` rises from 25% towards 87%, the Collective's ceiling while issue forms replace legacy templates; the engine and codesign rise once their descriptions and the defaults count.
- That GitHub itself accepts the forms: the validator encodes the documented schema, but GitHub's parser was not run. After merge, GitHub shows an error on a form's page if it rejects it.
- Submitting a form, a discussion or a private vulnerability report.

## Related Docs

- [`2026-10-16-licence.md`](2026-10-16-licence.md), [`2026-10-16-repository-presence.md`](2026-10-16-repository-presence.md)
- [`2026-10-16-superconducted-brand-system.md`](2026-10-16-superconducted-brand-system.md)
- The pattern this follows: `Cassandra-Collective/.github`, `docs/implementations/2026-10-14-community-health-files.md` and `2026-10-15-discussions-qa.md`
- The engine's conventions: [`docs/team.md`](https://github.com/SuperconducTED/superconducted-noise-engine/blob/main/docs/team.md), [`docs/decisions.md`](https://github.com/SuperconducTED/superconducted-noise-engine/blob/main/docs/decisions.md), [`docs/numerical-claims.md`](https://github.com/SuperconducTED/superconducted-noise-engine/blob/main/docs/numerical-claims.md)
- GitHub Docs: [Creating a default community health file](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file), [Configuring issue templates for your repository](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository), [Syntax for issue forms](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)

## As of 2026-10-16, later

Rebased unchanged onto `main` @ `68e40e7` as branch `docs/organisation-home`, which also moves
the brand kit and rewrites the READMEs (`2026-10-16-organisation-home.md`). The decision row
"Not naming superconducted-codesign in public files" is superseded: Mert dropped that rule on
2026-10-16.
