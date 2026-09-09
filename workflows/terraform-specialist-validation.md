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
