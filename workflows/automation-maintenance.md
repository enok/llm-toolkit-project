---
description: Safely inspect, rename, update, or delete scheduled LLM-tool automations while preserving schedule, status, prompt, and thread binding
---

# Automation Maintenance Workflow

Use this when a user asks to create, rename, update, inspect, pause, resume, or
delete a scheduled automation in an LLM tool (for example a Codex automation or
an equivalent scheduled task), asks for something to be done later and sent to
them (see "Deferred follow-ups"), or wants scheduled tasks inventoried and
tidied (see "Hygiene").

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
  scans natively on the computer. If the bridge shell shows Permission denied on
  folders or cannot delete git lock files, switch to the native shell instead of
  retrying. See learnings/cloud-session-device-bridge-file-io.md.

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

## Hygiene

Use when inventorying, consolidating, or tidying scheduled tasks.

- List completely: pass the completed filter (for example the trigger list
  tool's `include_completed` flag) or fired one-shots stay invisible. See
  learnings/scheduled-task-listing-hides-fired-one-shots.md.
- Delete fired one-shots only from an ID allow-list the owner approved; prefer
  one recurring task with an end condition over a chain of one-shots.
- Consolidate overlapping dailies into one task and pause (do not delete) the
  old ones until the new one has run well. See
  learnings/many-daily-automations-exhaust-usage-limits.md.
- Creation has no model field: ask the owner which model, or report the one the
  task actually got. See learnings/scheduled-task-create-cannot-set-model.md.
  A run-now call may be denied; do not work around it, tell the user to press
  Run now.
- A SUCCEEDED run lasting seconds for a job that needs real work is a finding:
  open the run session. See learnings/short-succeeded-run-is-not-evidence-of-work.md.
- Re-read live state before each change; an inventory snapshot goes stale. See
  learnings/inventory-snapshot-goes-stale-before-destructive-steps.md.
- Edit toolkit files in a separate worktree when the shared checkout is dirty.
  See learnings/dirty-shared-checkout-use-a-worktree.md.
- Before creating a digest or other recurring task, inventory the existing
  ones (names, pause state, delivery time) and present consolidate, resume, or
  new as a decision.
- Before a consolidation that writes to the shared repo, pause the scheduled
  writers (knowledge sync and any task that edits the repo or its ledger),
  record each task ID with its prior enabled state, and resume exactly those
  afterwards. Same record format as `workflows/folder-reorganization.md`
  steps 2-4; see `workflows/knowledge-base-sync.md` for the writer.
- Agent sessions are absent from chat-history tools; see
  learnings/chat-history-tools-exclude-agent-sessions.md. The full cleanup
  procedure is `workflows/assistant-workspace-cleanup.md`.

## Deferred follow-ups ("send me X when it is ready")

A request to do something later and deliver it is a one-shot scheduled task,
not a limitation (see `learnings/deferred-follow-up-declared-impossible.md`).

1. Check for an existing follow-up on the same subject first (Phases 1-3);
   update it instead of creating a duplicate.
2. Mechanism, strongest first, as confirmed by the session: a scheduled task
   that runs in a fresh session and notifies the user; a one-shot message back
   into this session when the work needs this conversation's context; a
   reminder on the user's device; otherwise tell the user when to come back.
3. Time the run after the publication window of what it waits for, in the
   user's timezone. Use the time the user named; ask once only if none was named.
4. Write the run prompt standalone: subject and date, every scope asked
   (including scope added later), source requirements, output language, and
   delivery channel. The run is read-only research plus a notification to the
   requester (`rules/external-write-authorization.md`).
5. Confirm only what the tool returned: name, time, approval mode, channel.
   See learnings/deferred-follow-up-declared-impossible.md.

## Chained automations

When one task consumes another's output:

- Keep a shared contract file (paths, naming, state keys the consumer may
  read) and stable names; update the contract and the consumer's routing
  together if a name changes.
- Stagger schedules so the producer runs first; the consumer never writes under
  the producer's folder.
- Write shared state with an expectedMtime guard and verify the sha256 after
  commit.
- Split ingest from consume: the ingest task alone downloads (silent when
  nothing is new; first-run dry run and a cutoff date); the consumer updates the
  workbook additively and never regenerates it. Update the prompt before the
  first firing, or that firing runs the old prompt. See
  learnings/chained-email-ingest-and-workbook-update-tasks.md and
  learnings/gmail-raw-for-attachments-plain-text-costs-tokens.md.
- After rebuilding a plan or document, audit every scheduled task that writes
  the same file and repoint or disable it; a stale generator overwrites the new
  version (learnings/scheduled-job-overwrites-newer-source-of-truth.md).
- A task bound to a local folder runs only while the computer and desktop app
  are on; say so in its description.

## Batch script run budgets

Scheduled scripts that process many items need caps, a per-item alarm, a global
budget strictly below the tool timeout, and a per-item error status with
bounded retries, or one slow item kills the daily run. See
learnings/scheduled-batch-scripts-need-time-budgets.md and
learnings/email-automation-sender-auth-and-link-allowlist.md. Resume on every
exit path: a run that stops early must leave state the next run continues from.

## Unsaved-work sweep

Use periodically, and before archiving chats: parallel "save learnings, then
archive" requests leave drafts in separate worktrees and in-progress ledger rows
(learnings/parallel-save-requests-leave-orphan-worktrees.md).

1. Run `python scripts/unsaved_work_sweep.py --root <repo-root> [--json]`; it
   is read-only.
2. Read each finding class: dirty worktrees, local branches with no remote,
   unpushed commits, untracked learnings, in-progress ledger rows, stale bundles
   in output folders.
3. The root presents the findings; it never auto-deletes or pushes
   (`rules/external-write-authorization.md`). Keep the main checkout off
   long-lived feature branches. See also
   learnings/dirty-shared-checkout-use-a-worktree.md.

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
