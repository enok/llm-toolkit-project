---
description: Safely inspect, rename, update, or delete scheduled LLM-tool automations while preserving schedule, status, prompt, and thread binding
---

# Automation Maintenance Workflow

Use this when a user asks to create, rename, update, inspect, pause, resume, or
delete a scheduled automation in an LLM tool (for example a Codex automation or
an equivalent scheduled task).

For automations bound to a specific ticket after implementation is solved,
compose this workflow with `workflows/ticket-pr-validation-loop.md` so the
automation preserves its schedule/thread binding while the run logic validates
the ticket, PR comments, fixes, and CI/CD on the current head.

## Phase 1 - Identify the existing automation

1. Prefer the automation API for view/update/delete operations.
2. If the user refers to "this chat" or "same name as this chat", resolve the
   current thread name from the local session index before choosing a name.
3. Search existing automation records by ID, name, prompt, target thread, and
   schedule before creating a new automation.
4. Prefer updating the matching automation over creating a duplicate.

## Phase 2 - Preserve fields

When updating an existing automation, preserve every field the user did not ask
to change:

- kind and destination;
- schedule;
- status;
- model and reasoning effort;
- prompt;
- target thread;
- workspace and execution environment.

Do not hand-edit automation config files as the primary path. Use direct file
inspection only to identify the correct automation when the API does not expose
enough search context.

## Phase 3 - Mutate and verify

1. Use the automation API update/delete/create operation.
2. Re-read the saved automation after mutation.
3. Verify the intended fields changed and preserved fields stayed unchanged.
4. Report the automation ID, schedule, status, thread binding, and any changed
   fields.

## Moving folders that automations use

When a folder that an automation reads or writes is renamed, moved, or
reorganized:

- Before the first move, pause every automation that touches the folder (an
  external write: right after the owner approves the plan, or earlier only when
  the owner asked) and write a recovery record (ID, enabled state before the
  pause, next run, pause time) so any session can re-enable exactly those; re-enable an automation only
  once every path it uses resolves. An attached folder is not editable through
  the scheduling API: update the prompt through the API, then have the user
  switch the attached folder in the task settings and re-enable it; prefer
  attaching a stable parent folder. See learnings/scheduled-task-attached-folder-rename.md.
- In a cloud-synced folder (for example Google Drive for desktop), rename and
  move in place so file and folder IDs survive, overwrite edited files in place,
  move (never re-create) pointer files, and ignore client-managed `desktop.ini`
  files when verifying counts. See learnings/google-drive-desktop-folder-reorg.md.
- When the files live on the user's computer and the session reaches them
  through a device bridge, move files with the file-transfer tools (never large
  pasted base64), refresh mounted files with `cat new > old`, and run whole-tree
  scans natively on the computer. See learnings/cloud-session-device-bridge-file-io.md.

For the full reorganization procedure (inspect, propose, approve, execute,
verify, resume) use `workflows/folder-reorganization.md`.

## Catch-up runs and overlapping sessions

A run the scheduler marks FAILED with a usage-limit reason may resume on its
own once usage returns (an observed overlap whose cause was inferred from
timing, not confirmed). A hand-fired catch-up can then run beside it. See
learnings/scheduled-run-resumes-after-usage-limit.md.

- Before a catch-up, read the task's run history and `last_run`. Prefer the
  next scheduled run when the skipped run is not time-critical.
- Fire at most once. Put a catch-up note in the fire text: what the earlier
  attempts did, that this run starts from scratch, and that it must check for a
  run already done today.
- Recommended: add a single-run guard to every scheduled prompt: at the start, detect a run
  already done or in progress today (for example the digest already sent, a
  state marker, freshly modified files), then send a one-line note and stop.
- After a suspected overlap, run a read-only integrity audit of the shared
  files (duplicate ids, contradictory states) before trusting them. Write
  shared files only with an mtime guard; if the mtime changed, re-read and redo.
- If a permission check denies a fire, create or enable call, do not retry or
  work around it (no replacement task, no other tool). Tell the owner the exact
  UI action (Run now, or the task's settings). Retry once only if the owner then
  explicitly asks you to do that same action. See
  learnings/scheduled-task-attached-folder-rename.md.

## Failure handling

- If the requested automation cannot be uniquely identified, ask one concise
  clarifying question or list the conflicting candidates.
- If the API rejects the update, report the rejected field and leave the existing
  automation untouched.
- If a recurring task is obsolete, delete it and tell the user why the heartbeat
  stopped.

## Final Step - Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before
closing this workflow.
