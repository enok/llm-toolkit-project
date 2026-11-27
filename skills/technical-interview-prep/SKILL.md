---
name: technical-interview-prep
description: Coach a candidate through one technical job interview (human or AI interviewer) - build a truthful printable cheat sheet from the job post and the candidate's confirmed history, rehearse the 60-second intro, drill the likely coding patterns in Java, run a full mock interview with end-of-session scoring, and turn the problem actually asked into the next drill. Covers honest bridges for technologies never run in production, complexity-claim pitfalls, and recalling a pattern under pressure. Use whenever the user says "prepare me for the interview with X", "AI interviewer prep", "rehearse my intro", "simulate the interview", "mock coding round", "explain this solution line by line", "which algorithms will they ask", "turn my legacy migration into interview stories", "research this company before the call", or "I had the interview and this problem came up", or when a job-tracker row moves to an interviewing stage - even if they never say "prep".
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.3.0"
---

# Technical Interview Prep

Coach a candidate through one technical interview: facts first, then the spoken
story, then the coding round, then a full mock, then a debrief after the real
thing. This skill is the procedure and holds the rules and reusable material;
`workflows/technical-interview-prep.md` is only the route into it.

Modes: **full** (a day or more ahead) runs every section below; **urgent**
(interview within hours) runs short intake, the cheat sheet, intro rehearsal,
the single most likely coding problem, and final reminders, and says which
parts were skipped; **debrief only** (interview already happened) runs the
debrief.

## Inputs

Gather these first; a script built on a guessed history fails the first follow-up question.

- The job post (must-haves, nice-to-haves, platform, domain).
- The interview format: duration split (for example 20 minutes discussion +
  10 minutes coding), human or AI interviewer, camera and screen share, language.
- The candidate's real history, from their CV, private notes, or earlier prep
  documents (search past chats or their drive when tools allow; if a document
  is unreachable, ask them to paste it). Treat earlier prep documents as
  drafts, not truth. Personal history stays in the candidate's own files and
  never enters this toolkit.
- The interview language, the language the candidate wants coaching in, and
  the date and time (to choose the mode). Ask for what is missing in one batch.

## Hard Rules

They exist because an interviewer probes every claim: one invented detail costs credibility for the whole session.

1. **Truthful claims only.** Every line in a script is something the candidate
   confirmed. Never invent metrics (requests per second, latency, team size,
   revenue); leave a `<real>` placeholder the candidate fills or drops. Never
   upgrade "used in dev/test" to "ran in production", "used the equivalent
   product" to "used this product", or imply a certification.
2. **The candidate's corrections beat any prep document.** Re-verify the
   narrative with the candidate before the first rehearsal and propagate each
   correction to every block (intro, follow-up ammo, honesty bridges). Facts
   that drift most often: synchronous versus asynchronous flows, the scope of a
   leadership role (one project versus a whole area), the unit being counted
   (business rules versus applications), and product names.
3. **Practice in the interview language; coach in the candidate's language.**
   Scripts, cheat sheets, and the mock persona use the interview language;
   feedback and explanations use the language the candidate is speaking.
4. **Do not interrupt a rehearsal answer.** Feedback comes after the full turn.
   The single exception is a high-severity technical error inside a mock (for
   example a wrong complexity claim): step out of persona, say so explicitly,
   correct it in two or three sentences, and resume.
5. **Match the requested depth.** When the candidate says "shorter" or "I am
   short on time", switch to compact answers immediately; when they ask for a
   line-by-line walk, go one line at a time and wait.

6. **Verify company claims against primary sources.** Company facts in a prep
   pack (strategy, products, leadership) are claims, so run an adversarial lane
   that tries to falsify each one from primary sources, and date-stamp every
   claim. A company's direction can change days before the call (a recruiter
   may confirm it), so lead the playbook with the latest change.

## Cheat Sheet: Two Separate Blocks

Deliver as bullets, printable, in a document the candidate can export to PDF (a
document artifact or a document in their drive; a cheat sheet scattered across
chat messages cannot be printed, so consolidate it). List the open `<real>`
placeholders for the candidate. Keep the two blocks visually separate so the candidate never reads follow-up
detail aloud in the intro.

- **Block A - spoken intro (about 60 seconds).** Who I am (years, the role noun
  "software engineer", core stack, kind of systems) -> most recent role (title,
  scope, one owned system, one real metric) -> previous role (precisely scoped
  role, the counted unit, the platform, products by full name) -> closing bridge
  to the target role.
- **Block B - follow-up ammo (only if asked).** One sub-block per likely probe:
  architecture detail, how a metric was measured, organisation context,
  orchestration, infrastructure and cloud, CI/CD ownership framed honestly
  ("dedicated teams owned the pipelines; I worked hands-on with them").
- **Honesty-bridge blocks** for every must-have the candidate has not run in
  production: honest scope sentence -> concept mapping from what they did use ->
  how they would do it on the target platform -> how they would debug it. Ready
  material: `references/cloud-platform-concepts.md`. When the candidate asks
  how two platform concepts differ (PaaS versus load balancer, pod versus node
  autoscaling), answer one layer at a time from that file, then give the
  mapping table, and feed the new understanding back into these blocks.

## Intro Rehearsal Loop

The candidate delivers the intro in the interview language, uninterrupted. After
each round give what worked (one or two lines), then the numbered error list
with corrected phrasing; keep that list across rounds and re-check every item
each round. Pronunciation questions get the short answer first (the word, stress
marked); expand only when asked. Stop when a round is clean. Recurring classes: hedged or invented percentages, the wrong role
noun ("software engineering" for "software engineer"), the wrong counted unit,
abbreviated or misnamed products, a promotion presented as a separate job, a
missing employer name, mispronounced names, a dropped key qualifier (for example
"revenue-critical"), and a vague bridge to the target platform. A strong round
at 75-80 seconds is acceptable; trim the least load-bearing sub-point to reach 60.

## Coding Round Posture

- Restate the problem -> edge cases -> brute force aloud -> optimised approach
  -> code while narrating -> complexity -> a quick test by hand.
- Silence reads as being stuck; verbalise every step.
- Never claim O(1) space when the solution builds a map, set, or list that grows
  with the input; state time and space separately.
- When the mind goes blank, start from brute force aloud and walk the pattern
  cue table in `references/coding-patterns-java.md`; recall the pattern
  skeleton, not a memorised solution.
- Drilling: pick one problem themed on the employer's domain plus the most
  frequent warm-ups (that file). Use a three-item walk-through for abstract
  points (comparator tie-breaks, heap order, window movement). Have the
  candidate state complexity aloud before moving on. If they cannot see the
  code on their device, pause the line-by-line walk until they can. After a
  tangent (regex detail, library call, pronunciation), answer it, then resume
  the open item and say where you are resuming.

## Mock Interview

Run it as `references/mock-interview-protocol.md` describes: persona in the
interview language, realistic pressure on the must-haves, one re-ask when a
probe is not answered directly, and scoring only at the end. Merge the errors
into the running list and repeat while time allows; when the candidate decides
to stop practising, respect it. Close with three short reminders in the coaching
language (the honest-bridge lines for the weak must-haves, the one technical
rule they slipped on, "narrate while coding; never invent numbers") and stop.

## Example

Candidate: "They will ask about Kubernetes, which I only used in a test cluster." Write the bridge block as: honest scope ("I ran it in a test environment, not in production") -> mapping from what they did run (deployments, health checks) -> how they would do it on the target platform -> how they would debug a failing rollout. Do not write "I operated Kubernetes in production".

## Debrief After The Real Interview

Ask what went well and what did not; do not re-litigate what went well.
Identify the problem actually asked (a shared video link: resolve its title via
oEmbed, see Known pitfalls), name its pattern, write the skeleton, the simple
solution, and the optimised follow-up with complexity and traps, and add the
whole pattern family to the drill list in the candidate's notes (offer to add it
to the cheat sheet too). If they solved it before but could not recall it under
pressure, treat it as a recall problem: drill the skeleton and the
brute-force-first fallback, then offer a short mock of two or three problems
from the same family. Acknowledge the result plainly; one weak round rarely
decides an outcome.

## Tracker update and report

If the candidate tracks applications with `skills/job-search-pipeline/SKILL.md`
(`workflows/job-search-pipeline.md`), update the row's interview stage with the
evidence. Report: mode used and parts skipped; cheat sheet location and open
`<real>` placeholders; remaining items on the error list; next drill (pattern
family) if any.

## References

- `references/coding-patterns-java.md` - read when drilling or recalling a coding pattern: cues, Java skeletons, complexity, edge cases.
- `references/cloud-platform-concepts.md` - read when writing an honesty bridge for a platform the candidate has not run: concepts, product mappings, talking points.
- `references/mock-interview-protocol.md` - read before running a mock: persona, flow, probing, scoring, voice-session rules.
- `references/legacy-migration-story-bank.md` - read when the role involves legacy migration or modernisation: story shape, honesty rules, and the "migrate today with coding agents" section (structure only).

## Known pitfalls

- A prep document drafted before talking to the candidate gets architecture
  facts wrong (for example a two-phase asynchronous flow written as a blocking
  call); re-verify before rehearsing anything.
- Asked "did this run in production?", candidates tend to answer with adjacent
  breadth. Drill a one-sentence direct answer first, then the supporting detail.
- A video link of the problem that was asked cannot be read from a sandbox
  (YouTube answers HTTP 429); resolve its title through oEmbed.
- Voice transcription swaps technical terms ("regex" and "rejects", "heap" and
  "hip", "stack" and "step"); confirm the term in one line before explaining.
  Voice-session and no-screen-share rules: `references/mock-interview-protocol.md`.

## Related

- `workflows/technical-interview-prep.md` - the route into this skill
- `skills/job-search-pipeline/SKILL.md` - where the interviewing stage is tracked
- `skills/java-best-practices/SKILL.md` - production Java idioms
- `skills/youtube-video-curation/SKILL.md` - oEmbed verification of video IDs
- `skills/interview-prep-planner/SKILL.md` - plan versus drill: the planner sequences stages, gap analysis, and the weekly rotation; this skill runs the drills for one interview
