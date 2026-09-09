---
description: Improve agent orchestrator routing, model selection, validation, state checkpoints, and token efficiency from validated evidence
---

# Agent Orchestrator Evolution

Use this workflow when the coordinator produces a validated routing, model,
progress/SLA, state, notification, capability, or token-efficiency miss.

1. Capture the request, task table, platform evidence, validator verdict,
   checkpoint, corrected outcome, and why the lesson is reusable.
2. Classify the smallest generic destination: the canonical prompt
   (`tool-subagents/agent-orchestrator.md` and its `.toml` twin),
   `workflows/agent-orchestrator-validation.md`,
   `skills/agent-orchestrator/SKILL.md`, `INTENTS.md`,
   `rules/request-orchestration.md`, a provider overlay, or the consumer
   repo's `docs/llm/` for project-specific facts.
3. Preserve capability-first progressive disclosure; do not add broad catalogs
   or unconfirmed model/tool claims to shared context.
4. Keep the `.md` and `.toml` bodies identical when the canonical prompt
   changes.
5. Run `documentation-reviewer` on prompt, workflow, skill, index, and
   generated-surface changes, then validate with
   `node scripts/validate-specialist-agent.js agent-orchestrator`,
   `npm run workflows:size:check`, `npm run subagents:check`, and
   `npm run llm-content:security-check`.
6. Report evidence, files, validation, generated surfaces, and residual risk.
