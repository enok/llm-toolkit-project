---
description: Run the Terraform Specialist for module/root review, plan safety, state lifecycle, multi-env roots, and IaC readiness reporting
---

# Terraform Specialist Validation

Use this workflow whenever a request touches Terraform/OpenTofu: authoring or
reviewing `.tf`/`.tfvars`/lockfiles, plan/apply decisions, state or import
operations, multi-environment roots, IaC-provisioned observability, or an IaC
PR/ticket readiness call.

## Phase 1 - Live Scope

1. Establish repo, roots/modules touched, target environments, backend/state
   ownership, base/head, live head SHA, local freshness, and dirty-tree
   ownership.
2. Identify what infrastructure access is safe: none, read-only CLI, or
   plan-capable against a named backend. Never assume apply authority.
3. Establish the consumer's stack inventory (shared-module repos and their
   pinning convention, environment root topology, backend/state layout,
   provider pins, alarm/dashboard couplings). Read it from the consumer repo's
   `docs/llm/` when it exists; otherwise build it from the repo itself using
   `skills/terraform-specialist/references/stack-inventory.md`. Findings that
   depend on a convention nobody has recorded are reported as
   "inventory unknown", not guessed.
4. Load only relevant context: the changed roots and every root that
   instantiates a changed module, tfvars, `.terraform.lock.hcl`, phase
   ordering files, contract tests, and
   `skills/terraform-specialist/references/validation-checklist.md`.

## Phase 2 - Specialist Pass

1. Invoke or follow `tool-subagents/terraform-specialist.md`.
2. Provide the objective, diff, plan output or plan claims, live-access level,
   contract-test results, the stack inventory, and any reviewer/ticket asks.
3. Ask for stack inventory, plan-safety analysis, findings, validation
   evidence, decision, and related-specialist handoffs.

## Phase 3 - Reduce And Act

1. Accept only evidence-backed findings tied to the reviewed head; reject
   style preferences the repo does not follow.
2. Prefer codifying drift and fixing code over explaining anomalies away.
3. The root agent owns edits, applies, commits, pushes, and human-facing
   replies; keep apply/state mutations behind explicit user authorization.

## Phase 4 - Validate

Run the narrowest relevant checks from the correct directories:

- `terraform fmt -check` and `terraform validate` per touched root;
- repo contract tests per environment mode;
- byte-identity diffs for shared multi-env files;
- ticket-number and secret sweeps over added diff lines and new paths;
- `terraform plan` (or plan review) with expected imports/changes/destroys
  enumerated before reading the output; post-apply "No changes" check after
  any apply.

When an apply ran (or is being verified), also require the specialist's
post-apply test report: every resource verified live (read-only describe plus
a behavioral probe where the resource does work), a scenario matrix covering
happy and genuine error paths, each created resource linked by ARN/console
URL/name, and the verbatim requests/commands used to test - with untested
resources named explicitly.

## Phase 5 - Handoffs

- When Terraform cannot be applied in the target environment and an operator
  must act by hand, run `workflows/terraform-manual-infrastructure-handoff.md`
  in full before producing any resource table.
- When the change provisions Glue jobs, crawlers, catalogs, or Airflow/MWAA
  surfaces, route that lane through
  `workflows/dag-glue-specialist-validation.md`.
- When an IaC-provisioned alarm's live behavior is in question, route through
  `workflows/aws-alarm-investigator-validation.md`.

## Phase 6 - Evolve

If the specialist misses a destructive-plan risk, state-lifecycle hazard,
wiring gap, coupling smell, or burns tokens on irrelevant roots, run
`workflows/terraform-specialist-evolution.md`.

## Known pitfalls

- Before editing source to fix a symptom seen on a live artifact, fetch the live definition (for example `aws cloudwatch get-dashboard --dashboard-name <name> --region <region>`), normalize both sides with `jq -S`, diff them, and run `terraform plan`; if live is right and source is stale, codify live into source instead of "fixing" source. See learnings/diagnose-live-vs-source-before-assuming-source-causes-symptom.md.
- In a multi-copy stack, explain every changed file in `git status`/`git diff` and run `diff -rq` (excluding `.terraform`, logs, plans) between the branch copy and the real-backend working copy before committing; commit already-applied drift separately with an honest message, sync a stale copy from the ahead side instead of reverting, and re-verify all copies are byte-identical for the touched files after pushing. See learnings/reconcile-applied-drift-before-committing-in-multi-copy-stacks.md.
- In a parallel-stack cutover, order the changes: IaC first (a TEMPORARY, clearly labelled grant on the old role with a tracked removal at cutover; plan, confirm exactly one add, apply, re-plan to a clean no-op), then deploy the code and verify the deployed version, then flip the shared config, then send a real request and check for the success log line and zero new error events. See learnings/parallel-stack-parity-env-flip-needs-iam-first.md.
- Before any state migration, prove the target bucket+key is unused (`aws s3api head-object`, grep every Terraform root and open PR for the same bucket and key); on a hit, import the existing state or change the key. See learnings/terraform-state-migration-must-verify-target-key-unused.md.
- When a root's plan wants to create resources another root owns, compare the planned resource addresses of both roots; do not read "0 to destroy" as proof the creates are safe, and mark the legacy root targeted-apply-only with a committed README warning naming the safe `-target` addresses; if the other root is taking the resources over, import them there and remove them from the legacy state instead. See learnings/terraform-targeted-apply-root-needs-warning.md.
- Ignore state files with `*.tfstate` and `*.tfstate.*` (not only `terraform.tfstate*`), block staged `.tfstate` paths with a pre-commit hook, and verify the remote backend's object versions before deleting any local recovery file. See learnings/narrow-gitignore-patterns-miss-state-files.md.
- Put `allowed_account_ids` in the `provider` block, never in the `backend` block (`terraform init` fails with "Unsupported argument"). See learnings/terraform-allowed-account-ids-invalid-in-backend-block.md.
- On Windows, when `terraform init` of git-sourced modules fails with git errors such as "$GIT_DIR too big", run `terraform init -backend=false` and `terraform validate` in a short-path copy of the roots plus local modules, and keep one short-path copy initialized against the real backend for plan/apply; the repo checkout stays the source of truth. See learnings/terraform-init-git-modules-fail-on-deep-windows-paths.md.
- When `terraform plan` cannot refresh the SSO token (`InvalidGrantException`) while `aws sts get-caller-identity` works, run `eval "$(aws configure export-credentials --format env)"` and the Terraform command in the same shell invocation. See learnings/terraform-sso-token-refresh-fails-when-cli-works.md.
- When the SSO token is expired, ask the user to run `aws sso login --profile <profile>`; never complete the browser approval yourself, continue the work that needs no AWS access, and park AWS verifications in a named resume list. See learnings/aws-sso-device-login-cannot-run-unattended.md.
- For alarms, dashboards, and metrics, also apply the `## Known pitfalls` of `skills/terraform-specialist/references/validation-checklist.md`.
