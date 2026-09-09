---
description: Improve the PR Validator from validated live-head, ticket-trace, human-thread, CI, routing, or token-efficiency lessons
---

# PR Validator Evolution

Use this workflow when the PR Validator misses a real readiness issue, agrees
with unsupported comments, routes poorly, or wastes context.

## Steps

1. Capture evidence: request or automation, PR URL/head SHA, ticket data,
   comments or CI logs, specialist output, corrected outcome, and why it is
   reusable.
2. Classify the durable fix:
   - prompt contract: `tool-subagents/pr-validator.md`;
   - workflow procedure: `workflows/pr-validator-validation.md`;
   - trigger/routing: `INTENTS.md`, `rules/request-orchestration.md`;
   - skill entrypoint: `skills/pr-validator/SKILL.md`;
   - broader loop: `workflows/ticket-pr-validation-loop.md`,
     `workflows/gh-address-comments.md`, `skills/ci-watcher/SKILL.md`, or the
     consumer repo's `docs/llm/`.
3. Make the smallest generic update and keep PR/ticket-specific facts out of
   shared assets.
4. Run `documentation-reviewer` on changed docs, prompts, and workflows.
5. Validate with:
   - `node scripts/validate-specialist-agent.js pr-validator`
   - `npm run workflows:size:check`
   - `npm run subagents:check`
   - `npm run llm-content:security-check`
6. Report evidence, files changed, validation, and residual risk.
