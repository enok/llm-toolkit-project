---
name: credential-evaluation
description: Decide whether a degree, MBA, master's, bootcamp, or certification is worth it for a person's career and whether it carries weight in the market. Verify the awarding body in the regulator's own register, check legal recognition in the person's home country, grade market evidence by source type, weigh fit and opportunity cost, compare accredited alternatives and non-degree signals, and return a verdict (worth it / not worth it / conditional) with sources. Use for "is this program worth it", "is this degree accredited or recognized", "MBA vs master's", online or white-label degree checks.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.0.0"
---

# Credential evaluation

Generic procedure for "is this credential worth it, and does it carry weight in
the market?". Everything personal (credentials held, target roles and countries,
budget, weekly hours) comes from the request or the user's profile, never from
this skill.

- Checks, red flags, source grading, dated reference data: `references/evaluation-checklist.md`.
- Country notes (Brazil, United States, European Union): `references/jurisdiction-notes.md`.
- Ready-to-dispatch lane and validator prompts: `references/lane-prompts.md`.

## Contract

1. **Orchestrate first.** Follow `rules/request-orchestration.md` and
   `tool-subagents/agent-orchestrator.md`: print the tasks table with tier and
   explicit model per lane before work starts.
   - Wave 1: three read-only research lanes in parallel, each `standard`
     (sonnet / medium): L1 awarding-body legitimacy, L2 home-country
     recognition, L3 market perception + alternatives.
   - Wave 2: the root synthesizes, drafts the verdict, and lists the ~10
     load-bearing claims with their source URLs.
   - Wave 3: one claim-check validator, `light` (haiku / medium). It is a
     different invocation than every producer
     (`workflows/task-quality-loop.md`). Fix or drop every FAIL and
     UNVERIFIED claim before answering.
2. **Primary sources outrank the page.** The program page and the awarding
   body's own accreditation page are vendor-side and omit restrictions.
   Licence scope, recent notices, QA-agency status, and recognition rules live
   in the regulator, the accreditor database, the law, and the receiving
   institution's own rules.
3. **Grade every source** (primary / secondary press / vendor claim /
   competitor claim / forum anecdote). Vendor, competitor, and forum material
   are claims, never evidence of market weight. No independent employer
   evidence is itself a finding: say so.
4. **Date perishable facts** (prices, cutoffs, notices, accreditation status)
   as "verified <date> - re-verify before relying". Reference-file figures are
   starting points: reopen the source before quoting one as current.
5. **Read-only and candid.** Never enroll, pay, or apply. A credential can be
   legitimate and still add little signal. This is not legal or immigration
   advice: send binding questions to the regulator, the receiving university,
   or the immigration authority.

## Procedure

1. **Name it precisely.** Degree type (MSc vs MBA vs certificate; people often
   say "MBA" for an MSc), awarding body (often not the brand on the page),
   level (EQF level and ECTS, or US credit hours), delivery (self-paced online,
   live, on-campus), total hours, real total cost and pricing model
   (subscription vs tuition).
2. **Awarding-body legitimacy from primary sources.** Licence type in the
   regulator's own register ("university" vs "higher education institution");
   the regulator's announcements page for notices about the institution
   (restrictions often name enrollment-date cutoffs); whether the national QA
   agency is on EQAR (EU) or the accreditor is recognized by USDE/CHEA (US);
   "state authorization" is not accreditation; flag the partner or
   member-college (white-label) model.
3. **Recognition where it will be used.** Home-country legal recognition
   (see jurisdiction notes), target employer markets, credential evaluators,
   immigration routes.
4. **Market signal.** Independent evidence that employers value it, program
   age, graduate outcomes data; grade each source.
5. **Person fit.** Credentials already held, target roles and markets,
   marginal signal added, opportunity cost (hours per week x months) against
   current commitments.
6. **Alternatives.** Same price band, accredited, selective admission (that is
   what carries weight), plus non-degree signals (public projects, open
   source, writing); employer surveys rank these above degrees.
7. **Verdict.** Worth it / not worth it / conditional, stating the condition
   (for example "only as structured content, not as a credential").

## Output shape

1. Verdict in one or two sentences.
2. Reasons: the 3-5 load-bearing findings, each with its source grade.
3. When it would make sense: the conditions that flip the verdict.
4. Accredited alternatives and non-degree signals, with price bands.
5. Sources: every URL opened, graded, with the date verified.

## Known pitfalls

- "Accredited" on a program page says nothing about licence scope, QA-agency
  status, or home-country recognition; open the regulator's register and
  announcements page. See
  `learnings/degree-accreditation-claims-need-regulator-check.md`.
