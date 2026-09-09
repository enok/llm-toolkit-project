---
description: Improve the Diagram Creation Specialist from validated notation, export, image-quality, routing, or token-efficiency lessons
---

# Diagram Creation Specialist Evolution

Use this workflow when the Diagram Creation Specialist misses a real diagram
issue, produces noisy findings, routes poorly, or wastes context.

## Steps

1. Capture evidence: request, source files/docs/configs, diagram source,
   rendered artifact, image-quality result, specialist output, and corrected
   outcome.
2. Classify the durable fix:
   - prompt contract: `tool-subagents/diagram-creation-specialist.md` (mirror
     the body into the `.toml`);
   - workflow procedure: `workflows/diagram-creation-specialist-validation.md`;
   - trigger/routing: `INTENTS.md`, `rules/request-orchestration.md`;
   - skill entrypoint: `skills/diagram-creation-specialist/SKILL.md`;
   - notation/export detail: `skills/diagram-authoring/references/` or
     `skills/image-quality-inspection/references/`;
   - deterministic rendering/style miss:
     `skills/diagram-authoring/references/deterministic-diagram-system.md`;
   - project-specific renderer fact: the consumer repo's `docs/llm/` or other
     repo-local docs.
3. Make the smallest generic update and avoid embedding one-off service names
   or private architecture facts in shared assets.
4. Run `documentation-reviewer` on changed docs/prompts/workflows.
5. Validate with:
   - `node scripts/validate-specialist-agent.js diagram-creation-specialist`
   - `npm run workflows:size:check`
   - `npm run subagents:check`
   - `npm run llm-content:security-check`
6. Report evidence, files changed, validation, and residual risk.
