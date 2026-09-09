---
description: Improve the System Architecture Specialist from validated architecture, source-grounding, routing, handoff, or token-efficiency lessons
---

# System Architecture Specialist Evolution

Use this workflow when the System Architecture Specialist misses a real
architecture issue, produces unsupported findings, routes poorly, or wastes
context.

## Steps

1. Capture evidence: request, repos/services, code/config/docs/diagrams,
   tickets/PRs/logs/metrics, specialist output, corrected outcome, and why it is
   reusable.
2. Classify the durable fix:
   - prompt contract: `tool-subagents/system-architecture-specialist.md`
     (mirror the body into the `.toml`);
   - workflow procedure: `workflows/system-architecture-specialist-validation.md`;
   - trigger/routing: `INTENTS.md`, `rules/request-orchestration.md`;
   - skill entrypoint: `skills/system-architecture-specialist/SKILL.md`;
   - broader method: `skills/best-practices`, `skills/llm-application-architecture`,
     `workflows/project-discovery.md`, `workflows/document-creation.md`;
   - project-specific architecture fact: the consumer repo's `docs/llm/`, never
     a shared asset.
3. Make the smallest generic update and keep product-specific architecture
   details (service names, hostnames, account layouts) out of shared assets.
4. Run `documentation-reviewer` on changed docs/prompts/workflows.
5. Validate with:
   - `node scripts/validate-specialist-agent.js system-architecture-specialist`
   - `npm run workflows:size:check`
   - `npm run subagents:check`
   - `npm run llm-content:security-check`
6. Report evidence, files changed, validation, and residual risk.
