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

## Known pitfalls

- Before committing a notebook with Plotly or other rich-output cells, run the project's `scripts/clear_notebook_outputs.py` (or its equivalent; it clears all `outputs` and resets `execution_count` to `null`) and check file sizes: an embedded `application/vnd.plotly.v1+json` choropleth was about 40 MB per cell and one notebook reached 124 MB against GitHub's 100 MB limit. Wire the script into the pre-commit hook and re-stage the stripped notebooks so the bloat cannot land. See learnings/notebook-embedded-plotly-output-size.md.
- Before staging notebooks, compare cell sources with `HEAD` (do not judge by `git diff --stat` counts) and revert files whose only change is `ExecuteTime` metadata with `git checkout -- <notebook>`; keep the noise out of later diffs with an `nbstripout` filter in `.gitattributes` or by stripping `metadata.ExecuteTime` in the output-clearing script. See learnings/notebook-timestamp-noise-in-diff.md.
- Never hardcode bucket or profile names in code cells: read them from environment variables first, then from the project's runtime config file (for example `config/runtime_config.json`), and never `print()` them (printed values land in committed outputs). Edit the notebook JSON cells with a Python script, because text-replace edit tools in most IDEs cannot edit `.ipynb` JSON. See learnings/notebook-hardcoded-aws-credentials.md.
- Never debug with `jupyter nbconvert --inplace`: it overwrites the notebook with failed-execution outputs and destroys fixes applied between runs. Write to a temp file (`--output /tmp/test.ipynb`) and copy back only on success. See learnings/gold-schema-drift-breaks-notebooks.md.

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
