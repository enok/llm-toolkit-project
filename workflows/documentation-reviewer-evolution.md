---
description: Improve the Documentation Reviewer specialist from validated misses, noisy findings, and routing gaps
---

# Documentation Reviewer Evolution

Use this workflow when the Documentation Reviewer specialist needs a durable
improvement.

## Steps

1. Capture concrete evidence of the miss, noisy output, stale routing, or token
   inefficiency. Include the bad doc claim, the source evidence, and the
   expected reviewer finding.
2. Classify the fix across the prompt (`tool-subagents/documentation-reviewer.md`),
   the workflow (`workflows/documentation-reviewer-validation.md`), the skill
   (`skills/documentation-reviewer/SKILL.md`), the routing map (`INTENTS.md`,
   `rules/request-orchestration.md`), tool-config overlays, a validation gate,
   generated-surface sync, or a companion specialist.
3. Make the smallest generic update.
4. Run `node scripts/validate-specialist-agent.js documentation-reviewer`.
5. Sync tool-config surfaces and run the repository validation required by the
   task, including documentation review of the updated docs.
6. Report the evidence, updated files, validation, residual risk, and whether
   the lesson should also update the consumer repo's `docs/llm/` or another
   project-local doc.
