---
description: Evolve the Terraform Specialist after misses, noisy findings, or token-inefficient runs
---

# Terraform Specialist Evolution

Run this workflow when a Terraform Specialist pass missed a real defect,
reported noise, or spent context inefficiently.

## Triggers

- A destructive or execution-skipping plan shipped despite a specialist pass.
- A state-lifecycle hazard (import blocks left behind, ownership handoff gap,
  destruction-sequencing capability gap) surfaced after review.
- A module-variable wiring gap, metadata smell (ticket numbers, hardcoded
  ARNs), or secret leak was caught by a human or bot instead of the specialist.
- A stack-inventory assumption was wrong: a pinning convention was demanded
  where the repo tracks a default branch, a module was called missing when the
  repo has no module for that class, or a root was reported missing in an
  environment that never had it.
- Findings were rejected as unsupported, style-only, or out of repo scope.
- The pass loaded irrelevant roots/modules or re-derived evidence the root
  agent already supplied.

## Procedure

1. Reconstruct the miss: what evidence existed at review time, which
   procedure step should have caught it, and why it did not.
2. Classify the fix target:
   - detection rule -> `skills/terraform-specialist/references/validation-checklist.md`
   - inventory question the specialist should have asked ->
     `skills/terraform-specialist/references/stack-inventory.md`
   - change-safety pattern -> `skills/terraform-change-safety/SKILL.md`
   - procedure/output gap -> `tool-subagents/terraform-specialist.md`
     (mirror the body into the `.toml`)
   - scoping/loading waste -> `workflows/terraform-specialist-validation.md`
   - cross-specialist routing -> `INTENTS.md`, `rules/request-orchestration.md`
   - consumer-specific Terraform fact -> the consumer repo's `docs/llm/`, never
     a shared asset
3. Write the smallest durable edit; encode the mistake as a checkable rule
   (grep pattern, command, or plan assertion), not prose advice. Keep
   organization-specific repo names, account IDs, and page links out of the
   shared toolkit.
4. Run `documentation-reviewer` on changed docs, prompts, and workflows.
5. Validate with:
   - `node scripts/validate-specialist-agent.js terraform-specialist`
   - `npm run workflows:size:check`
   - `npm run subagents:check`
   - `npm run llm-content:security-check`
6. Record the lesson through `workflows/specialist-agent-evolution.md` if it
   generalizes beyond Terraform, and report evidence, files changed,
   validation, and residual risk.
