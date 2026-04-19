---
description: Capture a trial-and-error discovery as a shared learning so any future LLM session goes directly to the happy path
---

# Capture Learning

Use this workflow after recovering from trial-and-error, discovering a non-obvious solution, or hitting a platform/toolchain gotcha. The output is a committed markdown file in `learnings/` that any LLM tool can consume.

## When to trigger

- You tried 2+ approaches before finding the correct one.
- A command, API, or config behaved unexpectedly.
- A platform-specific issue caused failures (OS, shell, path, permissions).
- A build/test/deploy step needed a non-obvious flag or order.

Do **not** capture trivial typos or one-off environment blips.

## Steps

### 1. Identify the learning

Summarize in one sentence what you just discovered. If you cannot state it clearly, the learning is not ready to capture yet.

### 2. Ensure the directory exists

If `learnings/` does not exist at the repo root, create it along with the `README.md` template:

```bash
mkdir -p learnings
```

Copy the README template from the toolkit's `learnings/README.md` or create one following the convention in `rules/error-driven-learning.md`.

### 3. Write the learning file

Create a new file in `learnings/` named with lowercase kebab-case summarizing the topic:

```
learnings/<topic>.md
```

Use this structure:

```markdown
---
title: Short descriptive title
category: environment | build | api | architecture | testing | toolchain | deployment
created: YYYY-MM-DD
tags: [relevant, searchable, terms]
---

# Problem
What was being attempted and what went wrong.

# Failed Approaches
What was tried and why it didn't work.
Include commands, error messages, or code snippets.

# Solution
The correct approach — the happy path.

# Why
Root cause explanation.
```

### 4. Quality check

Before saving, verify:

- [ ] Title is specific enough to match on a keyword scan.
- [ ] Failed approaches include concrete details (commands, errors), not just "it didn't work."
- [ ] Solution is copy-pasteable or directly actionable.
- [ ] Root cause is explained — not just "use X instead of Y" but **why**.
- [ ] File is 20–60 lines. If longer, split into multiple learnings.
- [ ] Tags cover the keywords a future LLM would search for.

### 5. Supplement tool-specific memory (optional)

If your LLM tool has built-in memory (Windsurf memories, Cursor context, etc.), also store a brief reference there pointing to the learning file:

> See `learnings/<topic>.md` for the full solution.

This gives faster retrieval within that tool while keeping the committed file as the shared source of truth.

### 6. User Approval Gate (MANDATORY)

**STOP and present the learning file content to the user for review.**

**Do NOT commit until the user explicitly approves.** If the user requests changes, revise the learning file and re-run the quality check. Skip this gate only if the user explicitly asked to skip approval.

### 7. Commit

Stage and commit the learning file. Use commit category 2 (Documentation) per `rules/git-conventions.md`:

```bash
git add learnings/<topic>.md
git commit -m "<TICKET-ID>: Add learning — <short description>"
```

If no ticket context exists, use a descriptive prefix:

```bash
git commit -m "docs: Add learning — <short description>"
```
