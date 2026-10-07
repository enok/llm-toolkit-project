---
description: Run one job-search scan for a candidate profile - reconcile inbox and board status, apply owner-approved rows, discover and screen new postings, update the xlsx tracker safely, map skill gaps, and send a ranked digest
---

# Job Search Pipeline Workflow

Use this for a scheduled or on-demand job scan ("run my job scan", "daily job
pipeline", "check my applications and find new jobs"). Capability:
`skills/job-search-pipeline/SKILL.md`. First-time setup for a new candidate:
`workflows/job-search-setup.md`.

All personal data comes from the candidate's profile
(`skills/job-search-pipeline/references/profile-template.md`). Instructions in
the routine prompt override the profile for that run only. They can never
relax the skill's safety contract: owner-only approval; no accounts,
passwords, terms, or CAPTCHAs; no guessed answers.

`tracker_ops` below means
`python skills/job-search-pipeline/scripts/tracker_ops.py`. Every write passes
`--expect-mtime <m> --backup-dir <paths.backup_dir>`. After each write, set
`<m>` to the `mtime` the write prints.

---

## Phase 0 - Start and orchestrate

1. Record the start time (`date -u +%s` or equivalent) for the elapsed line.
2. Load `rules/request-orchestration.md` and `tool-subagents/agent-orchestrator.md`.
   If the subagent file is unreadable, apply the rule alone and say so in the digest.
3. Read the profile. If any required field (marked `# required` in the
   template) is missing, or the routine asks for `report-only`, run in
   **report-only mode**: no tracker writes, no applications, no moves, and a
   digest labelled `REPORT-ONLY`.
4. Check that the tracker path (local bridge or drive connector), the mail
   connector, and the browser session are reachable. Each unreachable piece
   becomes a blocker line, and the run continues with what is reachable.
5. Print the tasks table with these columns: lane, tier, explicit
   model/effort, wave, validator, and status. Use the lane table in
   `skills/job-search-pipeline/references/lane-prompts.md`. The root owns
   writes.

## Phase 1 - Snapshot the tracker and run state

1. Run `tracker_ops known --tracker <t> --out <working_dir>/known.json`, then
   `tracker_ops approvals --tracker <t>`. Keep the printed `mtime` as `<m>`.
2. Read `<working_dir>/job-scan-state.json`. It holds `last_successful_run`
   and `pending_moves`. With no state file, use the profile `cadence.window`.
   The inbox window starts one day before `last_successful_run`, so a missed
   or failed run loses no evidence.
3. Retry every `pending_moves` entry first: rows that were submitted but never
   moved.

## Phase 2 - Wave 1 read-only lanes (parallel)

Dispatch these from `skills/job-search-pipeline/references/lane-prompts.md`,
each with its explicit model:

- L1 inbox;
- L2 board discovery and screening, given `known.json`;
- L3 board application status;
- optionally L4 side gigs.

While they run, the root starts Phase 3.

## Phase 3 - Approvals (root)

For each `approve` row:

1. Skip rows whose `Decision notes` record a blocker the owner must clear.
   Carry them into the digest.
2. **Before any submit**, re-run `approvals` to confirm the owner's mark still
   stands. Then check the board's applied list and the inbox for an existing
   application. If one exists, record it as applied and do not submit again.
3. Board quick-apply: submit with the CV and the profile's standard answers.
   If a question has no standard answer, stop, keep the row, and list the
   question in the digest.
4. External ATS: fill only what works without an account or password.
   Otherwise leave the link for the owner.
5. After a confirmed submit, write the journal entry first: add
   `{link, channel, date}` to `pending_moves` in the state file. Then run
   `tracker_ops move --link <url> --to Applied --channel <channel>` and drop
   the journal entry once that succeeds.

`reject` rows: `move --to Excluded --detail "Declined by owner"`. `later` and
`pending` rows: leave them. Enforce `apply.never` and `apply.owner_rules` on
top of the skill contract.

## Phase 4 - Reduce lane output and update the tracker (root)

1. Judge each lane for evidence, scope, and consistent counts. Return the
   defect list for a bounded refine (`workflows/task-quality-loop.md`).
2. Stage moves from L1 and L3 evidence follow the transition table in
   `skills/job-search-pipeline/references/tracker-schema.md`:
   - to Interviewing: `move --to Interviewing --interview-stage <s> --interview-date <d> --detail <evidence>`;
   - to Closed: `move --to Closed --outcome <Rejected|No response|Withdrawn|Offer> --detail <evidence>`.

   A status text on its own is not a move.
3. Re-verify every L2 kept posting with an in-page hard-rule keyword scan.
   Then write `kept.json` and `excluded.json`, using the jobs JSON schema in
   `tracker-schema.md`. Run `append --jobs kept.json --cv-skill <each
   profile.cv_skills>`, then `exclude --jobs excluded.json`. Report any
   `ignored_keys`.
4. On exit 3, re-read (Phase 1 step 1), redo the step, and never force. On
   exit 4 the file is open or locked: skip the writes and add a digest
   blocker.

## Phase 5 - Skill gaps and study plan (root, optional)

Act according to `study_plan.mode`:

- `gaps`: run `tracker_ops gaps --rules <study_plan.rules>` and collect `repeated_gaps`.
- `command`: copy `study_plan.inputs` into `working_dir` and run the command
  there. Verify its output. Copy back only the `commit_back` files, after an
  mtime check. Never run anything in `study_plan.retired`. If a prerequisite
  is missing, skip this phase and say so.
- `none`: skip this phase.

## Phase 6 - Side gigs (optional)

If `side_gigs.enabled`, write a JSON list built from L1 and L4 evidence and
run `tracker_ops sidegig --data <json>` to upsert rows by platform.

- Add a platform only if all three hold: it meets `side_gigs.floor`, it pays
  in `side_gigs.currency`, and it accepts the candidate's location.
  Otherwise list it as excluded, with the reason.
- Mirror the changes into `side_gigs.mirror_json` when that is set.
- Never create accounts or accept terms.

## Phase 7 - Digest and close

1. Compute elapsed = now - start, formatted as `Xh Ym` or `Y min`.
2. Send one message on `notify.channel` with the subject `notify.subject`.
   Include:
   - new positions, ranked by tier, fit, and readiness, each with its link, a
     one-line reason, and flags;
   - applications sent, and the ones that need the owner (blocker plus link);
   - stage moves and upcoming interviews;
   - side-gig changes;
   - skills that are a GAP in 2+ jobs;
   - blockers and run notes;
   - `notify.last_line` as the last line.

   If nothing changed, send one line saying so, plus the elapsed line. If the
   profile was unreadable, send the digest to the routine prompt's target or
   in the session reply.
3. In an unattended run the digest is the notification. Send a push as well
   only if the profile asks for one.
4. Write `last_successful_run` to the state file, but only when Phases 1-4
   completed. Close any browser tabs you opened. Delete scratch files only
   inside `working_dir`.
5. End the final reply with the same elapsed line.

## Failure handling

| Situation | Action |
| --- | --- |
| Profile unreadable | No writes. Send the digest via the fallback target and stop. |
| Tracker locked or changed mid-run | Retry the read once, then skip the writes and report it. |
| Browser or board unavailable | Skip L2 and L3. Run the inbox and approvals parts only; no submits without the board check. |
| Mail connector unavailable | Skip L1 and the stage moves, and say so. Keep the state window unchanged. |
| A lane exceeds its SLA or fails validation twice | Escalate one tier per the orchestration contract, or report it. |

## Final Step - Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before
closing. Put candidate-specific lessons in the profile or the candidate's
notes, not in this toolkit.
