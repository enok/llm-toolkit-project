---
title: Job search tracker schema
tags: [job-search, tracker, xlsx, schema]
---

# Tracker schema

`scripts/tracker_ops.py init` creates these sheets. The script addresses columns
by header name, so owners may add, reorder, or hide columns; unknown sheets are
preserved. Legacy names are accepted as aliases (for example `Gmail link`
for `Mail link`, `AI Gigs` for `Side Gigs`).

openpyxl keeps cells, formats, and list validations. It does not keep charts,
images, pivots, or in-cell checkbox extensions. Row deletes in `move` and
`expire` do not shift conditional formats. Keep the tracker to plain cells, and
store links as text.

Hyperlinks on cells (for example a clickable `Job link`) are re-anchored to
their own cell on every save, so deleting a row no longer leaves a stale link
reference behind. Trackers written by earlier versions may still hold orphan
rows from that bug; `repair` removes them.

| Sheet | Purpose | Key columns |
| --- | --- | --- |
| Summary | Legend for the owner | free text |
| For Approval | Screened postings waiting for the owner's decision | `#`, `Approve ☐`, `Decision notes`, `Tier`, `Fit score`, `Company`, `Title`, `Job link`, `Posted`, `Location / eligibility`, `Pay (as posted)`, `Currency`, `Est. USD/mo min/max`, `Meets pay rule`, `Apply method`, `Required skills`, `Nice to have`, `Readiness %`, `Covered`, `In study plan`, `Missing (not in plan)`, `Next study action`, `Red flags`, `Summary`; optional at the end: `ATS match %`, `Missing keywords`, `Apply kit` |
| Applied | Submitted applications | `Channel`, `Date applied`, `Latest status`, `Pipeline stage`, `Stage history`, `Next action`, `Follow-up date`, `Mail link`, `Notes` |
| Interviewing | Active processes | Applied columns + `Interview stage`, `Next interview date`, `Interviewers`, `Prep material` |
| Closed | Finished processes | `Closed date`, `Outcome`, `Outcome detail`, `Stage reached`, `Stage history`, `Lessons / notes` |
| Excluded | Postings screened out or declined | `Company`, `Title`, `Job link`, `Reason`, `Fit`, `Pay` |
| Side Gigs | Optional freelance / AI-training platforms | `Platform`, `My status`, `Pay (USD/hr)`, `Meets my floor`, `Eligible from my country`, `Next action`, `Next action date`, `Last activity` |
| Skill Map | One row per job x skill | `Company`, `Title`, `Bucket` (= pipeline sheet), `Skill`, `Required/Nice`, `Status`, `Study plan ref`, `Week/phase` |
| Gap Summary | Rebuilt by `gaps` | `Skill`, `# jobs requiring`, `Status`, `Study plan ref`, `Suggested action` |

## Optional For Approval columns

| Column | Content | Jobs JSON key |
| --- | --- | --- |
| `ATS match %` | integer 0-100, matched hard-requirement keywords / total (method in [cv-tailoring.md](cv-tailoring.md)); empty when unknown | `ats_match` |
| `Missing keywords` | posting keywords the master CV does not support, separated by semicolons | `missing_keywords` |
| `Apply kit` | path or link to the row's apply-kit folder | `apply_kit` |

The script appends these columns at the end of `For Approval` when they are
absent. It never reorders or renames owner columns. A tracker without them keeps
working: `shortlist` treats a missing `ATS match %` as unknown and ranks it after
rows that have one.

## Approval marks (For Approval, column `Approve ☐`)

| Mark | Meaning | Run action |
| --- | --- | --- |
| `☐` | Not decided | leave |
| `☑ Approve` (or `TRUE`) | Owner approves | apply after the owner's chat OK for that form (SKILL.md item 3), then `move --to Applied` after a confirmed submit |
| `✖ Reject` | Owner declines | `move --to Excluded --detail "Declined by owner"` |
| `⏸ Later` | Parked | leave |
| `FALSE` or blank | Treated as `☐` (pending) | leave |

### Decision notes

Owner free text and tagged run entries share this cell; `approvals` prints it
as `notes`.

- **Needs owner.** When a run cannot finish a row's step (sign-in, consent box,
  code, assessment, missing standard answer), it writes
  `[<agent> <YYYY-MM-DD>] Needs owner: <reason>` with `set --column "Decision
  notes"`. `set` replaces the cell, so write `<current notes> | <entry>` and
  never drop owner text. The row keeps its mark. Later runs that see
  `Needs owner:` skip that step and list the row in the digest with its link. The owner deletes the
  entry once the blocker is cleared; the next run retries.
- **Owner decisions.** Free text on a rejected row ("never apply here
  again") is a standing rule. Propose adding the company to
  `criteria.blocked_companies` (or a hard rule); edit the profile only when
  the owner's words are explicit. `move --to Excluded` copies the notes into
  `Reason`.

## Stage transitions

| Evidence | Move |
| --- | --- |
| Confirmed submit (board confirmation page or "application was sent" mail) | For Approval -> Applied; follow-up = +7 days |
| Recruiter scheduling, screening call, assessment, take-home | Applied -> Interviewing; set `Interview stage`, `Next interview date` |
| "Not moving forward", "unfortunately", board status "Not moving forward" | -> Closed, `Outcome = Rejected` |
| Posting closed and no reply for `cadence.stale_days` | -> Closed, `Outcome = No response` |
| Withdrawal or offer | -> Closed, `Outcome = Withdrawn` / `Offer` |
| "No longer accepting applications" on its own | note only; not a close |

## Skill Map status values

`Experience (CV)` (the CV clearly shows it) · `Study plan - <state>` /
`Plan - <state>` (covered by a plan item; `Study plan ref` holds its id) ·
`GAP - not in plan` · `n/a (JD not captured)`. Owner-set values are kept unless
`gaps --recompute`.

Readiness % = (CV + 0.5 x plan) / scored skills. Required and Nice rows both
count. `n/a` rows are left out. A status counts as plan when it has a
`Study plan ref` or starts with `Study plan` or `Plan`. Any other owner value
counts as neither CV nor plan.

`move` only goes forward: For Approval -> Applied -> Interviewing -> Closed.
Only For Approval rows can go to Excluded. Pass `--allow-backward` to reopen a
Closed or Applied row; it does **not** reopen a row that was moved to Excluded.
Undo a bulk exclusion by re-adding the rows from the snapshot taken before the
change, or by restoring the timestamped backup. Take that snapshot before any
bulk move, and never promise an undo before proving it (dry-run one row, or
read the command's rules); when a doc or reply turns out wrong, correct it
immediately. Design rules for any sync of a plan with a progress tracker (study plan,
online sheet): it must refuse to guess. Write to a separate output path by
default, never over the tracker. Refuse (exit 2) when ANY output path already
holds ticks, unless an explicit carry-ticks option is given; checking only
output == tracker lets a re-run wipe ticks in an earlier output. Ticks are user
data that cannot be rebuilt.
For a tracker kept in an online sheet see [sheet-tracker-mode.md](sheet-tracker-mode.md). Dedup (`known`) includes Closed and Excluded, so a reposted role with the
same company and title is not suggested again.

## Dedup list command

### `known`

```bash
python skills/job-search-pipeline/scripts/tracker_ops.py known --tracker ./job-tracker.xlsx [--out known.json]
```

Read-only, so no `--expect-mtime`. It prints this JSON, or writes it to `--out`
and prints only the counts and the `out` path.

| Key | Content |
| --- | --- |
| `mtime` | the tracker's modification time |
| `ids` | sorted job ids (or normalized links) of every row on the pipeline sheets and `Excluded` |
| `company_title` | sorted `company \| title` keys of the same rows, lower-cased with spacing collapsed |
| `rejected_companies` | sorted, unique company names of `Closed` rows whose `Outcome` is `Rejected` |

`rejected_companies` matches `Outcome` case-insensitively, skips rows with a
blank company, and lists names that differ only in case once. It is empty when
no row qualifies. The board lanes use it when the profile sets
`criteria.exclude_rejected_companies: true`
([lane-prompts.md](lane-prompts.md)).

## Review queue commands

Both work on `For Approval` rows with no owner decision: `Approve ☐` is blank,
`☐`, or `FALSE`. A row with any other mark (`☑ Approve`, `✖ Reject`, `⏸ Later`,
or text the script does not recognise) is never ranked and never moved.

### `shortlist`

```bash
python skills/job-search-pipeline/scripts/tracker_ops.py shortlist --tracker ./job-tracker.xlsx --size 10
```

Read-only, so no `--expect-mtime`. It ranks the undecided rows by tier (A, then
B, then C), then `ATS match %`, then `Fit score`, then `Posted` (newest first),
and prints the top `--size` rows as a JSON list. Each entry has the sheet row
(`row`), `num` (the `#` column), `company`, `title`, `link`, `tier`, `fit`,
`ats_match`, `posted`, and `apply_method`. The profile's `queue.shortlist_size`
supplies `--size`. Use the list for the day's approval batch and for rows that
get an apply kit (`apply.kit_for: [shortlist]`).

### `expire`

```bash
python skills/job-search-pipeline/scripts/tracker_ops.py expire --tracker ./job-tracker.xlsx --days 30 --expect-mtime <mtime> --backup-dir ./backups [--today YYYY-MM-DD] [--dry-run]
```

Moves undecided rows whose `Posted` date is older than `--days` (counted back
from `--today`, default today) to `Excluded` with the reason
`Expired unreviewed (N days)`, where N is the value of `--days`. It never
touches a marked row. A row whose `Posted` date cannot be read is left in
place and listed in the output. `--dry-run` prints what would move and writes
nothing. The profile's `queue.expire_unreviewed_days` supplies `--days`; when
the key is absent, do not run it.

`expire` is a guarded write, so the contract in `SKILL.md` applies: pass the
tracker's `--expect-mtime`, use a backup dir, and pass the new `mtime` to the
next write. Because `Excluded` rows count for dedup, an expired posting that is
reposted with the same company and title is not suggested again.

## Repair command

### `repair`

```bash
python skills/job-search-pipeline/scripts/tracker_ops.py repair --tracker ./job-tracker.xlsx --expect-mtime <mtime> --backup-dir ./backups [--dry-run]
```

Deletes orphan rows from `For Approval`, `Applied`, `Interviewing`, `Closed`
and `Excluded`: rows with no `Company` and no `Title` but at least one other
filled cell, usually only a repeated `Job link`. A row with a `Company` or a
`Title`, a fully blank row and every other tab are never touched. It also resets
a `Job link` hyperlink whose target differs from the cell's URL text to that
text (`links_fixed`). It prints
`{"<sheet>": [row numbers removed], ..., "links_fixed": {"<sheet>": [cell refs]}, "mtime": ...}`
with rows and refs as they were before the delete. `--dry-run` lists them and
writes nothing; with nothing to change the file is not rewritten. It is a guarded write, so the
contract in `SKILL.md` applies: pass the tracker's `--expect-mtime`, use a
backup dir, and pass the printed `mtime` to the next write.

## Cell update command

### `set`

```bash
python skills/job-search-pipeline/scripts/tracker_ops.py set --tracker ./job-tracker.xlsx --link <url> --column "Apply kit" --value <path> [--sheet "For Approval"] --expect-mtime <mtime> --backup-dir ./backups
```

Writes one cell on an existing row, for data that arrives after the row was
appended, such as the `Apply kit` path of an approved or shortlisted row. It
finds the row by `Job link`, in `--sheet` or, when that is omitted, across all
tabs. It exits 2 when no row matches or more than one does, and writes nothing.

| Column | Rule |
| --- | --- |
| `ATS match %`, `Missing keywords`, `Apply kit`, `Decision notes`, `Next action`, `Notes` | Allowed. A column that is absent from the sheet is appended at the end. |
| Any header that starts with `Approve` | Refused (exit 2): the approval mark stays the owner's. |
| `#`, `Job link`, `Company`, `Title` | Refused (exit 2): they identify the row. |

`set` is a guarded write, so the contract in `SKILL.md` applies: pass the
tracker's `--expect-mtime`, use a backup dir, and pass the `mtime` printed in its
JSON output to the next write.

## Batch writes

Each write re-saves the whole workbook; chain many `move`/`set` writes with
`scripts/tracker_batch.py`:

```bash
python skills/job-search-pipeline/scripts/tracker_batch.py --tracker ./job-tracker.xlsx --ops ops.json --expect-mtime <mtime> --backup-dir ./backups --log ./batch.log [--resume] [--plan]
```

- `ops.json`: a JSON list of `move` and `set` ops whose keys mirror the
  command flags (format in the script's docstring). Write it from Python as
  UTF-8; PowerShell `>` writes UTF-16.
- It chains each printed `mtime` into the next op and logs one JSON line per
  op, so a timed-out call is checked in `--log`, not re-run. It stops at the
  first failure with that op's exit code; `--resume` skips ops logged OK;
  `--plan` validates and writes nothing. Output is read as UTF-8, so a
  non-ASCII title cannot crash a Windows run.

Before each batch, re-run `approvals` and use its fresh `mtime`: the owner may
edit the file mid-run. Add new owner marks to the batch (a new `✖ Reject`
becomes `move --to Excluded`). After moves to Applied, clear their
`pending_moves` entries and verify: `approvals`, `repair --dry-run` (no
orphans, no link fixes), and the last Applied rows.

## Skill rules file (`gaps --rules`)

```json
{
  "cv_skills": ["<same regex list as profile cv_skills>"],
  "rules": [
    {"match": "kubernetes|\\bk8s\\b", "ref": "PLAN-12", "status": "Study plan - scheduled", "week": "W3"},
    {"match": "system design", "ref": "PLAN-04"}
  ]
}
```

First matching rule wins; anything unmatched becomes `GAP - not in plan`.

## Jobs JSON (`append --jobs`, `exclude --jobs`)

A list, or `{"jobs": [...]}`. Every entry needs `company`, `title`, `link`.

| Key | Column |
| --- | --- |
| `tier`, `fit` | `Tier`, `Fit score` |
| `posted`, `originally_posted` | `Posted`, `Originally posted` |
| `location`, `employment_type` | `Location / eligibility`, `Employment type` |
| `pay`, `currency`, `usd_month_min`, `usd_month_max`, `meets_pay` | pay columns |
| `apply_method`, `years`, `english` | `Apply method`, `Years required`, `English` |
| `required`, `nice` (lists) | `Required skills`, `Nice to have`, and one Skill Map row each |
| `ats_match` (0-100), `missing_keywords` (list or semicolon text), `apply_kit` | `ATS match %`, `Missing keywords`, `Apply kit` |
| `red_flags` (list or text), `summary`, `notes` | `Red flags`, `Summary`, `Decision notes` |
| `reason` (exclude only) | `Reason` |

Unknown keys are reported as `ignored_keys`, never written.

## Side gigs JSON (`sidegig --data`)

A list of `{platform, link, status, applied, pay, meets_floor, eligible,
payment, next_action, next_action_date, last_activity, mail_link, notes}`.
Rows are matched by `platform`, case-insensitive. A new platform is appended.
An existing one is updated only in the keys given.
