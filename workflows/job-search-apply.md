---
description: Apply to owner-approved job-search rows - re-read approvals, move rejects, check duplicates, build kits, inspect every apply form, send the owner one batch message with the exact answers, submit only forms the owner OKs in chat, move submits to Applied in one guarded batch, and verify
---

# Job Search Apply Workflow

Use this for Phase 3 of `workflows/job-search-pipeline.md` and on demand
("apply to my approved jobs", "submit the rows I approved"). Capability:
`skills/job-search-pipeline/SKILL.md`. Form mechanics, the ATS-by-host table,
confirming a submit, and owner-only steps:
`skills/job-search-pipeline/references/apply-playbook.md`. A candidate-portal
profile the owner signed in to themselves:
`workflows/job-portal-profile-sync.md`.

All personal data comes from the candidate's profile
(`skills/job-search-pipeline/references/profile-template.md`). `tracker_ops` and
`tracker_batch` below mean `python skills/job-search-pipeline/scripts/<name>.py`.
Every tracker write passes `--expect-mtime <m> --backup-dir <paths.backup_dir>`.
The root owns every write.

**Authorization.** The tracker mark approves a row. It does not authorize typing
into or submitting a form: each form needs the owner's explicit chat OK
(Phase 6); one message may OK several named forms. Consent, privacy and terms
boxes are always the owner's to tick. Never create accounts, enter passwords,
request email codes, or solve CAPTCHAs. Answers come only from the profile's
standard answers, the pay policy below, or the owner's chat reply. `apply.never`
and `apply.owner_rules` apply on top, and no routine prompt relaxes any of this.

**Pay figure** (`criteria.pay.ask_policy`): posting gives no value or range ->
`no_range`; posted range or max -> `fraction_of_posted_max` x max, never
below `floor`. A numeric-only field takes one number, not a range. The policy
beats any older free-text anchor in the standard answers.

**Orchestration.** Print the tasks table first (`rules/request-orchestration.md`).
Lane F: light, haiku / medium. Lane L6 kits: standard, sonnet / medium.
Fill and submit is R2 in `references/lane-prompts.md`: the root, or a standard
lane with an explicit model that owns its own browser tab. Tracker writes stay
with the root.

In report-only mode run Phases 1 and 3 only and list the approved rows.

---

## Phase 1 - Read approvals

1. Run `tracker_ops approvals --tracker <t>`; keep the printed `mtime` as `<m>`.
2. The owner edits the tracker while you work. Re-run `approvals` and re-read
   `<m>` immediately before **every** write batch, and act on marks added since
   the last read in that same batch.
3. Sort the rows and read each row's `Decision notes`. `approve`: continue.
   `reject`: Phase 2. `later` and `pending`: leave. An `approve` row whose notes
   already say "Needs owner" is not retried; list it in the report with its
   blocker.

## Phase 2 - Rejects

Build one `move` op per reject row:
`{"op":"move","link":"<url>","to":"Excluded","detail":"<the owner's Decision notes text, else Declined by owner>"}`.
The note is kept in the Excluded detail. Re-run `approvals`, then run the ops
now with `tracker_batch` as in Phase 8 step 3, log `<working_dir>/apply-rejects.log`:
the owner's reject should not wait for a chat reply. A reject added later joins
the Phase 8 batch.

## Phase 3 - Duplicate check

For each approve row, look for an existing application in: the board's applied
list (L3 evidence, or a read-only look at the board's status page), the inbox
(L1 evidence, or a mail search by company and title), and every tracker tab
(`known`).

- Applied on the board or in the inbox, but the row is still in For Approval:
  queue a `move` op to Applied whose `detail` names the evidence. Do not submit.
- Already on Applied, Interviewing, Closed or Excluded: do not submit; tell the
  owner.
- In the pipeline run, L1 and L3 may still be running. Continue with Phases
  4-6, and start no Phase 7 submit until they have returned and this check is
  complete.

## Phase 4 - Kits

When `apply.kit_for` includes `approved`, build a kit for each approve row that
has none: `workflows/job-search-pipeline.md` Phase 5 steps 4-7 (lane L6 per row
in parallel, validate with `references/cv-tailoring.md`, write, render, record
`Apply kit`). Without `cv.master` or `cv.tailored_dir`, or when `apply.kit_for`
omits `approved`, build none and use the profile CV. Collect the posting issues
the kits flag (local-employment benefit wording, an office location against a
remote label, a stack that differs from the title, the same text under two ids)
for Phase 6.

## Phase 5 - Inspect the forms

Dispatch lane F (`references/lane-prompts.md`, light tier, explicit model) per
approve row's apply URL, in parallel (simple ATS forms; gated portals). It is
read-only and returns the final URL and ATS, whether the posting is open,
whether an account, login or email code is needed, a visible CAPTCHA, every
field (label, type, required, options), consent boxes, resume formats, and the
cover-letter field. Classify each row with the host table in `apply-playbook.md`:

- **Fillable**: no account or code, no CAPTCHA to solve. Board quick-apply
  counts when `apply.board_quick_apply` allows it; otherwise owner-only.
- **Owner-only**: account, password, email code, CAPTCHA, talent network,
  signed-in portal, OAuth prefill, recordings or assessments. If the owner signs
  in to a candidate portal and asks you to work in that session, run
  `workflows/job-portal-profile-sync.md` for the forms they name.
- **Closed or failed**: posting closed, form unreachable. Record why.

## Phase 6 - One batch message to the owner

Send the message as plain text first, in full, then ask the question in a
separate turn (text placed before a question widget is not shown). Contents:

1. Each fillable form: company, title, ATS, link, the CV (the kit's rendered CV
   when it validated, else the profile CV) and cover note to attach, and the
   **exact answers to be typed** with their source: work authorization,
   sponsorship, pay figure, English level, contract type, each yes/no. A question with no standard answer is an `OWNER:` line to answer.
2. Owner-only items, each with link, reason and kit path. Where a required
   consent box blocks submit, offer: "fill everything, leave the tab open, you
   tick consent and press Submit".
3. Posting issues from Phase 4, so the owner can drop a row before it is sent.
4. The question: which named forms to submit, which to fill and leave open,
   which to skip.

Submit nothing without the reply. In an unattended run, send the message as the
digest section and stop: the rows stay approved for the next run.

## Phase 7 - Fill and submit (per OK'd form)

1. Re-run `approvals` and repeat the duplicate check for this row: a mark the
   owner removed, or an application that has appeared, ends it.
2. Open the form in your own tab and fill it with the `apply-playbook.md`
   mechanics. Type only the answers in the batch message. A field the message
   did not cover stops the form: ask the owner and keep the row.
3. "Fill and leave open" forms: stop before consent and Submit; tell the owner
   which tab. The row is not Applied until a confirmation shows.
4. Submit, then confirm with the playbook's signals (confirmation page, "received"
   mail, board status). Anything less is not a submit.
5. Journal first: add `{link, channel, date, detail}` to `pending_moves` in
   `<working_dir>/job-scan-state.json`. Run Phase 8 after each group of submits,
   not only at the end.

## Phase 8 - Move and annotate (one guarded batch)

1. Re-run `approvals`; set `<m>` to the fresh `mtime`.
2. Write `<working_dir>/apply-ops.json` from Python or with an explicit UTF-8
   encoder (a PowerShell `>` writes UTF-16). Ops, in this order:
   - rejects added since Phase 2, and duplicates found in Phase 3 (a `move` to
     Applied whose `detail` names the evidence);
   - each confirmed submit:
     `{"op":"move","link":"<url>","to":"Applied","detail":"<channel>; CV: <kit or profile>; <answers that matter>","channel":"<channel>","date":"<YYYY-MM-DD>"}`;
   - each row left to the owner:
     `{"op":"set","link":"<url>","column":"Decision notes","value":"[<agent> <date>] Needs owner: <reason>","sheet":"For Approval"}`.
3. Run `tracker_batch --tracker <t> --ops <apply-ops.json> --expect-mtime <m>
   --backup-dir <paths.backup_dir> --log <working_dir>/apply-batch.log`. Add
   `--plan` first to preview. It chains the ops, passes each `mtime` forward,
   logs one line per op, stops at the first failure, and prints
   `{"ok":n,"failed":<index|null>,"mtime":m}`. If the call times out, read the
   log; do not re-run. Fix the cause of a `failed` index, then re-run with
   `--resume` (it continues from the first op not logged OK).

## Phase 9 - Verify and report

1. `tracker_ops approvals`: the submitted rows are gone from For Approval.
   `tracker_ops repair --dry-run` shows no orphans and no link fixes. Read the
   tail of Applied and confirm each new row and its detail line.
2. Remove the moved entries from `pending_moves`.
3. Standing owner rules: free text in the `Decision notes` read in Phase 1 ("do
   not apply to <company> any more", "looks like employment-contract only") is a
   standing rule. When the words are explicit, propose adding the company to
   `criteria.blocked_companies` (or a new hard rule) and edit the profile once
   the owner agrees. List every question that lacked a standard answer, as a
   proposed standard-answers addition.
4. Close the tabs you opened. Delete scratch files only inside `working_dir`.
5. Report: submitted (company, title, channel, CV used); filled and left open;
   owner-only with link and kit path; rejects moved; duplicates; blockers.

## Failure handling

| Situation | Action |
| --- | --- |
| Validation error after submit, or no confirmation signal | Treat as not sent. Fix the field, retry once, re-check the board before another try. Never journal it. |
| Browser disconnected or tab lost mid-form | Re-open, reload to see the true state ("already applied" counts as sent), then journal or restart the form. |
| Owner does not answer the batch message | Stop before any submit. Rows stay approved; report them. |
| Required consent box, account, code or CAPTCHA | Owner-only. Write the `Needs owner` note; offer "fill and leave open". |
| `tracker_batch` or `tracker_ops` exit 3 | The file changed. Re-read (Phase 1), rebuild the ops from the fresh marks, re-run. Never force. |
| `tracker_batch` or `tracker_ops` exit 4 | File open or locked. Keep `pending_moves`, report the blocker, retry next run. |
| `failed` index in `tracker_batch` output | Journal stays. Fix the cause, re-run with `--resume`. |
| Lane F fails twice, or the form cannot be read | Classify the row owner-only; never fill an uninspected form. |
| Posting closed or listing removed | Do not submit. Note it in the report; leave the row for the owner. |

## Final Step - Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before
closing. Put candidate-specific lessons in the profile or the candidate's
notes, not in this toolkit.
