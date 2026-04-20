---
title: Notebook ExecuteTime metadata creates misleading git diffs with no source change
category: toolchain
created: 2026-04-20
tags: [notebook, metadata, ExecuteTime, git, diff, noise, revert, ipynb]
---

# Problem

`git diff --stat` showed `00_etl_pipeline.ipynb` and `00_etl_pipeline.pt-BR.ipynb`
as modified (68 and 287 line deltas respectively). Detailed inspection revealed the
only changes were `ExecuteTime` timestamps inside cell metadata — **no source code
changed at all**. Including these in commits pollutes history with zero-value noise.

# Failed Approaches

- Eyeballing `git diff --stat` line counts alone does not distinguish timestamp
  noise from real changes — large counts can come from either.

# Solution

Before staging notebooks, run a source-only comparison to detect true code changes:

```python
import json, subprocess
from pathlib import Path

for p in Path('notebooks').glob('*.ipynb'):
    r = subprocess.run(['git', 'show', f'HEAD:{p}'], capture_output=True)
    if r.returncode != 0:
        continue
    old_src = [''.join(c.get('source', [])) for c in json.loads(r.stdout)['cells']]
    new_src = [''.join(c.get('source', [])) for c in json.loads(p.read_text('utf-8'))['cells']]
    diffs = sum(1 for a, b in zip(old_src, new_src) if a != b)
    if diffs == 0 and len(old_src) == len(new_src):
        print(f"REVERT (timestamp only): {p.name}")
```

Then revert the timestamp-only files:

```bash
git checkout -- notebooks/00_etl_pipeline.ipynb notebooks/00_etl_pipeline.pt-BR.ipynb
```

**Permanent fix:** add `*.ipynb` to `.gitattributes` with `nbstripout` filter, or
strip `metadata.ExecuteTime` in `clear_notebook_outputs.py` before committing.

# Why

JupyterLab and VS Code write `ExecuteTime` start/end timestamps into each code
cell's `metadata` block whenever a cell is executed, regardless of whether the
source changed. `git.attributes` `text=auto` normalises line endings but does not
strip metadata. The result is a noisy diff every time a notebook is re-run.
