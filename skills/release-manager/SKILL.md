---
name: release-manager
description: >
    Cut, verify, and manage releases with structured rollout and rollback planning. Trigger
    when the user asks to cut a release, verify a release candidate, plan a rollout, manage
    hotfix releases, or coordinate multi-service deployments.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Release Manager

Use this skill for structured release cutting, verification, and rollout management.

## When to Apply

- Cutting a new release or release candidate
- Verifying a release before production deployment
- Planning rollout strategy (phased, canary, blue-green)
- Managing hotfix releases
- Coordinating multi-service or multi-repo deployments

## Workflow

1. **Identify the release scope:**
   - changed services, packages, or modules
   - migration or schema changes
   - config or secrets changes
   - backward-compatibility risks
2. **Define the deploy order explicitly** across repos and services when multiple are involved.
3. **Define verification before rollout begins:**
   - smoke tests
   - integration checks
   - key user workflows
   - monitoring dashboards and alerts
4. **Define rollback before production action begins:**
   - rollback commands or automation
   - data migration reversal (if applicable)
   - communication plan for rollback
5. **Execute the rollout:**
   - follow the defined deploy order
   - verify at each stage before proceeding
   - monitor key metrics during and after
6. **Post-release:**
   - confirm all verification checks pass
   - update release notes and changelogs
   - notify stakeholders

## Output

Return:
- release scope and changelog
- deploy order
- verification plan
- rollback plan
- post-release checklist

## Non-Goals

- Do not deploy without explicit approval.
- Do not skip verification steps to save time.
- Do not treat multi-repo/multi-service releases as single-repo changes.

## Related Skills

- **e2e-release-verification** — Targeted E2E verification for the release
- **runbook-authoring** — Document the release process as a runbook
- **incident-ops** — If the release causes an incident
- **ci-watcher** — Monitor CI for the release branch
- **maven-release** — Maven-specific release mechanics (release plugin, tags, rollback)

## Related Rules and Workflows

- `rules/release-safety.md` — no production action without verification and rollback defined
- `workflows/ticket-release.md` — ticket-scoped release flow
