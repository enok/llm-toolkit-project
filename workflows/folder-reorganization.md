---
description: Reorganize a folder tree (renames, moves, archive) without breaking automations, scripts, documents, or cloud-sync links - inspect, propose, get approval, pause automations, execute, verify, resume, report
---

# Folder Reorganization Workflow

Use this when a folder tree must change shape and something reads it: scheduled
automations, scripts with relative paths, spreadsheets or documents that hold
paths, or cloud-sync links. The capability, scripts, and file formats are in
`skills/folder-reorganization/SKILL.md`; the proposal and ledger skeletons are
in `skills/folder-reorganization/references/proposal-template.md`.

Standing rules: nothing moves before approval; move and rename in place, never
copy and recreate; never delete (old material goes to `archive/`, deletions go
to `_to_delete/` for the owner to empty, and deleting needs the owner's
explicit ask); historical files are not rewritten.

## Orchestration

Route through `rules/request-orchestration.md` and
`tool-subagents/agent-orchestrator.md`. Print the wave-ordered task table with a
tier and explicit model per lane (light: haiku, standard: sonnet, deep: opus).
Typical split: inventory and scripted scans are `light`; consumer lanes,
proposal drafting, and execution are `standard`; a large or ambiguous tree may
need `deep` for the proposal. Inspection lanes are read-only and run in
parallel. The root owns every write, move, edit, and owner message. Keep the
ledger (`TASKS_TABLE.md`, `CONTEXT_STATE.md`) current after each wave.

## Phase 1 - LIST related automations

1. List every automation that reads or writes the tree (search the scheduling
   API by prompt text, attached folder, and name). This is read-only.
2. Pausing an automation is an external write. Pause now only when the owner's
   request explicitly asks for it. Otherwise leave them running, put the pause
   and its recovery record in the proposal, and pause right after approval,
   before preflight (Phase 5).
3. Whenever the pause happens, write the recovery record first: ID, enabled
   state before the pause, next run, attached folder, pause time. Then pause
   each one. Re-enable only in Phase 7.
4. If a pause is refused, do not work around it. Give the owner the exact
   settings action. See `workflows/automation-maintenance.md`.

## Phase 2 - INSPECT (read-only)

1. Inventory the tree with `reorg_scan.py inventory`: files, bytes, folders,
   ignoring client-managed files. Run it natively on the machine that owns the
   files. The meta folder (`--out-dir`, `--meta`) is created now; the tree
   itself stays read-only. Put the meta folder outside the root when the tree is
   synced or shared (the log holds the hostname and absolute paths, and backups
   hold file copies). Inside the root is acceptable for a private folder, and
   the scripts always skip it.
2. Reference-scan every consumer root with `reorg_scan.py refscan`. Cover all
   forms: absolute paths; relative paths and path pieces joined in code; mounted
   spellings that a remote shell sees (a mount root plus the folder name, drive
   letter versus POSIX form); cloud folder and file IDs and URLs in prompts,
   links, and pointer files; paths stored in spreadsheet cells and Office files;
   automation prompts and attached folders.
3. Mark historical hits with `--historical` (past reports, sent copies, run
   logs). They become "not rewritten" entries, each with a reason.
4. In a cloud-synced tree, note which folder and file IDs external links use.
   Keep that folder as the one you rename. Read the IDs through the cloud API
   when it is reachable.
5. Run lanes in parallel by consumer type. Each returns outcome, evidence,
   blockers, and decisions in at most 40 lines.

## Phase 3 - PROPOSE

1. Design the final tree, the naming convention, and where old material goes.
2. Write `pathmap.csv`, `edits.json` (edits plus a whitelist of files that may
   keep old paths, each with a reason), and the new prompt text for every
   automation that will be paused. Run `reorg_exec.py plan-check` against the inventory and
   fix collisions and missing parents.
3. Fill in `references/proposal-template.md`, including the pause step and its
   recovery record. Every number comes from the inventory and the scan.
4. Validate with an independent read-only lane (not the author): re-derive the
   consumer list from the reference scan and confirm each hit is edited,
   whitelisted with a reason, or listed as an owner action; recheck the counts.
   Loop per `workflows/task-quality-loop.md`.

## Phase 4 - STOP for approval

1. Send the full proposal as its own plain message. Send the approval question
   in a separate turn (`rules/external-write-authorization.md`). Offer defaults
   for each decision.
2. Do not move, edit, or pause anything until the owner approves this proposal
   (unless the request itself asked for the pause). Record the approval and the
   chosen options in the ledger.
3. A change after approval is re-proposed as a delta and approved again.

## Phase 5 - EXECUTE (resumable)

1. Pause the listed automations now, unless Phase 1 already did (recovery
   record first).
2. `reorg_exec.py preflight` (add `--strict-inventory` when the tree should be
   quiet). Fix every problem it reports. Run it only before `run` starts: after
   a partial run it reports missing sources and existing destinations by design.
3. `reorg_exec.py snapshot` writes the tree-before listing and the rollback
   script. `run` refuses to start without both files, on every OS.
4. `reorg_exec.py run` moves in order and stops at the first failure. Fix the
   cause and run `run` again; it skips ops already done. Do not re-run
   preflight. Use `--stop-after` to split long runs into waves.
5. `reorg_exec.py edits` overwrites files in place after planning every edit and
   verifying a backup per file. After an interruption, run it again; it skips
   edits already applied.
6. Update the ledger after each step. Run scripts natively on the machine that
   owns the files; through a bridge, move files with the transfer tools and
   write multi-line Python to a temp file.

## Phase 6 - VERIFY

1. `reorg_exec.py verify` and `tree-after`: every file at its mapped path with
   the same size, no old paths outside the whitelist. Ignore sync-client churn
   such as `desktop.ini`; explain any other byte or count delta exactly.
2. Run the live consumers against scratch outputs, not the real ones: each
   script, query, or prompt command that used the old paths, with output
   redirected to a temporary location. A grep alone does not prove a path
   resolves.
3. Confirm cloud folder and file IDs are unchanged through the cloud API when
   reachable.
4. On failure, fix forward or run `reorg_exec.py rollback`. Rollback restores
   edited files from their backups and overwrites any change made to them after
   the edit, so check those files first. If automations were already resumed,
   pause them again and revert their prompts to the old paths, then roll back.
   Resume them again once their old paths resolve.

## Phase 7 - RESUME automations

1. For each paused automation, update the prompt through the scheduling API
   with the new paths, then re-read it to confirm the change.
2. Settings the API cannot change (such as an attached folder) go to the owner
   with exact steps. If a permission check denies a fire, create or enable
   call, do not retry or work around it. Tell the owner the exact UI action.
   Retry once only if the owner then explicitly asks you to do that same
   action.
3. Re-enable an automation only when every path it uses resolves. For skipped
   runs, follow "Catch-up runs and overlapping sessions" in
   `workflows/automation-maintenance.md`.

## Phase 8 - REPORT

1. Report counts before and after, operation counts, edits, verification
   results, the rollback command, skipped runs, and items left for the owner.
2. Update external references that mention the old paths (docs, project notes,
   memory). Each is an external write: draft it and get an instruction first
   (`rules/external-write-authorization.md`).
3. Run `workflows/capture-learning.md` for any new gotcha.

## Known pitfalls

- Pause every related automation (right after approval, or earlier only when the owner asked) and write the recovery record before the first move; a task that fires during the move reads a half-built tree. (sig: coordination/automation-ran-during-folder-move)
- Rename the existing folder in place instead of creating a new one and moving contents out: a new folder is a new cloud ID and breaks every link to the old one. See `learnings/google-drive-desktop-folder-reorg.md`. (sig: wrong-assumption/new-folder-keeps-cloud-id)
- Scan for relative, mounted-path, and cloud-ID references as well as absolute paths; an absolute-only scan misses consumers that join path pieces in code. (sig: validation-gap/reference-scan-missed-relative-and-mounted-paths)
- Have a lane other than the proposal's author check the proposal against the reference scan before approval. (sig: validation-gap/proposal-not-checked-against-reference-scan)
- Show the full proposal as a plain message before the approval question; text placed before a question widget can be hidden. (sig: tool-misuse/approval-question-hid-proposal-text)
- Exclude client-managed files such as `desktop.ini` from before and after counts; the sync client creates and removes them during a move. (sig: validation-gap/verify-counted-sync-client-files)
- Prove a new path by running the consumer against scratch outputs, not by grep alone. (sig: validation-gap/path-update-checked-by-grep-only)
- Pass attached-folder changes to the owner and do not create a replacement task to get around a refusal. See `learnings/scheduled-task-attached-folder-rename.md`. (sig: safety-near-miss/worked-around-permission-denial)
- Check the run history before a catch-up fire and fire at most once; a run that ended FAILED on a usage limit appears to resume later and overlap (overlap observed, cause inferred). See `learnings/scheduled-run-resumes-after-usage-limit.md`. (sig: coordination/catch-up-overlaps-resumed-run)
- Run whole-tree scans natively on the machine that owns the files; a scan through a mount timed out. See `learnings/cloud-session-device-bridge-file-io.md`. (sig: env-constraint/whole-tree-scan-through-mount-timed-out)
