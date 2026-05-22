---
description: Upgrade dependencies with compatibility, security, and validation in mind
---

# Dependency upgrade workflow

Use when upgrading libraries, SDKs, runtimes, or build tooling.

## Steps

1. Identify what is changing: direct dependency, transitive issue, runtime, or shared platform package.
2. Read release notes, changelogs, and local usage patterns before editing.
3. Split impact analysis across backend, frontend, infrastructure, and docs when the change spans multiple surfaces.
4. Apply the smallest safe upgrade.
5. Run targeted validations first, then broaden if shared code or runtime behavior changed.
6. Record breaking changes, migration notes, and follow-up work.

See `rules/e2e-scoped-coverage.md` when UI or E2E behavior may shift.

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
