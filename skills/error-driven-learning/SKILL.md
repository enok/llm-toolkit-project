---
name: error-driven-learning
description: |
  ALWAYS-ON continuous learning discipline. Before starting ANY task, scan `learnings/`
  (especially `learnings/INDEX.md`) for prior discoveries. After ANY recovery from
  trial-and-error, a non-obvious fix, a platform/toolchain gotcha, or a repeated mistake,
  capture a new learning via the `capture-learning` workflow. This skill is baseline
  context for every session and every workflow — the user should NEVER have to ask for it.
license: MIT
metadata:
  author: llm-toolkit
  version: "1.0.0"
  always_on: true
---

# Error-Driven Learning (Always-On)

Every LLM session must produce **auto-improvement**: the agent consults past learnings before acting and captures new ones when trial-and-error led to a discovery. This is how subsequent interactions avoid repeating the same mistakes.

> This skill is **always on**. Do not wait for the user to mention learnings, `capture-learning`, or past discoveries. Apply this discipline automatically in every session.

## The Learning Loop

```
          ┌────────────────────────────────┐
          │  1. READ `learnings/INDEX.md`  │
          │     at session / task start    │
          └──────────────┬─────────────────┘
                         │
                         ▼
          ┌────────────────────────────────┐
          │  2. DO THE TASK                │
          │     (avoid known dead ends)    │
          └──────────────┬─────────────────┘
                         │
                         ▼
          ┌────────────────────────────────┐
          │  3. DID I HIT TRIAL-AND-ERROR? │
          │     (≥2 failed attempts /      │
          │     non-obvious fix / gotcha)  │
          └──────────────┬─────────────────┘
                         │ yes
                         ▼
          ┌────────────────────────────────┐
          │  4. CAPTURE via                │
          │     workflows/capture-learning │
          └────────────────────────────────┘
```

## Phase 1 — Consult Learnings (session / task start)

**Every new session and every non-trivial task:**

1. Read `learnings/INDEX.md` (fast scan, one line per learning).
2. Open any entry whose tags, title, or category overlap with the current task.
3. Follow the happy path documented there. Do not retry the failed approaches listed in those files.

If the task matches an existing learning exactly, say so to the user ("I found a prior learning at `learnings/<file>.md` that covers this — using its solution directly").

## Phase 2 — Work the Task

Proceed with the normal workflow. While working, keep a mental note of any of the following **capture triggers**:

| Trigger | Example |
|---|---|
| **2+ failed approaches** before success | Tried bash array, then jq, then finally yq — capture yq-only path |
| **Non-obvious fix** | Setting `AWS_SDK_LOAD_CONFIG=1` was required even though docs say otherwise |
| **Platform gotcha** | Junction on Windows needs `mklink /J`, not `ln -s` inside Git Bash |
| **Toolchain quirk** | awk -v truncates at newlines; must use ENVIRON lookup instead |
| **Repeated-mistake detection** | User had to correct the same assumption twice in one session |
| **API / config surprise** | Endpoint returns 403 without param X, even though docs only list Y |

Do **not** capture:

- Trivial typos.
- One-off environment blips that are not reproducible.
- Information already documented clearly in existing `learnings/` files.

## Phase 3 — Capture (task end or on trigger)

When a capture trigger fires, invoke `workflows/capture-learning.md`. Summary:

1. One-sentence problem statement.
2. Failed approaches with concrete commands / error messages.
3. Correct solution (copy-pasteable).
4. Root cause (*why* it works).
5. Tags for future keyword scan.
6. **User approval gate** before commit.
7. Commit + append to `learnings/INDEX.md`.

## Integration Points

Every workflow that acts on code, data, or infra MUST:

- Begin with: *"Consult `learnings/INDEX.md` for prior discoveries relevant to this task."*
- End with: *"If this session produced a new learning per the capture triggers above, run `capture-learning`."*

The main orchestration workflows (`project-execution-main.md`, `thesis-writing-main.md`, `review-and-fix.md`, `ticket-implementation.md`) enforce this bookend explicitly.

## Index Hygiene

`learnings/INDEX.md` is the fast-scan entry point. When you add a new learning file, also append one line to `INDEX.md`:

```markdown
- [`<file>.md`](./`<file>.md`) — <one-line summary> (`tag1`, `tag2`)
```

When a learning is superseded, mark its INDEX line as `~~strikethrough~~ (superseded by <new>.md)` rather than deleting — history matters.

## Why This Skill Is Always-On

The biggest failure mode of LLM-assisted development is **repeating the same mistakes across sessions** because no memory persists. The `learnings/` directory is the memory; this skill is the discipline that uses and grows it.

If the agent waits for the user to mention learnings, the loop breaks. So the rule is simple:

> **Session start → read `learnings/INDEX.md`. Session end → capture if a trigger fired. No exceptions. No prompting required.**

## Related

- `workflows/capture-learning.md` — step-by-step capture procedure
- `learnings/README.md` — file format and conventions
- `learnings/INDEX.md` — fast-scan index (keep current)
