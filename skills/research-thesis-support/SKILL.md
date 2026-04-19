---
name: research-thesis-support
description: Plan and execute evidence-heavy research, capstone, thesis, or dissertation work in data science and analytics repositories. Use for refining research questions, mapping methods to datasets, coordinating notebooks and reusable code, and keeping claims, limitations, figures, and written deliverables aligned.
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Research Thesis Support

Help analysts and engineers keep research work scoped, reproducible, and connected to the written argument it supports.

## When to Apply

- thesis, dissertation, capstone, or paper support
- research question or hypothesis refinement
- method selection for statistical or ML analysis
- figure, table, or results updates
- notebook, code, and narrative synchronization
- limitations, validity threats, ethics, or governance checks

## Steps

1. State the objective in plain language: question, unit of analysis, target or outcome, comparison, time boundary, and audience.
2. Separate exploratory work from confirmatory claims before choosing methods or metrics.
3. Map each important claim to its supporting data source, code path, notebook, figure, table, and document section.
4. Keep stable preprocessing, feature logic, and statistical helpers in reusable code once they matter beyond one notebook pass.
5. Record dataset versions, seeds, filters, major parameters, and assumptions so another session can reproduce the result.
6. Write limitations and causal caveats explicitly, especially when the work may influence policy, compliance, or high-stakes decisions.
7. Update the written deliverable when analytical evidence changes, not later.

## Related Rules And Workflows

- `rules/research-rigor.md`
- `rules/evidence-based-reporting.md`
- `workflows/research-analysis-cycle.md`
- `workflows/document-creation.md`

## Pair With

- `ml-engineering`
- `notebook-analysis`
- `data-governance`
- `doc-delta`
