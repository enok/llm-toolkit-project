---
description: Improve the Java change validator from validated misses, noisy findings, and reusable Java review lessons
---

# Java Validator Evolution

Use this workflow when the Java validator misses a real issue, produces noisy
findings, lacks project-local context hooks, or repeatedly consumes too much
context.

## Phase 1 - Capture Evidence

Collect only concrete evidence:

- the diff, call path, reviewer thread, CI/test/build output, or docs where the
  validator failed;
- the validator output and why it was incomplete, stale, noisy, or too broad;
- the corrected finding or better validation path.

Do not encode project-specific hostnames, ticket IDs, or business facts in the
shared validator. Put those in the consumer repo's `docs/llm/` or other
repo-local docs.

## Phase 2 - Classify The Improvement

| Signal | Destination |
| --- | --- |
| Missing Java validation behavior | `tool-subagents/java-change-validator.md` |
| Repeatable validation process | `workflows/java-change-validation.md` |
| Skill trigger or usage gap | `skills/java-change-validator/SKILL.md` |
| Generic Java rule | `skills/java-best-practices/` or a shared rule |
| Routing gap | `INTENTS.md` and `rules/request-orchestration.md` |
| Specialist pattern | `workflows/specialist-agent-evolution.md` |

## Phase 3 - Update Surgically

1. Keep the validator read-only.
2. Add the smallest instruction that would have caught the miss.
3. Prefer references or workflows for detail instead of bloating the subagent
   prompt.
4. Keep human-facing reply guidance aligned with
   `rules/human-comment-reply-gate.md`.

## Phase 4 - Validate

```bash
node scripts/validate-specialist-agent.js java-change-validator
npm run subagents:check
npm run workflows:size:check
npm run llm-content:security-check
```

Then run the broader toolkit validation required by the current task.

## Phase 5 - Report

Summarize the miss, the durable change, validation, remaining risk, and any
lesson that should move to the consumer repo's `docs/llm/` instead of the
shared toolkit.
