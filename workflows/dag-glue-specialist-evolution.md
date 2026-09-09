---
description: Improve the DAG/Glue Specialist from validated Airflow, Glue, crawler, Data Catalog, runtime-safety, external-source, and routing lessons
---

# DAG and Glue Specialist Evolution

Use this workflow when the DAG/Glue Specialist needs a durable improvement.

## Steps

1. Capture concrete evidence of the miss, noisy output, stale routing, unsafe
   runtime recommendation, weak related-specialist handoff, external-source
   lesson, or token inefficiency.
2. Classify the fix target:
   - specialist prompt -> `tool-subagents/dag-glue-specialist.md` (mirror the
     body into the `.toml`);
   - validation procedure -> `workflows/dag-glue-specialist-validation.md`;
   - detection rule -> `skills/dag-glue-specialist/references/validation-checklist.md`;
   - skill entrypoint -> `skills/dag-glue-specialist/SKILL.md`;
   - trigger/routing -> `INTENTS.md`, `rules/request-orchestration.md`;
   - external-source note -> `skills/dag-glue-specialist/references/external-source-intake.md`;
   - pipeline-specific fact (DAG IDs, job names, catalog layout) -> the consumer
     repo's `docs/llm/`, never a shared asset.
3. Keep the update generic and provider-neutral unless the validated lesson is
   explicitly Airflow, MWAA, Astro, AWS Glue, crawler, Data Catalog, or cloud
   runtime specific.
4. When importing external skill patterns, use `skills/external-skill-intake/SKILL.md`,
   scan the downloaded source with the configured security tools, avoid running
   external scripts, and preserve only distilled reusable guidance.
5. Make the smallest durable update and preserve unrelated dirty work.
6. Run `documentation-reviewer` on changed docs, prompts, and workflows.
7. Validate with:
   - `node scripts/validate-specialist-agent.js dag-glue-specialist`
   - `npm run workflows:size:check`
   - `npm run subagents:check`
   - `npm run llm-content:security-check`
8. Report the evidence, updated files, validation, external sources reviewed,
   remaining blockers, and residual risk.
