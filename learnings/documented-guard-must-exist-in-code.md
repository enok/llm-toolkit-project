---
title: A documented script guard must exist in code before the text ships
category: testing
created: 2026-11-25
tags: [documentation, guard, validation, skills, restore, claims, review]
---

# Problem

During the validator review of a new skill, one sentence described a safety
check that a script performs before a restore operation. No code implemented
that check. The sentence was a claim about code that the code did not back.
Evidence is a single run record (validator-sourced, high severity).

# Failed Approaches

None recorded beyond the first attempt described in Problem.

# Solution

The fix recorded in the run was to replace the sentence with a description of
what the code actually does.

Reusable practice: a sentence in a skill, rule or document saying that a script
checks, refuses, verifies or guards something is a claim about code. Before it
ships, point to the lines or the test that implement it. When none exist, do
one of two things:

- implement the guard, or
- rewrite the sentence as a manual step that a person or agent must perform.

No automated guard exists for this class yet; this case was found by a
validator reviewing the skill.

# Why

A reader, human or agent, treats a sentence like "the script refuses to ..." as
a guarantee and skips the check it describes. When the code does not implement
the guard, the safety net is imaginary, and the risk lands on whatever
operation the guard was meant to protect.

This "why" is reasoned, not measured: the record holds one occurrence, and no
data was collected on how readers behave. Treat both options (implementing the
guard, or rewriting the sentence as a manual step) as general guidance, not
observed; the run record shows only the replace-with-actual-behaviour fix.
