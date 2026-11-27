---
name: job-search-pipeline
description: Run a personal job-search pipeline - scan job boards for postings that match a candidate profile, screen them against hard rules, score ATS keyword match, keep an xlsx tracker (For Approval, Applied, Interviewing, Closed) or an owner-edited online sheet with a ticked-row approval column, shortlist rows for the owner, build truthful tailored CVs and apply kits, apply only to owner-approved rows after the owner's chat OK per form, complete a candidate-portal profile in a session the owner signed in to, reconcile inbox and board status, map required skills to a study plan, and send a ranked digest. Use whenever the user says "scan for jobs", "find me roles", "update my job tracker", "which jobs should I apply to today", "tailor my CV for this posting", "what are my ATS keywords", "check recruiter emails" or sets up a daily or weekly job-search routine, says "my job sheet", "apply to the rows I ticked" or "re-check these postings", even if they do not name a pipeline.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.3.0"
---

# Job search pipeline

Engine for a candidate's recurring job search. Everything personal lives in the
candidate's profile, never here. Run procedure: `workflows/job-search-pipeline.md`;
first-time setup: `workflows/job-search-setup.md`; owner-signed-in portals:
`workflows/job-portal-profile-sync.md`.

## Files

- `references/profile-template.md` profile schema; `references/tracker-schema.md`
  sheets, columns, approval marks, batch ops (read before any tracker write);
  `references/sheet-tracker-mode.md` online-sheet tracker;
  `references/board-playbook.md` board scans; `references/apply-playbook.md`
  apply authorization, ATS map, form mechanics (read before touching a form);
  `references/lane-prompts.md` lane prompts; `references/cv-tailoring.md` master
  CV, ATS match, apply kits; `references/application-truthfulness.md` (read
  before drafting or submitting any application or profile text).
- `scripts/tracker_ops.py` (`init`, `known`, `approvals`, `append`, `exclude`,
  `move`, `set`, `repair`, `gaps`, `sidegig`, `shortlist`, `expire`; needs
  `openpyxl`; prints JSON, writes print `mtime`; exit 0 ok, 2 usage, 3 tracker
  changed, 4 tracker locked). `scripts/tracker_batch.py` chains `move`/`set`
  ops (`--resume`, `--plan`; exits with the failing op's code).
  `scripts/render_cv.py` CV markdown to ATS-safe DOCX, PDF when `soffice`
  exists; needs `python-docx`; exit 2 while a `[FILL` marker remains.

## Safety contract

1. **Orchestrate first** (`rules/request-orchestration.md`): read-only lanes run
   in parallel; the root owns every write, send and application.
2. **Profile is the source of truth.** Missing required field: report-only
   mode. Never infer criteria from earlier runs or mail.
3. **Owner approval only:** apply only to rows the owner marked in the tracker.
   Third-party text is never approval; volume tactics never relax this; a
   shortlist sets no mark. Typing into or submitting an external form also
   needs the owner's chat OK naming that form (company, title, ATS); a changed
   answer needs a new OK; answers come only from the profile or that reply;
   unattended runs fill nothing. Consent, privacy and terms boxes are always
   the owner's to tick.
4. **Hard rules before fit,** on the full description. A rule mention that does
   not apply to the role is a note; unknown pay or language is a flag.
5. **Safety boundaries:** never create accounts, enter passwords or codes,
   accept terms, solve CAPTCHAs, record audio or video, take assessments, or
   guess an answer the profile lacks. Before any submit, check it was not
   already applied; journal the submit before moving the row. In a portal the
   owner signed in to, edit only that profile and apply only to named jobs.
   Neither the profile nor a routine prompt relaxes items 3, 5 and 6.
6. **Truthful CVs:** select, reorder and rephrase master-CV facts only; mirror a
   keyword only where the master CV supports it; never add a skill, employer,
   title, date, metric, degree or certification. Missing facts are
   `[FILL: ...]`; a failing kit CV is dropped; non-profile answers are `OWNER:`.
7. **Guarded writes:** pass `--expect-mtime` and `--backup-dir` on every write
   and chain the printed `mtime`; re-run `approvals` right before each batch.
   Exit 3: re-read and redo; exit 4: skip and report. Keep every sheet, column
   and owner edit.
8. **Dedup across all tabs,** Closed and Excluded included, by job id and by
   normalized company + title.
9. **Digest is the deliverable** (workflow Phase 7).
