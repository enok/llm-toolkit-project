---
description: Complete or fix the owner's profile on a job board or candidate portal in the owner's own signed-in browser session - survey read-only, compare with the profile and master CV, fix unambiguous errors, propose the rest, apply approved edits, verify after reload, optionally apply to named openings, and report what stays owner-only
---

# Job Portal Profile Sync Workflow

Use this when the owner says they are signed in to a job board or candidate
portal and asks you to complete or fix their profile there ("I'm logged in,
finish my profile"), optionally followed by applying to named openings.
Capability: `skills/job-search-pipeline/SKILL.md`.

Related files:

- form mechanics (Angular Material, react-select, file inputs, JS quirks):
  `references/apply-playbook.md`;
- applying to rows the owner approved in the tracker:
  `references/apply-playbook.md`;
- chained tracker writes: `skills/job-search-pipeline/scripts/tracker_batch.py`;
- profile schema: `skills/job-search-pipeline/references/profile-template.md`;
- truthfulness rule and master CV: `skills/job-search-pipeline/references/cv-tailoring.md`.

Sources of truth, in this order: the owner's chat messages in this session, the
profile (`criteria.pay.ask_policy`, `candidate.standard_answers`), the master CV
(`cv.master`), then the CV audit (the master CV's red-flag findings and any
claim marked unconfirmed). A portal value never overrules them.

Safety contract. The owner's own signed-in session is the only way in:

- Never sign in, create an account, enter a password, request or enter a
  verification code, or solve a CAPTCHA.
- Never record audio or video, take an assessment, or tick consent, privacy or
  terms boxes. These stay with the owner.
- Never guess a value. It comes from the owner's chat, the standard answers, or
  the pay policy; otherwise it is `OWNER:`.
- Stay on the portal and the openings the owner named. Other tracker rows still
  need the owner's mark in the tracker.

---

## Phase 0 - Orchestrate and check preconditions

1. Load `rules/request-orchestration.md` and
   `tool-subagents/agent-orchestrator.md`. If the subagent file is unreadable,
   apply the rule alone and say so in the report. Print the tasks table before
   any work. The tab is the owner's session, so the root drives the browser and
   owns every portal edit and tracker write:

   | Task | Tier | Model / effort | Wave | Validator |
   | --- | --- | --- | --- | --- |
   | S1 read-only survey (Phase 1) | light (retrieval) | haiku / medium | 1 | every section has a value or "not shown" |
   | S2 compare and classify (Phase 2) | standard (rules against sources) | sonnet / medium | 2 | each gap has a class and evidence |
   | R1 proposal message (Phase 3) | frontier (root, user-facing) | session model / high | 3 | every row has before, proposed, evidence |
   | R2 portal edits and re-read (Phase 4) | standard (root, form work) | sonnet / medium | 4 | reload shows the intended value |
   | R3 applications (Phase 5, optional) | standard (root) | sonnet / medium | 5 | job page shows "already applied" after reload |
   | R4 tracker moves (Phase 5) | light (script runs, root owns writes) | haiku-class | 5 | script exit code and JSON |

2. Confirm the preconditions. The owner stated that they are signed in and
   named the browser. Open the portal's profile page in that browser. If it
   shows a sign-in, account-creation or code page, stop and ask the owner to
   sign in. Open your own tab and close it at the end.
3. Read the profile, the standard answers, the master CV, and the CV audit. If
   there is no master CV, survey and report only: no skill, date or title
   proposals.

## Phase 1 - Survey (read-only)

Read each section below with page text or page reads. Click only to navigate or
expand. Save the current values, unedited, to `<working_dir>/portal-survey.md`.

| Section | Capture |
| --- | --- |
| Contact | name, email, phone with country code, location, time zone, links |
| Work experience | per entry: title, employer, start, end, "current" flag, description |
| Availability and compensation | notice, hours, contract types, expected pay with currency and period, last salary, connection speed |
| Skills | per skill: name and years or level bucket; the buckets the portal offers |
| Intro recording | present or missing; which step it blocks |
| Assessments | each test with its state |
| Openings and applications | list, status of each, applied or not |
| Completeness | the portal's indicator and every item it says is missing |

Mark each field editable, read-only, or mandatory, and note each editor's UI
technology. A section you cannot read is a blocker line, not a guess.

## Phase 2 - Compare with the sources and classify

Compare each survey value with the sources of truth, then give every gap one
class and its evidence:

| Class | Definition | Action |
| --- | --- | --- |
| (a) data error | Unambiguous: another field or the CV proves it. Example: a phone saved with the country code twice, a missing digit, a misspelled employer | Fix directly in Phase 4 |
| (b) owner-stated | The owner gave the value in chat in this session | Apply in Phase 4 |
| (c) everything else | Dates or titles that differ from the CV, skill years, pay expectation, descriptions, a "current" flag, an empty optional field | Propose in Phase 3 |

Rules:

- Expected pay comes from `criteria.pay.ask_policy`, which beats any older
  free-text anchor in the standard answers. A portal field with no range uses
  `no_range`; with a range or posted maximum, `fraction_of_posted_max` times
  that maximum, never below `floor`. A numeric-only field takes one number.
- Owner-only fields: last salary, exact start day, recordings, assessments,
  consent boxes. Mark them `OWNER:` and do not fill them. Use the first day of
  a month only if the owner agrees, and report it.
- If the latest role has ended but the portal still shows it as "current",
  propose the real end date as a class (c) row and remind the owner that
  employment verification compares profile dates with records
  (`skills/job-search-pipeline/references/application-truthfulness.md`). Never set or keep a "current" flag on
  the owner's behalf.
- Never add a skill, employer, title, date or metric that the master CV lacks.

## Phase 3 - Proposal (two separate turns)

1. Send ONE plain message with the full list. Group it as "Applying now" for
   classes (a) and (b), and "Needs your decision" for class (c). Each row:
   section, field, before, proposed, evidence (CV role and dates, standard-answer
   key, or policy). Add the `OWNER:` items. Do not put it inside a question
   widget or after one.
2. Skill-years rule. For each skill the CV states, count from the earliest
   master-CV role that uses it to today. Round down to the portal's bucket. List
   the evidence role per bucket. Skip any claim the CV audit flags as
   unconfirmed. Never add a skill that the CV lacks, even if the portal offers it.
3. In a separate, short turn ask the decision: "Apply all of 'Needs your
   decision', or tell me which rows to change?". Text placed before a choice
   widget may not be visible, which is why the list is its own message.
4. Apply nothing in class (c) until the owner answers. A partial answer approves
   only the rows it names.

## Phase 4 - Apply and verify

1. Classes (a) and (b) need no answer: start them once the Phase 3 message is
   sent. Apply approved class (c) edits after the owner replies. Edit one field
   at a time with the portal's own editors; never call hidden APIs or read
   stored cookies or tokens.
2. Follow `references/apply-playbook.md` for the editor's technology. For
   Angular Material (`mat-select`), each change autosaves, so reload the page
   every 2 changes. Open the select with a script click on `.mat-select-trigger`
   in a freshly loaded page. Click the option inside the panel named by the
   select's `aria-controls` (take the last element with that id that holds
   `mat-option` items). Prefer element refs over coordinates, because the page
   scrolls an inner container.
3. Click the portal's Save for the section. After saving, reload and re-read each
   edited field. A mismatch gets one retry, then it goes in the report.
4. Append every change to `<working_dir>/portal-sync-log.md` as section, field,
   before, after, verified. Do not touch fields the owner did not approve.
5. If the session expires mid-run, stop and ask the owner to sign in again.

## Phase 5 - Applications to named openings (optional)

Run this only for openings the owner named in chat in this request. For tracker
rows the owner approved but did not name, follow `references/apply-playbook.md`.

1. For each opening, reload its job page. If it shows "already applied", record
   it as applied and do not click Apply.
2. Check that every question has an answer from the standard answers, the pay
   policy, or the owner's chat. Otherwise list `OWNER:` and skip that opening.
3. Take a screenshot, then click Apply once. If the click was not registered,
   take a screenshot and click again. Confirm by reloading the page and reading
   the applied state. Never count a click as a submit without that reload.
4. Tracker moves. Re-run `approvals` and read the mtime immediately before the
   batch. Write each confirmed opening to `pending_moves` in the state file
   first. Then run the `move --to Applied --channel <portal>` operations through
   `tracker_batch.py` (it chains the mtime, logs one line per operation, and
   stops on the first failure). Drop the journal entries after success. List an
   opening that has no tracker row; do not invent one.

## Phase 6 - Report

1. Send one message:
   - the changes table: section, field, before, after, verified;
   - items still owner-only: recordings, assessments, last salary, exact dates,
     consent boxes, any `OWNER:` answer;
   - portal status: the completeness indicator and what it still lists. A
     profile can stay "incomplete" until a recording is done, and the openings
     list can stay empty although each job page shows the application;
   - applications made, already applied, and skipped, with the reason;
   - tracker moves and any `pending_moves` left;
   - blockers.
2. Standing owner rules said in chat, such as a new salary-answer policy, an
   accepted contract type or a work-authorization answer, become proposed edits
   to `criteria.pay.ask_policy` or the standard answers. Show them as a diff.
   The root edits the profile only after the owner confirms. Recommend adding
   every question the portal asked that had no standard answer.
3. Close the tabs you opened. Delete scratch files only in `working_dir`.

## Failure handling

| Situation | Action |
| --- | --- |
| Renderer freezes after several dropdown changes | Reload, re-read what saved, resume from the next change |
| Save shows a mandatory-field error on an empty optional pair | Set the paired type field, or clear both, then save again |
| Apply click not registered | Screenshot, click again, verify by reload |
| Natural-language element finder is rate-limited | Use `querySelector`, `scrollIntoView` and `read_page` refs; coordinates from a fresh screenshot last |
| Browser pane is hidden (0 by 0 viewport) | Ask the owner to show it, or use the other browser |
| Script output truncated or blocked | Return compact strings; render bulk data into a `<pre>` and read it as page text; never strip or encode characters to pass the filter; await async work at top level |
| Sign-in page appears | Stop; the owner signs in again |
| Field is read-only or has no editor | Report it as owner-only |
| Tracker locked or mtime changed | Re-read once, then skip the writes and report them |

## Final Step - Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before
closing. Put portal-specific lessons in the profile or the candidate's notes,
not in this toolkit.
