---
title: Execute Notebooks to Temporary Output During Repairs
impact: MEDIUM
impactDescription: nbconvert --inplace can overwrite source notebooks with partial failed execution output
tags: python, jupyter, notebook, nbconvert, validation
---

## Avoid `--inplace` during notebook repair loops

When iterating on notebook fixes, execute to a temporary output file first. Copy results back only after execution succeeds.

```bash
jupyter nbconvert --to notebook --execute \
  --ExecutePreprocessor.timeout=300 \
  notebooks/example.ipynb \
  --output /tmp/example.executed.ipynb
```

Use `--inplace` only for final runs where failure would not destroy uncommitted fixes. Failed inplace execution may still write partial output and traceback cells into the source notebook.
