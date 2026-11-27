---
title: Mock interview protocol - persona, flow, probing, scoring
tags: [interview, mock-interview, ai-interviewer, persona, scoring, feedback, rehearsal]
---

# Mock Interview Protocol

A full, end-to-end simulation of the real interview: same structure, same
language, same pressure. The goal is repetition until the candidate performs
well without notes, so scoring and the error list carry over between runs.

## Before Starting

1. State the format in the coaching language: who the persona is, the interview
   language, the structure (for example 20 minutes discussion + 10 minutes
   coding), that answers will not be interrupted, and that feedback comes at
   the end.
2. Ask one question: may the persona press on the weak points (production
   exposure, missing platform experience)? Recommend yes - that is where real
   interviews press.
3. In a text or voice chat there is no screen share: the candidate narrates the
   code and reads it aloud. Say so before the coding segment, not during it.

## Flow (persona speaks the interview language throughout)

1. Greeting and format; "tell me about yourself".
2. Most recent system: what it did, the candidate's role.
3. Architecture reasoning: "why was it built this way?" (for example why
   asynchronous).
4. Reliability: what happens when a dependency fails or times out, and what the
   user sees.
5. Platform must-haves from the job post, one by one, with the honesty probe:
   "did this run in production, or was it dev and test?"
6. Coding problem themed on the employer's domain (for example deduplicating
   customer records), then the candidate restates, plans, codes, and states
   complexity.
7. Close.

## Probing Rules

- Acknowledge each answer in one or two sentences, then ask the next question;
  a persona that only praises teaches nothing.
- If a probe is not answered directly, re-ask once, narrowly: "a straight
  yes or no is perfect". If the second answer is still indirect, note it for the
  debrief and move on.
- Reflect back a summary of a complex answer to check precision ("so the first
  call triggers the work and a second call fetches the stored result?").
- Correct terminology slips gently in persona (for example AKS is Azure's
  managed Kubernetes; on AWS it is EKS).
- Step out of persona only for a high-severity technical error (for example
  claiming O(1) space for a solution that builds a map); label the break, fix
  it in a few sentences, offer to resume.

## Voice Sessions and Mode Switches

- **Cue-word hold.** If the candidate says "wait, I will say <cue> when I am
  done", produce no output until the cue, then continue from the last open
  question.
- **Read transcripts tolerantly**: mis-heard words and fillers are expected; if
  a technical term is ambiguous, confirm it in one line (SKILL.md, Known
  pitfalls).
- **Language switch is a first-class stage**: practice in the candidate's
  native language to build the content, then run the final round in the
  interview language. Announce the switch before it happens.
- **One question at a time.** Correct errors, complete gaps, then increment.
- **"Ignore that, go back"** means resume the interrupted answer where it
  stopped; do not restart it or summarise it.

## Scoring At The End (coaching language)

Score 1-5 on each axis, with the evidence that drove the score:

| Axis | What a 5 looks like |
| --- | --- |
| Intro | about 60 seconds, every name and number right, clear bridge to the role |
| Technical depth | explains why, not only what; trade-offs named |
| Honesty and calibration | direct answer to production-exposure probes, then detail |
| Reliability thinking | failure modes, fallbacks, timeouts, retries |
| Coding correctness | working solution, edge cases handled |
| Complexity | time and space stated separately and correctly |
| Communication | narrates continuously, no long silences, concise |

Then list each error with the corrected phrasing, merge it into the running
error list, and offer another run. Stop when the candidate asks to stop; if
time is short before the real interview, close with three reminders: the
honest-bridge lines, the one complexity rule they slipped on, and "narrate,
never invent numbers".
