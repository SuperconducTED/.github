# Contributing to SuperconducTED

Thank you for your interest. This is the organisation's general guide. GitHub shows it in every repository of the organisation that has no `CONTRIBUTING.md` of its own.

**A project's own `CONTRIBUTING.md` and documented conventions set its specific rules and take precedence over this guide.** Read them first when the project has them.

## The organisation

SuperconducTED is a student research group from TED University, Ankara. We study the noise of superconducting quantum computers and build open tools to model it: noise as a range, not a number. ([Organisation profile](https://github.com/SuperconducTED))

| Repository | What it is |
|---|---|
| [superconducted-noise-engine](https://github.com/SuperconducTED/superconducted-noise-engine) | A fuzzy-logic noise engine for Qiskit Aer-based quantum computer emulators. It reads IBM calibration snapshots and aims to produce interval-valued simulation output that tracks the hardware across calibration cycles. Research preview. |
| [`.github`](https://github.com/SuperconducTED/.github) | The organisation's profile, its brand and these shared community files. |

## What we value

- **Claims are tested honestly.** A claim comes with its evidence: the command, its output, the test, the measurement. Say what was tested, on what, and what was not.
- **Every number has a source.** A number in a public document traces to a paper, a file, a committed script or a procedure someone else can rerun. The noise engine keeps these in its [numerical claims register](https://github.com/SuperconducTED/superconducted-noise-engine/blob/main/docs/numerical-claims.md).
- **Decisions are written down.** Design decisions are recorded with their context and consequences before the code depends on them, as in the engine's [decision ledger](https://github.com/SuperconducTED/superconducted-noise-engine/blob/main/docs/decisions.md).
- **Documentation changes with the code.** If a change makes a document wrong, the same pull request fixes the document.

Everyone taking part follows the [code of conduct](https://github.com/SuperconducTED/.github/blob/main/CODE_OF_CONDUCT.md).

## How to start

1. Read the project's README and, if it has them, its own `CONTRIBUTING.md` and `docs/` folder.
2. Find an issue. Every project keeps its backlog as GitHub issues. Good places to begin:
   - [`good first issue`](https://github.com/search?q=org%3ASuperconducTED+label%3A%22good+first+issue%22+state%3Aopen&type=issues): small, well-described tasks for newcomers;
   - [`help wanted`](https://github.com/search?q=org%3ASuperconducTED+label%3A%22help+wanted%22+state%3Aopen&type=issues): tasks where help is especially welcome.

   If both lists are empty, ask what would help most, in the repository's Discussions or with its Question form.
3. Comment on the issue to say you would like to take it, and wait for a maintainer to confirm, so that two people do not do the same work.

Questions are welcome: ask in the repository's Discussions, in its Q&A category, where it has them, and see [getting help](https://github.com/SuperconducTED/.github/blob/main/SUPPORT.md).

## How a change gets in

1. **Issue first.** For anything beyond a typo or a broken link, open an issue (or use an existing one) before writing code, so the approach can be agreed before the work is done. Use the repository's issue forms or templates.
2. **Branch.** Fork the repository, or branch from `main` if you have write access. Name the branch after the kind of change, for example `docs/fix-install-steps` or `fix/42-snapshot-loading`; a project's own guide may set a stricter pattern.
3. **Keep it focused.** One change per pull request.
4. **Open a pull request** that references the issue (`Closes #42`) and fill in the template.
5. **Show the evidence** in the pull request: the commands you ran and their output, test results, or before and after screenshots. Say what you did not test.
6. **Update the docs** that the change affects, in the same pull request.
7. **Review and merge.** A maintainer reviews the pull request. In the noise engine, the reviewers are the module owners listed in its [`docs/team.md`](https://github.com/SuperconducTED/superconducted-noise-engine/blob/main/docs/team.md). Merging is the maintainers' decision.

## Reporting security problems

Never report a vulnerability in a public issue. Follow the [security policy](https://github.com/SuperconducTED/.github/blob/main/SECURITY.md).

## Contributing to this repository (`.github`)

- **Brand changes are made in [`brand/tools/build_brand.py`](https://github.com/SuperconducTED/.github/blob/main/brand/tools/build_brand.py) and its sibling scripts, never by editing the exported files in `brand/kit/`.** Rebuild and check as [`brand/README.md`](https://github.com/SuperconducTED/.github/blob/main/brand/README.md) describes under "Rebuilding"; `check_brand.py` must report no problems.
- **The community files here are defaults for the whole organisation.** A change to `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md` or the templates in `.github/` reaches every repository that has no file of its own, so open an issue first.
- **Every meaningful change has an implementation document,** `docs/implementations/YYYY-MM-DD-<slug>.md`, copied from [`docs/implementations/_TEMPLATE.md`](https://github.com/SuperconducTED/.github/blob/main/docs/implementations/_TEMPLATE.md).
- **Prose style:** plain English, and no em or en dashes; use a comma, a colon, a middle dot or a new sentence.
- **Licence:** you contribute under the terms of the part you change. Code and text are under the MIT License (`LICENSE`); the brand files are under CC BY 4.0 (`brand/LICENSE-BRAND.md`). `NOTICE` says which part is which and lists the exceptions.
