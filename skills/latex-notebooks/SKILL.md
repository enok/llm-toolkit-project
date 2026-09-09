---
name: latex-notebooks
description: Write and maintain LaTeX math inside Jupyter notebooks and technical docs. Use for equation cleanup, notation consistency, markdown math rendering, export issues, and explaining formulas with readable prose.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# LaTeX Notebooks

Help engineers express technical math clearly in notebook markdown and adjacent documentation.

## When to Apply

- equation formatting or cleanup
- notation consistency problems
- MathJax rendering issues in Jupyter markdown
- export-to-HTML or PDF math regressions
- technical report polish for statistics, optimization, or ML formulas

## Steps

1. Identify the key equations and the symbols that readers must understand.
2. Standardize notation across prose, math blocks, code variables, and charts where practical.
3. Prefer editable markdown plus LaTeX over screenshots or pseudo-math.
4. Add short prose around equations so the reader knows what each expression is used for.
5. Verify rendering in the notebook or export target before considering the change done.
6. Keep the final notation aligned with the implementation and dataset terminology.

## Related Rules And Workflows

- `skills/notebook-analysis/references/latex-in-notebooks.md`
- `skills/notebook-analysis/references/notebook-discipline.md`
- `workflows/notebook-latex-polish.md`

## Pair With

- `jupyter-notebook`
- `notebook-analysis`
- `ml-engineering`
