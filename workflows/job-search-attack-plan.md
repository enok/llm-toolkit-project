---
description: Run an urgent, runway-limited job-search sprint for a candidate - two-track intake (bridge income plus target roles), posting analysis, ranked tiers, owner-approved applications with a tracker, a day-by-day plan with templates, interview prep and a resumable context file, delivered as a PDF with clickable links
---

# Job Search Attack Plan Workflow

Use this when a candidate needs results fast (short pay runway, sudden
availability) and wants an interactive sprint: "which of these jobs fit me",
"find more positions", "give me an attack plan starting tomorrow", "prepare me for
the interviews", "keep a list of everything I applied to". The unattended
recurring scan is `workflows/job-search-pipeline.md`. This workflow composes it with the skills
below instead of repeating them.

Rules in force: `rules/request-orchestration.md`,
`skills/job-search-pipeline/references/application-truthfulness.md`, `rules/external-write-authorization.md`,
`rules/human-comment-reply-gate.md`.

---

## Phase 0 - Inputs and ground rules

1. Ask once, in one batch, only what is missing: pay floor and target (currency
   and period), runway in days, work-authorization and residency facts, target
   roles and seniority, what may be said about employment status, where files and
   the tracker live, working languages.
2. Fix the ground rules and repeat them in the plan: a truthful one-line framing of
   the candidate's availability; a bridge rule (accept an offer at or above the
   bridge floor while target-pay processes keep running); a pay anchor above the
   target and a floor; never mention the runway to an employer; ask the pay range
   in the first call.
3. Print the orchestrator task table (tier and model per lane) before any work.

## Phase 1 - Intake (read-only lanes, parallel)

1. Sources: postings the candidate shares; recruiter messages in the inbox (a
   recruiter who has followed up several times is the warmest lead); board
   searches via `skills/job-search-pipeline/references/board-playbook.md`; other
   boards when the candidate asks for postings beyond one site.
2. Dispatch read-only analysis lanes (three to five postings
   each) and one inbox lane. Lanes are read-only and return the four-block
   contract.
3. Keep a known list (applied, attempted, rejected) so nothing is analyzed or
   applied twice.

## Phase 2 - Rank into tiers

| Tier | Contents |
| --- | --- |
| A - Applied | Every application the candidate confirmed, with date, link, route and status |
| B - Apply next | At or above the pay floor, best fit first; warm leads before cold ones |
| C - Bridge and boards | Lower pay but fast onboarding: local-currency roles, hourly marketplaces (vet with `skills/contract-platform-vetting/SKILL.md`), staffing agencies |
| Skip | Below floor, wrong stack, duplicates, superseded postings |

Normalize pay (foreign-currency pay with an FX range; hourly pay with a
realization factor). Answer the candidate directly: which fit, why, what to enter,
what to skip. Never claim a stack fit the profile does not support.

## Phase 3 - Applications (owner-approved, one at a time)

1. For tracker rows the owner approved, follow `skills/job-search-pipeline/references/apply-playbook.md`.
   For ad-hoc chat requests, only apply or submit when the candidate asks or
   confirms. Answer form
   questions from facts (work authorization and sponsorship per
   `skills/job-search-pipeline/references/application-truthfulness.md`); add one clarifying line where free text
   exists.
2. Use the CV file the owner named; on portals that store a résumé, confirm the
   stored file is the intended one. Enter rates per the vetting skill.
3. Never create accounts, enter passwords, accept terms or solve captchas; hand
   those to the owner with the link.
4. A form that will not advance: run `skills/web-form-submit-debugging/SKILL.md`
   (15-minute time-box), then move on.
5. Record each application in the tracker and the plan the moment the candidate
   says it was submitted. "Attempted" is a separate status from "Applied".

## Phase 4 - Résumé and profile

- A profile export is not a résumé. Build a two-page ATS-safe CV (summary with
  metrics, skills grid, bullets weighted by recency, older roles collapsed) as PDF
  plus an editable DOCX using `skills/job-search-pipeline/references/cv-tailoring.md`
  and `skills/job-search-pipeline/scripts/render_cv.py`. Render it and look at the
  first page before delivering. Offer two tailoring variants (AI-native roles,
  backend roles) as reorder instructions.
- Profile edits: audit mode on LinkedIn; other portals:
  `workflows/job-portal-profile-sync.md`.

## Phase 5 - Interview prep

Run `skills/interview-prep-planner/SKILL.md`: stage tactics, week-one triage,
dated schedule, resource tables with links, STAR slots, design-story skeleton. For
a single imminent screening, use `workflows/screening-interview-quick-prep.md`.

## Phase 6 - The plan document (PDF and markdown)

1. Order: status line; **Tier A applied table first** (date, clickable link, pay,
   status); Tier B; Tier C; marketplace assessment; day-by-day schedule starting
   with a dated "do now" block; study plan with links; message templates
   (recruiter reply in each working language, agency, warm network, referral ask);
   the rehearsed design story; file list.
2. Build with a PDF library that keeps links clickable, render at least one table
   page to an image and check it, and version the file name (`-v<N>-<date>`).
   Never overwrite an older version.
3. Every "I applied to X" from the candidate moves X into table A with the date,
   rebuilds the document and re-delivers it.
4. Deliver to the chat and to the candidate's synced folder. When uploading to a
   cloud drive, send binaries and PDFs with conversion disabled, check the returned
   type and size, and ask the candidate to delete any stray converted copy.

## Phase 7 - Tracker

Write rows in the tracker's column order. If the tracker is a hosted spreadsheet
the connector cannot write, try the browser; if the browser extension stalls,
save a CSV in column order beside the plan and give the import steps. Flag template
targets that conflict with the candidate's real floor.

## Phase 8 - Daily loop

1. Reply to warm inbox leads first, then applications (aim for 20 touches a
   day), then one follow-up after four business days. To watch named threads
   for replies, use `workflows/conversation-monitoring.md`.
2. In every screen: ask the pay range, contract form, start date and time-zone
   overlap before selling.
3. Rank live processes by probability x pay x speed; push the fastest at-or-above-
   floor option to an offer; accept a bridge offer at or above the bridge floor.

## Phase 9 - Save state

Write a resumable context file for the candidate (their folder, not the toolkit):
situation and framing, matching profile facts, applied table with links, pending
applications, ground rules, templates, study-plan pointer, file list, and the
one-line prompt that resumes the work. Personal data never enters this toolkit.

## Gates

- Nothing is submitted, sent or edited without current explicit approval; drafts
  are labeled NOT SENT.
- Hand to the owner: captchas, passwords, account creation, terms, payments,
  identity documents.
- Finish with what remains: pending applications, open risks, next action.
