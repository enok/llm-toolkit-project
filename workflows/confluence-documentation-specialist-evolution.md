---
description: Improve the Confluence Documentation Specialist from validated wiki, hierarchy, attachment, comment, routing, or token-efficiency lessons
---

# Confluence Documentation Specialist Evolution

Use this workflow when the Confluence Documentation Specialist misses a real
wiki/docs issue, produces unsupported findings, routes poorly, or wastes
context.

## Steps

1. Capture evidence: request, target page/thread, page read-back, source docs,
   code/diff, Jira/PR context, specialist output, and corrected outcome.
2. Classify the durable fix:
   - prompt contract: `tool-subagents/confluence-documentation-specialist.md`
     (mirror the body into the `.toml`);
   - workflow procedure: `workflows/confluence-documentation-specialist-validation.md`;
   - trigger/routing: `INTENTS.md`, `rules/request-orchestration.md`;
   - skill entrypoint: `skills/confluence-documentation-specialist/SKILL.md`;
   - broader pattern: `skills/confluence-documentation/`, `integrations/confluence.md`,
     or `workflows/confluence-documentation.md`;
   - project- or page-specific fact (space key, page ID, page map): the
     consumer repo's `docs/llm/`, never a shared asset.
3. Make the smallest generic update and keep project/page-specific facts out of
   shared assets.
4. Run `documentation-reviewer` on changed docs/prompts/workflows.
5. Validate with:
   - `node scripts/validate-specialist-agent.js confluence-documentation-specialist`
   - `npm run workflows:size:check`
   - `npm run subagents:check`
   - `npm run llm-content:security-check`
6. Report evidence, files changed, validation, and residual risk.
