---
title: Gold schema changes break notebooks with hardcoded column names
category: architecture
created: 2026-04-08
tags: [notebook, gold, schema, column-names, data-pipeline, drift]
---

# Problem

When Gold dataset schema changes (e.g., renaming `avg_income_2010` → `avg_income_real_2010_2022_brl`), notebooks that reference column names directly break with `KeyError`. This affects both English and pt-BR notebook variants.

Particularly tricky: notebooks that dynamically construct column names like `norm_features = [f'{col}_norm' for col in raw_features]` — the `raw_features` list must also be updated, not just explicit `_norm` references.

# Failed Approaches

1. Only updating explicit `_norm` column references — missed the `raw_features` list that dynamically generates normalized column names via f-string suffix.
2. Using `jupyter nbconvert --inplace` during debugging — overwrites the notebook with failed-execution outputs, destroying fixes applied between runs.

# Solution

When updating Gold schema:

1. **Update all column references** across all notebooks (EN + pt-BR pairs).
2. **Check dynamic column name generation** — search for patterns like `f'{col}_norm'` or list comprehensions that build column names from a base list.
3. **Also check pt-BR translation maps** in `src/config/pt_br_translations.py` for renamed columns.
4. **Never use `--inplace` during debugging** — write to a temp file first (`--output /tmp/test.ipynb`), then copy back only on success.

Use this script pattern to batch-fix column names in notebooks:

```python
import json
replacements = [
    ("'old_column_name'", "'new_column_name'"),
]

def apply_all(line):
    # Apply every pair to the same line; one output line per input line.
    for old, new in replacements:
        line = line.replace(old, new)
    return line

for fname in ["notebook.ipynb", "notebook.pt-BR.ipynb"]:
    with open(fname, encoding="utf-8") as f:
        nb = json.load(f)
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            cell["source"] = [apply_all(line) for line in cell["source"]]
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
```

Correction (2026-10-07): an earlier version of this snippet used a nested comprehension
(`for old, new in replacements for line in cell["source"]`) that emitted every line once per
replacement pair, duplicating the cell source whenever there were two or more pairs.

# Why

Gold datasets are contracts. Notebooks are downstream consumers. When the contract changes (column rename), all consumers must update. The bilingual notebook pattern doubles the maintenance surface. Dynamic column name construction hides references from simple grep searches.
