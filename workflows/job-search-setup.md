---
description: Onboard a candidate to the job-search pipeline - build the profile from their CV and criteria, derive target roles, ATS keywords and a truthful master CV, create or adopt the tracker, wire connectors, and schedule the recurring scan
---

# Job Search Setup Workflow

Use this once per candidate ("set up my job scan", "start tracking my job
search", "adopt my existing job tracker"). The recurring run is
`workflows/job-search-pipeline.md`. Capability:
`skills/job-search-pipeline/SKILL.md`.

---

## Phase 1 - Gather inputs

1. Ask, in one batch, only for what the CV and existing files cannot answer:
   - target roles and seniority;
   - pay floor and target (currency and period);
   - location and work-authorization constraints;
   - deal-breakers, which become hard rules;
   - dislikes, which become preferences;
   - where files should live;
   - digest channel and cadence;
   - how many rows they will review per day (`queue.shortlist_size`), and
     whether unreviewed rows should expire after N days
     (`queue.expire_unreviewed_days`; unset means never);
   - which rows get an apply kit (`apply.kit_for`: `approved`, `tier_A`,
     `shortlist`) and the CV file formats they want (`cv.formats`,
     `cv.pdf_footer`).
2. Read the CV and any existing tracker or procedure notes. Extract the
   candidate's own stated rules verbatim; do not invent criteria.
3. Locate or create the standard screening answers. These cover:
   - years per core skill;
   - notice period;
   - work authorization;
   - salary policy;
   - profile links.

   Leave any answer the candidate has not given blank. A blank answer means
   that question is skipped at apply time.

## Phase 2 - Write the profile

1. Copy `skills/job-search-pipeline/references/profile-template.md` into the
   candidate's job-search folder as `job-search-profile.md` and fill it in.
2. Turn every deal-breaker into a `hard_rules` entry. Give each one a check
   method and its exceptions.
3. Turn every soft dislike into a `preferences` entry.
4. Set `cv_skills` from skills the CV states explicitly.
5. Targeting and master CV. Method and CV markdown format:
   `skills/job-search-pipeline/references/cv-tailoring.md`.
   - Derive `targeting.roles` from the CV (section 1): the 20 best-fit
     titles a recruiter would search for, each with the exact ATS keywords
     for that title (`ats_keywords`). Set `targeting.refresh_days` and
     `targeting.queries_from_roles`.
   - Write the master CV (`cv.master`, section 2): every achievement bullet
     as "Accomplished X as measured by Y by doing Z", then clear the
     ten-second red-flag checklist (section 3). Use only facts from the CV
     and the candidate's own files. A missing metric or fact becomes
     `[FILL: ...]`, never an estimate. Tag bullets with `<!-- kw: ... -->`
     and `<!-- src: ... -->`.
   - Preview it with `python skills/job-search-pipeline/scripts/render_cv.py
     --in <cv.master> --out-dir <working_dir> --allow-fill`. Set
     `cv.tailored_dir` for apply kits.
6. Show back the hard rules, the pay rule, the 20 titles with their keywords,
   and the master CV with every `[FILL: ...]` item. The candidate must confirm
   them before the first run. A kit CV that still carries a `[FILL` marker
   is not rendered, so resolve them early.

## Phase 3 - Tracker

- New candidate: `tracker_ops.py init --tracker <path>`.
- Existing tracker: run `tracker_ops.py known` and `approvals` on a copy.
  Sheets or headers that differ are fine when they map through aliases. When
  they don't, add the missing sheets or columns by header name and preserve
  every existing sheet. Never rewrite the owner's data.
- Optional: create `skill-rules.json` (schema in
  `skills/job-search-pipeline/references/tracker-schema.md`) when the
  candidate keeps a study plan.

## Phase 4 - Connectors and dry run

1. Confirm that each of these is reachable: the mail connector, the browser
   session logged in to each board, and file access to the tracker folder
   (desktop bridge or drive connector).
2. Run `workflows/job-search-pipeline.md` once in report-only mode. Make no
   tracker writes, no applications, and no apply kits. Send the digest, with
   its first "Approve today" list, to the candidate for review.
3. Fix the profile from the candidate's feedback.

## Phase 5 - Schedule

Create the recurring task with the platform's scheduler. For updates, follow
`workflows/automation-maintenance.md`. The task prompt stays short and
generic:

> Run the job-search pipeline (llm-toolkit `workflows/job-search-pipeline.md`)
> through the Orchestrator Agent for the profile at <path>. Follow the profile;
> root owns writes; end with the elapsed-time line.

Put run-specific overrides, such as a one-off exclusion, in the profile.
Keep them out of the scheduled prompt so the prompt does not drift.

## Phase 6 - Hand-off

Tell the candidate:

- where the profile and tracker live;
- how to mark approvals: `☐` / `☑ Approve` / `✖ Reject` / `⏸ Later`;
- when the scan runs;
- that only marks they make in the file count as approval: the digest's
  "Approve today" list is a suggestion, never an approval;
- where apply kits land (`cv.tailored_dir`), and that `[FILL: ...]` and
  `OWNER:` items in them are theirs to complete;
- that a tailored CV only selects, reorders, and rephrases master-CV facts;
  keywords the CV cannot support appear as `Missing keywords`, never in the CV.

## Final Step - Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before
closing this workflow.
