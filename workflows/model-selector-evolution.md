---
description: Improve the Model Selector specialist from mis-tiered tasks, overspend misses, and stale lookup rows
---

# Model Selector Evolution

Use this workflow when the Model Selector specialist needs a durable improvement.

## Steps

1. Capture concrete evidence: the task, the tier and model assigned, what
   actually ran, and either the overspend (cheap work on an expensive model) or
   the under-assignment (a tier that kept failing validation).
2. Distinguish the two failure shapes. A task that repeatedly failed validation
   at its assigned tier means the lookup row is too low — cost per completed task
   was worse, not better. A task that completed easily on an expensive model
   means the lookup row is too high or was never consulted.
3. Classify the fix across the lookup table, the escalation triggers, the prompt
   (`tool-subagents/model-selector.md` and its `.toml` twin), the skill
   (`skills/model-selector/SKILL.md`), the model selection contract in
   `rules/request-orchestration.md`, the client model map in
   `tool-subagents/agent-orchestrator.md`, or the companion workflows.
4. Make the smallest generic update. Add a lookup row for a recurring task type
   rather than special-casing one request; keep the triggers a closed list so
   "this looks hard" cannot re-enter as a reason.
5. Run `node scripts/validate-specialist-agent.js model-selector`.
6. Run `bash scripts/validate-toolkit-indexes.sh` and
   `./scripts/validate-skills-with-skillspector.sh`, then sync provider
   surfaces if the canonical prompt or skill changed.
7. Report the evidence, updated files, validation, residual risk, and whether the
   lesson belongs in the consumer repo's `docs/llm/` instead of the shared
   lookup.
