---
title: Workspace cleanup classification rubric
tags: [workspace-cleanup, classification, approval-gate, reversibility]
---

# Classification rubric

How the classifier lane (or `tool-subagents/workspace-hygiene-auditor.md`)
turns an inventory into a plan, and how the plan is grouped for approval.
The classifier never acts; the root validates every row against live state
before the owner sees it.

## Actions

| Action | Meaning | Reversible |
| --- | --- | --- |
| KEEP | Leave untouched | n/a |
| ARCHIVE | Agent session or similar whose work is finished or superseded | yes |
| DELETE | Empty, trivial one-off, or superseded chat; fired one-shot task; obsolete or duplicate artifact | no |
| DELETE-OPTIONAL | Personal Q&A the owner may want; flag, never push | no |
| PAUSE | Scheduled task that is replaced, redundant, or failing; keep the definition | yes |
| CONSOLIDATE | Several scheduled tasks merged into one new task (new task plus PAUSE of the originals) | mostly |
| UNSURE | Evidence too thin; treated as KEEP (or ARCHIVE where reversible) until the owner decides | n/a |

## Keep-rules (any one forces KEEP)

- Touched in the last 3 days.
- Has a live process: running agent session, enabled scheduled task with a
  future run, open pull request or job it drives. The one exception is the
  merge rule for overlapping recurring tasks (see Rules per item type).
- It is the current session, or a session running concurrently.
- Source-of-truth chat: the place where a decision, plan, or spec is the only
  record (check whether memory or a document already holds it).
- Pinned or starred items.
- A project that still contains any non-archived session, doc, file, or
  scheduled task.
- Shared with other people and not clearly the owner's to remove.

## Rules per item type

| Type | Default | Notes |
| --- | --- | --- |
| Agent / Cowork task | ARCHIVE when finished or superseded; KEEP otherwise | Never DELETE on title alone. |
| Regular chat | DELETE when empty, trivial one-off, or superseded by a newer chat or by saved memory; KEEP otherwise | Mark DELETE-OPTIONAL for personal Q&A. An "Untitled" chat needs an emptiness check first. |
| Project | KEEP unless empty | Resolve contents first. |
| Fired one-shot task (enabled=false, ended_reason set) | DELETE | Clutter by definition; still re-read before deleting. |
| Recurring task, healthy | KEEP | Healthy means plausible run duration and no repeated failure. |
| Recurring task, redundant or overlapping | Propose CONSOLIDATE at low confidence; otherwise KEEP | Overlapping recurring tasks may be proposed for CONSOLIDATE at low confidence: create the replacement, then pause the originals (pause, not delete) until the replacement has run well. Otherwise the keep-rule applies. |
| Recurring task, suspicious duration or repeated failure | KEEP + flag, or PAUSE | Open the run session before recommending. |
| Artifact | DELETE only if obsolete or duplicate; KEEP otherwise | Per-item owner confirmation at execution. |
| Ledger section (tasks table, context state) | ARCHIVE when its remaining-count row is 0 | Never trust header wording like "all waves complete"; keep the current session. |

## Confidence

Every row carries `high`, `medium`, or `low`.

- **high**: decided from content or metadata you read (message count, last
  activity, run history, linked artifacts).
- **medium**: partial content plus metadata.
- **low**: title only, or the inventory could not read the item.

Rules: low confidence never yields DELETE; downgrade to ARCHIVE or KEEP and
mark UNSURE. A DELETE needs high confidence, or medium confidence with the
owner explicitly approving that row.

## Plan row schema

`id` (stable ID or URL uuid), `type`, `title_as_shown` (kept in the run
files only, never in the toolkit), `action`, `confidence`, `reason` (at most
12 words), `evidence` (`content` | `metadata` | `title-only`), `group`, and
`flags` (`duplicate-title`, `untitled`, `stale-risk`, `suspicious-duration`,
`shared`).

## Root validation (before the owner sees the plan)

1. Re-read live state for every row whose action is not KEEP and for every
   scheduled task. Snapshots go stale: a task observed paused at inventory
   time was re-enabled by another session about ten minutes later, and the
   classifier still recommended "PAUSE (already paused)".
2. Re-read the sessions touched since the snapshot; they may now trip a
   keep-rule.
3. Resolve duplicate titles by ID; confirm each look-alike is on the
   deny-list of the lane that will act.
4. Override rows where the rubric disagrees with the classifier; record the
   override count ("n of N rows overridden") and why, in the plan.
5. Check totals: items per type in the plan equal the inventory counts, and
   unread or unreadable items are listed, not silently dropped.

## Approval groups (ordered by reversibility)

Ask separately, so the owner can approve a safe group without approving a
destructive one. Nothing is pre-selected.

| Group | Contents | Reversible | Extra confirmation |
| --- | --- | --- | --- |
| A. Archive | ARCHIVE rows (sessions) and ledger compaction | yes | none |
| B. Pause / config | PAUSE rows | yes | none |
| C. New or changed scheduled tasks | CONSOLIDATE (new task plus pausing originals) | mostly | model choice for each new task, asked here |
| D. Delete, chats and sessions | DELETE rows of regular chats | no | allow-list shown |
| E. Delete, fired one-shots | DELETE rows of fired scheduled tasks | no | allow-list shown |
| F. Delete, artifacts | DELETE rows of artifacts | no | per-item confirmation again at execution |
| G. Optional | DELETE-OPTIONAL rows | no | each row individually |

Skip empty groups. When the owner edits a group, revalidate the changed rows
before executing. Unselected groups are reported as "not done", not dropped.

## Edge cases

- Same title, different IDs: act only on the IDs in the approved list.
- Item changed after approval (new activity, re-enabled, renamed): skip it and
  report; do not search by title for a replacement.
- Item type not covered here: default to KEEP and ask.
