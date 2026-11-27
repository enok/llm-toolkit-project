---
name: productivity-impact-estimate
description: Estimate how much engineering time the toolkit saves per week, month and year with a transparent, reproducible model (baseline week by activity, conservative and likely saving percentages, team-of-1/5/10 roll-ups), clearly labelled as an estimate and not a measurement. Use whenever someone asks "how much time does the toolkit save", "what is the productivity impact", "what is the ROI of these assets", "build the adoption case for the team", "justify rolling this out", or wants hours-saved numbers for a slide or proposal, even if they do not say "estimate".
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.0.0"
---

# Productivity impact estimate

Produce a defensible, labelled estimate of weekly time saved by the toolkit.
Impact claims invite challenge, so the value of this skill is that every number
traces to an assumption the reader can change; a precise-looking figure with no
visible assumptions is worse than no figure.

## Steps

1. **Ask for the team's own baseline once.** If the user knows how their week
   splits (review, coding, CI, ops, docs, meetings), collect hours per activity
   and save them as a JSON rows file (format in
   `references/estimate-model.md`, section 4). If they do not know, say you will
   use the default assumed week and that it is an assumption.
2. **Run the script** (stdlib only; no network):

   ```bash
   python3 skills/productivity-impact-estimate/scripts/productivity_estimate.py \
     --out estimate.csv [--rows my_baseline.json] [--json]
   ```

   `--out` is the per-activity table, `--json` prints the roll-ups (week,
   month, year, team of 1, 5 and 10).
3. **Check the asset names** in the table with `ls` against the current
   repository before showing them; assets are renamed and the table must not
   point at things that do not exist.
4. **Present as an estimate.** Use this shape:

   ```text
   Estimate (not a measurement): <low> to <high> hours saved per person per week
   Baseline: <assumed week | the team's own week>, <N> h
   Per year at 46 weeks: <low> to <high> h; team of <n>: <low> to <high> FTE
   Assumptions you can change: <baseline hours>, <saving % per activity>
   Not verified: the study citations behind the bands (see reference)
   ```
5. **Keep citations honest.** The studies behind the saving bands were not
   verified in the sandbox that produced the model. Each is marked
   "unverified — verify before quoting" in `references/estimate-model.md`
   section 5. Open the source and confirm it before quoting any of them; until
   then describe the bands as judgment.

## Example

Request: "Give me a number for how much time the toolkit saves, for my manager."
Response: run with defaults, report "an estimated 2.2 to 6.4 hours per person
per week (5% to 16% of an assumed 40-hour week)", list the assumptions, offer to
rerun with the team's real split, and do not cite any study as proof.

## When to read the reference

Read `references/estimate-model.md` when replacing the baseline, explaining a
band, checking the wording rules, or when someone asks where the percentages
come from.
