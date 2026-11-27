---
description: Write a trial-and-error discovery into the skill, rule or workflow that owns it, or capture a short-lived `learnings/` intake item when the owner is unclear
---

# Capture Learning

Use this workflow after recovering from trial-and-error, discovering a non-obvious solution, or hitting a platform/toolchain gotcha. The preferred output is the lesson written into the asset that owns it, so the next session meets it where it works. A file in `learnings/` is only a short-lived intake for a lesson whose owner is not yet clear; it is migrated and deleted.

> This workflow is invoked automatically by the always-on `error-driven-learning` skill (see `skills/error-driven-learning/SKILL.md` and `rules/error-driven-learning.md`). Trigger conditions are listed there — the agent should not wait for the user to ask.

## When to trigger

- You tried 2+ approaches before finding the correct one.
- A command, API, or config behaved unexpectedly.
- A platform-specific issue caused failures (OS, shell, path, permissions).
- A build/test/deploy step needed a non-obvious flag or order.

Do **not** capture trivial typos or one-off environment blips.

## Steps

### 1. Identify the learning

Summarize in one sentence what you just discovered. If you cannot state it clearly, the learning is not ready to capture yet.

### 2. Find the owner

Name the skill, rule, workflow, agent, script or test whose work the lesson changes (`python3 scripts/kb.py search` helps). If the owner is clear, go to step 3. Only if it is not, go to step 4.

### 3. Write it into the owner (preferred)

Add the smallest form that carries the lesson, and create no learning file:

- a skill: one `## Known pitfalls` bullet, or a section in one of its `references/` files when the lesson needs detail;
- a workflow: one `## Known pitfalls` bullet (`rules/workflow-authoring.md`);
- a rule: one line;
- a script or test: the fix plus a regression test.

A bullet is imperative, states the happy path and why, and ends with `(sig: <signature>)` when the run log has one. Then go to step 5.

### 4. Capture an intake file (owner unclear)

Create `learnings/<kebab-topic>.md` (lowercase kebab-case summarizing the topic). If `learnings/` does not exist, create it with the `README.md` template from the toolkit's `learnings/README.md`. Use this structure:

```markdown
---
title: Short descriptive title
category: environment | build | api | architecture | testing | toolchain | deployment | security | data-pipeline
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

Add one line to `learnings/INDEX.md` under `## Pending intake`, in the same change:

```markdown
- [`<file>.md`](./<file>.md) — <one-line summary> (`tag1`, `tag2`, `tag3`).
```

### 5. Quality check

Before saving, verify:

- [ ] The happy path is specific enough to match on a keyword scan (title and tags for an intake file).
- [ ] Failed approaches include concrete details (commands, errors), not just "it didn't work."
- [ ] Solution is copy-pasteable or directly actionable.
- [ ] Root cause is explained — not just "use X instead of Y" but **why**.
- [ ] An owner bullet is one or two sentences; an intake file is 20–60 lines (split it if longer).
- [ ] Every statement is a recorded fact: guidance that was not tried in the session is labelled as such (for example "General guidance, not observed in this session"), and no failed approach is invented.
- [ ] No ticket IDs, customer names, hostnames or credentials.
- [ ] No reference to `learnings/<slug>.md` for a file that does not exist (`tests/test_learning_promotion_coverage.py`).

### 6. Supplement tool-specific memory (optional)

If your LLM tool has built-in memory, store a brief pointer to the owning asset (or the intake file) there. The committed asset stays the shared source of truth.

### 7. User Approval Gate (MANDATORY)

**STOP and present the change (owner edit or intake file) to the user for review.**

**Do NOT commit until the user explicitly approves.** If the user requests changes, revise and re-run the quality check. Skip this gate only if the user explicitly asked to skip approval.

### 8. Commit

Use the Documentation commit category from `rules/git-conventions.md`:

```bash
git add <owning-asset-path>            # or: learnings/<topic>.md learnings/INDEX.md
git commit -m "<TICKET-ID>: Add learning — <short description>"
```

If no ticket context exists, use a descriptive prefix:

```bash
git commit -m "docs: Add learning — <short description>"
```

### 9. Migrate intake items

An intake file is migrated into its owner (step 3) and deleted, together with its `learnings/INDEX.md` line, in the change that migrates it — at the latest in the next toolkit maintenance pass. A migrated learning never keeps its file, and nothing may keep linking it. If an item cannot be migrated safely yet, leave it pending and report the blocker.

## Known pitfalls

- Cite only facts recorded in the session and label untested guidance as such (for example "General guidance, not observed in this session"); never present untested behaviour as observed, and when the record states no failed approach, write "None recorded beyond the first attempt described in Problem." instead of inventing one. (sig: quality-defect/unobserved-claims-presented-as-fact)

---

## Final Step — Self-improvement

Run the per-run retrospective (`workflows/run-retrospective.md`) before closing this workflow.
