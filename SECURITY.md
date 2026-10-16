# Security policy

This policy covers every repository in the [SuperconducTED](https://github.com/SuperconducTED) organisation that does not have a `SECURITY.md` of its own. A repository's own policy takes precedence.

## Reporting a vulnerability

**Do not open a public issue, pull request, discussion or comment for a security problem.**

Report it privately, in either of two ways.

1. **GitHub's private vulnerability reporting** (preferred). It is enabled on the organisation's public repositories. Open the repository's **Security** tab and select **Report a vulnerability**, or go straight to the form:

   | Repository | Private report |
   |---|---|
   | superconducted-noise-engine | [Report a vulnerability](https://github.com/SuperconducTED/superconducted-noise-engine/security/advisories/new) |
   | `.github` (profile, brand and community files) | [Report a vulnerability](https://github.com/SuperconducTED/.github/security/advisories/new) |

   For any other public repository, the form is at `https://github.com/SuperconducTED/<repository>/security/advisories/new`. You need a GitHub account to use it. GitHub does not offer this form on private repositories: use email for those.

2. **Email** to **sensoymertefe@gmail.com**, with `SECURITY` in the subject line.

## What to include

- The repository, and the commit, branch or release you looked at.
- What the problem is and where it is: file, function, workflow or configuration.
- Steps to reproduce it, or a proof of concept.
- What you think the impact is: who could do what, and under which conditions.
- Whether anyone else knows about it, and whether you plan to publish it, and when.

Describe secrets and personal data rather than pasting them. If you found a live token or key (for example an IBM Quantum API token), say where it is; do not use it.

## What to expect

SuperconducTED is a small research group run by university students. There is no security team and no guaranteed response time. What we aim for:

- A person reads every report and replies. We aim to acknowledge a report within a few days; it can take longer, especially during exams and holidays.
- We tell you whether we could reproduce the problem, and keep you informed while it is fixed.
- When a fix is ready, we publish a GitHub security advisory where it is warranted, crediting you unless you would rather stay anonymous.

## Scope

In scope: the code, configuration, workflows and published files of the organisation's repositories. For example:

- a secret, token or key committed to a repository or its history, such as an IBM Quantum token;
- code that loads, imports or executes an untrusted file or network input in an unsafe way, such as a calibration snapshot or a stored dataset;
- a GitHub Actions workflow that an outside pull request or issue can abuse, for example to read the secrets a scheduled workflow uses;
- a dependency vulnerability that our code actually makes reachable.

Out of scope:

- Vulnerabilities in third-party software or services themselves (for example Qiskit, Qiskit Aer or the IBM Quantum platform). Report those to their maintainers, and tell us if our use of them makes the problem worse.
- How well the engine's noise models or intervals predict real hardware. A wrong or misleading result is a research finding or a bug: open an ordinary issue. It is a security problem only if it exposes private data or lets someone run code or reach systems they should not.
- Problems that need an attacker who already controls your machine or your account.

## Supported versions

The projects are research software in preview. Security fixes go to each repository's default branch (`main`) only, unless that repository's own policy says otherwise.

## Disclosure

Please give us a reasonable time to ship a fix before you publish anything. We coordinate disclosure through GitHub security advisories.
