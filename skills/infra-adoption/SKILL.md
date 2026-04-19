---
name: infra-adoption
description: >
    Adopt or import existing infrastructure into managed IaC. Trigger when the user is
    importing resources into Terraform or similar IaC repos, migrating from manual or
    unmanaged infrastructure, or planning a safe state-adoption workflow.
---

# Infra Adoption

Use this skill for safe infrastructure adoption into code and state.

## When to Apply

- Importing existing cloud resources into Terraform/OpenTofu state
- Migrating from manual or click-ops infrastructure to IaC
- Planning a safe state-adoption workflow
- Adopting infrastructure from another team or project

## Workflow

1. **Define the source and destination:**
   - current infrastructure ownership model (manual, another tool, another team)
   - target repo/module/state layout
2. **Inventory resources and dependencies** before importing anything.
3. **Plan the order of imports, state moves, and cleanups explicitly.**
4. **Require dry-run or plan verification before apply:**
   - `terraform plan` should show no unexpected changes after import
   - verify resource attributes match the live infrastructure
5. **Capture rollback or recovery options** for bad imports and state mistakes.
6. **Pair with `terraform` skill** when writing or editing the IaC itself.

## Output

Return:
- adoption scope (resources, accounts, regions)
- import/migration order plan
- validation steps (plan output, attribute verification)
- cleanup and rollback notes

## Non-Goals

- Do not import resources without verifying the plan output.
- Do not skip the inventory step — unknown dependencies cause cascading failures.
- Do not modify live infrastructure without explicit approval.

## Related Skills

- **terraform** — IaC module writing and testing
- **cloudformation** — Alternative IaC approach
- **security** — Infrastructure security review
- **best-practices** — Architecture patterns for infrastructure
