---
title: Credential evaluation checklist
tags: [credential-evaluation, accreditation, source-grading, checklist, reference-data]
---

# Evaluation checklist

Expands the seven procedure steps in `SKILL.md`. Tick each check with a source
URL you actually opened. A check you could not complete is reported as
"unverified", never as passed.

## 1. Name it precisely

- [ ] Degree type written out (MSc, MA, MBA, graduate certificate, bootcamp
      certificate, vendor certification). Users often say "MBA" for an MSc;
      confirm which one the program awards and what the diploma says.
- [ ] Awarding body named exactly as on the diploma, and compared with the
      brand on the marketing page. A different name is the white-label signal.
- [ ] Level: EQF level (7 = master's) and ECTS, or US credit hours. Convert:
      60 ECTS is about one full-time year at 25-30 hours per ECTS.
- [ ] Delivery: self-paced online, live online, hybrid, on-campus. Several
      recognition regimes treat this as a filter (see jurisdiction notes).
- [ ] Total hours, program length, and whether the degree is awarded by
      coursework alone or needs a supervised thesis.
- [ ] Real total cost: tuition, per-term fees, exam or proctoring fees,
      graduation or certificate fees, currency, and pricing model
      (subscription that keeps billing vs fixed tuition).

Red flags: "MBA" with ECTS but no business-school accreditation; price shown
per month with no total; diploma issued by a different entity than the one
marketed; "limited seats" countdowns.

## 2. Awarding-body legitimacy

- [ ] Open the regulator's own register and read the licence type and scope
      (a "university" licence differs from a "higher education institution"
      licence; scope may cover only teaching the institution delivers itself).
- [ ] Open the regulator's announcements or news page and search the
      institution's name. Restrictions often name enrollment-date cutoffs
      (students enrolled before a date unaffected, later ones restricted).
- [ ] EU: is the national QA agency itself registered on EQAR? Check the
      agency, not only the institution.
- [ ] US: is the institutional accreditor recognized by USDE or CHEA? State
      authorization or state approval to operate is not accreditation.
- [ ] Partner or member-college model: does the brand sell a degree that a
      different institution awards and quality-assures? Who teaches, who
      examines, who handles complaints?
- [ ] Cross-check the awarding body's own accreditation page against the
      register; the page is vendor-side and omits restrictions.

Red flags: accreditation claimed without naming the accreditor; accreditor not
in USDE/CHEA or EQAR lists; a notice on the regulator's page that the vendor
never mentions; "recognized in N countries" with no list.

## 3. Recognition where it will be used

- [ ] Home country: legal recognition path, who decides, what filters apply,
      cost, and real turnaround. Needed for public-sector posts, career
      progression, and university teaching.
- [ ] Target employer markets: does a hiring manager there know the awarding
      body? Is the degree even asked for in the target job postings?
- [ ] Credential evaluators (US: NACES members; some evaluators decline
      certain foreign institutions): ask before enrolling.
- [ ] Immigration routes: degree requirements of the visa or permit the
      person may use (some require a degree from a local accredited
      institution, others accept recognized degrees or experience).

Red flag: assuming "accredited in country X" implies recognition at home.

## 4. Market signal

- [ ] Independent evidence (survey of employers, hiring data, regulator or
      agency statistics) that employers value this credential.
- [ ] Program age and cohort size; graduate outcomes if published and audited.
- [ ] Grade every source with the table below. Search for reviews, then ask
      who funds each page.

Red flag: the only "reviews" are vendor marketing, a competitor's comparison
pages, and forum anecdotes. That is an absence of evidence; report it as such.

## 5. Person fit

- [ ] Credentials the person already holds (a degree in a related field makes
      a second credential add less).
- [ ] Target roles and markets, and what those postings actually require.
- [ ] Marginal signal: what hiring managers would learn from this line on a CV
      that they do not already know.
- [ ] Opportunity cost: hours per week x months, set against current job,
      job search, and family commitments. Compare with what the same hours
      would produce as public projects.

## 6. Alternatives

- [ ] At least two accredited programs in the same price band with selective
      admission; selectivity is what carries weight.
- [ ] Non-degree signals: public projects, open-source contributions, writing,
      talks. Employer surveys rank these above degrees (see data points).
- [ ] Employer-recognized vendor certifications only where job postings ask
      for them by name.

## 7. Verdict

- [ ] One of: worth it / not worth it / conditional.
- [ ] If conditional, state the condition in one sentence and who can falsify
      it (for example "only as structured content, not as a credential").
- [ ] Claim-check validator run over the load-bearing claims
      (`references/lane-prompts.md`, prompt V); defects fixed or claims dropped.

## Source grading

| Grade | Type | Examples | How to use |
| --- | --- | --- | --- |
| A | Primary | Regulator register and announcements, law and official gazette text, accreditor or QA-register database, a university's own recognition rules | Can carry a factual claim alone |
| B | Secondary press | News article reporting a survey or notice, law-firm or provider explainer | Context; open the primary behind it; note who ran the survey and their interest |
| C | Vendor claim | Program page, brochure, sales call, awarding body's marketing or accreditation page | A claim only; confirm in grade A |
| D | Competitor claim | A rival's "alternatives" or comparison pages | A claim with a conflict of interest; use to find leads |
| E | Forum anecdote | Discussion threads, social posts, single reviews | A lead; n=1; never the basis of a verdict |

## Reference data points (verified 2026-10-21 — re-verify before relying)

Starting points for step 4 and step 6. Reopen each source before quoting.

- **Employer survey** (verified 2026-10-21 — re-verify before relying). Reported
  by Fortune on 18 Dec 2025, from a survey of 200+ engineering leaders run by a
  nonprofit coding-education organization (an interested party: grade B). Share
  of leaders citing each as a hiring signal: side projects 38%, public code 34%,
  degree 23%, credentialing programs 4%. Source:
  https://fortune.com/2025/12/18/tech-hiring-slow-but-not-fully-stalled-exclusive-codepath-data-new-secret-to-land-tech-role/
- **Accredited online master's price points** (verified 2026-10-21 —
  re-verify before relying; prices change each term):
  - Georgia Tech online MS in computer science: $227 per credit hour plus a
    per-semester online fee of $212 (under 4 credits) or $531 (4+ credits);
    30 credits is about $9k in total.
    https://bursar.gatech.edu/student/tuition/fa26/fa26_omscs.pdf
  - UT Austin online MS in AI: $10,000 total tuition. https://cdso.utexas.edu/
  - UIUC online MS in computer science: $19,840 to $25,376 (program page not
    captured here; open the university's own tuition page).
  - CU Boulder MS in AI: $15,750, with performance-based admission.
    https://www.coursera.org/degrees/ms-artificial-intelligence-boulder/tuition-financing
