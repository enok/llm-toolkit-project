---
title: Jackson streaming copy can round big decimals - use copyCurrentEventExact
category: api
created: 2026-11-26
tags: [java, jackson, json, streaming, big-decimal, masking, validators, false-positive]
---

# Problem
A streaming JSON field-masking proxy copied untouched fields from a `JsonParser` to a
`JsonGenerator` with `copyCurrentStructure` / `copyCurrentEvent`. Large or high-precision
decimal values came out rounded, so the pass-through was not byte-faithful.

# Failed Approaches
- Assuming "copy" means exact: the generic copy methods can convert a floating-point token to
  a double on the way through.
- Reviewing with a summary only: reviewer lanes that were given a CV-style summary of the
  design, not the source, flagged false positives.

# Solution
- Use `copyCurrentEventExact` (Jackson 2.15 and later) when copying events that must not
  change, and add a test with a decimal that does not fit a double.
- Pass the full source text, not a summary, to any validator or reviewer lane, so findings
  refer to what the code does.
- On older Jackson, keep numbers as text (`getText()` / `writeNumber(String)`) instead of
  decoding them.

# Why
The exact variant preserves the number's textual form, while the generic copy may route it
through a lossy numeric type. Validators reason from what they are given; a summary invites
guesses. Check the Jackson version in the project before relying on the method name.
