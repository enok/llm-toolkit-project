---
name: terraform-specialist
description: Read-only Terraform/OpenTofu specialist for module/root review, plan/apply safety, state and import lifecycle, multi-environment roots, IaC-provisioned alarms and dashboards, secrets/metadata hygiene, drift codification, and manual infrastructure handoffs. Use for every request that authors or reviews .tf/.tftpl/.tfvars/lockfiles, decides a plan or apply, touches state or imports, provisions observability through IaC, or judges IaC PR/ticket readiness.
license: MIT
metadata:
  author: dev-tools
  version: "1.1.0"
---

# Terraform Specialist

Use this skill to route work through the Terraform Specialist. Routing is
mandatory for every request that touches Terraform/OpenTofu: authoring or
reviewing `.tf`/`.tftpl`/`.tfvars`/lockfiles, plan/apply decisions, state or
import operations, multi-environment roots, IaC-provisioned observability,
or IaC PR/ticket readiness.

The specialist is the review-and-safety lane. Pair it with
`skills/terraform/SKILL.md` for general authoring guidance (module hierarchy,
`count` vs `for_each`, native tests, Terratest, CI/CD templates,
trivy/checkov) and with `skills/terraform-change-safety/SKILL.md` for the
change-safety patterns the specialist enforces.

## Workflow

1. Load `workflows/terraform-specialist-validation.md`.
2. Invoke or follow `tool-subagents/terraform-specialist.md`.
3. Establish the consumer's stack inventory before judging anything:
   shared-module repos and their pinning style, environment root
   repos/folders, backend/state layout, provider/version pins, and where
   alarm/dashboard couplings live. `references/stack-inventory.md` defines
   what must be established, the review duties derived from it, and where
   the filled-in inventory lives (the consumer repo's `docs/llm/`, never the
   toolkit).
4. When Terraform cannot be applied by the current project or target
   environment and an operator needs a manual resource inventory, load and
   follow `workflows/terraform-manual-infrastructure-handoff.md` before
   generating the table.
5. Load `references/validation-checklist.md` for the detailed detection
   rules (style, pinning, state safety, plan discipline, multi-env,
   secrets, observability coupling, serverless wiring, testing,
   claims-vs-evidence). When the request is WRITING Terraform (new modules,
   roots, docs, or tests), also load `references/authoring-guide.md`
   (create/structure/document/test conventions, terraform-docs, testing
   pyramid, contract-test mechanisms).
6. Keep root-agent ownership for edits, validation, commits, pushes, and
   user-facing communication; the specialist is read-only.
7. Compose with related specialists only when their evidence lanes are
   relevant (`pr-validator`, `dag-glue-specialist`, `aws-alarm-investigator`,
   `security-auditor`, `release-coordinator`).
8. If the specialist misses a real defect or reports noise, run
   `workflows/terraform-specialist-evolution.md`.
9. Keep the specialist synced BOTH WAYS with the consumer's canonical
   Terraform surfaces: when a shared-module repo, an environment root repo,
   or the consumer's Terraform documentation changes materially (new
   modules, changed consumption pattern, new conventions), update the
   consumer's stack inventory in the same change set; when the specialist's
   own conventions or validation rules evolve, propagate the change to the
   consumer's documentation in the same change set. If any surface drifts
   from the others, report the drift as a finding so the root agent re-syncs
   all of them.
