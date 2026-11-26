---
title: Profile summary for fit scoring
tags: [linkedin, job-search, profile, fit-scoring, read-only]
---

# Profile summary for fit scoring

A job-search run scores postings against what the profile **states**. Reading
five profile pages for every run is slow and inconsistent, so a read-only lane
builds a cached summary once and the scoring lanes read that file. This
reference is the template only: the summary itself is personal data and lives
in the owner's working folder, never in the toolkit.

## When to build or refresh

- The cache is missing, or older than a week (refresh on a fixed weekday).
- The owner just changed the profile (skills, experience, headline).
- A role is marked current: flag it for the owner to confirm before scoring,
  because fit depends on whether it is still true.

## How to build it

Read-only, one tab, owner's signed-in browser
([browser-session-notes.md](browser-session-notes.md)). Open the main page,
experience, skills, certifications and education details pages
([details-pages.md](details-pages.md)) and write one file with these sections:

```text
# Profile summary (built <date>, source: live profile pages)
Headline and open-to-work state: <text>
Experience: <title, employer type, start - end> per role (dates as shown)
Skills (as listed): <list>
Certifications: <name, issuer, date>
Languages: <language, level>
Years per technology: <technology: years> computed from role date ranges
Gaps versus the profile: <see below>
Fit keywords: <only what the profile states>
```

- **Years per technology** come from the date ranges of the roles that
  mention it. Subtract gaps between roles. When a stated duration differs from
  the computed one, record both and say which you used.
- **Gaps versus the profile**: top skills that appear in the header or in
  experience tags but are missing from the skills tab; entries that are not
  skills (a school, a company) sitting at the end of the skills list. These are
  findings for the owner and feed
  [skills-reconciliation.md](skills-reconciliation.md); change nothing.
- **Fit keywords: only what the profile states.** Never add a skill because a
  posting asks for it; that is how a score turns into an untrue claim
  (`rules/application-truthfulness.md`).

## How the scoring lanes use it

Lane L0 in `skills/job-search-pipeline/references/lane-prompts.md` builds the
file; screening lanes score a posting as the share of its required skills the
summary states. A required skill that is absent is a gap in the row's "why it
fits" note, not a guess.
