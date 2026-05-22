---
description: Capture mistakes as happy-path learnings, identify reusable skills/workflows, and safely harvest external LLM-tool skills
---

# Self-Improvement Workflow

Run this at the end of any workflow or substantial task.

## Phase 1 — Capture mistakes as learnings

1. Review the session for errors, failed commands, wrong assumptions, tool gotchas, CI failures, or validation failures.
2. If a mistake required trial-and-error or revealed a reusable gotcha, save a learning with:
   - problem attempted
   - failed approaches and observed errors
   - happy path that should be followed next time
   - root cause explanation
3. Use `workflows/capture-learning.md` for the exact learning format.
4. Keep project-specific details in the source project; shared toolkit learnings must be generic or explicitly evidence-focused.

## Phase 2 — Convert repeated value into reusable capability

1. Ask what should become a rule, workflow, skill, reference, script, or learning.
2. Prefer a skill or workflow for specialized procedures instead of adding always-loaded rules.
3. Avoid duplication by linking to existing guidance rather than copying it.
4. Keep new guidance generic: no branch names, ticket IDs, customer names, internal hostnames, or project-specific commands unless they are placeholders.
5. Update every index needed to keep knowledge reachable: `AGENTS.md`, `README.md`, `INTENTS.md`, `workflows/README.md`, and relevant skill/workflow cross-links.

## Phase 3 — Harvest external LLM-tool skills safely

1. Search official or main public repositories/docs for relevant Claude, Codex, Cursor, Windsurf, MCP, or agent skill/workflow patterns.
2. Use `skills/external-skill-intake/SKILL.md` before importing, copying, or executing any external content.
3. If accepted, adapt the pattern into this toolkit’s generic skill/workflow format and document attribution or source notes when required by license.
4. Run `scripts/validate-toolkit-indexes.sh` and `scripts/security-check-toolkit.sh` before considering the import complete. In PowerShell, use `scripts/validate-toolkit-indexes.ps1` and `scripts/security-check-toolkit.ps1`.

## Phase 4 — Final report

Summarize:

- mistakes captured or explicitly not worth capturing
- new or updated skills/workflows/rules/learnings
- external skill sources reviewed and their security result
- indexes and validation commands run
- any deferred follow-ups
