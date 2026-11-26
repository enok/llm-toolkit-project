---
description: Prepare a candidate for one technical interview (human or AI interviewer) - intake, fact-checked narrative and printable two-block cheat sheet, concept gaps, intro rehearsal, coding-pattern drills, full mock with scoring, final reminders, and a debrief that turns the problem actually asked into the next drill
---

# Technical Interview Prep Workflow

Use this when a candidate asks for help preparing for, rehearsing, or debriefing
a technical interview. Capability and rules:
`skills/technical-interview-prep/SKILL.md` (read its Hard Rules first). The
application pipeline that tracks interview stages is
`workflows/job-search-pipeline.md`. For a multi-week plan across several interviews (stages, gap analysis, weekly
rotation) use `skills/interview-prep-planner/SKILL.md`; this workflow is the
drill for one interview.

Everything personal (CV, employers, metrics, the cheat sheet itself) lives in
the candidate's own files or documents, never in this toolkit.

---

## Phase 0 - Pick the mode

- **Full mode** (a day or more before): run every phase.
- **Urgent mode** (interview within hours): Phase 1 (short), Phase 2, Phase 4,
  Phase 5 for the single most likely problem, Phase 7. Say which phases were
  skipped.
- **Debrief only** (interview already happened): Phase 8.

## Phase 1 - Intake

1. Collect, in one batch, only what is not already available:
   - the job post or role summary (must-haves, platform, domain);
   - the format: duration split, human or AI interviewer, camera, screen
     share, live coding environment;
   - the interview language and the language the candidate wants coaching in;
   - the candidate's history: CV, private notes, earlier prep documents (search
     past chats or the candidate's drive when tools allow; if a referenced
     document is unreachable, ask the candidate to paste it);
   - the date and time, to choose the mode.
2. Treat earlier prep documents as drafts, not truth (Phase 2).

## Phase 2 - Fact-check the narrative and build the cheat sheet

1. Walk the candidate's story with them and correct it before anything is
   rehearsed. Ask specifically about the facts that drift: synchronous versus
   asynchronous flows, the scope of each leadership role, the unit behind every
   number, product names, and which environments each technology ran in.
2. Record every correction and apply it to all blocks.
3. Build the cheat sheet in the interview language, as bullets, with the two
   separate blocks from the skill (Block A spoken intro, Block B follow-up ammo)
   plus one honesty-bridge block per must-have the candidate has not run in
   production (`skills/technical-interview-prep/references/cloud-platform-concepts.md`).
4. Leave `<real>` placeholders for any metric the candidate has not confirmed;
   list them for the candidate. Never fill them with plausible numbers.
5. Deliver it as a printable document (a document artifact or a document in the
   candidate's drive that exports to PDF). A cheat sheet scattered across chat
   messages cannot be printed - consolidate it.

## Phase 3 - Close concept gaps

When the candidate asks how two platform concepts differ (for example a PaaS
versus a load balancer, pod versus node autoscaling, gateway versus load
balancer), answer from `skills/technical-interview-prep/references/cloud-platform-concepts.md` with one layer at
a time, then the mapping table. Feed any new understanding back into the
honesty-bridge blocks.

## Phase 4 - Rehearse the intro

1. The candidate delivers the intro in the interview language. Do not interrupt.
2. After each round: what worked (one or two lines), then the numbered error
   list with the corrected phrasing. Re-check all earlier errors on every round.
3. Pronunciation questions get the short answer first (the word, stress marked);
   expand only when asked.
4. Stop when a round is clean. Target 60 seconds; accept 75-80 for a clean round
   and point to the sub-point to trim.

## Phase 5 - Drill the coding patterns

1. Pick the likely problems: one themed on the employer's domain plus the most
   frequent warm-ups
   (`skills/technical-interview-prep/references/coding-patterns-java.md`).
2. Explain each at the depth requested: overview, or line by line when asked,
   pausing for questions. When the candidate interrupts for a tangent (a regex
   detail, a library call, pronunciation), answer it, then resume the open item
   and say where you are resuming.
3. Use concrete examples for abstract points (comparator tie-breaks, heap order,
   window movement) - a three-item walk-through beats a paragraph.
4. Before moving on, have the candidate state complexity aloud; correct any
   claim of O(1) space for a structure that grows with input.
5. If the candidate cannot see the code on the current device, pause until they
   can; do not continue a line-by-line walk they cannot follow.

## Phase 6 - Full mock interview

Run `skills/technical-interview-prep/references/mock-interview-protocol.md` end
to end. Score only at the end,
merge the errors into the running list, and repeat while time allows. When the
candidate decides to stop practising, respect it and move to Phase 7.

## Phase 7 - Final reminders

Three short bullets, in the coaching language: the honest-bridge lines for the
weak must-haves, the one technical rule they slipped on in practice, and
"narrate while coding; never invent numbers". Then wish them well and stop.

## Phase 8 - Debrief after the real interview

1. Ask what went well and what did not; do not re-litigate the parts that went
   well.
2. Identify the problem actually asked. If the candidate shares a video link,
   resolve its title through oEmbed (the watch page is rate-limited from
   sandboxes; see the skill's Known pitfalls).
3. Name the pattern, give the skeleton, the simple solution, and the optimised
   follow-up with complexity and traps.
4. If the candidate says they solved it before but could not recall it under
   pressure, treat it as a recall problem: drill the pattern skeleton and the
   brute-force-first fallback, then offer a short mock of two or three problems
   from the same family.
5. Add the pattern family to the candidate's drill list in their own notes, and
   offer to add it to their cheat sheet document.
6. If the candidate tracks applications with `job-search-pipeline`, update the
   row's interview stage there with the evidence.

## Report

- mode used and phases skipped;
- cheat sheet location and the open `<real>` placeholders;
- remaining items on the error list;
- next drill (pattern family) if any.
