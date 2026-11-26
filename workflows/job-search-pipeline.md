---
description: Run one job-search scan for a candidate profile - reconcile inbox and board status, apply owner-approved rows, discover, screen and ATS-score new postings, update the xlsx tracker safely, shortlist and build apply kits, map skill gaps, and send a ranked digest
---

# Job Search Pipeline Workflow

Use this for a scheduled or on-demand job scan ("run my job scan", "daily job
pipeline", "check my applications and find new jobs"). Capability:
`skills/job-search-pipeline/SKILL.md`. First-time setup for a new candidate:
`workflows/job-search-setup.md`. Online-sheet tracker: `references/sheet-tracker-mode.md`.

On demand: approved rows are `workflows/job-search-apply.md`; one posting's
apply kit is Phase 5 steps 4-7; best-fit roles, ATS keywords, or an XYZ-format
CV rewrite is `workflows/job-search-setup.md` Phase 2 step 5.

All personal data comes from the candidate's profile
(`skills/job-search-pipeline/references/profile-template.md`). Instructions in
the routine prompt take precedence over the profile for that run only. They
can never relax the skill's safety contract: owner-only approval; truthful
CVs; no accounts, passwords, terms, or CAPTCHAs; no guessed answers.

`tracker_ops`, `tracker_batch` and `render_cv` below mean
`python skills/job-search-pipeline/scripts/<name>.py`. Every tracker write
passes `--expect-mtime <m> --backup-dir <paths.backup_dir>`; after each write set
`<m>` to the printed `mtime`. For many moves or sets (Phase 4 step 2, Phase 5
step 7) use `tracker_batch --tracker <t> --ops <ops.json> --expect-mtime <m>
--backup-dir <dir> --log <file> [--resume]`: it chains the ops, logs each, stops
at the first failure, prints `{"ok","failed","mtime"}`, and exits like
`tracker_ops`; op shapes: `workflows/job-search-apply.md` Phase 8. Run child
processes with `encoding='utf-8', errors='replace'` and
`PYTHONIOENCODING=utf-8` (a non-ASCII dash in a title once crashed a run after
`append` succeeded).

---

## Phase 0 - Start and orchestrate

1. Record the start time (`date -u +%s` or equivalent) for the elapsed line.
2. Load `rules/request-orchestration.md` and `tool-subagents/agent-orchestrator.md`.
   If the subagent file is unreadable, apply the rule alone and say so in the digest.
3. Read the profile. If any required field (marked `# required` in the
   template) is missing, or the routine asks for `report-only`, run in
   **report-only mode**: no tracker writes, no applications, no moves, no
   apply kits, and a digest labelled `REPORT-ONLY`.
4. Check that the tracker (local bridge or drive connector), the mail
   connector, and the browser session are reachable. Each unreachable piece
   is a blocker line; the run continues with the rest.
5. Print the tasks table (lane, tier, explicit model/effort, wave,
   validator, status) from the lane table in `references/lane-prompts.md`.
   The root owns writes.

## Phase 1 - Snapshot the tracker, run state, and targeting

0. Duplicate-run guard. A `<working_dir>/run-in-progress.lock` younger than 6
   hours, or a `counted_<run date>` marker in the state file, means another run
   is active or done today: run **report-only** as a supplement and never count
   query stats again. Otherwise create the lock with the start time (replace a
   stale one).
1. Run `tracker_ops known --tracker <t> --out <working_dir>/known.json`, then
   `tracker_ops approvals --tracker <t>`. Keep the printed `mtime` as `<m>`.
2. Read `<working_dir>/job-scan-state.json`. It holds `last_successful_run`,
   `pending_moves`, `targeting_refreshed`, and `cv_mtime`. With no state
   file, use the profile `cadence.window`. The inbox window starts one day
   before `last_successful_run`, so a missed run loses no evidence.
3. Retry every `pending_moves` entry first: rows that were submitted but never
   moved.
4. Targeting refresh, when `targeting.refresh_days` have passed since
   `targeting_refreshed` or `candidate.cv` / `cv.master` changed since
   `cv_mtime`: a standard-tier read-only lane re-derives the 20 titles and
   ATS keywords (`references/cv-tailoring.md` section 1) into
   `<working_dir>/targeting-proposal.yaml`. Record the date and mtime, and
   list the additions and removals for the owner. Runs keep the confirmed
   `targeting.roles`; the root edits the profile only after the owner confirms.

## Phase 2 - Wave 1 read-only lanes (parallel)

Dispatch these from `references/lane-prompts.md`, each with its explicit model:

- L1 inbox;
- L2 board discovery and screening, given `known.json`, per board in
  `search.boards` that is due today (`cadence` `daily`, the default, or
  `weekly:<Mon..Sun>`), except Indeed. Queries: `search.queries` plus every
  `targeting.roles[].title` when `targeting.queries_from_roles` is true,
  deduplicated; a board's own `queries` replace them;
- L5 Indeed, same input, only when `indeed` is in `search.boards` and due today;
- L3 board application status;
- optionally L4 side gigs.

While they run, the root starts Phase 3.

## Phase 3 - Approvals (root)

Run the **job-search-apply** workflow (workflows/job-search-apply.md) in full.
It runs while the Wave 1 lanes run and submits nothing before their L1 and L3
evidence feeds its duplicate check. A submit needs the owner's per-form chat
OK; the tracker mark alone is not enough.

## Phase 4 - Reduce lane output and update the tracker (root)

1. Judge each lane for evidence, scope, and consistent counts. Send the
   defects back for a bounded refine (`workflows/task-quality-loop.md`).
2. Stage moves from L1 and L3 evidence follow the transition table in
   `references/tracker-schema.md` (batch them):
   - to Interviewing: `move --to Interviewing --interview-stage <s> --interview-date <d> --detail <evidence>`;
   - to Closed: `move --to Closed --outcome <Rejected|No response|Withdrawn|Offer> --detail <evidence>`.

   A status text on its own is not a move.
3. Re-verify every kept posting with an in-page hard-rule keyword scan. For
   each kept row, set `ats_match` and `missing_keywords`
   (`references/cv-tailoring.md` section 4): computed against `cv.master`
   when set, which replaces the lane estimate; otherwise spot-check it.
4. When `apply.kit_for` includes `tier_A`, build kits for Tier A kept rows
   now (Phase 5 steps 4-7) so their `apply_kit` goes into `kept.json`.
5. Write `kept.json` and `excluded.json` with the jobs JSON schema in
   `tracker-schema.md`. Run `append --jobs kept.json --cv-skill <each
   profile.cv_skills>` (it fills `ATS match %`, `Missing keywords`, and
   `Apply kit`), then `exclude --jobs excluded.json`. Report `ignored_keys`. Write
   `counted_<run date>` to the state file so a second run today skips the
   query stats.
6. On exit 3, re-read (Phase 1 step 1), redo the step, and never force. On
   exit 4 the file is open or locked: skip the writes and add a digest
   blocker.

## Phase 5 - Queue hygiene and apply kits (root)

1. If `queue.expire_unreviewed_days` is set, run `expire --days <n> --today
   <run date in candidate.timezone>` (`--dry-run` in report-only mode). It
   moves only unmarked rows; report the count.
2. If `queue.shortlist_size` is set, run `shortlist --size <n>` (read-only)
   and keep its JSON for "Approve today". A shortlist is a suggestion, never
   an approval: it sets no mark, and Phase 3 submits only owner-marked rows.
3. Kit targets: rows matching `apply.kit_for` (`approved`, `tier_A`,
   `shortlist`) that have no kit: no `Apply kit` cell and no
   `*-<company-slug>-<title-slug>` folder in `cv.tailored_dir`. Without
   `cv.master` or `cv.tailored_dir`, build no kits and say so.
4. Dispatch L6 (`lane-prompts.md`) per target, in parallel. It writes kit
   files only to a root-named scratch folder; never owner files, sends or applies.
5. Validate each kit with `references/cv-tailoring.md`. A CV line that breaks
   the truthfulness rule is a defect: one bounded refine, then drop the kit's
   CV. `cover-note.md` stays within 150 words; `answers.md` uses only standard
   answers, and an unknown answer is `OWNER:`.
6. Copy the validated L6 files to
   `<cv.tailored_dir>/<YYYY-MM-DD>-<company-slug>-<title-slug>/`. Run `render_cv
   --in <kit>/cv.md --out-dir <kit> --basename cv`, adding `--pdf` when
   `cv.formats` has pdf and `--footer "<cv.pdf_footer>"` when set. Exit 2
   means a `[FILL` remains: no rendered CV; list the item for the owner.
7. Record the kit path: `apply_kit` for rows not yet appended; for rows
   already in the tracker, `tracker_ops set --link <url> --column "Apply kit"
   --value <path>`, or, if it fails, the path in the digest.

## Phase 6 - Study plan and side gigs (optional)

Study plan, according to `study_plan.mode`:

- `gaps`: run `tracker_ops gaps --rules <study_plan.rules>` and collect `repeated_gaps`.
- `command`: copy `study_plan.inputs` into `working_dir` and run the command
  there. Verify its output. Copy back only the `commit_back` files, after an
  mtime check. Never run anything in `study_plan.retired`. A missing
  prerequisite skips this part; say so.
- `none`: skip this part.

Side gigs: if `side_gigs.enabled`, run `tracker_ops sidegig --data <json>`
with a list built from L1 and L4 evidence to upsert rows by platform. Add a
platform only if it meets `side_gigs.floor`, pays in `side_gigs.currency`, and
accepts the candidate's location; otherwise list it as excluded, with the
reason. Mirror changes into `side_gigs.mirror_json` when set. Never create
accounts or accept terms.

## Phase 7 - Digest and close

1. Compute elapsed = now - start, formatted as `Xh Ym` or `Y min`.
2. Send one message on `notify.channel` with the subject `notify.subject`,
   in this order:
   - **Approve today**: the `shortlist` rows (at most `queue.shortlist_size`),
     each with tier, fit, ATS match %, link, and kit path, noting that only a
     mark in the tracker approves;
   - applications sent (the apply report), and the items that need the owner:
     blocker plus link, external-ATS rows with their kit path, `OWNER:` answers,
     `[FILL` items, and a pending targeting proposal;
   - new positions, ranked by tier, fit, ATS match %, and readiness, each
     with its link, a one-line reason, and flags;
   - stage moves, upcoming interviews, and the expired-row count;
   - side-gig changes and skills that are a GAP in 2+ jobs;
   - blockers and run notes;
   - `notify.last_line` as the last line.

   If nothing changed, send one line saying so, plus the elapsed line.
3. In an unattended run the digest is the notification. Send a push as well
   only if the profile asks for one.
4. Write `last_successful_run` to the state file, but only when Phases 1-4
   completed. Close any browser tabs you opened. Delete scratch files only
   inside `working_dir`. Remove `run-in-progress.lock` if this run created it.
5. End the final reply with the same elapsed line.

## Failure handling

| Situation | Action |
| --- | --- |
| Profile unreadable | No writes. Send the digest to the routine prompt's target, else in the session reply, and stop. |
| Tracker locked or changed mid-run | Phase 4 step 6; if the retry fails, skip the writes and report it. |
| Browser or board unavailable | Skip L2 and L3. Run the inbox and approvals parts only; no submits without the board check. |
| Mail connector unavailable | Skip L1 and the stage moves, and say so. Keep the state window unchanged. |
| A lane exceeds its SLA or fails validation twice | Escalate one tier per the orchestration contract, or report it. |
| `shortlist` or `expire` unavailable | Skip that step and say so. |
| `render_cv` fails, the PDF renderer is missing, or a kit fails validation | Keep the kit's text files, drop the failed CV or PDF (a missing renderer only drops `cv.pdf`), submit with the profile CV, and note it. |

## Final Step - Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before
closing. Put candidate-specific lessons in the profile or the candidate's
notes, not in this toolkit.
