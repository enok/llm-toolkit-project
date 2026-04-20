---
title: pt-BR notebook patch anchor silently fails when EN/pt-BR cell strings diverge
category: toolchain
created: 2026-04-20
tags: [notebook, patch, anchor, ptbr, translation, ipynb, scripted-edit, silent-failure]
---

# Problem

A Python patch script (`_fix_06_maps.py`) correctly patched the EN notebook
but printed `WARNING: anchor not found` for the pt-BR version and silently skipped
the cell replacement. The script targeted the same anchor string in both notebooks.

# Failed Approaches

1. **Assumed pt-BR and EN notebooks had identical code cell content** — they do not.
   pt-BR notebooks sometimes retain English strings in error messages or print
   statements even after translation passes, especially in `try/except` blocks
   where the error message was never localised.
2. **Used the translated Portuguese string as anchor** — the actual cell still
   contained the English `print("[!] pyshp not installed - skipping GeoJSON.")`
   even though surrounding prose was Portuguese.

# Solution

Before writing any patch anchor, **verify the exact cell content** in the target
notebook via:

```python
import json
nb = json.loads(Path('notebooks/target.pt-BR.ipynb').read_text(encoding='utf-8'))
for i, c in enumerate(nb['cells']):
    src = ''.join(c.get('source', []))
    if 'pyshp' in src:
        print(f"Cell {i}:\n{src[:400]}")
```

Then use the **exact string found** as the anchor, not an assumed translation.
Patch scripts should also assert the replacement happened (count replacements,
raise on zero).

# Why

pt-BR notebooks are typically produced by translating EN notebooks with a script.
Code-path strings inside `except` blocks and debug `print()` calls are often
skipped during translation because they are not user-facing prose. This creates
a hidden divergence: the file is "Portuguese" but contains English strings in
low-visibility locations. Patch scripts that assume full translation have brittle
anchors that silently miss.
