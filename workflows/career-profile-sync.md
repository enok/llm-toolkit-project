---
description: Keep employment facts, skills, and certifications consistent across a public profile, the CV and its master, and job-search working files (for example "sync my CV with LinkedIn") - ledger first, one-pass update list with intentional snapshots, profile edits, CV re-render and visual check, truthfulness review, hash-checked device writes
---

# Career Profile Sync Workflow

Use when a career fact changes ("I left that employer", "set the end date",
"add this skill and project", "I earned this certification", "drop the old
courses") or when asked to "sync my CV with LinkedIn", and the same fact appears
in more than one place. The recurring
job-search runs are `workflows/job-search-pipeline.md` and
`workflows/job-search-setup.md`; they read the files this workflow keeps in
step. Public-profile mechanics live in
`skills/linkedin-profile-maintenance/SKILL.md`.

Everything personal (employers, dates, titles, handles, file locations) comes
from the owner and their files, never from this workflow. Every edit to a
system outside the working folder is an external write bound to the owner's
current instruction (`rules/external-write-authorization.md`).

---

## Phase 0 - Orchestrate

Follow `rules/request-orchestration.md` and `tool-subagents/agent-orchestrator.md`:
print the wave-ordered tasks table with tier and explicit model per task. The
root owns every write and the browser session. Read-only lanes (evidence mining,
cross-file consistency search) may run in parallel; the truthfulness review in
Phase 5 is a different invocation than whoever produced the text
(`workflows/task-quality-loop.md`).

## Phase 1 - Read the ledger and the current state first

Instructions about the same fact can conflict across parallel sessions or chat
branches ("keep the end date open", then "set the end date").

1. Read the shared ledger (`CONTEXT_STATE.md`, `TASKS_TABLE.md`, or the owner's
   notes) and any prior-session summary.
2. Read the current text of every affected file and, read-only, the current
   public profile. State the fact as it stands now, in each place.
3. Apply the latest explicit instruction from the owner. Record a reversal in
   the ledger (what changed, which instruction supersedes which) and tell the
   owner. Never act on a remembered instruction without checking the ledger.

## Phase 2 - One-pass update list and intentional snapshots

Build both lists before editing anything, and get the owner's approval.

1. **Fact sheet.** For each changing fact: the new value, its source (the
   owner's words, a document, the repository), and the old value.
   Employment facts include end dates, current versus past tense, titles,
   "available immediately" and notice-period wording.
2. **Update list.** Every place the fact lives, for example: public profile
   experience, skills, certifications and projects; the CV and its master CV;
   the standard-answers file; the targeting or role-ranking file; job-scan
   profile files and their comments; and applicant portals (ATS). Search the
   working folder for the old value and its variants so nothing is found later by
   accident. Each row: location, old text, new text.
3. **Intentionally unchanged snapshots.** Old CV versions, sent messages,
   application kits, audits, and interview notes record what was true or sent at
   the time. List them with the reason they stay as they are, so a later search
   hit there is not mistaken for a miss.
4. Present both lists in a plain message of their own, then wait for the go.

## Phase 3 - Apply the edits

Update every row of the list in this one pass; a fact fixed in some places but
not others is the failure this workflow exists to prevent.

1. **Local files.** Edit the master CV first, derive the CV from it, then the
   standard answers, targeting, and job-scan profile files. Update source and
   HTML comments as well as visible text: a stale comment can contradict the
   page.
2. **Public profile.** Use `skills/linkedin-profile-maintenance/SKILL.md`:
   inventory, backup, owner approval, one item at a time, re-read. The owner's
   signed-in browser is used; the agent never signs in or passes a bot check.
3. **Applicant portals.** Each portal is an external write in the owner's
   account. Prepare the exact values per portal and hand them to the owner, or
   edit only where the owner has an open session and approved that portal.
4. **Counts and derived numbers** quoted in any document are recomputed from the
   source they summarise, not copied from a README or an earlier draft. See
   `learnings/readme-catalog-counts-drift-from-disk.md`.

## Phase 4 - Re-render the CV to its page budget

When the CV changed, regenerate it with the CV project's own render script
(named in its README or ledger) at the owner's page budget and paper size, then
check the result; do not assume the edit left the layout intact.

1. Re-render, then read the page count and any "N of M" footer.
2. Inspect the page images (`skills/image-quality-inspection/SKILL.md`), not
   only the text: look for overflow, orphaned headings, and blank bands.
3. Keep-with-next rules can leave several blank lines at the bottom of a page.
   Levers that worked:
   - merge skill-group lines;
   - move languages into the contact line;
   - tighten bullets whose last line holds only one to three words.
4. Re-render after every layout change and repeat the checks.

## Phase 5 - Truthfulness review

Dispatch `tool-subagents/cv-truthfulness-reviewer.md` (read-only; `standard`
tier, explicit model per the orchestrator's client map) with the CV, the master
CV, the profile export or read-back, and the repository facts the CV cites. It
compares the text with the evidence: claims, dates and titles, verb strength,
open-source wording, counts from disk, stale comments, and employment status
across files. Fix every UNSUPPORTED or CONTRADICTED claim and narrow PARTIAL
ones, then re-run within the loop budget of `workflows/task-quality-loop.md`;
unresolved items go to the owner with the evidence.

## Phase 6 - Device writes and protected folders

When files travel between a cloud session and the owner's machine:

1. Stage every commit in a fresh staging subfolder, never re-commit under a
   path already used, and verify the SHA-256 on the machine through the device
   shell before trusting the file. See
   `learnings/device-commit-to-existing-path-can-keep-stale-bytes.md`.
2. If `skills/` or `tool-subagents/` is unreadable through the bridge, read
   through a cloud clone; to run a script from a protected folder, copy it to a
   non-protected folder first and park the copy for deletion afterwards. See
   `learnings/cowork-bridge-hides-skills-dirs-read-via-cloud-clone.md`.

## Phase 7 - Cross-check and report

1. Search every location on the update list for the old value and its variants
   ("present", "currently", the old end date, "available immediately"). Remaining
   hits must all be on the intentionally-unchanged list.
2. Report in one message: rows changed (location, old, new), snapshots left as
   they are and why, portals handed to the owner, the reviewer's verdict, the
   CV page count and visual-check result, hash checks, and the backup location
   for any profile deletes.
3. Append the run to the ledger, including any reversal recorded in Phase 1.

---

## Known pitfalls

- Conflicting owner instructions across sessions: Phase 1.
  (sig: coordination/conflicting-owner-instructions-across-sessions)
- A fact updated in only some places: Phases 2 and 3.
  (sig: spec-gap/employment-fact-updated-in-one-place)
- CV layout not checked on the page images: Phase 4.
  (sig: validation-gap/cv-layout-not-visually-checked)
- Catalog counts drift from disk. See
  `learnings/readme-catalog-counts-drift-from-disk.md`.
- A re-committed staged path can keep old bytes. See
  `learnings/device-commit-to-existing-path-can-keep-stale-bytes.md`.
