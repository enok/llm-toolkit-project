---
title: Point exclusions in a detection rule get reopened; use an allow-list
category: security
created: 2026-11-25
tags: [detection-rule, allow-list, exclusion-list, hidden-text, untrusted-content, review-loop]
---

# Problem

A detection rule for hidden text in untrusted content kept being reported as
incomplete. Each review found one more input the rule missed, and the task hit
its iteration cap without ever getting a clean review.

# Failed Approaches

- Excluding the reported input, four times in a row. Each fix covered only the
  input a reviewer had just named. Each independent re-review then found
  another carrier of the same class, so the point fix was reopened every time.

Evidence is a single run record (validator-sourced, high severity).

# Solution

What ended the loop in that run:

- Rewrite the exemption as an allow-list: name what is permitted and flag
  everything else.
- State the remaining limit of the rule in the operational document.
- Record the stronger fix as an open item.

Not verified: the allow-list version was not independently re-reviewed before
that run ended, so it is not proven to be complete.

General guidance, not observed beyond the run above: when a second review finds
a new variant of the same class after a point fix, stop adding exclusions.
Describe the class, invert the rule to an allow-list where possible, and test
the class instead of the reported sample.

# Why

Reasoning, not observed in the run: a rule built from exclusions only covers
the variants already seen, so every unseen variant of the class is a new
finding for the next reviewer. An allow-list changes the default: anything not
named is flagged, so a new variant fails closed instead of slipping through.
Testing the class rather than the reported sample checks the property that
matters, not one instance of it.
