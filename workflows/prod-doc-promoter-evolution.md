---
description: Improve the Prod Doc Promoter specialist from validated promotion misses, unsafe automation decisions, destination-map gaps, and routing issues
---

# Prod Doc Promoter Evolution

Use this workflow when the Prod Doc Promoter misses a real deployed-ticket
documentation promotion issue, produces unsupported blockers, routes poorly, or
loads too much context.

## Steps

1. Capture concrete evidence: ticket state, production deployment evidence,
   source folder read-back, destination map, Confluence versions/operations,
   specialist output, executed promotion, validation result, and corrected
   outcome.
2. Classify the durable fix:
   - prompt contract: `tool-subagents/prod-doc-promoter.md` (mirror the body
     into the `.toml`);
   - workflow procedure: `workflows/prod-doc-promoter-validation.md`;
   - trigger/routing: `INTENTS.md`, `rules/request-orchestration.md`;
   - skill entrypoint: `skills/prod-doc-promoter/SKILL.md`;
   - Confluence operations guidance: `skills/confluence-documentation/`,
     `integrations/confluence.md`, or `workflows/confluence-documentation.md`;
   - project-specific destination map, intake folder, or label convention: the
     consumer repo's `docs/llm/` (for example `docs/llm/doc-promotion-map.md`)
     or the automation prompt.
3. Make the smallest generic update. Keep tenant IDs, real folder defaults,
   Jira ticket keys, internal hostnames, and product-specific page maps in
   automation prompts or the consumer repo's `docs/llm/`, never in this
   toolkit.
4. Run `documentation-reviewer` on changed docs/prompts/workflows.
5. Validate with:
   - `node scripts/validate-specialist-agent.js prod-doc-promoter`
   - `npm run workflows:size:check`
   - `npm run subagents:check`
   - `npm run llm-content:security-check`
6. Sync provider surfaces (`scripts/sync-tool-configs.sh` or `.ps1`) and run
   the repository validation required by the task.
7. Report evidence, files changed, validation, residual risk, and any remaining
   automation blocker.
