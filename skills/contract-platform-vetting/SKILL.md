---
name: contract-platform-vetting
description: Vet and use AI-training and expert-contractor marketplaces (output-based hourly work such as reinforcement-learning environments, code evaluation, data labeling) as bridge income - five-point legitimacy check, rate selection inside a posted band, ranking postings by band and task fit, effective-hourly math, weekly-hour caps and application hygiene. Use whenever a candidate shares gig-platform or freelance-expert postings, asks "is this platform legit", "which of these should I apply to", "what hourly rate do I enter", "is this worth my time" or "how much can I earn on the side", or is weighing bridge income while job hunting, even if the word marketplace is never used.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.0.1"
---

# Contract platform vetting

Marketplaces that place experts on AI-lab projects pay per accepted task, quote an
hourly band, and onboard in days. They are useful bridge income for a candidate
whose target is a full-time or long-term contract role. This skill decides which
to use, what to enter, and how much time to give them.

## Contract

1. **Bridge, not destination.** Position the work as bridge income. Cap it at
   10-20 hours a week: per-task pay is lumpy, and the hours it eats are the
   same ones interviews, referrals and applications need. Say this plainly in
   the recommendation.
2. **The band is a ceiling.** Pay is typically per accepted task with a weekly
   minimum of submissions. Effective hourly = pay per accepted task x tasks per
   hour. Treat the first week as a measurement, not an income promise, and
   compute monthly income as `rate x hours x realization` (use 60-80% realization
   until measured) when comparing with a salary target.
3. **Check legitimacy before applying**, because fee-based and exclusivity
   schemes target people in a job search. All five must pass:
   1. no fee, deposit, equipment purchase or paid "assessment", ever;
   2. rate and payment cadence stated in writing before work starts;
   3. a real legal entity, an official company page and independent reviews
      (employee and contractor communities, not only the platform's own pages);
   4. no exclusivity: the contract lets the candidate work elsewhere;
   5. the tasks match the candidate's level (code and architecture evaluation,
      environment building), not generic labeling.

   For a recruiter, vendor chain or contract that needs a deeper look (headers,
   firms, money and terms), run `workflows/recruiter-legitimacy-check.md`.
4. **Unverified newer platforms:** apply only after the check passes; refuse
   unpaid multi-hour trials; ask who the end client is, the task type, guaranteed
   hours and the pay date. Report what could not be verified.
5. **Owner approves every application and every rate.** A rate and a résumé on a
   marketplace are statements made in the candidate's name, so the candidate
   enters them or gives an explicit OK first (`skills/job-search-pipeline/references/application-truthfulness.md`).

## Choosing the rate inside a band

Enter about 85-90% of the top of the band for a senior candidate whose experience
matches the exact task. The ceiling invites screening filters and the middle of
the band lowers per-task pay on platforms that scale it with the stated rate.
Examples: `$50-100 -> 90`, `$80-120 -> 110`, `$100-150 -> 130`,
`$245-280 -> 250`. Lower the number only if the first screening round rejects the
profile. Keep the same figure across platforms for similar work unless the band
differs.

## Ranking postings

- Same task, higher band first; mark lower-band duplicates as superseded.
- Credential lines such as "preferred: top company, top university, English-speaking
  country" are preferences, not requirements: apply, and let the screener decide.
- Prefer tasks that double as truthful evidence for the target roles (environment
  building, tool-protocol work, code evaluation) and say so in the tracker note.
- Typical pipeline: profile -> AI-led interview -> assessment -> project start
  within about 48 hours. Profiles persist on the site; check that the stored
  résumé file is the intended one.
- If the application form's Next/Submit does nothing, run
  `skills/web-form-submit-debugging/SKILL.md` and time-box it (15 minutes);
  a broken form is rarely worth more than that for a bridge gig.

## Tracker note format

`<platform> - <role> - band <low>-<high>/h - entered <rate>/h - ~<hours>/week - applied <date> - status`.

## Output

A ranked list, one block per posting, in this shape:

```text
<rank>. <platform> - <role>
   Band: <low>-<high>/h   Enter: <rate>/h   Cap: <n> h/week
   Legitimacy: pass | fail | unverified (missing: <item>)
   Monthly estimate: <rate x hours x 4.3 x 0.6> to <... x 0.8> (realization 60-80%)
   Note: <superseded by ... | evidence for target role | refuse trial>
```

Example: a posting at `$80-120/h` for code evaluation, 12 h/week, passes all
five checks: `Enter: 110/h`, monthly estimate `110 x 12 x 4.3 x 0.6` = about
3,400 to `x 0.8` = about 4,500, flagged "measure in week one".
