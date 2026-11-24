---
title: App-level global instructions were not visible to a CLI session; copy the directive into the user-level instruction file
category: environment
created: 2026-11-24
tags: [global-instructions, cli, user-level, onboarding, spec-gap, directive]
---

# Problem
Global instructions set at the application level were not visible to a CLI session, so the session
missed the toolkit. It was found only when the directive was copied into the user-level instruction
file.

# Failed Approaches
- Relying on the app-level global instructions to reach the CLI session. They did not.

# Solution
Put the directive in the user-level instruction file that the CLI session reads. After the copy,
the toolkit was found. Related: `docs/global-install.md`.

# Why
The record shows the CLI session did not see the app-level instructions and did see the user-level
file. The record does not state why. Inference, not observed: the two surfaces load instruction
sources separately.
