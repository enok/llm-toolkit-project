---
description: Improve reusable specialist agents from validated misses, noisy outputs, weak routing, and token-efficiency lessons
---

# Specialist Agent Evolution

Use this workflow when a specialist agent misses a real issue, produces noisy or
unsupported findings, lacks useful routing, or wastes context.

## Phase 1 - Gather Evidence

Collect:

- the user request or automation that selected the specialist;
- specialist prompt and output;
- source files, diffs, tests, logs, comments, or artifacts proving the miss;
- the corrected outcome and why it is reusable.

Do not add project-specific facts to shared assets. Put those in the consumer
repo's `docs/llm/` or other repo-local docs.

## Phase 2 - Classify Fix

| Problem | Durable destination |
| --- | --- |
| Prompt too broad or missing output field | `tool-subagents/<agent>.md` |
| Missing or noisy related-specialist handoff | `tool-subagents/<agent>.md`, `rules/request-orchestration.md` |
| Provider metadata stale | `tool-subagents/<agent>.toml` |
| Procedure unclear | `workflows/<agent>-validation.md` |
| Repeated miss/noise pattern | `workflows/<agent>-evolution.md` |
| Trigger/routing mismatch | `INTENTS.md`, `rules/request-orchestration.md` |
| Skill entrypoint unclear | `skills/<agent>/SKILL.md` |
| Client overlay drift | `clients/README.md` and provider sync output |

## Phase 3 - Update Surgically

Make the smallest generic change that would have improved the prior run. Keep
the specialist single-purpose and avoid copying large reference material into
the prompt. Keep the `.md` and `.toml` bodies identical. When the update changes
docs, prompts, workflows, generated surfaces, or human-facing draft guidance,
run `documentation-reviewer` before final validation.

## Phase 4 - Validate

Run:

```bash
node scripts/validate-specialist-agent.js <agent-name>
npm run subagents:check
npm run workflows:size:check
npm run llm-content:security-check
```

Then run the broader validation required by the task.

## Phase 5 - Report

State the evidence, updated files, validation results, residual risk, and
whether additional learning belongs in the consumer repo's `docs/llm/` instead
of the shared toolkit.
