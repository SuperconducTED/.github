# Getting help

This guide covers every repository in the [SuperconducTED](https://github.com/SuperconducTED) organisation that does not have a `SUPPORT.md` of its own.

## Where to ask

Ask in the **Discussions** of the repository your question is about, in its **Q&A** category. There an answer can be marked as the answer, and the next person with the same question finds it:

| Project | Ask a question | Questions tracked as issues |
|---|---|---|
| superconducted-noise-engine | [Discussions, Q&A](https://github.com/SuperconducTED/superconducted-noise-engine/discussions/categories/q-a) | [`question` issues](https://github.com/SuperconducTED/superconducted-noise-engine/issues?q=is%3Aissue+label%3Aquestion) |
| `.github` (profile, brand and community files) | [Discussions, Q&A](https://github.com/SuperconducTED/.github/discussions/categories/q-a) | [`question` issues](https://github.com/SuperconducTED/.github/issues?q=is%3Aissue+label%3Aquestion) |

When a question turns out to need work (a bug, a missing document), a maintainer turns it into an issue. If you want a question tracked as an issue from the start, use the repository's **Question** form on its new-issue page, where it has one; the form adds the `question` label for you.

If your question is about the organisation as a whole, or about the brand, ask it in the `.github` repository.

## Before you ask

- Read the repository's README and its `docs/` folder, if it has one. For the noise engine, [`docs/architecture.md`](https://github.com/SuperconducTED/superconducted-noise-engine/blob/main/docs/architecture.md) and the decision ledger, [`docs/decisions.md`](https://github.com/SuperconducTED/superconducted-noise-engine/blob/main/docs/decisions.md), answer many design questions.
- Search the repository's issues and discussions, open and closed. Your question may already have an answer.

## What to include

- What you are trying to do, not only the step that failed.
- What you tried: the exact commands, and their output as text rather than a screenshot.
- The commit or version, your operating system, your Python version and the versions of the key libraries (for the engine: `qiskit`, `qiskit-aer`, `numpy`, `scipy`).
- For a question about calibration data or a simulation: the IBM backend and the snapshot (or its date) you used.
- What you have already read, so the answer can start from there.

## What not to ask in public

- **Security problems:** follow the [security policy](https://github.com/SuperconducTED/.github/blob/main/SECURITY.md) instead.
- **Conduct concerns:** contact the address in the [code of conduct](https://github.com/SuperconducTED/.github/blob/main/CODE_OF_CONDUCT.md).
- **Secrets:** never post a token, key or password, even an expired one. This includes your IBM Quantum token and the contents of your `.env` file.

## What to expect

There is no paid support, no support contract and no guaranteed response time. The projects are maintained by university students, who answer when they can. A question that shows what you tried is usually answered sooner.

If an answer shows that the documentation was unclear, we treat that as a documentation bug and fix it.
