---
trigger: always_on
description: Research rigor and evidence-based reporting — question framing, method fit, claim discipline, narrative sync, and honest limitations
---

# Research Discipline

Analytical research is not complete when a model runs or a chart looks plausible. It is complete when the question, evidence boundary, method choice, and limits of the conclusion are all explicit.

## Frame the Question First

- State the research or decision question before changing code, methods, or notebook structure.
- Name the unit of analysis, time boundary, target or outcome, comparison group or baseline, and intended reader.
- Distinguish predictive, descriptive, diagnostic, and causal goals. Do not let the language imply a stronger claim than the method supports.

## Match Method to Claim

- Choose statistical or ML methods that fit the actual data structure, not the most advanced method available.
- Prefer a simpler method when it answers the question with fewer assumptions.
- Treat robustness checks, diagnostics, and alternative specifications as part of the result, not optional polish.

## Protect Validity

- Make leakage, selection effects, survivorship bias, missingness, and temporal ordering explicit before trusting a result.
- Check whether aggregation level, geography, or entity linkage could distort the inference.
- Separate exploratory signal from evidence strong enough to support a written conclusion.

## Claim Discipline

- Every important claim should map to a reproducible artifact: code, notebook cell sequence, figure, table, or documented metric.
- Avoid summary language like "proved" or "demonstrated" when the underlying method only supports association, ranking, or exploratory signal.
- Keep assumptions, exclusions, and threshold choices close to the claim they affect.

## Figures and Tables

- Prefer figures and tables that answer a specific question instead of dumping intermediate diagnostics into the main narrative.
- Label the population, time window, aggregation level, and metric definition clearly.
- Regenerate derived visuals and tables from code when data or methods change; do not hand-edit outputs that should be reproducible.

## Narrative Sync

- Update the written argument in the same change when the result changes materially.
- Revise limitations and caveats whenever a method, dataset boundary, or interpretation changes.
- If a repo maintains translated or paired analytical documentation, keep the companion surface aligned or explain the intentional divergence.

## Reproducibility

- Record dataset versions, extraction dates, seeds, filters, joins, and major parameters.
- Keep stable transformations and repeated statistics in committed code, not hidden notebook state.
- Make figures, tables, and narrative claims traceable to committed analysis artifacts.

## State Limits Honestly

- Document sample-size limits, proxy-label caveats, and measurement issues.
- If the work touches public policy, compliance, fairness, or governance, call out those constraints explicitly.
- Prefer a narrower defensible claim over a broad but weak conclusion.
- Surface uncertainty, non-results, and failed approaches when they materially affect the recommendation.
- Leave enough traceability that another engineer or reviewer can rebuild the evidence chain without private context.
