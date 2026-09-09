---
name: java-change-validator
description: Read-only Java change validator specialist for Java diffs, tests, framework wiring, architecture, migrations, build evidence, docs, and Java-related human reply drafts. Use when Java changes need an independent validation pass before approval, merge, PR replies, or handoff to an implementer.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.0.0"
---

# Java Change Validator

Use this skill when Java changes need an independent, evidence-backed
validation pass before approval, merge, PR replies, or handoff to an
implementer. The specialist is read-only: it returns findings; the root agent
acts on them.

## When to Use

- "validate these Java changes", "review this Java diff", "is this Java PR safe"
- A reviewer comment on Java code needs a grounded answer or a draft reply
- A migration, transaction boundary, concurrency change, or framework wiring
  change needs a second opinion before merge

## Route

1. Load `workflows/java-change-validation.md`.
2. Invoke or follow `tool-subagents/java-change-validator.md` as a read-only
   specialist. The root agent owns edits, validation commands, commits, pushes,
   PR actions, and user-facing replies.
3. Apply `rules/human-comment-reply-gate.md` for Java-related reviewer replies.
4. Use `skills/java-best-practices/SKILL.md` only for Java guidance that is
   relevant to the changed surface.
5. Compose with `pr-validator`, `documentation-reviewer`,
   `system-architecture-specialist`, `confluence-documentation-specialist`, and
   `diagram-creation-specialist` only when their evidence lanes are relevant.
6. If the specialist misses a reusable pattern, run
   `workflows/java-validator-evolution.md`.

## Required Context

- Full diff against the base branch, not only modified hunks.
- Project-local Java version, framework, build, DI, migration, and test guidance
  (`AGENTS.md`, `docs/llm/`, build files).
- Relevant code paths, tests, docs, PR body, ticket acceptance criteria, and
  reviewer threads.
- Existing validation evidence and the exact commands already run.

## Expected Output

Ask for actionable findings that include evidence, impact, exact implementer
action, recommended validation, claim drift, human reply draft status
(`Posting status: NOT POSTED`), and a related-specialist handoff plus a
learning/token-efficiency note.
