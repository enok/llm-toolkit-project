---
title: Folder reorganization proposal and resume ledger templates
tags: [folder-reorganization, proposal, approval, ledger, resume, templates]
---

# Proposal and ledger templates

Two skeletons. The proposal is what the owner approves. The ledger lets any
session resume after a context reset or a credit stop.

Present the proposal as its own plain message, complete, with no summary
standing in for it. Ask the approval question in a separate turn
(`rules/external-write-authorization.md`). Every number comes from the
inventory and reference scan, not from memory.

## 1. Proposal skeleton

````markdown
# Reorganization proposal: <root name>

Status: PROPOSED. Nothing has been moved or edited.

## 1. Final tree (two levels)

<root>/
  <folder>/            <what lives here, file count>
    <subfolder>/       <file count>
  archive/             <old material, kept>
  _to_delete/          <for the owner to empty; the run never deletes>
  _meta/               <only if the meta folder is inside the root: ledger, logs, rollback script>

Naming convention: <case, separators, date format, ordering prefixes>.

## 2. Numbers

| Measure | Before | After |
| --- | --- | --- |
| Files | <n> | <n> (must be equal) |
| Bytes | <n> | <n> (must be equal) |
| Folders | <n> | <n> |

Operations: <n> mkdir, <n> rename, <n> move, <n> to archive, <n> to
`_to_delete`, 0 deletes. Client-managed files (for example `desktop.ini`) are
excluded from both counts.

## 3. Renames and moves

| Old path | New path | Operation | Why |
| --- | --- | --- | --- |

Group by top-level folder. The full path map is `<meta>/<pathmap file>`.

## 4. References updated

| File | Line(s) | Old | New |
| --- | --- | --- | --- |

One row per edit. Source: the reference scan (absolute, relative, mounted-path,
and cloud-ID references). Edits are made in place with a backup per file.

## 5. Not rewritten, and why

| File or pattern | Reason (for example historical record, sent copy, run log) |
| --- | --- |

## 6. Automations

| Task | Prompt change (old -> new) | Setting only the owner can change | State before pause |
| --- | --- | --- | --- |

Pausing is an external write. These tasks are paused right after you approve
this proposal, before preflight (earlier only if you asked for that), and each
task's state is recorded first so it can be restored exactly. Prompts are
updated through the scheduling API after the move. Settings the API cannot
change (such as an attached folder) are listed for the owner with the exact
steps. A task stays paused until every path it uses resolves.

## 7. How it will run

- Order: approval, pause automations (recovery record), preflight, snapshot, run,
  edits, verify, resume automations.
- Who runs what, where (natively on the machine that owns the files), and the
  time estimate. Anything over 30 minutes is split into waves.
- Rollback: `<meta>/<tag>-rollback.ps1` is written before the first move. A
  failure stops the run at that operation; re-running `run` resumes it. Rollback
  restores edited files from their backups, so check those files first.
- Verification: every file at its mapped path with the same size, no old paths
  outside section 5, the live scripts run against scratch outputs, cloud IDs
  confirmed if the API is reachable.

## 8. Decisions for the owner

| # | Question | Options | Default if no answer |
| --- | --- | --- | --- |

## 9. Information only

- <Items that need no decision: counts, risks accepted, things left as they are.>
````

## 2. Ledger skeleton

Keep both files under the meta folder (`--meta`; outside the root when the tree
is synced or shared). Copy the table to the working project root when the
orchestrator keeps its ledger there. The root agent owns every write.
Update them after each wave, not only at the end.

````markdown
# TASKS_TABLE.md

| # | Wave | Task | Tier / model | Status | Evidence | Next |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0 | List dependent automations (read-only; pause now only if the owner asked) | light / haiku | todo | | |
| 2 | 1 | Inventory + reference scan (read-only lanes) | standard / sonnet | todo | | |
| 3 | 2 | Proposal (includes the pause) + independent validation against the scan | standard / sonnet | todo | | |
| 4 | 3 | Owner approval (own message, question in a separate turn) | root | todo | | |
| 5 | 4 | Pause automations, write recovery record (right after approval) | light / haiku | todo | | |
| 6 | 4 | preflight, snapshot, run, edits | standard / sonnet | todo | | |
| 7 | 5 | verify + live-consumer checks | standard / sonnet | todo | | |
| 8 | 6 | Update prompts, hand settings to the owner, resume automations | standard / sonnet | todo | | |
| 9 | 7 | Report, external references, capture learning | standard / sonnet | todo | | |

Status values: todo, running, done, blocked, breached (kept in the table).

# CONTEXT_STATE.md

## Goal
<one sentence> Root: <path>. Meta: <path>. Tag: <tag>.

## Approval
Approved: <yes/no>, by <owner>, at <time>. Approved proposal file: <path>.
Decisions taken: <list with the chosen option>.

## Paused automations (recovery record)
| Task id / name | Enabled before pause | Next run | Paused at | Prompt updated | Owner action done | Resumed |
| --- | --- | --- | --- | --- | --- | --- |

## Inputs
Inventory: <path>. Path map: <path>. Edits: <path>. Reference scan: <path>.

## Progress
Last completed operation id: <id>. Edits done: <n of n>. Verify: <pass/fail, file>.

## Resume instructions
1. Read this file and the run logs under `<meta>`.
2. If `run` has not started, run `reorg_exec.py preflight`. Once `run` has
   started, do not re-run preflight: after a partial run it reports missing
   sources and existing destinations by design. Re-run `run` (it skips ops
   already done), then `edits` (it skips edits already applied).
3. Do not re-pause or re-resume a task already marked in the table above.
4. To undo: `<meta>/<tag>-rollback.ps1` (Windows) or `reorg_exec.py rollback`.
   Rollback overwrites later changes to edited files; check them first.

## Open decisions and lanes in flight
<list>
````
