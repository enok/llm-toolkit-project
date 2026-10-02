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
images, pivots, or in-cell checkbox extensions. Row deletes in `move` do not
shift hyperlinks or conditional formats. Keep the tracker to plain cells, and
store links as text.

| Sheet | Purpose | Key columns |
| --- | --- | --- |
| Summary | Legend for the owner | free text |
| For Approval | Screened postings waiting for the owner's decision | `#`, `Approve ☐`, `Decision notes`, `Tier`, `Fit score`, `Company`, `Title`, `Job link`, `Posted`, `Location / eligibility`, `Pay (as posted)`, `Currency`, `Est. USD/mo min/max`, `Meets pay rule`, `Apply method`, `Required skills`, `Nice to have`, `Readiness %`, `Covered`, `In study plan`, `Missing (not in plan)`, `Next study action`, `Red flags`, `Summary` |
| Applied | Submitted applications | `Channel`, `Date applied`, `Latest status`, `Pipeline stage`, `Stage history`, `Next action`, `Follow-up date`, `Mail link`, `Notes` |
| Interviewing | Active processes | Applied columns + `Interview stage`, `Next interview date`, `Interviewers`, `Prep material` |
| Closed | Finished processes | `Closed date`, `Outcome`, `Outcome detail`, `Stage reached`, `Stage history`, `Lessons / notes` |
| Excluded | Postings screened out or declined | `Company`, `Title`, `Job link`, `Reason`, `Fit`, `Pay` |
| Side Gigs | Optional freelance / AI-training platforms | `Platform`, `My status`, `Pay (USD/hr)`, `Meets my floor`, `Eligible from my country`, `Next action`, `Next action date`, `Last activity` |
| Skill Map | One row per job x skill | `Company`, `Title`, `Bucket` (= pipeline sheet), `Skill`, `Required/Nice`, `Status`, `Study plan ref`, `Week/phase` |
| Gap Summary | Rebuilt by `gaps` | `Skill`, `# jobs requiring`, `Status`, `Study plan ref`, `Suggested action` |

## Approval marks (For Approval, column `Approve ☐`)

| Mark | Meaning | Run action |
| --- | --- | --- |
| `☐` | Not decided | leave |
| `☑ Approve` (or `TRUE`) | Owner approves | apply, then `move --to Applied` after a confirmed submit |
| `✖ Reject` | Owner declines | `move --to Excluded --detail "Declined by owner"` |
| `⏸ Later` | Parked | leave |
| `FALSE` or blank | Treated as `☐` (pending) | leave |

A row whose `Decision notes` already says it needs the owner (blocked portal,
missing answer) stays approved and is listed again in the digest; do not retry
the blocked step each run.

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
row. Dedup (`known`) includes Closed and Excluded, so a reposted role with the
same company and title is not suggested again.

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
| `red_flags` (list or text), `summary`, `notes` | `Red flags`, `Summary`, `Decision notes` |
| `reason` (exclude only) | `Reason` |

Unknown keys are reported as `ignored_keys`, never written.

## Side gigs JSON (`sidegig --data`)

A list of `{platform, link, status, applied, pay, meets_floor, eligible,
payment, next_action, next_action_date, last_activity, mail_link, notes}`.
Rows are matched by `platform`, case-insensitive. A new platform is appended.
An existing one is updated only in the keys given.
