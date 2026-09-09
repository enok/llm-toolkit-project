---
name: jenkins-to-github-actions
description: Migrate CI/CD from Jenkins or Jenkinsfile pipelines to GitHub Actions workflows. Use when converting Jenkins stages, agents, triggers, parameters, credentials, artifacts, reports, shared libraries, deployment approvals, or rollback gates into `.github/workflows/*.yml`, or when the user asks how a Jenkins construct maps to Actions.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.0.0"
---

# Jenkins to GitHub Actions

## Goal

Move Jenkins CI/CD behavior to GitHub Actions without silently changing build,
test, artifact, deployment, approval, or credential semantics.

## Inputs

Collect only what is needed for the current migration slice:

- Jenkinsfile or job XML/config, including scripted-pipeline sections.
- Shared-library calls, plugin-dependent steps, shell scripts, build images, and
  tool versions.
- Branch/tag/path triggers, cron schedules, parameters, upstream/downstream job
  links, and manual approvals.
- Credentials, secret scopes, environment variables, service accounts, cloud
  roles, deployment environments, and runner/network requirements.
- Existing `.github/workflows/`, branch protection, required checks, release
  process, rollback process, and artifact/report consumers.

## Process

1. **Inventory behavior before translating syntax.** List triggers, stages,
   agent needs, tools, caches, env vars, secrets, artifacts, reports,
   notifications, deployments, approvals, and rollback gates.
2. **Classify gaps.** Mark each Jenkins feature as direct mapping, partial
   mapping, custom script/composite action, reusable workflow, self-hosted
   runner need, or manual redesign.
3. **Design the workflow shape.** Map long-lived Jenkins stages to Actions jobs
   when they need separate runners, permissions, parallelism, artifacts, or
   branch-protection checks. Keep simple sequential commands as steps in one job.
4. **Preserve security boundaries.** Use least-privilege `permissions`, scoped
   secrets, protected environments for approvals, and OIDC/cloud federation when
   practical. Do not move Jenkins credentials into workflow YAML or logs.
5. **Migrate in slices.** Prefer CI first, then artifacts/reports,
   non-production deploys, approval gates, production deploys, and finally
   Jenkins retirement.
6. **Validate parity.** Run Jenkins and Actions in parallel until the new checks
   produce equivalent results or documented intentional differences.

## Reference Loading

- Read `references/mapping.md` when converting Jenkinsfile constructs to
  workflow YAML.
- Read `references/security.md` when credentials, cloud deploys, forks,
  self-hosted runners, permissions, or third-party actions are involved.
- Read `references/validation.md` when planning rollout, parity checks,
  required-check changes, or Jenkins decommissioning.

## Related Toolkit Capabilities

- `skills/ci-migration-and-parity/SKILL.md` for the CI-system-agnostic parity
  method when the migration is not Jenkins-to-Actions specific.
- `workflows/gh-fix-ci.md` for debugging failing GitHub Actions checks after
  migration.
- `skills/ci-watcher/SKILL.md` for post-push CI monitoring on an open PR.
- `rules/ci-feedback-loop.md` for converting CI failures into future review
  guidance.
- `skills/shell-scripting/SKILL.md` for portable shell steps embedded in
  workflows.
- `skills/external-skill-intake/SKILL.md` for future external skill harvesting.

## Source Notes

This skill adapts patterns from official GitHub migration and Actions security
documentation (see `metadata.json` for the reference list). No external
executable code is vendored.
