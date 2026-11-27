---
title: Legacy migration story bank (structure only)
tags: [interview, stories, legacy-migration, behaviour-preservation, ai-assisted]
---

# Legacy migration story bank

Read when the target role involves modernising or migrating an old system and
the candidate has real migration work to turn into interview stories. This file
holds the **structure** only. The facts (systems, numbers, outcomes) come from
the candidate and stay in the candidate's own files; an unknown fact is a
`<real>` placeholder, never an estimate (Hard Rules in `SKILL.md`).

## Story shape

Write each story in five beats:

1. **Business problem.** Why the system had to change (cost, risk, support
   ending, speed of delivery), in one or two sentences.
2. **Technical solution.** What was done, at the level an interviewer can probe.
3. **AI component.** Where an AI tool helped (mapping the repository,
   generating tests, drafting the change), and what a human still decided.
4. **Validation.** How you knew behaviour was preserved.
5. **Outcome.** The result the candidate can confirm, with its real metric or
   an honest "no metric measured".

## Rules that keep the stories credible

- **Name testing gaps openly.** If the validation was manual functional
  testing only, say so, then say what you would add. A story that claims a full
  suite and then admits "we only tested by hand" under follow-up loses the
  whole session.
- **Reframe trial and error as evidence-driven work** when it is true: you read
  every producer and consumer of the value, chose the narrowest type that all of
  them support, and let the compiler prove the change. Describe the method, not
  the number of attempts.
- **Never contradict an earlier answer.** Keep one list of the claims made
  across stories and check each new story against it.

## "How I would run this migration today with coding agents"

Close the bank with a forward-looking section the candidate can say in two
minutes:

1. **Map the repository first** (modules, entry points, who calls what), read-only.
2. **Generate characterization tests with an agent**, and require them to pass on
   the **unmodified baseline** before any change; a test that fails on the old
   code describes the agent's guess, not the system.
3. Change in small steps, re-run the characterization tests after each, and
   review diffs as a human.
4. Technical checklist for the Java case:
   `skills/maven-build-troubleshooting/references/jdk17-legacy-migration.md`.
