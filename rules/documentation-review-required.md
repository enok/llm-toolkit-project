---
trigger: always_on
description: Require specialist review for documentation created or changed by agents, chats, automations, scripts, or humans
---

# Documentation Review Required

When a task creates or changes documentation, route the documentation through
`documentation-reviewer` (`tool-subagents/documentation-reviewer.md`) before
treating the work as complete.

Documentation includes README files, runbooks, architecture docs, generated LLM
or client surfaces, PR bodies, release notes, changelogs, Confluence/wiki
content, API docs, diagrams, screenshots, PDFs, rendered documents, and
human-facing documentation replies.

The reviewer must check source-grounded accuracy, audience fit, structure,
claim drift across code/tests/docs/PRs/comments/generated surfaces, and required
artifact quality gates. Human-facing replies remain draft-only until the user
approves the exact text and target.

The root agent owns edits, validation, commits, pushes, PR actions, and final
reporting.
