---
description: Capture mistakes as happy-path learnings, identify reusable skills/workflows, and safely harvest external LLM-tool skills
---

# Self-Improvement Workflow

Run this at the end of any workflow or substantial task.

## Phase 1 — Judge execution evidence

1. Review parent-agent and subagent outputs before learning from them.
2. Accept a subagent result only when it cites concrete evidence, stayed inside scope, respected constraints, and produced actionable findings or validation. Also judge whether the task's assigned complexity tier fit the work: a `light`-tiered task that returned shallow or wrong analysis, or a `deep`-tiered task that was trivially mechanical, is a tier-misassignment signal.
3. Mark low-evidence, conflicting, stale, or out-of-scope results as a redo, risk, or non-learning. Do not promote them into durable guidance.
4. Prefer measured outcomes, traces, validators, tests, user corrections, or repeated failures over single-run intuition.

## Phase 2 — Capture mistakes as learnings

1. Review the session for errors, failed commands, wrong assumptions, subagent misses, tool gotchas, CI failures, or validation failures.
2. If a mistake required trial-and-error or revealed a reusable gotcha, save a learning with:
   - problem attempted
   - failed approaches and observed errors
   - happy path that should be followed next time
   - root cause explanation
3. Use `workflows/capture-learning.md` for the exact learning format.
4. Keep project-specific details in the source project; shared toolkit learnings must be generic or explicitly evidence-focused.
5. When useful lessons are spread across chat history, memory, rollout summaries, or automation runs, use `workflows/chat-knowledge-curation.md` and `skills/chat-knowledge-curation/SKILL.md` to mine and convert a bounded evidence batch.

## Phase 3 — Convert repeated value into reusable capability

1. Ask what should become a rule, workflow, skill, reference, script, or learning.
2. Prefer a skill or workflow for specialized procedures instead of adding always-loaded rules.
3. Avoid duplication by linking to existing guidance rather than copying it.
4. Keep new guidance generic: no branch names, ticket IDs, customer names, internal hostnames, or project-specific commands unless they are placeholders.
5. When an orchestrator or subagent gap recurs — including repeated complexity-tier misassignments for a task shape — update the smallest durable surface: `tool-subagents/<agent>.md`, `rules/request-orchestration.md`, a focused workflow, a focused skill reference, or a validation gate.
6. Update every index needed to keep knowledge reachable: `AGENTS.md`, `README.md`, `INTENTS.md`, `workflows/README.md`, and relevant skill/workflow cross-links.

## Phase 4 — Harvest external LLM-tool skills safely

1. Search official or main public repositories/docs for relevant Claude, Codex, Cursor, Windsurf, MCP, or agent skill/workflow patterns.
2. Use `skills/external-skill-intake/SKILL.md` before importing, copying, or executing any external content.
3. For agent-evaluation, orchestration, and self-evolving-agent patterns, start from `skills/external-skill-intake/references/agent-evolution-sources.md`.
4. For skill source URLs, run the Gen Agent Trust Hub URL check before import; for new local skill files, run SkillSpector and Snyk Agent Scan through `scripts/security-check-toolkit.sh`.
5. If accepted, adapt the pattern into this toolkit’s generic skill/workflow format and document attribution or source notes when required by license.
6. Run `scripts/validate-toolkit-indexes.sh` and `scripts/security-check-toolkit.sh` before considering the import complete. In PowerShell, use `scripts/validate-toolkit-indexes.ps1` and `scripts/security-check-toolkit.ps1`.

## Phase 5 — Final report

Summarize:

- subagent results accepted, rejected, or rerun and why
- mistakes captured or explicitly not worth capturing
- new or updated skills/workflows/rules/learnings
- external skill sources reviewed and their security result
- indexes and validation commands run
- any deferred follow-ups
