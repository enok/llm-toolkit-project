---
name: folder-reorganization
description: Use when reorganizing a folder tree (renames, moves, archiving old material) without breaking what reads it - scheduled automations, scripts with relative paths, spreadsheets or documents that hold paths, and cloud-sync links. Approval-first proposal, path map and edits plan, resumable scripted execution with a rollback script, and verification against the live consumers.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.0.0"
---

# Folder reorganization

Restructure a folder tree and keep everything that reads it working. The tree is
the easy part. The risk is in the consumers: scheduled automations with folder
names in their prompts or attachments, scripts with relative paths, spreadsheets
and documents that store paths, and cloud-sync links that depend on file and
folder IDs.

- Run procedure (phases, gates, lanes): `workflows/folder-reorganization.md`.
- Approval proposal and resume ledger skeletons: `references/proposal-template.md`.
- File formats, options, and a worked example for the scripts: `references/data-formats.md`.
- Automation pause and resume details: `workflows/automation-maintenance.md`.

## Contract

1. **Nothing moves before approval.** Show the full proposal as its own plain
   message, then ask the question in a separate turn
   (`rules/external-write-authorization.md`). Read-only inspection, scans, and
   writing the proposal files are allowed before approval. Pausing automations
   is an external write, so it also waits for approval unless the owner's
   request explicitly asks for it.
2. **Move and rename in place. Never copy and recreate.** A same-volume move
   keeps cloud file IDs, folder IDs, and links. A new folder or a re-created
   file is a new object with a new ID and breaks every link to the old one.
3. **Never delete.** Old material goes to `archive/`. Things that should go
   away go to `_to_delete/` for the owner to empty. Deleting needs the owner's
   explicit ask.
4. **Historical files are not rewritten.** Past reports, sent-mail copies, run
   logs, and old digests record what was true then. List them in the proposal as
   not rewritten, with the reason.
5. **Resumable ledger, logs, and rollback.** Keep state in a meta folder
   (`--meta`). Put it outside the root when the tree is synced or shared: the
   log holds the hostname and absolute paths, and the backups hold file copies.
   `<root>/_meta` is acceptable for a private folder, and the scripts always
   skip it. The folder is created at inspection time (the inventory writes
   there); the tree itself stays read-only. Write the rollback script before
   any move. A context reset or a credit stop must be resumable from the ledger
   alone.
6. **Decide the naming convention in the proposal** (case, separators, date
   format, ordering prefixes) and apply it uniformly. Do not improvise names
   during execution.
7. **Find every consumer before proposing.** List the related automations
   (read-only), then scan for absolute, relative, mounted-path, and cloud-ID
   references. Pause the automations right after approval, before the first
   move; pause earlier only when the owner's request explicitly asks for it.
   A consumer found after the move is a defect.
8. **Edits overwrite in place** and are planned in full, with a backup per file,
   before the first write.

## When to use

- The user asks to reorganize, restructure, clean up, rename, or archive a
  folder tree that automations, scripts, or documents depend on.
- A cloud-synced folder (for example Google Drive for desktop) must change shape
  while external links keep working.

Skip it for a single file rename with no consumers, or a tree nothing reads.

## Process at a glance

LIST automations (read-only), INSPECT (inventory, reference scan, parallel
read-only lanes), PROPOSE (tree, path map, edits, the pause with its recovery
record, new automation prompts, independent validation against the scan), STOP
for approval, EXECUTE (pause automations, preflight, snapshot, run, edits),
VERIFY (including the live consumers), RESUME automations, REPORT. Details and gates: `workflows/folder-reorganization.md`.

## Scripts

Both scripts need Python 3.9 or newer and the standard library only. Run them
with the platform's launcher (`python`, `python3`, or `py -3`). Folders and files
are moved with `os.rename` on one volume; `run` never deletes anything. Exit
codes: 0 ok, 1 problem or failure, 2 usage error. Every option, every file
format, and a worked example are in `references/data-formats.md`.

| Command | Purpose |
| --- | --- |
| `reorg_scan.py inventory` (`--root --out-dir --label`, `--ignore`, `--skip-dir`) | Write `<label>-inventory.tsv` (path, bytes, mtime per file) and `<label>-area-totals.tsv` (files and bytes per top-level folder); run it before and after |
| `reorg_scan.py refscan` (`--root`, `--pathmap` and/or `--pattern`, `--out`, `--historical`, `--ignore`, `--skip-dir`) | Write a TSV of every text line and Office XML member that mentions an old path; hits in `--historical` files are classed historical |
| `reorg_exec.py plan-check` | Simulate the path map against the inventory: collisions, missing sources or parents, totals per top-level folder |
| `reorg_exec.py preflight` | Read-only check against the real tree: sources, destinations, locks, path length, inventory drift, and a dry run of every edit |
| `reorg_exec.py snapshot` | Write `<tag>-tree-before.txt` and the `<tag>-rollback.ps1` script under `--meta` (pass `--edits` so the script restores edited files) |
| `reorg_exec.py run` | Execute the path map in order; resumable; stops at the first failure; refuses to start without the snapshot files; `--stop-after OP` runs part of it |
| `reorg_exec.py edits` | Plan every edit, verify backups, then overwrite files in place; resumable |
| `reorg_exec.py verify` | Compare inventory with the final tree (sizes, xlsx deep check) and scan for old paths outside the whitelist |
| `reorg_exec.py tree-after` | Write the tree-after listing |
| `reorg_exec.py rollback` | Restore edited files from backups, then reverse the moves; `--prune-empty` removes the directories mkdir ops created, when empty |

`run` requires the snapshot files on every OS: `<tag>-tree-before.txt` and
`<tag>-rollback.ps1` (the `.ps1` is written on Linux and macOS too, but only
`pwsh` can run it). On Linux and macOS roll back with `reorg_exec.py rollback`.
Once `run` has started, do not re-run `preflight`: after a partial run it
reports missing sources and existing destinations by design. Re-run `run` (it
skips ops already done), then `edits` (it skips edits already applied).

Common arguments: `--root`, `--meta`, `--pathmap`, `--edits`, `--inventory`,
`--tag` (prefix of every file under `--meta`, default `reorg`). Options:
`--ignore`, `--no-default-ignore`, `--allow-new`, `--old-pattern`, `--skip-dir`,
`--case-insensitive`, `--strict-inventory`, `--force-snapshot`, `--no-guard`,
`--stop-after`, `--prune-empty`, `--whitelist-extra`. Client-managed files such
as `desktop.ini`, `Thumbs.db`, and `.DS_Store` are ignored by default by both
scripts.

## Quick start

```bash
S=skills/folder-reorganization/scripts
M=<meta-dir>   # outside <root> when the tree is synced or shared; <root>/_meta is fine for a private folder
python $S/reorg_scan.py inventory --root <root> --out-dir $M --label before --skip-dir .git
python $S/reorg_scan.py refscan --root <consumer-root> --pathmap pathmap.csv --out $M/refscan.tsv --historical <glob> --skip-dir _meta
python $S/reorg_exec.py plan-check --pathmap pathmap.csv --inventory $M/before-inventory.tsv --edits edits.json
# stop here: show the proposal and wait for approval
python $S/reorg_exec.py preflight --root <root> --meta $M --pathmap pathmap.csv --inventory $M/before-inventory.tsv --edits edits.json
python $S/reorg_exec.py snapshot  --root <root> --meta $M --pathmap pathmap.csv --edits edits.json
python $S/reorg_exec.py run       --root <root> --meta $M --pathmap pathmap.csv
python $S/reorg_exec.py edits     --root <root> --meta $M --edits edits.json
python $S/reorg_exec.py verify    --root <root> --meta $M --pathmap pathmap.csv --inventory $M/before-inventory.tsv --edits edits.json
python $S/reorg_exec.py tree-after --root <root> --meta $M
python $S/reorg_scan.py inventory --root <root> --out-dir $M --label after
# undo: python $S/reorg_exec.py rollback --root <root> --meta $M --pathmap pathmap.csv --edits edits.json [--prune-empty]
```

`inventory` does not skip `.git` on its own (`refscan` does), so name it with
`--skip-dir .git`; whatever the inventory skips must also be passed as
`--ignore NAME` to `preflight`, `snapshot`, `verify`, `tree-after`, and
`rollback`. `inventory` writes `before-inventory.tsv` and
`before-area-totals.tsv` under `--out-dir`; `reorg_exec.py` writes its log, snapshots, rollback script, edit
backups, and `reorg-verify.txt` under `--meta`. `pathmap.csv` (header
`op,wave,action,old_path,new_path`) and `edits.json` (keys `edits` and
`whitelist`) are written during the proposal phase; keep them under `$M` or
outside `<root>`, or `verify` reports them as new files. The `whitelist` lists
the historical files that may keep old paths, each with a reason; `verify`
reads it through `--edits`. Pass `--edits` to `snapshot` too, so the rollback
script restores the edited files. In PowerShell set
`$S = 'skills\folder-reorganization\scripts'` and `$M = '<root>\_meta'`, and
call `python "$S\reorg_exec.py" ...`. When the tree is reached through a remote
or mounted shell, run the scripts natively on the machine that owns the files
and read only their output files (see the pitfalls below).

## Known pitfalls

- A cloud-synced folder keeps file and folder IDs only for in-place renames and
  moves. Do not plan "new folder, move contents out", keep the renamed folder as
  the one external links point to, move pointer files (`.gsheet`, `.gdoc`)
  instead of recreating them, and ignore client-managed `desktop.ini` churn when
  comparing counts. A file saved through a temp file and `os.replace` in the same
  folder was observed to keep its ID, but overwrite in place for one-off edits.
  See `learnings/google-drive-desktop-folder-reorg.md`.
- When a cloud session reaches the files through a device bridge, move files with
  the file-transfer tools (never large pasted base64), refresh mounted files with
  `cat new > old` because the mount refuses unlink, run whole-tree scans
  natively, and write multi-line Python to a temp file instead of `python -c`.
  See `learnings/cloud-session-device-bridge-file-io.md`.
- A computer-bound scheduled task's attached folder cannot be changed through the
  scheduling API. Pause the task with a recovery record before the move, update
  the prompt through the API, and give the owner the settings change; do not work
  around a permission denial. See `learnings/scheduled-task-attached-folder-rename.md`.
- A scheduled run that ended FAILED on a usage limit may resume later and overlap
  a catch-up (overlap observed, cause inferred from timing). Check the run history before firing, fire at most once, and audit
  shared files afterwards. See `learnings/scheduled-run-resumes-after-usage-limit.md`.
- `rollback` restores edited files from their backups, so it overwrites any
  change made to those files after the edit. Check them first. If automations
  were already resumed, pause them again and revert their prompts before rolling
  back.
