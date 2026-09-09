---
trigger: always_on
description: Capture trial-and-error wins as indexed learnings, consult learnings/ before starting a task, and migrate reusable lessons into durable toolkit assets
---

# Error-Driven Learning

When an LLM finds the correct solution after trial-and-error, capture the knowledge so future sessions — regardless of tool — go directly to the happy path. Treat `learnings/` as committed intake, not the final knowledge base: durable, reusable guidance belongs in rules, workflows, skills, agents, docs, scripts, tests, templates, generated surfaces, or validation gates, and a learning is the evidence that earns that promotion.

## When to capture

Capture a learning when:

- You tried two or more approaches before finding the one that works.
- A command, API call, or configuration behaved differently than expected.
- A platform-specific gotcha caused a failure (Windows vs Unix, shell differences, path handling).
- A build, test, or deploy step required a non-obvious flag, order, or workaround.
- An integration between components required specific wiring that was not obvious from the code alone.

Do **not** capture trivial typos, one-off user misunderstandings, or temporary environment blips.

## Where learnings live

Repositories keep a `learnings/` directory at the root. Files inside are plain markdown with YAML frontmatter, and the directory is committed to version control so every LLM tool and every developer benefits.

```text
learnings/
  README.md              # Convention docs and template
  INDEX.md               # One-line entry per learning, grouped by category
  <topic>.md             # One reusable lesson per file
  sam-build-docker.md    # Example learning
```

- Every learning gets a one-line entry in `learnings/INDEX.md` under its category heading, committed together with the file.
- In `toolkit-maintenance` runs, process learnings in batches of at most 5 files. After a selected learning is migrated into a durable asset and validated, delete or move the consumed file and update the index. If a selected learning cannot be safely migrated, leave it in place and report the blocker.

## File format

```markdown
---
title: Short descriptive title
category: environment | build | api | architecture | testing | toolchain | deployment | security | observability | data-pipeline
created: YYYY-MM-DD
tags: [searchable, terms]
---

# Problem
What was being attempted and what went wrong.

# Failed Approaches
What was tried and why it didn't work. Be specific — include commands, error messages, or code snippets.

# Solution
The correct approach. This is the happy path a future LLM should take directly.

# Why
Root cause explanation so the reader understands, not just copies.
```

## How to consume

Before starting a task, check whether `learnings/` contains anything relevant:

1. Read `learnings/INDEX.md`, then scan filenames and tags for topic overlap with the current task.
2. Read matching files before planning your approach.
3. Prefer the documented solution over re-discovering it from scratch.

If the repository does not have a `learnings/` directory yet, create one (with `README.md` and `INDEX.md`) the first time you capture a learning that cannot immediately be migrated to a durable asset.

## How to write

Follow the `capture-learning` workflow (`workflows/capture-learning.md`). Key principles:

- **One file per learning.** Keep each focused on a single problem–solution pair.
- **Name files descriptively.** Use lowercase kebab-case that summarizes the topic: `maven-windows-sh-plugin.md`, `dynamodb-batch-limit.md`.
- **Include failed approaches.** This is what prevents future LLMs from repeating the same mistakes.
- **Include the root cause.** A solution without explanation is fragile — it breaks the moment conditions change.
- **Keep it concise.** A learning is not a tutorial. Target 20–60 lines.
- **Keep it generic.** No ticket IDs, customer names, internal hostnames, or credentials; keep project-only facts in the consumer repo's `docs/llm/`.

## Tool-specific memory is supplementary

Some LLM tools have built-in memory or tool-native context (Windsurf memories, Cursor context, Claude Code memory). Use those too — they provide faster retrieval within that tool. The committed file is the source of truth because it works across tools, survives tool migrations, and is code-reviewable: the learning until it is migrated, then the durable toolkit asset it became.

When using tool-specific memory, reference the committed asset:
> See `learnings/<topic>.md` (or, after migration, `skills/<name>/SKILL.md` or `rules/<name>.md`) for details.

## Categories

| Category | Covers |
|---|---|
| **environment** | OS, shell, permissions, auth, path handling, locale |
| **build** | Compilation, packaging, dependencies, plugins, flags |
| **api** | SDK usage, method signatures, request/response, rate limits |
| **architecture** | Component wiring, data flow, service dependencies |
| **testing** | Test setup, fixtures, mocking, assertion patterns |
| **toolchain** | CLI tools, IDE config, linters, formatters, notebooks |
| **deployment** | Deploy process, infra, config, rollback |
| **security** | Auth, secrets, vulnerability scans, data exposure, secure defaults |
| **observability** | Logs, metrics, tracing, alarms, dashboards, operational signals |
| **data-pipeline** | Ingestion, schema drift, orchestration, dataset contracts, pipeline ops |
