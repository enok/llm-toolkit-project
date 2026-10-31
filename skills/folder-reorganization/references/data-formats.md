---
title: Folder reorganization script CLI and data formats
tags: [folder-reorganization, reorg_exec, reorg_scan, path-map, edits, inventory, refscan, rollback]
---

# Script CLI and data formats

Reference for `scripts/reorg_scan.py` (read-only inventory and reference scan)
and `scripts/reorg_exec.py` (plan check, preflight, snapshot, run, edits,
verify, rollback). Both need Python 3.9 or newer and the standard library only.
Exit codes for both: `0` ok, `1` problem or failure, `2` usage error.

Paths in every input file are relative to `--root` and may use `/` or `\`.
Every relative path the scripts write uses forward slashes, and every file they
write is UTF-8 with LF line endings (the PowerShell rollback script is the one
exception, see below).

## Shared rules

- **Globs** (`--ignore`, `--allow-new`, `--historical`): a pattern without `/`
  is tested against every path component, so `.git` drops the whole directory
  and `*.log` every log file. A pattern with `/` is tested against every leading
  and every trailing part of the relative path, so `archive/*.log` matches
  `archive/run.log` and `x/archive/run.log`.
- **Default ignore globs**: `desktop.ini`, `Thumbs.db`, `.DS_Store` (sync-client
  churn). `--no-default-ignore` turns them off.
- **Case sensitivity** (`--case-insensitive auto|yes|no`, default `auto`):
  `auto` probes `--root` by looking up its folder name with the letter case
  swapped, and falls back to the OS (Windows and macOS: insensitive). On a
  case-insensitive filesystem every path comparison, glob, and old-path regex
  ignores case.
- **Text, binary, Office classification** (refscan and the verify scan):
  known text extensions are scanned as UTF-8 (undecodable bytes replaced);
  known binary extensions are skipped; any other file is skipped when its first
  8 KiB hold a NUL byte. `.xlsx .docx .pptx .odt .ods .odp` are opened as zip
  files and their `.xml` and `.rels` members are scanned. Text files above
  20 MB and Office files above 60 MB are not scanned and are reported.
- **Default old-path regex** (refscan `--pathmap`, verify): one alternative per
  distinct `old_path` of a move or rename op. Separators match any run of `/`
  or `\`. A multi-segment path must not be preceded by a name character
  (`\w`, `.`, `-`) or followed by a name continuation. A single segment (a bare
  folder name) counts only in a path context: followed by a separator, or
  preceded by one. A match that lies inside the op's own `new_path` is not a
  hit (old `logs`, new `archive/logs`: the text `archive/logs/run.log` is
  clean).

## reorg_scan.py

```text
reorg_scan.py inventory --root ROOT --out-dir DIR --label LABEL
                        [--ignore GLOB]... [--no-default-ignore] [--skip-dir NAME]...
                        [--case-insensitive auto|yes|no]
reorg_scan.py refscan   --root ROOT (--pathmap MAP.csv | --pattern REGEX ...) --out OUT.tsv
                        [--historical GLOB]... [--ignore GLOB]... [--no-default-ignore]
                        [--skip-dir NAME]... [--case-insensitive auto|yes|no]
```

| Option | Subcommand | Meaning |
| --- | --- | --- |
| `--root ROOT` | both | Folder to walk (required) |
| `--out-dir DIR` | inventory | Folder for the two outputs; created if missing; left out of the walk when it lies inside `--root` |
| `--label LABEL` | inventory | Output file prefix; letters, digits, `.`, `_`, `-` (for example `before`, `after`) |
| `--pathmap MAP.csv` | refscan | Derive the default old-path regex from the path map |
| `--pattern REGEX` | refscan | Repeatable raw Python regex; combine with `--pathmap` for cloud IDs, mount spellings, and similar forms |
| `--out OUT.tsv` | refscan | Output file; its parent is created; the file itself is never scanned |
| `--historical GLOB` | refscan | Repeatable; hits in matching files get class `historical` |
| `--ignore GLOB` | both | Repeatable; files and directories left out |
| `--no-default-ignore` | both | Do not add the default ignore globs |
| `--skip-dir NAME` | both | Repeatable directory name that is not entered. refscan always skips `.git __pycache__ node_modules .idea .mvn`; inventory skips only what you name |
| `--case-insensitive` | both | `auto` (default), `yes`, `no` |

`inventory` writes `<label>-inventory.tsv` and `<label>-area-totals.tsv` under
`--out-dir`. A file it cannot stat becomes an `ERR` row and the run exits `1`;
fix access and run it again, because `reorg_exec.py` refuses an inventory with
error rows. `inventory` never skips `.git` or similar on its own: whatever it
leaves out with `--skip-dir` must also be left out of `reorg_exec.py` with
`--ignore NAME`, or `verify` reports those files as unexpected.

`refscan` needs `--pathmap`, `--pattern`, or both, and writes one TSV. It exits
`1` when a file could not be read (a `scan-error` row); the TSV is still
written.

## reorg_exec.py

```text
reorg_exec.py MODE --root ROOT --meta META --pathmap MAP.csv [--edits EDITS.json]
                   [--inventory INV.tsv] [--tag TAG] [options]
```

| Mode | Required | Also reads | Writes |
| --- | --- | --- | --- |
| `plan-check` | `--pathmap --inventory` | `--edits` (each target must be produced by the moves) | nothing |
| `preflight` | `--root --meta --pathmap --inventory` | `--edits` (dry run on the pre-move originals), `--strict-inventory` | nothing |
| `snapshot` | `--root --meta --pathmap` | `--edits` (files the rollback script restores), `--force-snapshot` | tree-before, rollback script, log |
| `run` | `--root --meta --pathmap` | `--no-guard`, `--stop-after OP` | the moves, log |
| `edits` | `--root --meta --edits` | | edited files in place, backups, log |
| `verify` | `--root --meta --pathmap --inventory` | `--edits`, `--whitelist-extra`, `--allow-new`, `--old-pattern`, `--skip-dir` | verify report, log |
| `tree-after` | `--root --meta` | | tree-after, log |
| `rollback` | `--root --meta --pathmap` | `--edits` (files to restore), `--prune-empty` | the reverse moves, restored files, tree-rolledback, log |

`plan-check` needs no tree: `--root` is optional there and only feeds the
case-sensitivity probe. Every mode also honours `--tag`, `--ignore`,
`--no-default-ignore`, and `--case-insensitive`.

| Option | Meaning |
| --- | --- |
| `--tag TAG` | Prefix of every file written under `--meta` (default `reorg`); letters, digits, `.`, `_`, `-` |
| `--case-insensitive MODE` | `auto` (default), `yes`, `no` |
| `--strict-inventory` | preflight: inventory drift (missing, extra, or resized files) is a problem, not a warning |
| `--force-snapshot` | snapshot: rename the existing tree-before to `<tag>-tree-before.<UTC timestamp>.txt` and write a new one (without it an existing tree-before is kept; the rollback script is always rewritten) |
| `--no-guard` | run: do not require the snapshot files (`<tag>-tree-before.txt` and `<tag>-rollback.ps1`, both required on every OS) |
| `--stop-after OP` | run: execute only ops whose id is `<= OP`; run again without it to resume |
| `--prune-empty` | rollback: `rmdir` directories created by mkdir ops when they are empty, deepest first; never deletes a file |
| `--whitelist-extra JSON` | verify: more whitelist items, as `{"whitelist": [...]}` or a bare list |
| `--ignore GLOB` | Repeatable; left out of verify, the tree files, and every inventory comparison |
| `--no-default-ignore` | Do not add the default ignore globs |
| `--allow-new GLOB` | Repeatable; verify: files that may exist without an inventory row |
| `--old-pattern REGEX` | Repeatable; verify: replaces the default old-path regex |
| `--skip-dir NAME` | Repeatable; verify scan: directory names not entered (always skipped: `.git __pycache__ node_modules .idea .mvn` and `--meta`) |

Behaviour that the formats below depend on:

- **preflight** walks the real tree (the `--meta` folder is left out), reports
  lock files (`~$*`, `.~lock.*#`), simulates every op, checks the longest final
  path (problem at 260 characters on Windows, warning from 240), compares the
  inventory with the disk, and dry-runs every edit.
- **run** executes ops in op order and stops at the first failure. A mkdir whose
  directory exists is `skip-done`. A move whose source is gone and destination
  exists is `skip-done`; an existing destination, a missing parent, or a
  missing source and destination is a failure. Moves use `os.rename`, so the
  destination must be on the same volume. A case-only rename on a
  case-insensitive filesystem goes through a temporary sibling named
  `<new name>.<tag>-case-<op>.tmp`. Once `run` has started, do not re-run
  `preflight`: after a partial run it reports missing sources and existing
  destinations by design. Re-run `run` (it skips ops already done), then
  `edits` (it skips edits already applied).
- **edits** plans every edit before writing anything; one mismatch means
  nothing is written and no backup is taken. A file whose edits all show as
  already applied is `already-applied`. Before the first write to a file it
  takes a verified byte copy (mtime kept). A pending edit whose file differs
  from an existing backup (a stale backup) is a problem. Files are overwritten
  in place and read back; zip files are rebuilt under `<tag>-tmp/` first. If
  the process dies during an in-place write, the file can be left partly
  written, and a rerun of `edits` reports a mismatch for it. Restore it from
  its backup (copy it from `<tag>-edit-backups/`, or use `rollback`, which also
  reverses the moves, so run `run` again afterwards) and rerun `edits`.
- **verify** (a) maps every inventory row through the moves and checks the size
  (edited text files: original size plus `count * (len(new) - len(old))` in
  UTF-8 bytes; `xlsx-xml` files: every member compared with the backup) and
  flags files not in the inventory unless `--allow-new` matches them;
  (b) scans text files and Office XML for old paths; each hit must be covered by
  a whitelist item. `RESULT: OK` only when both pass.
- **rollback** restores edited files from their backups in place (mtime
  included), reverses the moves in reverse op order (a move whose new path is
  absent is skipped; old and new both present stops with a conflict),
  optionally prunes empty mkdir directories, then writes
  `<tag>-tree-rolledback.txt` and exits `1` when it differs from the
  tree-before. Because it restores edited files from their backups, it
  overwrites any change made to those files after the edit: check them first.
  If automations were already resumed, pause them again and revert their
  prompts before rolling back.

## Path map CSV

UTF-8 (a BOM is accepted), header exactly `op,wave,action,old_path,new_path`.

| Column | Rule |
| --- | --- |
| `op` | Integer, unique, rows in ascending order. Rows with an empty `op` are skipped |
| `wave` | Free label for grouping (for example `1`, `2`); informational. `--stop-after` uses `op` |
| `action` | `mkdir`, `move`, or `rename` (case does not matter) |
| `old_path` | Empty for `mkdir`; required for `move` and `rename` |
| `new_path` | Required for every action |

- Paths are relative to `--root`: no drive letter, no leading separator, no
  `..` that leaves the root, never the root itself.
- `move` and `rename` need different old and new paths. `rename` must keep the
  parent directory; use `move` to change it.
- `mkdir` creates one directory whose parent already exists (or is created by
  an earlier op).
- Ops apply in order to the tree left by the ops before them. Moving a folder
  moves everything under it; a later op addresses those files by their new path.
- A case-only rename (`src/Main.java` to `src/main.java`) is a `rename`.

## Edits JSON

```json
{
  "_comment": "keys that start with _ are ignored",
  "edits": [
    {"file": "docs/readme.md", "kind": "text",
     "replacements": [{"old": "docs/old-notes/", "new": "archive/notes/", "count": 1}]},
    {"file": "data/index.xlsx", "kind": "xlsx-xml",
     "replacements": [{"old": "xl/sharedStrings.xml|docs/old-notes/a.md", "new": "archive/notes/a.md", "count": 1}]}
  ],
  "whitelist": [
    {"file_prefix": "archive/reports/", "why": "past reports record the paths of their time"},
    {"file": "docs/changelog.md", "contains": "docs/old-notes", "why": "changelog entry describes the move"}
  ]
}
```

The top level is an object with `edits` and `whitelist`; any other key that
does not start with `_` is rejected.

Edit item:

| Key | Rule |
| --- | --- |
| `file` | Relative path of the file AFTER the moves (edits run after `run`) |
| `kind` | `text` or `xlsx-xml` |
| `replacements` | Non-empty list of `{"old": str, "new": str, "count": int}`; `count` defaults to 1 and must be at least 1 |

- `old` and `new` are literal text (no regex, separators are not converted).
  Replacements apply in list order, each on the text the previous one left.
- `count` is the exact number of occurrences of `old`. Exactly `count` found:
  all are replaced. None found and `new` present at least `count` times:
  already applied. Anything else is a mismatch, and then nothing is written.
- `old` must not be contained in `new`, so a second run cannot double-apply.
- `text`: the file is read as UTF-8 with its line endings kept. A replacement
  that adds a bare LF to a CRLF file triggers a warning.
- `xlsx-xml`: `old` has the form `<zip member>|<text>`, for example
  `xl/sharedStrings.xml|docs/old-notes/a.md`. Only the named members change;
  every other member keeps its bytes, order, compression, and timestamp. The
  same form works for any Office Open XML zip (`word/document.xml` in a .docx,
  `ppt/slides/slide1.xml` in a .pptx).
- Two edits must not share a backup name (the path with separators replaced by
  `__`, compared without case).

Whitelist item (old paths allowed to stay, for example in historical files):

| Key | Rule |
| --- | --- |
| `file` or `file_prefix` | Exactly one. `file` is a final relative path; `file_prefix` matches the start of the relative path (`archive/reports/` covers that folder) |
| `contains` | Optional literal text the hit line (or the XML context of an Office hit) must contain |
| `why` | Required, non-empty reason; shown in the proposal |

## Inventory TSV (`<label>-inventory.tsv`)

Written by `reorg_scan.py inventory`, read by `reorg_exec.py --inventory`.
Header `rel_path<TAB>bytes<TAB>mtime_utc<TAB>kind`, one row per file, sorted by
`rel_path`. Directories are not listed, so an empty folder is invisible here
(`preflight` sees it in the real tree).

| Column | Value |
| --- | --- |
| `rel_path` | Path relative to `--root`, forward slashes |
| `bytes` | Size in bytes; `-1` on an error row |
| `mtime_utc` | Modification time, whole seconds, `YYYY-MM-DDTHH:MM:SSZ`; empty on an error row |
| `kind` | `file`, or `ERR <reason>` when the file or folder could not be read |

`reorg_exec.py` requires the `rel_path` header, needs at least the first two
columns, treats a missing `kind` as `file`, skips `dir` rows, refuses any row
whose `kind` starts with `ERR`, and applies its own ignore globs to the rows.

## Area totals TSV (`<label>-area-totals.tsv`)

Header `area<TAB>files<TAB>bytes`. One row per top-level folder (files directly
under the root are grouped as `(root files)`), sorted, then a `TOTAL` row.
Error rows are not counted. Compare the `before` and `after` files to prove
that counts and bytes are unchanged; `plan-check` prints the same per-area
before and after table from the path map.

## Refscan TSV (`--out`)

Header `file<TAB>line<TAB>class<TAB>pattern<TAB>snippet`.

| Column | Value |
| --- | --- |
| `file` | Path relative to the refscan `--root`, forward slashes |
| `line` | 1-based line number in a text file; the zip member name (for example `xl/sharedStrings.xml`) in an Office file; `0` on a `scan-error` or `not-scanned` row |
| `class` | `historical` when the file matches a `--historical` glob, else `live` |
| `pattern` | The path-map `old_path` (forward slashes) the hit refers to, or the `--pattern` regex as given; `scan-error` or `not-scanned` on those rows |
| `snippet` | Text files: the trimmed line, or 80 characters either side of the match when the line is longer than 200. Office members: 80 characters either side of the match. Tabs and line breaks become spaces |

Text files give one row per line and pattern; Office members give one row per
match. Every `live` row must end up as an edit, a whitelist item, or an owner
action in the proposal.

## Files under `--meta`

`reorg_exec.py` keeps all its state in `--meta` and leaves that folder out of
every walk, tree listing, and scan. `<tag>` defaults to `reorg`. `--meta` may
lie inside the root (for example `<root>/_meta`, acceptable for a private
folder) or outside it. Prefer outside when the tree is synced or shared: the
log holds the hostname and absolute paths, and the backups hold file copies.

| File | Written by | Content |
| --- | --- | --- |
| `<tag>-log.md` | snapshot, run, edits, verify, tree-after, rollback, and the rollback script | Append-only ledger: one `## <UTC> mode=<mode> root=<root> meta=<meta> host=<host> python=<version>` header per run, then lines such as `- <UTC> \| op 3 \| move \| docs/old-notes -> archive/notes \| ok` (results: `ok`, `skip-done`, `FAIL: ...`, `rolled back`, `rollback skip: ...`, `pruned empty directory`) and `- <UTC> \| edit \| <file> \| <kind> \| applied 1 replacements (pre-mtime=... pre-bytes=...) \| backup=<name> \| ok` |
| `<tag>-tree-before.txt` | snapshot | Header `rel_path<TAB>bytes<TAB>mtime_utc`; every file not ignored, sorted (without case on a case-insensitive filesystem) |
| `<tag>-tree-before.<UTC>.txt` | snapshot `--force-snapshot` | The previous tree-before, kept |
| `<tag>-rollback.ps1` | snapshot | PowerShell rollback: restore edited files, reverse moves, prune with `-PruneEmpty`. UTF-8 with BOM and CRLF for Windows PowerShell 5.1 |
| `<tag>-edit-backups/<flat name>` | edits | Byte copy of each file before its first edit, mtime kept; `<flat name>` is the relative path with separators replaced by `__` (`docs/readme.md` becomes `docs__readme.md`) |
| `<tag>-tmp/` | edits | Transient rebuilt zip files; removed when empty |
| `<tag>-verify.txt` | verify | Report: (a) inventory against the final tree, xlsx deep check, `MISSING`, `SIZE`, `EXTRA`, `ALLOWED` lines; (b) old-path hits, whitelist coverage, `HIT` lines; last line `RESULT: OK` or `RESULT: FAIL - ...` |
| `<tag>-tree-after.txt` | tree-after | Same format as tree-before |
| `<tag>-tree-rolledback.txt` | rollback | Same format; compared byte for byte with tree-before |

Run the PowerShell rollback with
`powershell -NoProfile -ExecutionPolicy Bypass -File <meta>/<tag>-rollback.ps1 [-PruneEmpty]`
(or `pwsh -File ...`). `run` requires `<tag>-rollback.ps1` next to
`<tag>-tree-before.txt` on every OS, but on Linux and macOS (without `pwsh`)
roll back with `reorg_exec.py rollback`. The script covers the edits passed to `snapshot`; if the edits
file changes later, run `snapshot` again (it keeps the tree-before and rewrites
the script) or use `reorg_exec.py rollback --edits <file>`.

## Worked example: `docs/old-notes` to `archive/notes`

Tree before (`<root>`):

```text
README.md                   "Start at docs/readme.md"
docs/readme.md              "Notes live in docs/old-notes/ now."
docs/old-notes/a.md
docs/old-notes/b.md
data/index.xlsx             a cell holds "docs/old-notes/a.md"
logs/2026-01-run.log        "moved docs/old-notes/a.md"   (historical)
```

`pathmap.csv`:

```text
op,wave,action,old_path,new_path
1,1,mkdir,,archive
2,1,move,docs/old-notes,archive/notes
3,2,move,logs,archive/logs
```

`edits.json`: the example in "Edits JSON" above, with the whitelist item
`{"file_prefix": "archive/logs/", "why": "run logs record the paths of their time"}`.

Commands (POSIX shell; in PowerShell use `$S = '...'` and `"$S\reorg_exec.py"`):

```bash
S=skills/folder-reorganization/scripts
M=<root>/_meta
python $S/reorg_scan.py inventory --root <root> --out-dir $M --label before
python $S/reorg_scan.py refscan --root <root> --pathmap pathmap.csv --out $M/refscan.tsv \
  --historical logs --skip-dir _meta
python $S/reorg_exec.py plan-check --pathmap pathmap.csv --inventory $M/before-inventory.tsv --edits edits.json
python $S/reorg_exec.py preflight --root <root> --meta $M --pathmap pathmap.csv \
  --inventory $M/before-inventory.tsv --edits edits.json
python $S/reorg_exec.py snapshot --root <root> --meta $M --pathmap pathmap.csv --edits edits.json
python $S/reorg_exec.py run      --root <root> --meta $M --pathmap pathmap.csv
python $S/reorg_exec.py edits    --root <root> --meta $M --edits edits.json
python $S/reorg_exec.py verify   --root <root> --meta $M --pathmap pathmap.csv \
  --inventory $M/before-inventory.tsv --edits edits.json
python $S/reorg_exec.py tree-after --root <root> --meta $M
python $S/reorg_scan.py inventory --root <root> --out-dir $M --label after
```

`before-inventory.tsv` (columns separated by tabs):

| rel_path | bytes | mtime_utc | kind |
| --- | --- | --- | --- |
| `README.md` | 24 | 2026-01-10T09:00:00Z | file |
| `data/index.xlsx` | 5120 | 2026-01-10T09:00:00Z | file |
| `docs/old-notes/a.md` | 120 | 2026-01-10T09:00:00Z | file |
| `docs/old-notes/b.md` | 80 | 2026-01-10T09:00:00Z | file |
| `docs/readme.md` | 35 | 2026-01-10T09:00:00Z | file |
| `logs/2026-01-run.log` | 26 | 2026-01-10T09:00:00Z | file |

`refscan.tsv`:

| file | line | class | pattern | snippet |
| --- | --- | --- | --- | --- |
| `data/index.xlsx` | `xl/sharedStrings.xml` | live | `docs/old-notes` | `...<t>docs/old-notes/a.md</t>...` |
| `docs/readme.md` | 1 | live | `docs/old-notes` | `Notes live in docs/old-notes/ now.` |
| `logs/2026-01-run.log` | 1 | historical | `docs/old-notes` | `moved docs/old-notes/a.md` |

Each `live` row has an edit; the `historical` row has a whitelist item. After
`run` and `edits`, `verify` reports 6 inventory rows, 2 of 2 edited files as
expected (the xlsx through the member-by-member deep check), 1 hit covered by
the whitelist, 0 uncovered hits, and `RESULT: OK`. `before-area-totals.tsv`
and `after-area-totals.tsv` show the same `TOTAL` file count; the bytes differ
only by the edited-file delta that `verify` explains. To undo:

```bash
python $S/reorg_exec.py rollback --root <root> --meta $M --pathmap pathmap.csv --edits edits.json --prune-empty
```

`--prune-empty` removes the now-empty `archive/`; the rollback ends with
`tree vs tree-before snapshot: IDENTICAL`.
