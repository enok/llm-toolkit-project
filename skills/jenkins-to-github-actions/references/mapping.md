---
title: Jenkins to GitHub Actions construct mapping
tags: [ci, jenkins, github-actions, migration, yaml]
---

# Jenkins to GitHub Actions Mapping

Use this as a checklist, not as a blind syntax converter. Preserve behavior first.

## Pipeline Structure

| Jenkins | GitHub Actions | Notes |
| --- | --- | --- |
| Declarative `pipeline` | workflow YAML file | One Jenkinsfile can become one or more workflows if CI and deploy lifecycles differ. |
| `stage` | job or step group | Use jobs for independent runners, permissions, parallelism, artifacts, or required checks. Use steps for simple sequence. |
| `steps` | `jobs.<job_id>.steps` | Keep existing scripts checked in where possible instead of rewriting large shell blocks in YAML. |
| `agent any` | `runs-on: ubuntu-latest` or repo standard | Confirm OS/tool parity before defaulting to GitHub-hosted runners. |
| `agent { label 'x' }` | `runs-on: [self-hosted, x]` | Use self-hosted labels when Jenkins depended on private network, custom hardware, or licensed tools. |
| `agent { docker { image 'x' } }` | job `container:` or Docker action | Confirm volume, user, shell, and network assumptions. |
| `tools` | setup actions or preinstalled runner tools | Pin tool versions and check runner images for drift. |
| `environment` | workflow/job/step `env`, variables, or secrets | Do not put secrets in plain `env`. |
| `credentials()` | GitHub secrets, environment secrets, OIDC, or deploy keys | Prefer federated auth for cloud deploys; scope secrets to repo, org, or environment intentionally. |
| `parameters` | `workflow_dispatch.inputs` or reusable workflow inputs | Keep default values and allowed choices explicit. |
| `when` | job/step `if:` | Use event, branch, path, tag, or input context deliberately. |
| `post { always/success/failure }` | steps with `if: always()`, `success()`, or `failure()` | Keep cleanup and notification behavior even when earlier steps fail. |
| `options { timeout(...) }` | `timeout-minutes` | Apply at job level unless a specific command needs its own timeout wrapper. |
| `retry` | action-native retry or bounded shell retry | Do not retry destructive deploy steps unless idempotency is proven. |
| `parallel` | independent jobs or `strategy.matrix` | Use `needs` only where ordering is required. |
| Jenkins matrix axes | `strategy.matrix` | Preserve exclusions, fail-fast behavior, and max parallelism where relevant. |
| `archiveArtifacts` | `actions/upload-artifact` | Preserve names, retention, paths, and downstream consumers. |
| `stash` / `unstash` | upload/download artifacts or cache | Artifacts move build outputs; cache restores dependencies. Do not mix them casually. |
| `junit` | test reporter action or uploaded XML | Keep report paths stable for code owners and trend tools. |
| `input` approval | protected GitHub environment or manual dispatch input | Use environment required reviewers for deployment gates. |
| cron trigger | `on.schedule` | GitHub cron uses UTC and does not support Jenkins `H` hashing. |
| multibranch pipeline | `on.push`, `on.pull_request`, branch filters | Recreate branch/tag/path filters and required check names. |
| upstream/downstream jobs | `needs`, `workflow_run`, `repository_dispatch`, or reusable workflows | Prefer explicit `needs` inside one workflow when jobs are in the same repo. |
| shared library | checked-in scripts, composite action, or reusable workflow | Avoid copying opaque Groovy logic into inline YAML. |

## Translation Heuristics

- Start with one workflow per lifecycle: CI, release, deploy, or scheduled maintenance.
- Keep language build commands in repo scripts (`mvn`, `npm`, `gradle`, `make`) so Jenkins and Actions can run the same command during parity.
- Split deploy jobs by environment when they need different secrets, reviewers, cloud roles, or rollback gates.
- Name jobs for stable branch-protection checks; changing names later breaks required checks.
- Use `concurrency` for deploys or long-running branch checks that must not overlap.
- Prefer reusable workflows for organization-standard CI/deploy patterns; prefer composite actions for repeated step sequences.
