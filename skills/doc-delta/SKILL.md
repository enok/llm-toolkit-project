---
name: doc-delta
description: Suggest or apply documentation updates from staged changes. Use after code changes when the user wants to "update docs," "document my changes," or keep README/config in sync.
---

# Documentation Delta (in-agent)

Suggest or apply documentation updates (e.g. README, config docs) based on the staged diff. You perform the analysis and edits using the IDE's LLM; no external CLI.

## When to Apply

- User says "update docs" or "document my changes"
- After adding or changing APIs, config, or behavior that should be documented
- User wants to keep README or `docs/` in sync with code

## Steps

1. **Get staged diff.** Use `git diff --cached` or Cursor's context over staged files to see what changed.
2. **Identify doc impact.** Determine which docs are affected (README, config docs, API docs, etc.) and what should be added or updated.
3. **Suggest or apply.** Using the IDE's LLM, propose concrete doc changes. If the user asked to apply, edit the files (e.g. README.md, `docs/`) to reflect the new behavior. If only suggesting, present the edits as a clear list or diff.
4. **Follow repo conventions.** Match the project's docs layout and style. Do not invent new sections or files unless the user asks.
5. **Ticket artifacts go to `docs/jira/<TICKET>/`.** When generating output files (reports, plans, etc.), write them to `docs/jira/<TICKET>/` — infer `<TICKET>` from the branch name or ask the user. Do not write to hidden/gitignored directories.

After running, the user can review and tweak.
