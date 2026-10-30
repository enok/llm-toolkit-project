---
title: Degree accreditation claims need a regulator check, not the program page
category: toolchain
created: 2026-10-22
tags: [credential-evaluation, accreditation, regulator, white-label-degree, research, source-grading]
---

# Problem

A person asked whether an online AI master's, sold by an edtech brand and
awarded by a partner institution abroad, was worth taking and carried weight
in the market. The program page said "accredited degree", "recognized in 60+
countries", and listed ECTS credits. Nothing on the page said who exactly
awards the degree, what that institution's licence covers, or whether the
person's home country would recognize it.

# Failed Approaches

- **Trusting the program page and the awarding body's own accreditation
  page.** Both are vendor-side and omit restrictions; "accredited" there says
  nothing about licence scope or home-country recognition.
- **Searching for reviews.** The results were vendor marketing, a competitor's
  "alternatives" comparison pages, and forum anecdotes. There was no
  independent employer evidence at all.
- **Assuming "accredited in Europe" implies recognition at home.** Recognition
  is decided by the home country's rules and by each receiving university,
  and several major universities in the person's country refuse distance or
  hybrid foreign master's degrees.

# Solution

Follow `skills/credential-evaluation/SKILL.md`; the checks that decided this
case, all from primary sources:

1. Open the regulator's register and its announcements page. A notice dated
   25 Sep 2026 restricted the institution's licence to teaching the
   institution delivers itself; students enrolled before 1 Sep 2026 were
   unaffected (verified 2026-10-21 — re-verify before relying).
2. Check whether the national QA agency is registered on EQAR. This one had
   been rejected in 2025 (verified 2026-10-21 — re-verify before relying).
3. Read the home country's foreign-degree recognition rules and the current
   rules of the largest receiving universities, including any filter on
   delivery mode.
4. Grade every source (primary / secondary press / vendor claim / competitor
   claim / forum anecdote) and report "no independent employer evidence" as a
   finding.
5. Run a cheap claim-check validator (light tier, different invocation than
   the researchers) over the load-bearing claims before answering; 10 of 10
   passed in this case.

# Why

White-label degrees market the brand and the word "accredited", while the
facts that decide market weight - licence scope, QA-agency status, enrollment
cutoffs, and home-country recognition - live in primary sources that the
vendor never quotes. A page can be technically true and still silent on the
restriction that matters, so the verdict has to come from the regulator's
register and announcements, not from the page that sells the program.
