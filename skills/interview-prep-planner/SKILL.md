---
name: interview-prep-planner
description: Build an interview-preparation plan for a candidate - classify the interview types the target roles use (aptitude test, coding, system design, AI-native practical, business case, behavioral), run a gap analysis against the candidate's profile, and produce a prioritized study plan with books, videos, courses, drills, a week-one triage, STAR story prompts, one rehearsed system-design story and a four-week language rotation. Use whenever a candidate says "prepare me for interviews", "what should I study", "I have a live-coding round", "modern Java refresher", "aptitude test prep", "how do I practice system design" shares target roles and asks for a study schedule, or reports progress ("I did up to item 8, re-plan the rest"), even without the words interview plan. For one imminent screening call use the quick-prep workflow instead.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.1.0"
---

# Interview prep planner

Turn a list of target roles plus a profile into a study plan the candidate can
start tonight. Read `references/resource-catalog.md` when filling the plan's resource tables
(books, videos, drills, aptitude sets; starred items are the week-one set); the plan
document itself is produced by `workflows/job-search-attack-plan.md` (or on its
own as a PDF or markdown file with clickable links). For one imminent screening
interview or short test use `workflows/screening-interview-quick-prep.md`.

For the plan file's format (one timeline table, real checkboxes, pre-ticked
done items, weekday-only, one tab per week, purchase list) and for re-planning
after a progress report, read `references/deliverable-format-and-replan.md`.

## Contract

1. **Derive the interview types from the postings, not from habit.** Read the
   hiring-process text and stage names. Typical stages: cognitive aptitude test,
   live or timed coding, system design, AI-tooling practical, written business
   case, behavioral/leadership, hiring-manager conversation.
2. **Gap analysis before resources.** List every skill that appears in two or
   more target roles, then rate the candidate's evidence: `blocker` (cannot pass
   the stage today), `signal` (needed to look credible, can be shown with a
   small artifact), `nice`. Only blockers and signals get study time in week one.
3. **Triage to the runway.** If interviews arrive within days, prepare only:
   the stage-specific tactics, eight STAR stories, and one rehearsed
   system-design story. A long grind started now displaces the applications
   and networking that create more interviews.
4. **Time-box and measure.** Every item has a duration and an output (a solved
   set, a recorded run, a repo, a written story), because a plan without outputs
   is a reading list and gives no way to see progress.
5. **Truthful positioning.** Stories and numbers come from the candidate. A
   missing metric is `[FILL]`, never an estimate: a rehearsed invented number
   gets repeated to an interviewer (`skills/job-search-pipeline/references/application-truthfulness.md`).

## Stage tactics

- **Cognitive aptitude test (50 questions, ~15 minutes, no calculator).** Never
  take it cold: do two or three timed practice sets first. About 18 seconds per
  question; skip anything past ~25 seconds and return; answer everything (no
  penalty for guessing); take it fresh, on a desktop, in a quiet room.
- **Live coding.** Talk aloud in the interview language; state the approach, edge
  cases and complexity before typing; run the examples; keep a 25-minute budget
  per medium problem in practice. Secondary languages need idiom fluency, not
  only syntax: use mentored exercises plus timed re-solves of problems already
  solved in the primary language.
- **System design.** Use one framework every time: requirements -> core entities
  -> API -> high-level design -> deep dives -> trade-offs. Pre-build one story
  from the candidate's real work (template below).
- **AI-native practical.** Show the loop: spec -> plan -> agent executes -> tests
  or evals gate -> review. Have the tools open, a public artifact (an MCP server
  or agent harness with evals) and the language of outcomes and verification,
  not "I wrote the code".
- **Written business case.** Situation -> three options -> recommendation with
  trade-offs -> risks -> 30/60/90 plan -> metrics. Time-box, plain language,
  one page when allowed.
- **Behavioral.** Eight STAR stories, one page each: situation, action, metric,
  what you would change. Slots: performance win, outage or SLA recovery, data
  scale, security hardening, leadership/mentoring, a conflict, a migration, an
  AI or automation initiative.

## System-design story template (rehearse out loud, 45 minutes)

Context and constraint -> ingest/data path -> reliability (SLOs, retries,
idempotency, observability, fault injection) -> security -> trade-offs the
candidate can defend (streaming vs queue, sync vs async, freshness vs cache,
exactly-once vs at-least-once plus idempotency) -> numbers (latency, scale,
cost, improvement factor).

## Modern Java topic order (for candidates strong in Java 8)

`var` (10) -> HTTP Client (11) -> switch expressions (14) -> text blocks (15) ->
records (16) -> sealed classes (17) -> pattern matching for `instanceof` and
`switch`, record patterns (16-21) -> virtual threads and structured concurrency
(21) -> sequenced collections (21) -> stream additions (`takeWhile`, `toList()`,
`mapMulti`, `teeing`) -> Optional additions -> `CompletableFuture` -> JFR and
G1/ZGC basics -> Spring Boot 3 (Jakarta namespace, observability). Drill: rewrite
one old class with records + sealed interface + switch patterns, build a small
async pipeline with virtual threads, add tests. Time-box 60 minutes.

## Live-coding drills (any language, repeat weekly)

Four 60-minute tasks, from scratch, with tests: a rate limiter, an LRU cache, a
CSV-to-JSON ETL with validation, and a small HTTP service with one endpoint. Record
the screen, review the recording for hesitation, repeat with the next language.

## Four-week rotation (45-60 minutes per day)

Week 1 secondary language A (official tutorial, mentored exercises, timed
re-solves) -> week 2 modern primary-language features -> week 3 secondary
language B -> week 4 mixed: one recorded drill per language. Keep system design
and STAR work in parallel; weekly mock interview alternating coding and design.

## Output

A document with these sections, in order; offer it as PDF plus markdown:

```text
1. Interview types per role   | role | stages | source line in posting |
2. Gap table                   | skill | roles | evidence | blocker/signal/nice |
3. Week-one triage             | day | item | minutes | output |
4. Dated schedule              | week | daily block | output |
5. Resources                   | purpose | link | starred |
6. STAR slots                  | slot | story | metric or [FILL] |
7. System-design story         | skeleton from the template above |
```

Example gap row: `Kubernetes | 3 of 4 roles | one internal tool, no production cluster | signal`.
