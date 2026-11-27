---
name: error-driven-learning
description: |
  ALWAYS-ON continuous learning discipline. Before starting ANY task, follow the owning
  assets' known pitfalls and scan `learnings/INDEX.md` for pending intake items. After ANY
  recovery from trial-and-error, a non-obvious fix, a platform/toolchain gotcha, or a
  repeated mistake, write the lesson into the skill, rule or workflow that owns it via the
  `capture-learning` workflow. This skill is baseline context for every session and every
  workflow — the user should NEVER have to ask for it.
license: MIT
metadata:
  author: llm-toolkit
  version: "1.0.0"
  always_on: true
---

# Error-Driven Learning (Always-On)

Every LLM session must produce **auto-improvement**: the agent consults past lessons before acting and records new ones in the asset that owns them when trial-and-error led to a discovery. This is how subsequent interactions avoid repeating the same mistakes.

> This skill is **always on**. Do not wait for the user to mention learnings, `capture-learning`, or past discoveries. Apply this discipline automatically in every session.

## The Learning Loop

```
          ┌────────────────────────────────┐
          │  1. READ owner known pitfalls  │
          │     + `learnings/INDEX.md`     │
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

1. Read the `## Known pitfalls` (and references) of the skills, rules and workflows the task uses: migrated lessons live there.
2. Read `learnings/INDEX.md`: it lists only pending intake items (normally none). Open any entry whose tags, title, or category overlap with the current task.
3. Follow the happy path documented there. Do not retry the failed approaches listed.

If the task matches a recorded lesson exactly, say so to the user and name the asset that holds it.

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
- Information already documented clearly in the owning asset or a pending intake item.

## Phase 3 — Capture (task end or on trigger)

When a capture trigger fires, invoke `workflows/capture-learning.md`. Summary:

1. One-sentence problem statement, failed approaches, correct solution, root cause.
2. **Owner clear (preferred):** write the lesson into the owning asset — a skill `## Known pitfalls` bullet or reference, one workflow bullet, or one rule line. No learning file.
3. **Owner unclear:** capture an intake file `learnings/<kebab-topic>.md` plus its `learnings/INDEX.md` line. It is migrated into its owner and deleted, with its INDEX line, in the change that migrates it — at the latest in the next toolkit maintenance pass.
4. **User approval gate** before commit.
5. Never reference `learnings/<slug>.md` for a file that does not exist; `tests/test_learning_promotion_coverage.py` fails on a dangling reference or a missing INDEX line.

## Integration Points

Every workflow that acts on code, data, or infra MUST:

- Begin with: *"Consult the owning assets' known pitfalls and `learnings/INDEX.md` for prior discoveries relevant to this task."*
- End with: *"If this session produced a new learning per the capture triggers above, run `capture-learning`."*

The main orchestration workflows (`project-execution-main.md`, `thesis-writing-main.md`, `ticket-implementation.md`) enforce this bookend explicitly.

## Index Hygiene

`learnings/INDEX.md` lists pending intake items only. When you capture an intake file, append one line to `INDEX.md` in the same change:

```markdown
- [`<file>.md`](./<file>.md) — <one-line summary> (`tag1`, `tag2`)
```

When the item is migrated into its owner, delete the file and its INDEX line in that change. Git history keeps the record.

## Why This Skill Is Always-On

The biggest failure mode of LLM-assisted development is **repeating the same mistakes across sessions** because no memory persists. The owning skills, rules and workflows are the memory (`learnings/` is only their short-lived intake); this skill is the discipline that uses and grows it.

If the agent waits for the user to mention learnings, the loop breaks. So the rule is simple:

> **Session start → read the owners' known pitfalls and `learnings/INDEX.md`. Session end → capture into the owner if a trigger fired. No exceptions. No prompting required.**

## Related

- `workflows/capture-learning.md` — step-by-step capture procedure
- `learnings/README.md` — intake file format and conventions
- `learnings/INDEX.md` — pending intake items (normally none)
