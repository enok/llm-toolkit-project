---
title: Consumer stack inventory - shared modules and environment roots
tags: [terraform, opentofu, modules, environments, state, backend, inventory, review]
---

# Consumer Stack Inventory: Shared Modules and Environment Roots

Every organization lays out its Terraform differently: which repos hold shared
modules, how consumers pin them, whether each environment is a repo or a
folder, how state is keyed, which account each environment lives in, and where
alarms and dashboards are wired. The specialist cannot judge a plan, a
`source` line, or a missing root without first establishing that layout.

This reference defines WHAT must be established and the review duties that
follow from it. The filled-in inventory is consumer context and lives in the
consumer repo's `docs/llm/` (for example
`docs/llm/terraform-stack-inventory.md`), never in the toolkit. All names
below are placeholders.

## 1. Shared-module repositories

Establish, per shared-module repo the consumer depends on:

- **Identity and layout**: repo (`<org>/<shared-modules-repo>`), module path
  convention (flat `modules/<name>` or namespaced `modules/<cloud>/<name>`),
  and whether it is active, frozen, or retired. A retired repo whose
  references are still valid is not a defect; a repo declared active
  supersedes any earlier retirement note.
- **Consumption source syntax**, exactly as consumers write it, for example
  `git::ssh://git@github.com/<org>/<shared-modules-repo>.git//modules/<name>?ref=vX.Y.Z`
  or `git@github.com:<org>/<shared-modules-repo>.git//modules/<name>`.
- **Pinning convention per repo**: tag-pinned (`?ref=vX.Y.Z`), SHA-pinned, or
  default-branch tracking (no `?ref=`). The convention decides the review
  outcome: where tag-pinning is the convention, an unpinned consumer is a
  finding; where default-branch tracking is the documented convention, a pin
  is optional hardening to recommend, never a blocker.
- **Module inventory by resource class**: which classes have a module
  (network, compute, IAM, storage, serverless, messaging, observability,
  deployment), which classes have none (raw resource blocks are then
  expected, not promotion debt), and which modules exist only in an app repo
  pending promotion into the shared repo (record the promotion branch/PR so
  input renames during promotion can be flagged).
- **Module conventions**: internal name composition (typically
  `<org>-<type>-<environment>-<purpose>` with a `coalesce()` full-name
  override defaulting to `null`), required tag-contract variables (for
  example a required `common_tags` map with keys such as
  `managed_by`/`service`/`environment`), `required_providers` pinned in a
  `versions.tf` (or deliberately absent for render-only helper modules), and
  `configuration_aliases` (a module declaring `aws.iam` validates only from a
  calling root).
- **Canonical copies**: when two repos ship a same-purpose module (for
  example a single-alarm wrapper ported from one repo to another), record
  which copy is canonical, whether the internal resource address is identical
  (consumers then repoint without `moved` blocks), and which consumers still
  point at the non-canonical copy.

## 2. Environment roots

Establish, per environment:

- **Topology**: one repo per environment (`<org>/<env-root-repo>`, for
  example `infra-live-dev`, `infra-live-stage`, `infra-live-prod`) or one
  repo with `environments/<env>/`; one folder per stack; whether every stack
  exists in every environment.
- **Layout per stack folder**, for example `main.tf` (provider + backend +
  resources), `variables.tf`, `outputs.tf`, `versions.tf` (newer stacks),
  `<stack>.tfvars` or `*.auto.tfvars`, and `files/` for IAM JSON and
  bootstrap artifacts. Note where older and newer stacks differ (for example
  newer stacks omit an AWS `profile` because the pipeline assumes a role
  while older stacks still set one) - match the stack's own convention and
  flag mixed usage within one stack.
- **Backend and state layout**: bucket/table naming pattern (for example
  `<org>-tfstate-<env>` and `<org>-tflock-<env>`), key pattern
  (`<stack>/<stack>.tfstate`), locking mechanism (S3 native `use_lockfile`
  or a DynamoDB table), and state ownership (local, pipeline, or handoff in
  progress).
- **Account topology**: which environments share a cloud account (namespaced
  resource names keep their stacks disjoint; per-environment state keeps
  state disjoint) and which are isolated (production is normally a separate
  account with `allowed_account_ids` pinned).
- **Promotion pattern**: a stack promotes `dev -> qa/stage -> prod` by copying
  the root byte-identical except backend values and per-environment tfvars.
- **Presence rule**: a stack is not required to exist in every environment.
  Verify the folder exists in the target environment root instead of
  assuming it; treat a missing environment root as scoped work, not an error
  (an environment root may arrive long after its siblings).

## 3. Versions, tooling, and pipelines

- `required_version`, provider `~>` constraints, committed
  `.terraform.lock.hcl`, and whether multi-platform hashes are recorded.
- Static tooling in use (tflint, checkov, trivy, pre-commit), `terraform test`
  adoption, the contract-test runner and its module discovery list, and any
  phase-ordering file that sequences verification roots before apply roots.
- Apply mechanism (pipeline role, local break-glass) and which backends are
  safe to plan against from a workstation.

## 4. Observability couplings

- Where alarms and dashboards are defined (module vs raw blocks), how names
  are composed (module convention vs caller-side override), which shared
  notification topics they route to, which dashboard bodies are
  `templatefile()` templates, and where the consumer's alarm inventory lives.
- Which Lambda/API integrations are alias-fronted (permission wiring lives on
  the alias qualifier) and which functions are CI-deployed (`ignore_changes`
  expected on code/environment attributes).

## 5. Documentation surfaces and the two-way sync contract

- Where the consumer documents its Terraform: a wiki hub page with one child
  page per sub-topic (shared modules, environment roots, active migrations,
  archived conventions), module READMEs, root READMEs, runbooks.
- The sync contract: when a shared-module repo, an environment root repo, or
  the documentation changes materially, the stack inventory is updated in the
  same change set; when the specialist's conventions or validation rules
  evolve, the consumer documentation is updated in the same change set.
  Drift between surfaces is reported as a finding.

## Inventory template

Copy this into the consumer repo's `docs/llm/` and fill it with real values.

| Surface | Value | Convention | Evidence (commit/date) |
| --- | --- | --- | --- |
| Shared-module repo | `<org>/<shared-modules-repo>` | `modules/<name>`, tag-pinned `?ref=vX.Y.Z` | `<sha>` |
| Shared-module repo (secondary) | `<org>/<legacy-modules-repo>` | `modules/<cloud>/<name>`, default-branch tracking | `<sha>` |
| Module inventory | network, compute, IAM, storage, serverless, observability | gaps: `<class>` (raw blocks expected) | `<sha>` |
| Pending promotions | `<app-repo>/terraform/modules/<name>` -> shared repo | branch `<name>`, PR pending | `<date>` |
| Environment roots | `<org>/infra-live-{dev,qa,stage,prod}` | one folder per stack; `<stack>.tfvars` | `<sha>` |
| Backend | `<org>-tfstate-<env>` / `<org>-tflock-<env>` | key `<stack>/<stack>.tfstate` | `<sha>` |
| Accounts | non-prod shared (`<account-id>`), prod isolated (`<account-id>`) | `allowed_account_ids` per root | `<date>` |
| Providers | `hashicorp/aws ~> X.Y`, `required_version >= 1.x` | lockfile committed | `<sha>` |
| Contract tests | `tests/` per root, module discovery list at `<path>` | byte-identity + no-env-leak | `<sha>` |
| Alarm routing | shared topic `<org>-alerts-<env>` | no stack-created personal-subscriber topics | `<date>` |
| Documentation hub | `<wiki-url>` | child page per sub-topic; two-way sync | `<date>` |

## Review duties derived from the inventory

- Verify a module consumer's actual `source` lines in the merged tree, not a
  PR title or description (squash merges make the tree authoritative).
- New resources consume or extend an existing shared module when the
  inventory says one exists for that class; flag fresh raw duplicates as
  promotion debt. Where no module exists, raw blocks are correct.
- Apply the repo's own pinning convention (finding vs optional hardening).
- Review every root that instantiates a changed module, in every environment
  listed in the inventory - not only the environment the request names.
- When a change alters a pattern the shared repos or documentation describe,
  the documentation update is part of the same review.
- Never report an authorization failure (missing IAM permission) as missing
  provider support; the inventory records which tag/permission gates are
  environment-specific.

## Failure modes this inventory prevents

- Flagging references to a re-activated shared-module repo as defects because
  an older note said it was retired.
- Demanding `?ref=` pins where the documented convention is default-branch
  tracking, or accepting unpinned sources where tag-pinning is required.
- Assuming a stack exists in every environment and reporting a missing root
  as a regression.
- Reviewing only the named environment and missing the root that still
  forwards an old variable name.
- Confusing two same-purpose modules in different repos and recommending the
  non-canonical copy.
- Planning against a backend nobody said was safe, or treating a DynamoDB
  lock table as a blocker when it is the consumer's standard.
