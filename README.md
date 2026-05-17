<!--
  SuperconducTED · organization profile README
  Path: .github/profile/README.md  (inside a repo named ".github" at the org level)
  Style: no em/en dashes; middle dots and colons only.
-->

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://capsule-render.vercel.app/api?type=waving&color=0:0b0d17,50:1e1b4b,100:06b6d4&height=210&section=header&text=SuperconducTED&fontSize=72&fontColor=ffffff&fontAlignY=38&desc=The%20TED%20in%20superconducted%20%C2%B7%20TED%20University%20%C2%B7%20Ankara&descAlign=50&descAlignY=62&descSize=16&animation=fadeIn">
  <img alt="SuperconducTED" src="https://capsule-render.vercel.app/api?type=waving&color=0:0b0d17,50:1e1b4b,100:06b6d4&height=210&section=header&text=SuperconducTED&fontSize=72&fontColor=ffffff&fontAlignY=38&desc=The%20TED%20in%20superconducted%20%C2%B7%20TED%20University%20%C2%B7%20Ankara&descAlign=50&descAlignY=62&descSize=16&animation=fadeIn">
</picture>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=500&size=17&duration=3200&pause=900&color=06B6D4&center=true&vCenter=true&width=760&lines=Fuzzy+logic+%C2%B7+quantum+noise+%C2%B7+Qiskit+Aer;Research+preview+%C2%B7+TED+University+%C2%B7+Ankara;Bracketing+IBM+hardware+across+calibration+cycles" alt="tagline" />
</p>

<p align="center">
  <a href="https://github.com/SuperconducTED/superconducted-noise-engine"><img src="https://img.shields.io/badge/flagship-superconducted--noise--engine-7f5af0?style=for-the-badge" alt="flagship"></a>
  <img src="https://img.shields.io/badge/status-research%20preview-f59e0b?style=for-the-badge" alt="status">
  <img src="https://img.shields.io/badge/license-MIT-10b981?style=for-the-badge" alt="license">
  <img src="https://img.shields.io/badge/python-3.11%20%7C%203.12-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="python">
</p>

<p align="center">
  <a href="https://github.com/SuperconducTED"><img src="https://img.shields.io/badge/Ankara%20%C2%B7%20TR-Computer%20Engineering%20%40%20TEDU-0b0d17?style=flat-square" alt="location"></a>
  <img src="https://img.shields.io/badge/Qiskit%20Aer-noise%20modeling-6929C4?style=flat-square&logo=qiskit&logoColor=white" alt="qiskit-aer">
  <img src="https://img.shields.io/badge/IT2%20fuzzy-Takagi%C2%B7Sugeno%C2%B7Kang-1e1b4b?style=flat-square" alt="it2-tsk">
</p>

---

## ❯ Manifesto

Qiskit Aer accepts **crisp** numbers for noise. Real superconducting qubits drift between every IBM calibration. We close the gap with a Takagi·Sugeno·Kang fuzzy inference layer that turns calibration snapshots into an *ensemble* of `NoiseModel` instances, then aggregates simulations into **interval-valued** predictions that bracket real hardware across calibration cycles.

If `0.686%` fidelity deviation on a single snapshot is the bar (Bautra et al., 2026), **transferability across snapshots** is the rope we're trying to climb past it.

## ❯ The pipeline

```mermaid
flowchart LR
    A[IBM<br/>Calibration<br/>Snapshot] --> B[Feature<br/>Extraction]
    B --> C[Fuzzification<br/>+ TSK Rules]
    C --> D[Defuzzification]
    D --> E[Squashing]
    E --> F[Channel<br/>Projection]
    F --> G[Aer<br/>NoiseModel<br/>Ensemble]
    G --> H((Interval<br/>Prediction))

    classDef stage fill:#1e1b4b,stroke:#06b6d4,stroke-width:1px,color:#fff;
    classDef io fill:#0b0d17,stroke:#7f5af0,stroke-width:1.5px,color:#fff;
    class A,H io;
    class B,C,D,E,F,G stage;
```

<sub>Six stages, one Factory · Ensemble at the seam with Aer. The no-per-shot-Python-hook constraint is respected by realising epistemic uncertainty at <i>ensemble construction time</i>, not at simulation time.</sub>

Architecture detail: [`docs/architecture.md`](https://github.com/SuperconducTED/superconducted-noise-engine/blob/main/docs/architecture.md) · Decision ledger (ADRs): [`docs/decisions.md`](https://github.com/SuperconducTED/superconducted-noise-engine/blob/main/docs/decisions.md)

## ❯ Stack

<p align="center">
  <img src="https://img.shields.io/badge/Qiskit-6929C4?style=flat-square&logo=qiskit&logoColor=white" alt="qiskit">
  <img src="https://img.shields.io/badge/Aer-1e1b4b?style=flat-square" alt="aer">
  <img src="https://img.shields.io/badge/IBM%20Quantum-052FAD?style=flat-square&logo=ibm&logoColor=white" alt="ibm-quantum">
  <img src="https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy&logoColor=white" alt="numpy">
  <img src="https://img.shields.io/badge/SciPy-8CAAE6?style=flat-square&logo=scipy&logoColor=white" alt="scipy">
  <img src="https://img.shields.io/badge/scikit--fuzzy-3776AB?style=flat-square" alt="scikit-fuzzy">
  <img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white" alt="pytorch">
  <img src="https://img.shields.io/badge/pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white" alt="pytest">
  <img src="https://img.shields.io/badge/GitHub%20Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white" alt="actions">
</p>

## ❯ Repositories

<p>
  <a href="https://github.com/SuperconducTED/superconducted-noise-engine">
    <img src="https://github-readme-stats.vercel.app/api/pin/?username=SuperconducTED&repo=superconducted-noise-engine&theme=tokyonight&hide_border=true&bg_color=0b0d17&title_color=06b6d4&icon_color=7f5af0" alt="superconducted-noise-engine" />
  </a>
</p>

## ❯ Roadmap

<table>
  <thead>
    <tr>
      <th width="80">Phase</th>
      <th width="260">Milestone</th>
      <th>Status</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center"><b>0</b></td>
      <td>Calibration polling pipeline</td>
      <td><img src="https://img.shields.io/badge/shipped-10b981?style=flat-square" alt="shipped"> <code>superconducted-poll</code> · cron · idempotent</td>
    </tr>
    <tr>
      <td align="center"><b>1</b></td>
      <td>≥ 630 snapshot dataset</td>
      <td><img src="https://img.shields.io/badge/accumulating-f59e0b?style=flat-square" alt="accumulating"> ANFIS training prerequisite</td>
    </tr>
    <tr>
      <td align="center"><b>2</b></td>
      <td>TSK rule base · fuzzy uncertainty envelope</td>
      <td><img src="https://img.shields.io/badge/in%20design-3b82f6?style=flat-square" alt="in-design"></td>
    </tr>
    <tr>
      <td align="center"><b>3</b></td>
      <td>Whitepaper · benchmark vs. Bautra 2026</td>
      <td><img src="https://img.shields.io/badge/planned-64748b?style=flat-square" alt="planned"></td>
    </tr>
  </tbody>
</table>

## ❯ Now shipping

> Phase 0 deliverable is live. `superconducted-poll` archives IBM backend calibration snapshots on a cron, building the historical record needed for fuzzy training. Phase 1 is dataset accumulation: every four hours, another data point.

<details>
  <summary><b>❯ Quick start</b> · clone, install, test</summary>

  ```bash
  git clone https://github.com/SuperconducTED/superconducted-noise-engine.git
  cd superconducted-noise-engine
  python -m venv .venv
  # Windows:  .venv\Scripts\activate
  # POSIX:    source .venv/bin/activate
  pip install -r requirements.txt -r requirements-dev.txt
  pip install -e . --no-deps
  pytest
  ```

  Then drop your IBM Quantum token into `.env` (template at `.env.example`) and run `superconducted-poll --backend ibm_fez`.
</details>

<details>
  <summary><b>❯ Why fuzzy, why now</b></summary>
  <br>
  <p>Aer's noise model is a single point in parameter space. Real backends move. The literature reports excellent fidelity on the snapshot it was tuned on, then degrades silently when calibration shifts. Interval Type·2 fuzzy systems let us encode <i>epistemic</i> uncertainty (we don't know exactly where the backend is right now) on top of the <i>aleatoric</i> noise Aer already handles. Ensemble construction respects Aer's no-per-shot-Python-hook constraint. It's the kind of fit that only looks obvious once you stop trying to make a single number do two jobs.</p>
</details>

<details>
  <summary><b>❯ The lab</b> · five contributors + faculty advisor</summary>
  <br>
  <p>The lab is part of the Computer Engineering program at TED University, Ankara. Module ownership and the contributor roster live in <a href="https://github.com/SuperconducTED/superconducted-noise-engine/blob/main/docs/team.md"><code>docs/team.md</code></a>.</p>
</details>

<details>
  <summary><b>❯ Contributing</b></summary>
  <br>
  <ul>
    <li>Open issues live on the <a href="https://github.com/SuperconducTED/superconducted-noise-engine/issues">flagship repo</a>.</li>
    <li>Run <code>pytest</code> before pushing. CI mirrors local.</li>
    <li>Architectural changes go through an ADR in <code>docs/decisions.md</code>.</li>
    <li>Never commit a real <code>IBM_QUANTUM_TOKEN</code>. <code>.env</code> is gitignored; <code>.env.example</code> is the template.</li>
  </ul>
</details>

---

<p align="center">
  <sub>Made in Ankara · powered by curiosity, caffeine, and Cooper pairs.</sub>
</p>

<picture>
  <img alt="" src="https://capsule-render.vercel.app/api?type=waving&color=0:06b6d4,50:1e1b4b,100:0b0d17&height=100&section=footer&animation=fadeIn">
</picture>
