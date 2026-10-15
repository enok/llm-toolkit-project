---
title: Renaming a folder that a computer-bound scheduled task has attached
category: deployment
created: 2026-10-15
tags: [scheduled-task, trigger, update_trigger, attached-folder, cowork, folder-rename, pause, resume]
---

# Problem
A folder reorg renamed a folder that a computer-bound Claude scheduled task had attached
("folders" in its settings). The task prompt could be updated, but the attachment could not.

# Failed Approaches
- `update_trigger`: has no folders field; only name, cron, enabled, model, prompt.
- Computer use on the Claude desktop app: the app does not resolve as a controllable app.
- Creating a replacement task with the new folder (keeping the old one disabled):
  refused by the auto-mode permission check; re-enabling a task can be refused the same way.

# Solution
- Before the move: pause every task that reads the folder and write a pause record
  (id, enabled_before, next run, pause time) so any session can resume exactly those.
- Attach the folder's PARENT (or a stable root) when creating tasks, so renames below it
  only need prompt edits; mount name = the folder's basename (`$HOME/mnt/<basename>`).
- After the move: update prompts with `update_trigger` (re-signed for the computer), then ask
  the user to change the attached folder in the task settings and toggle the task on.
- Keep a task paused while any path it uses is broken; record skipped runs and offer a
  one-off `fire_trigger` catch-up.

# Why
Folder attachments are approved by the user on the device and are not editable through the
scheduling API; enabling or creating device-bound tasks may need a human decision.
