---
description: Inventory, classify, approve, execute, and verify a cleanup of an AI-assistant workspace (chats, agent sessions, projects, scheduled tasks, artifacts, orchestration ledgers) with a reversibility-grouped approval gate, ID allow-listed lanes, and live-state verification
---

# Assistant Workspace Cleanup Workflow

Use this when asked to clean up, review, archive, delete, pause, or consolidate chats, agent sessions, projects,
scheduled tasks, or artifacts ("tidy my workspace", "delete the fired one-shots", "merge my daily tasks").

The procedure (five waves: inventory, classify, approval gate, execute, verify) and the safety contract live in
`skills/assistant-workspace-cleanup/SKILL.md`. Follow it. Its references hold the rest:

- `skills/assistant-workspace-cleanup/references/claude-surfaces.md` - where each item type lives and its gotchas
- `skills/assistant-workspace-cleanup/references/classification-rubric.md` - row actions, keep-rules, approval groups
- `skills/assistant-workspace-cleanup/references/lane-prompts.md` - lane prompts L1-L9

Nothing changes before the owner approves that group. Not for editing one scheduled task
(`workflows/automation-maintenance.md`).
