# Learnings

Shared knowledge captured from trial-and-error during LLM-assisted development. Each file documents a problem, the approaches that failed, and the correct solution — so any future LLM session skips directly to the happy path.

> **Entry point:** read [`INDEX.md`](./INDEX.md) first for a one-line summary of every learning. Governance is in `skills/error-driven-learning/SKILL.md` (always-on). Capture is via `workflows/capture-learning.md`.

## How it works

1. An LLM (any tool) hits a problem and recovers after multiple attempts.
2. Instead of losing that knowledge when the session ends, it writes a learning file here.
3. Next time any LLM encounters a similar task, it checks this directory first and uses the documented solution.

**This is not tool-specific.** Windsurf, Cursor, Claude Code, Codex, ChatGPT — any LLM that can read files benefits from these learnings.

## File format

Each learning is a standalone markdown file with YAML frontmatter:

```markdown
---
title: Short descriptive title
category: environment | build | api | architecture | testing | toolchain | deployment | security | data-pipeline | monitoring
created: YYYY-MM-DD
tags: [searchable, terms, for, this, learning]
---

# Problem
What was being attempted and what went wrong.

# Failed Approaches
What was tried and why it didn't work.

# Solution
The correct approach — the happy path.

# Why
Root cause explanation.
```

## Naming

Use lowercase kebab-case that summarizes the topic:

- `llm-toolkit-junction-architecture.md`
- `llm-adaptive-skill-loading.md`

## Rules

- **One problem per file.** Keep each learning focused.
- **Include failed approaches.** This prevents LLMs from repeating the same dead ends.
- **Explain the root cause.** Solutions without context break when conditions change.
- **Keep it concise.** Target 20–60 lines per file.
- **Commit to version control.** These are shared team knowledge, not personal notes.

## Promotion

Every learning ships in the same change as a link from the skill, rule,
workflow, or agent definition that owns its lesson (`learnings/<slug>.md`;
`tests/test_learning_promotion_coverage.py` enforces it). The
`toolkit-maintenance` workflow (`workflows/toolkit-maintenance.md`)
periodically promotes learnings that keep recurring into stronger checks; the
file and its `INDEX.md` line stay as the evidence those assets link. Only a
superseded learning's `INDEX.md` line is marked `~~strikethrough~~`, with the
replacement named.
