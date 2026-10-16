# SuperconducTED brand foundation

> **Status: draft, 2026-10-16.** The story is approved by the owner. Everything else here is a
> draft built from what the repositories already say (the engine's README, the organisation
> profile, `docs/team.md`) and waits for the owner: he picks the tagline, and the organisation
> profile fields at the end are applied to GitHub only on his word.

## 1. The story

> Qiskit can describe an IBM quantum computer in one line, `NoiseModel.from_backend`. It reads
> the machine's latest calibration and freezes it into one noise model. The machine does not
> stay frozen: its chip hangs at the bottom of a dilution refrigerator, about a hundredth of a
> degree above absolute zero, and its noise still drifts from one calibration to the next.
> SuperconducTED keeps every calibration and answers with the range the machine actually moves
> through: not one crisp number, but an interval that brackets the real hardware.

This is the project's real origin, in the owner's words: `from_backend` froze a machine that
keeps moving. Every part of the identity points back to it: the mark draws the machine, the
frozen snapshot, the drift and the range; the one colour rule gives the range its own colour.

## 2. What we say we are

**One-line descriptor** (the engine's README, unchanged): *Fuzzy-logic noise engine for Qiskit
Aer-based quantum computer emulators.*

**For the organisation:** *Student research at TED University on honest noise models for
superconducting quantum computers.*

**Positioning** (draft):

> For researchers and students who simulate IBM's superconducting quantum computers with
> Qiskit Aer, SuperconducTED is an open-source noise engine that treats a machine's noise as a
> range, not a single number. A noise model built from one calibration describes the machine
> on the day it was calibrated; ours keeps every calibration and aims to bracket the real
> hardware across them.

**A rule for every claim:** until the results phase reports, the bracketing is the research
*aim* (the README's word), not a result. Say "aims to bracket", "is designed to", "the research
aim is"; never "brackets real hardware" as a finding. Every number in public text traces to a
source or to the numerical-claims register of the repository it appears in.

## 3. Who it is for

| Audience | What they need from us |
| --- | --- |
| The team, the advisor, thesis committees | A shared, stable identity for reports, theses and reviews. |
| Quantum computing researchers and students using Qiskit Aer | A clear statement of what the engine does differently, and figures they can read at a glance. |
| The IBM Quantum and Qiskit community | Accurate credit for the tools we build on, and no implied affiliation. |
| Visitors to the GitHub organisation | Who we are, in one look at the avatar, the banner and the description. |

## 4. Character

Taken from how the team already works (the ADR ledger, the numerical-claims register, the
audits, the lab-log field notes), not invented:

- **Honest about uncertainty.** The engine's whole point is to report what we do not know.
  The brand does the same: ranges over false precision, "aims to" over "does".
- **Measured.** Numbers come with their source. If it was not measured, it is not stated.
- **Open.** MIT-licensed code, a public calibration archive, public decisions.
- **Precise and plain.** Technical words where they are the right words, plain English
  everywhere else.
- **Collegial.** Credit to IBM, Qiskit, the people whose work we build on, and each other.

## 5. Tagline shortlist (the owner picks one)

| # | Tagline | Why it fits |
| --- | --- | --- |
| 1 | **Noise as a range, not a number.** | The engine's thesis in seven words; pairs with the one colour rule (the accent is the range). |
| 2 | **The machine drifts. We give the range.** | The story in two beats: the problem, then our answer. |
| 3 | **Every calibration, not just the last.** | The method: we keep the whole archive where `from_backend` keeps one snapshot. |

How to set it: Space Grotesk Regular, sentence case, with its full stop; never inside a
lockup; at least the clear space away from the logo.

## 6. Boilerplate

**Short** (about 40 words, for posters, slides and author bios):

> SuperconducTED is a student research group at TED University, Ankara. Its open-source noise
> engine for Qiskit Aer turns the drift between IBM calibrations into interval-valued noise
> models, so simulations report a range instead of a single number.

**Long** (about 90 words, for papers, applications and the organisation profile):

> SuperconducTED is a student research group at TED University, Ankara, working on noise
> models for superconducting quantum computers. Qiskit Aer builds a noise model from one
> calibration of a machine, but real hardware drifts between calibrations. The group's
> open-source engine archives IBM calibration snapshots and passes them through a
> Takagi-Sugeno-Kang fuzzy inference layer that produces an ensemble of noise models, whose
> simulations give an interval rather than a single prediction. The research aim is an interval
> that brackets the real hardware across calibration cycles. The engine's code, calibration
> archive and design decisions are public.

## 7. Naming rules

- **SuperconducTED**: capital S, then lowercase, then capital TED. Never "Superconducted",
  "SuperConducTED" or "Super-conducTED" in running text. All capitals (SUPERCONDUCTED) only as
  display lettering drawn into a mark or a seal.
- **The flagship:** "the SuperconducTED noise engine" in prose; the repository is
  `superconducted-noise-engine`, the Python package `superconducted`, the poller command
  `superconducted-poll`, always lowercase in code.
- **TED:** the TED in SuperconducTED is TED University in Ankara, where the team studies; TED is
  Türk Eğitim Derneği (the Turkish Education Association). Say this in one line when a reader
  needs it, and never use the TED or TED University emblem or colours without the owner's and
  the university's approval.
- **IBM, Qiskit, Qiskit Aer:** named exactly so, credited as the tools and hardware we build on.
  Never imply that IBM or the Qiskit project endorses SuperconducTED.

## 8. Voice and tone

| Do | Don't |
| --- | --- |
| "The engine aims to bracket the hardware across calibrations." | "The engine predicts hardware perfectly." |
| "T1 drifted by up to X over N cycles (source: ...)" | Unsourced numbers, or round numbers that were never measured. |
| Plain verbs: builds, keeps, measures, reports. | Hype: revolutionary, next-generation, unlock, game-changing. |
| Code names in backticks: `NoiseModel.from_backend`. | Code names in prose fonts, or paraphrased API names. |
| Commas, colons, semicolons, middle dots ( · ). | Em dashes or en dashes. |
| English for everything public; Turkish, with a collapsed English summary, for team messages. | Mixing the two in one public document. |

Tone shifts with the reader, the voice does not: a README is direct and practical, a paper is
formal, a team message is warm, and all of them say what is known and what is not.

## 9. Drafts for the GitHub organisation profile

The organisation's profile fields are blank today. Proposed values, **to be applied only on
the owner's word** (a settings change):

| Field | Draft |
| --- | --- |
| Display name | SuperconducTED |
| Description (160 characters at most) | Student research at TED University: interval-valued noise models for IBM's superconducting quantum computers, built on Qiskit Aer. |
| Location | Ankara, Türkiye |
| Website | (none yet; leave blank rather than point at a placeholder) |
| Avatar | the chosen mark's avatar file from the brand kit, after the team's pick |

## 10. Endorsement and credit

SuperconducTED is an independent student project. The name and mark identify it and imply no
endorsement by IBM, by the Qiskit project, by TED (Türk Eğitim Derneği) or TED University, or
by anyone named in our story or our sources. IBM, Qiskit and other names are used only to
describe the tools and hardware the project works with.
