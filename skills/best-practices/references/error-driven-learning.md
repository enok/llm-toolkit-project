# Error-Driven Learning

When an LLM finds the correct solution after trial-and-error, that knowledge must be captured so that any future LLM session — regardless of tool — goes directly to the happy path.

## When to capture

Capture a learning when:

- You tried two or more approaches before finding the one that works.
- A command, API call, or configuration behaved differently than expected.
- A platform-specific gotcha caused a failure (Windows vs Unix, shell differences, path handling).
- A build, test, or deploy step required a non-obvious flag, order, or workaround.
- An integration between components required specific wiring that was not obvious from the code alone.

Do **not** capture trivial typos, one-off user misunderstandings, or temporary environment blips.

## Where learnings live

Each repository keeps a `learnings/` directory at the root. Files inside are plain markdown with YAML frontmatter. The directory is committed to version control so every LLM tool and every developer benefits.

```
learnings/
  README.md              # Convention docs and template
  windows-symlinks.md    # Example learning
  sam-build-docker.md    # Example learning
```

**Consuming projects** (repos that junction from `llm-toolkit-project`) have **two** learnings locations:

| Path | Contents |
|---|---|
| `learnings/` | Project-specific discoveries — committed in the consuming repo |
| `docs/llm-toolkit-learnings/` | Shared toolkit discoveries — junction to `llm-toolkit-project/learnings/` |

Always check **both** before starting a task. The toolkit learnings cover cross-project patterns (API auth, junction architecture, skill loading) that apply to any consuming project.

## File format

```markdown
---
title: Short descriptive title
category: environment | build | api | architecture | testing | toolchain | deployment
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

1. Scan filenames and tags for topic overlap with the current task.
2. Read matching files before planning your approach.
3. Prefer the documented solution over re-discovering it from scratch.

If the repository does not have a `learnings/` directory yet, create one (with `README.md`) the first time you capture a learning.

## How to write

Follow the `capture-learning` workflow. Key principles:

- **One file per learning.** Keep each focused on a single problem–solution pair.
- **Name files descriptively.** Use lowercase kebab-case that summarizes the topic: `maven-windows-sh-plugin.md`, `dynamodb-batch-limit.md`.
- **Include failed approaches.** This is what prevents future LLMs from repeating the same mistakes.
- **Include the root cause.** A solution without explanation is fragile — it breaks the moment conditions change.
- **Keep it concise.** A learning is not a tutorial. Target 20–60 lines.

## Tool-specific memory is supplementary

Some LLM tools have built-in memory (Windsurf memories, Cursor context, etc.). Use those too — they provide faster retrieval within that tool. But the committed `learnings/` file is the **source of truth** because it works across all tools, survives tool migrations, and is code-reviewable.

When using tool-specific memory, reference the learning file:
> See `learnings/windows-symlinks.md` for details.

## Categories

| Category | Covers |
|---|---|
| **environment** | OS, shell, permissions, auth, path handling, locale |
| **build** | Compilation, packaging, dependencies, plugins, flags |
| **api** | SDK usage, method signatures, request/response, rate limits |
| **architecture** | Component wiring, data flow, service dependencies |
| **testing** | Test setup, fixtures, mocking, assertion patterns |
| **toolchain** | CLI tools, IDE config, linters, formatters |
| **deployment** | Deploy process, infra, config, rollback |
