---
title: Verdicts on a live event lag it; partisan takes publish first
category: toolchain
created: 2026-10-22
tags: [current-events, debate, fact-check, polls, neutrality, search, live-event, timing]
---

# Problem

While a televised debate was still running and right after it ended, the user
asked in turn: what is the general analysis, who did better, who lied more,
and whether the assistant could fact-check what was said. Searches returned
live blogs, a handful of quotes, fact-checkers' pages saying checks were in
progress, and partisan outlets already declaring a winner or accusing the
other side of fake news. No independent consensus or fact-check tally existed
yet, and no transcript was available.

# Failed Approaches

- Treating early partisan headlines as the analysis: they are claims by one
  camp, published fastest precisely because they need no checking.
- Building an own "who lied more" count from claims quoted in news coverage:
  coverage selects claims unevenly, so the count would be partial and
  asymmetric.
- Searching again a few minutes later: the verdict sources run on hours (fact
  checks, columns) and days (polls with fieldwork after the event).

# Solution

Classify the event's maturity first (verdict-lag ladder in
`skills/current-events-briefing/SKILL.md`). While it is early, say plainly
that no consolidated verdict exists, give the main clashes for each side with
the same treatment, name the independent fact-checkers whose roundups are
pending, offer claim-by-claim checks of a specific statement the user names,
and schedule the follow-up after the publication window.

# Related

- `skills/current-events-briefing/SKILL.md`: the verdict-lag ladder and source tiers.
- `learnings/deferred-follow-up-declared-impossible.md`: scheduling the follow-up instead of
  declaring it impossible.

# Why

Reliable verdicts are produced by slower processes than the event itself, and
the earliest sources are the least independent. Reporting maturity honestly is
both more accurate and more even-handed than filling the gap.
