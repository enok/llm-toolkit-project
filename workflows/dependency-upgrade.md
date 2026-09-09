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
5. For security-driven bumps, verify the vulnerable path is actually removed or justified: dependency tree, lockfile, override/resolution, parent POM, or generated client output as applicable.
6. For runtime or framework jumps, check language/runtime compatibility before trusting compile success (for example Java release level, Spring/Boot generation, Node/browser support, or deprecated APIs). For legacy Java/Maven webapps, use `skills/maven-build-troubleshooting/references/legacy-java-webapp-runtime.md`; for JDK 17 migration diagnostics, also use `skills/maven-build-troubleshooting/references/jdk17-legacy-migration.md`.
7. Run targeted validations first, then broaden if shared code or runtime behavior changed.
8. Record breaking changes, migration notes, and follow-up work.

When UI or E2E behavior may shift, include the affected E2E paths in the targeted validation plan before broadening to full suites.

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
