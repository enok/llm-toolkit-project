---
name: jupyter-notebook
description: Work effectively in Jupyter notebooks. Use for notebook cleanup, kernel-state bugs, cell-order issues, output hygiene, notebook review, and promoting stable notebook logic into reusable code.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Jupyter Notebook

Help engineers work in notebooks without turning them into opaque, one-off artifacts.

## When to Apply

- notebook cleanup and restructuring
- kernel-state or cell-order bugs
- output cleanup and reviewability improvements
- data loading and environment setup inside notebooks
- promoting notebook logic into scripts or modules
- preparing a notebook for sharing, review, or reruns

## Steps

1. Inspect notebook inputs, environment assumptions, and data-loading cells before changing analysis logic.
2. Make the cell order executable from a clean kernel and remove hidden state dependencies.
3. Keep markdown explanations close to the logic they explain.
4. Clear or reduce noisy outputs that do not help review.
5. Extract stable logic into reusable code when the notebook is doing repeated or production-adjacent work.
6. Restart and run all before considering the notebook complete.

## Related Rules And Workflows

- `skills/notebook-analysis/references/notebook-discipline.md`
- `skills/notebook-analysis/references/analytics-discipline.md`
- `workflows/notebook-analysis-update.md`
- `workflows/notebook-to-script.md`

## Pair With

- `notebook-analysis`
- `latex-notebooks`
- `ml-engineering`
- `python-best-practices`
