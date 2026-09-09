---
title: Terraform validation checklist
tags: [terraform, opentofu, review, plan-safety, state, multi-env, secrets, observability, testing]
---

# Terraform Validation Checklist

Use this checklist when a request needs deeper Terraform/OpenTofu validation.
It merges vendor guidance (HashiCorp style guide and language docs, AWS
Prescriptive Guidance for the Terraform AWS provider, Google Cloud Terraform
best practices, Gruntwork production-grade IaC) with defect classes proven in
real multi-environment rollouts of detector/alarm stacks, serverless
pipelines, and backup-verification roots. Conventions that vary per consumer
(pinning style, lock-table standard, module precedents) come from the
consumer's stack inventory (`stack-inventory.md`).

## Code style and structure

- Resource labels: descriptive snake_case nouns that do not repeat the
  resource type; the sole resource of a type is `main` or `this`; singular
  names with meaningful differentiators (`primary`/`read_replica`).
- Every variable and output declares `type` and `description`; numeric
  variables carry units (`ram_size_gb`); booleans are positively named
  (`enable_x`, never `disable_x`); mark `sensitive` where applicable.
- Group resources into purpose-named files (`network.tf`, `iam.tf`) once a
  logical group grows; no one-file-per-resource sprawl; provider blocks live
  only in root modules, never in shared modules.
- Modules are single-purpose and composable; don't wrap a single resource in
  a module; keep nesting to 1-2 levels; every resource in a reusable module
  is referenced by at least one output (enables dependency graphs); reference
  resource attributes directly rather than round-tripping through variables.
- Prefer attachment resources (e.g. `aws_security_group_rule`) over inline
  embedded blocks to avoid coupled cause/effect diffs.
- Shared-module naming: compose `<org>-<type>-<environment>-<purpose>`
  internally from `org`/`environment`/`purpose` inputs with a
  `coalesce(var.<name_override>, "<composed>")` full-name override defaulting
  to `null`; follow the precedent modules recorded in the consumer's stack
  inventory.
- Variable/output `description` strings are ordinary HCL strings: a literal
  `${...}` is template syntax and gets interpolated (or errors) - write
  `<org>`-style angle-bracket placeholders (or escape as `$${...}`) in
  descriptions.
- `terraform fmt -check` and `terraform validate` clean per touched root.

## Versioning and pinning

- `required_version` floor matches the features used (`>= 1.6` for
  `terraform test`, `>= 1.7` for `moved`/`removed`/config-driven `import`
  blocks and test mocking, `>= 1.10` for ephemeral values and S3 native
  locking, `>= 1.11` for write-only arguments).
- Providers pinned with `~>` in `required_providers`; never unconstrained.
- `.terraform.lock.hcl` committed, never hand-edited; multi-platform hashes
  via `terraform providers lock -platform=...` for mixed-OS teams; provider
  upgrades deliberate (`init -upgrade` + release notes), never silent CI drift.
- Registry modules pin explicit `version`; git-sourced modules pin a tag or
  commit SHA (`?ref=`), never a floating branch. Exception: when the
  consumer's stack inventory records that a shared-module repo is consumed by
  default-branch tracking by convention, a pin is optional hardening to
  recommend, not a blocker.
- `allowed_account_ids` (or equivalent) pinned per environment so
  cross-account applies are impossible; provider aliases for multi-account
  roots, default provider listed first.

## State safety

- Remote backend with locking; S3-native locking (`use_lockfile = true`,
  Terraform >= 1.10) preferred; flag configs still relying only on the
  deprecated DynamoDB lock table without a migration path. Exception: when
  the consumer's environment roots standardize on a DynamoDB lock table
  (recorded in the stack inventory), report S3-native locking as an
  informational/optional migration there, not a blocker.
- State bucket: versioning + SSE enabled; per-environment backends (not CLI
  workspaces) for isolation; production state write access limited to CI/CD
  plus break-glass roles; alert on state unlocks originating outside CI/CD.
- Never hand-edit state; state surgery uses declarative `moved`/`removed`/
  `import` blocks over imperative `terraform state mv/rm` (auditable in the
  codebase); always `terraform state pull > backup.tfstate` first and dry-run
  plan the move before applying.
- `removed` blocks default to destroying the real resource unless
  `lifecycle { destroy = false }` is set; a resource address cannot have both
  a `resource` and a `removed` block; `import` blocks are root-module-only.
- Import lifecycle: import blocks whose targets are already in state fail
  every subsequent plan - any import file must carry a tracked removal plan
  (in business language) executed immediately after the first successful
  apply. State-ownership handoffs (local -> pipeline backend) are explicit.

## Plan/apply discipline

- Plan is generated to a saved artifact (`-out=plan.tfplan`), reviewed, and
  that exact artifact is applied - never a fresh plan after review.
- Enumerate expected imports/changes/destroys BEFORE reading plan output;
  0 to destroy unless destruction is the explicit intent; challenge any
  in-place update on provisioner-bearing resources and any change that must
  trigger execution but plans as an update.
- Post-apply plan must report "No changes"; CI gates use
  `-detailed-exitcode` (0 clean / 1 error / 2 changes) with wrapper
  exit-code swallowing disabled.
- Drift detection: scheduled `terraform plan -refresh-only -detailed-exitcode`;
  suppress known-benign drift with `lifecycle { ignore_changes }` so real
  drift is not buried; drift found in review is codified at its source and
  imported, never planned over - a plan that strips live configuration
  (encryption, lifecycle rules, alarms, IAM statements) is a code defect,
  not cleanup.
- Backup-before-apply, fail-closed: timestamped state backup + read-only
  cloud snapshots committed with the change; immutable versioned artifacts
  pinned by version-id + checksum; verification roots ordered before apply
  roots and erroring if the snapshot disappears or mutates.
- Destruction sequencing avoids capability gaps: destroy a superseded
  notification topic only after alarms re-point to its replacement.

## Multi-environment patterns

- Separate root directories/backends per environment; CLI workspaces are for
  same-credential lightweight variants only, never prod/dev isolation
  (HashiCorp's own guidance).
- Shared multi-env root files are byte-identical; every environment
  difference lives in per-env `.auto.tfvars`; equality and no-env-leak
  enforced by contract tests, so an edit to one root must be mirrored exactly.
- Feature gating via empty-value `count` guards
  (`count = var.secret_name != "" ? 1 : 0`) keeps pipelines green until an
  environment's prerequisite exists; enabling is a one-line tfvars change.
- Operator-set module variables traced end to end: declared and forwarded in
  every root (undeclared tfvars entries fail silently); documented commands
  executable verbatim from the named root directory.
- A stack need not exist in every environment root; verify the folder exists
  in the target environment instead of assuming presence.

## Security and secrets

- Least-privilege execution identity: IAM roles (OIDC federation in CI,
  `assume_role` locally), never long-lived access keys; build policies up
  from empty, not down from broad.
- Secrets never in tfvars, source, committed plans, or test fixtures
  (asserted by contract test); `sensitive = true` with empty defaults and
  secret-manager lookups at apply time; flag resources/data sources known to
  persist secrets into state; prefer ephemeral values (>= 1.10) and
  write-only arguments with their `*_wo_version` companion (>= 1.11, needs
  provider support) where available.
- Static scanning (tflint/checkov/trivy) and policy-as-code (mandatory tags,
  allowed types, no-destroy-prod guardrails) in the pipeline when present.
- No ticket numbers in resource tags, descriptions, comments, file paths, or
  strings - business/component language only (tickets close; live metadata
  and comments go stale). Sweep added diff lines
  (`git diff base...head` on `^+` lines) and new file paths, and when one
  instance is found, sweep the whole change set for the class.
- Alarm/notification routing points at shared team topics, never
  stack-created topics with personal-email subscribers; verify subscriber
  lists live before claiming routing works.

## Observability coupling

- Dashboard/alarm bodies loaded from files are templated with
  `templatefile()` from module outputs - never hardcode ARNs, account IDs,
  or names of resources a module in the same root manages; static test
  readers render templates against pinned per-env values and fail on
  unresolved placeholders.
- Alarm sensitivity on sparse/liveness metrics is justified with real,
  fresh traffic evidence documented in-code with a revisit condition;
  re-verify the evidence when challenged, never cite stale numbers; plan
  the first-datapoint behavior explicitly.
- Post-apply proof is live: body diffed against the deployed resource via
  canonical checksum, synthetic stimuli prove widgets render, alarm cycle
  OK -> ALARM -> OK exercised rather than assumed.
- Metric existence is proven before alarming: `get-metric-data` over a window
  where sibling metrics return datapoints - CloudWatch accepts any
  namespace/metric string, and alarms on phantom metrics sit OK forever
  (AWS/Lambda has no `Timeouts` metric; back it with a dimensionless
  CloudWatch Logs metric filter, `default_value = 0`, per-function log group
  scoping - filters cannot derive `FunctionName` from plain-text lines).
- Name-collision check before first apply of alarms/dashboards:
  `PutMetricAlarm`/`PutDashboard` are upserts, so a Terraform "create" of a
  same-name resource silently overwrites a live hand-made one with no plan
  warning - verify composed names are unused (`describe-alarms`,
  `list-dashboards`) or make the collision an explicit import.

## Serverless wiring (Lambda / API Gateway)

- `aws_lambda_permission` on an alias: `function_name` = bare function name,
  `qualifier` = alias. Baking `name:alias` into `function_name` applies
  cleanly but plans as a perpetual replacement forever after.
- Never add an unqualified "console visibility" twin permission for an
  alias-fronted API Gateway integration: the function-level Triggers tab
  cross-checks the statement against the integration URI (which targets the
  alias) and permanently flags it as a path/method mismatch. Alias-scoped
  trigger visibility lives only under Aliases > <alias> > Configuration >
  Permissions; document that instead.
- AWS_IAM-authorized APIs: SigV4 signing alone is not enough - callers also
  need an `execute-api:Invoke` identity policy; verify the caller role, not
  just the resource policy.
- CI-owned lambdas: `ignore_changes = [environment, filename,
  source_code_hash]` on the function and `[function_version]` on aliases so
  CI redeploys never drift the plan; flag their absence on any
  pipeline-deployed function, and flag `environment`/code assertions in
  post-apply tests against CI-owned functions (Terraform's values are
  initial-only).
- Modules declaring `configuration_aliases` (e.g. `aws.iam`) validate only
  from a calling root - a standalone `terraform validate` failure there is
  expected, not a defect; validate via the consuming root instead.

## Post-apply resource testing

- Live post-apply tests run ONLY in the pre-production (stage) environment:
  they issue real requests to application endpoints (e.g. token generation
  and redirect entry points) and write synthetic stimuli. Production
  validation stays offline/parse-only - read Terraform source and deployed
  read-only describes; never stimulate or send application requests to prod.
  Runners must hard-enforce this (reject non-stage post-apply modes and pin
  the target account ID), and any new live-test tooling must carry the same
  stage-only guard.
- Every applied resource class has a concrete live verification: a read-only
  describe/get proving existence and planned configuration, plus a behavioral
  probe where the resource does work (synthetic request through the ingestion
  endpoint, query against the target datastore, metric/log datapoint proving
  delivery, rendered widget, alarm cycle).
- Scenarios cover happy paths and the error paths that genuinely exist in the
  pipeline - never invented failure modes the system cannot produce.
- The test report outputs: a scenario matrix with pass/fail, every created or
  changed resource linked by ARN/console URL/unique name to its live
  counterpart, and the verbatim requests/commands issued to test (re-runnable
  as written). Resources not tested are listed explicitly as untested.

## Testing and CI

- Contract tests mirrored per `.tf` file: exact-resource assertions,
  byte-identity for shared files, assertions that no environment-specific
  value leaks into shared files and that credentials are absent from source,
  per-environment test modes with distinct counts tracked as evidence.
- Native `terraform test` (>= 1.6) where adopted: plan-mode runs for unit
  checks, apply-mode against disposable accounts, `expect_failures` for
  negative tests of custom conditions.
- Pre-commit hooks (`fmt`, tflint, checkov) catch issues before CI; shared
  modules ship with tests, not just root configs.
- Pipeline shape: PR -> plan visible in review -> human review of code AND
  plan together -> merge -> authoritative re-plan from the target branch ->
  approval gate -> apply from an isolated deploy mechanism, not ambient CI
  runner credentials.

## Cross-cutting sweeps

- When a file consumed by other code is renamed (e.g. a dashboard body
  `.json` -> `.json.tftpl`), grep the entire repo for the old filename -
  consumers outside the test tree (post-apply scripts, runbooks) are exactly
  what test suites miss.
- Import completeness without backend access: reconcile the import blocks
  1:1 against the module's count-gated resource inventory under the target
  environment's inputs - a cheap static substitute for a live plan.
- Sha/byte pins on backup artifacts belong in blocking `postcondition`s with
  `checksum_mode = "ENABLED"`, never warning-only `check` blocks; diff any
  new verification root against the repo's existing backup-root precedent
  before trusting a "fail-closed" comment.
- New verification/backup roots get mirrored contract tests like every other
  root; "full coverage per .tf file" claims are checked against the test
  runner's actual module discovery list.

## Claims vs evidence

- Post-apply resource claims are DRAFT until re-queried live under the
  owning state after the apply actually runs.
- PR-body claims are diffed against the latest commit specifically - bodies
  fossilize superseded design decisions.
- When a workflow bounds coverage (subset of roots, skipped environments),
  say what was skipped; silent truncation reads as full coverage.
