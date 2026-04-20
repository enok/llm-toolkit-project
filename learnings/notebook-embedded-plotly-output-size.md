---
title: Embedded Plotly outputs inflate notebook files to 100MB+ and block git push
category: toolchain
created: 2026-04-20
tags: [notebook, plotly, outputs, file-size, git, push, ipynb, clear-outputs]
---

# Problem

After adding interactive Plotly `scatter_mapbox` and `make_subplots` visualisations
to notebooks, `git push` was about to fail (and `git diff --stat` showed 4M+ line
deltas). Specifically, `04_clustering_analysis.pt-BR.ipynb` grew to **124 MB** because
a single cell contained a choropleth map rendered to `application/vnd.plotly.v1+json`
output embedded in the notebook JSON — the output was ~40 MB by itself.

# Failed Approaches

- None attempted for this specific issue — it was caught during pre-commit review
  before pushing.
- GitHub's 100 MB hard file-size limit would have rejected the push silently for
  that file.

# Solution

Run `scripts/clear_notebook_outputs.py` before committing any notebook that
contains Plotly (or any rich-output) cells. The script clears all `outputs` and
resets `execution_count` to `null` across all notebooks:

```bash
python scripts/clear_notebook_outputs.py
```

After clearing, `04_clustering_analysis.pt-BR.ipynb` shrank from 124 MB → 70 KB.

**Permanent fix:** wire `clear_notebook_outputs.py` into the pre-commit hook so
notebook output bloat can never land in a commit. Add to `.git/hooks/pre-commit`:

```sh
python "$REPO_ROOT/scripts/clear_notebook_outputs.py"
git add notebooks/*.ipynb  # re-stage the stripped versions
```

# Why

Plotly stores the entire figure data model as JSON inside the notebook output
(`application/vnd.plotly.v1+json`). A choropleth over 5,570 Brazilian municipalities
with full GeoJSON geometry embedded produces ~40 MB per cell. Multiple such cells
compound quickly. Jupyter never warns about this; it only becomes visible when
checking file sizes or hitting git's push limit.
