---
title: Migration validation and rollout
tags: [ci, migration, parity, rollout, rollback]
---

# Migration Validation And Rollout

## Migration Phases

1. **Inventory:** document Jenkins behavior, owners, credentials, plugins, runner needs, artifacts, and required checks.
2. **Dry run:** create Actions workflows on a feature branch or behind `workflow_dispatch`.
3. **Parallel CI:** run Jenkins and Actions on the same commits while Jenkins remains authoritative.
4. **Parity review:** compare status, duration, artifacts, test reports, coverage, package versions, deployment outputs, and notifications.
5. **Protection switch:** update branch protection required checks only after the Actions check names are stable.
6. **Deploy rollout:** enable non-production deploys, then production with protected environments and rollback confirmation.
7. **Retirement:** disable Jenkins jobs only after owners accept parity and rollback instructions are documented.

## Parity Checklist

- Same source ref and event type are tested.
- Same build/test/deploy commands run, or differences are documented.
- Tool versions and runtime images are pinned or intentionally allowed to drift.
- Cache behavior does not hide missing setup steps.
- Artifacts have equivalent paths, names, retention, and consumers.
- Test reports and coverage are visible to the same reviewers or dashboards.
- Required checks have stable, meaningful names.
- Secrets are scoped to the smallest repo, environment, or organization audience.
- Deploy approvals, change windows, notifications, and rollback gates are preserved.

## Rollback Checklist

- Jenkins job remains available until Actions passes production deployment parity.
- Branch protection can be reverted to Jenkins check names.
- Deployment workflow can be disabled without deleting history.
- Rollback command, artifact, or release procedure is documented near the workflow or runbook.
- Owners know which system is authoritative at each phase.

## Failure Handling

- If Actions fails and Jenkins passes, inspect environment, tool version, path, shell, permission, cache, and secret differences before changing application code.
- If both fail, treat it as a product/build issue and use the normal review/fix/test workflow.
- If Actions passes and Jenkins fails, do not retire Jenkins until the team agrees the Jenkins failure is obsolete or unrelated.
