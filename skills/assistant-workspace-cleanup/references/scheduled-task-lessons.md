# Scheduled-task lessons

Detail behind `workflows/automation-maintenance.md`. Read when renaming a
folder a scheduled task uses, firing a catch-up, scheduling a deferred
follow-up, building chained tasks, or consolidating tasks.

## Attached folder rename

A computer-bound scheduled task has attached folders ("folders" in its
settings). A reorg that renames one can update the task prompt but not the
attachment.

- `update_trigger` has no folders field (only name, cron, enabled, model,
  prompt). Do not try computer use on the Claude desktop app: it does not
  resolve as a controllable app.
- Do not create a replacement task with the new folder while keeping the old
  one disabled: the auto-mode permission check refused it; re-enabling a task
  can be refused the same way. `fire_trigger` for a one-off catch-up was also
  refused once; a single retry after the owner explicitly asked to finish the
  pending tasks went through.
- Before the move: pause every task that reads the folder and write a pause
  record (id, enabled_before, next run, pause time) so any session can resume
  exactly those.
- When creating tasks, attach the folder's PARENT (or a stable root) so renames
  below it only need prompt edits; mount name = the folder's basename
  (`$HOME/mnt/<basename>`).
- After the move: update prompts with `update_trigger` (re-signed for the
  computer), then ask the user to change the attached folder in the task
  settings and toggle the task on.
- Keep a task paused while any path it uses is broken; record skipped runs and
  offer a one-off `fire_trigger` catch-up after checking the run history (see
  "Catch-up after a usage limit").
- Why: folder attachments are approved by the user on the device and are not
  editable through the scheduling API; enabling or creating device-bound tasks
  may need a human decision.

## Catch-up after a usage limit

Observed once: a daily scan task (one schedule only) skipped its normal run
while paused for a folder move; catch-ups were then fired by hand. The owner
got three digest emails and the run history showed more sessions than fires.

- The first catch-up ended FAILED with reason USAGE_LIMIT_REACHED after about
  9 minutes; a second, fired 2 hours later, ended the same way. The third,
  hours later, succeeded (22 minutes) but was not the only run that day.
- During the third run two other sessions of the same task also ran: one of
  about 41 minutes that started before the third fire, and one of about 1
  minute that saw the work already done and only sent a note.
- Most likely these were the FAILED catch-ups resuming once usage returned
  (inferred from timing, not confirmed). A run ending FAILED on a usage limit
  is therefore not necessarily dead, and the task cannot know about the other
  session unless its prompt checks for work already done today.
- The shared xlsx tracker survived because every write was guarded by the
  file's mtime: one write aborted with exit 3, the run re-read the file and
  redid the write. A read-only audit afterwards found no duplicate ids.
- Do not treat a catch-up that ended FAILED as finished, and do not keep
  firing catch-ups until one succeeds (that produced the overlap): fire a
  catch-up at most once.
- The remaining catch-up guidance in `workflows/automation-maintenance.md` › Catch-up runs and overlapping
  sessions (check run history first, single-run guard, audit shared files) is
  general guidance, not observed in this session.

## Many daily automations

Rule: `workflows/automation-maintenance.md` › Hygiene. Rationale: the usage limit is shared across the window, so a retry hits the same limit and small start-time nudges keep the same total work in it (observed with back-to-back digests plus a priority task).

## Deferred follow-ups

Rule: `workflows/automation-maintenance.md` › Deferred follow-ups. Rationale: deferred tools are invisible until searched, so "I can't" needs evidence; the stated check lets the user see the limit is real.

## Chained email-to-folder and workbook-update tasks

Split one flow that turns emailed documents into saved files and then workbook
rows into two tasks with a shared contract file. A single task that downloads,
parses and rewrites the workbook is hard to review. Splitting the writers gives
each a small blast radius.

- Ingest task: only the mail downloader. It removes mail-carried passwords,
  saves under the existing naming convention, emails the saved paths only when
  something new arrived, and uses a lookback window with slack plus a cutoff
  date for the first run. Dry-run the first run and list the files it expects to
  save.
- Update task: runs later, reads the saved files, changes the workbook
  additively (never regenerates), keeps a state file and a log, and ignores
  history before the cutoff.
- Update the prompt BEFORE enabling or first firing: editing it after enabling
  let the first firing run the old prompt and do nothing.
- Review findings: cells starting with `=`, `+`, `-` or `@` are prefixed so
  they stay text (formula injection). Connector write tools cannot be removed
  from a task, so the prompt carries an allow-list and pins the SHA-256 of every
  script it may run; re-pinning needs the owner's approval. No unattended
  deletes; unknown or generic routes go to quarantine; a poison-pill guard stops
  on `#REF`; regex limits; a spreadsheet-lock check before each commit.
- A first create may attach only one requested folder: recreate once and verify.
- Local-folder tasks run only while the computer is on with the app open; say
  so in the task description.
- Never put derived passwords, tax ids, biller names, personal ids or folder
  paths in the prompt; use an untracked local secrets file.

## Consolidation: pause only enabled repository writers

Rule: `workflows/automation-maintenance.md` › Hygiene. Rationale: the recorded list is the only way to restore the prior schedule state without side effects. A long-lived consolidation PR is the base for further harvests.

## Orphaned worktrees from parallel save requests

Rule: `workflows/automation-maintenance.md` › Unsaved-work sweep. Parallel "save learnings, then archive" requests leave orphaned drafts in separate worktrees and stuck in-progress ledger rows. Rationale: a main checkout parked on a feature branch mixes new work with old and hides what is on main.
