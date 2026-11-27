# Learnings

Short-lived intake for trial-and-error lessons whose owning skill, rule or workflow is not yet clear. A lesson whose owner is clear is written straight into that owner (a skill `## Known pitfalls` bullet or reference, one workflow bullet, or one rule line) and gets no file here. This directory therefore normally holds only this README and [`INDEX.md`](./INDEX.md).

> **Entry point:** [`INDEX.md`](./INDEX.md) lists the pending intake items (normally none). Governance is in `rules/error-driven-learning.md` and `skills/error-driven-learning/SKILL.md` (always-on). Capture is via `workflows/capture-learning.md`.

## How it works

1. An LLM (any tool) hits a problem and recovers after multiple attempts.
2. It writes the lesson into the asset that owns it; only when no owner is clear does it capture an intake file here, with its `INDEX.md` line.
3. The intake file is migrated into its owner and deleted, together with its `INDEX.md` line, in the change that migrates it — at the latest in the next toolkit maintenance pass. A migrated learning never keeps its file, and nothing may reference a learning file that does not exist.

**This is not tool-specific.** Any LLM that can read files benefits.

## Intake file format

Each intake item is a standalone markdown file with YAML frontmatter:

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

Use lowercase kebab-case that summarizes the topic, for example `example-tool-flag-order` (a made-up name) as `learnings/<kebab-topic>.md`.

## Rules

- **One problem per file.** Keep each item focused.
- **Include failed approaches.** This prevents LLMs from repeating the same dead ends.
- **Explain the root cause.** Solutions without context break when conditions change.
- **Keep it concise.** Target 20–60 lines per file.
- **No ticket IDs, customer names, hostnames or credentials.**
- **Short-lived.** Migrate and delete; git history keeps the record.
