---
title: Creating a scheduled task cannot set its model, so it runs on the expensive default
category: toolchain
created: 2026-10-22
tags: [scheduled-task, create_trigger, update_trigger, model, cost, approval-gate, consolidation]
---

# Problem
Several daily tasks that ran on a cheaper model were consolidated into one new task. The
creation call has no model field, so the new task ran on the server default (a more
expensive model), and the "saving" raised the cost per run.

# Failed Approaches
- Looking for a model parameter on the create call: it accepts name, schedule, prompt and
  similar fields, but no model.
- Writing "use the small model" in the task prompt: the prompt cannot select the model the
  run is billed on.
- Assuming the new task inherits the model of the tasks it replaces or of the current session.
- Silently fixing it afterwards with `update_trigger`: the update call can change the model,
  but changing a user's model choice is a configuration change that needs their explicit
  request.

# Solution
- Put the model in the plan: record each replaced task's model, and name the model the new
  task will get by default.
- Ask inside the approval gate before creating: "this task will run on the default model;
  switch it to <model>?" Apply the answer with `update_trigger` (model only) right after
  creation.
- Read the task back after creation and confirm the `model` field before reporting done.

# Report the model the task got

- After creation, state the model the task actually received, not the one planned.
- Triggering an immediate run of the new task can be denied by the auto-mode classifier.
  Do not work around the denial; tell the owner to press "Run now" in the app.
- Folders attached at creation cannot be changed through the update call. To change them,
  recreate the task once, then read back schedule, enabled flag, connectors and prompt to
  confirm nothing was lost. See `learnings/scheduled-task-attached-folder-rename.md`.

# Why
Creation fills platform defaults for fields it does not expose, while update exposes the
model. The gap is invisible unless the saved task is read back, and the cost impact only
shows later on the usage page.
