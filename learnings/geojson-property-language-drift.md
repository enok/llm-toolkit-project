---
title: GeoJSON property names drift to whichever notebook language ran last
category: data-pipeline
created: 2026-04-20
tags: [geojson, qgis, ptbr, english, assets, schema, drift, notebook, presentation-assets]
---

# Problem

`docs/thesis_presentation_assets/qgis/brazil_municipalities_vulnerability_index.geojson`
had **English property names** committed (`municipality_code`, `avg_income_2022`, …).
After running the pt-BR notebook the file was regenerated with **Portuguese property
names** (`codigo_municipio`, `renda_media_2022`, …). Any QGIS project or downstream
consumer referencing the original English properties silently breaks.

# Failed Approaches

- No explicit fix was attempted during the session — the issue was discovered during
  the pre-commit diff review (`git diff --stat` showed 89,120 line delta on the file).
- Attempting to keep both sets of properties doubles GeoJSON size and adds confusion.

# Solution

**Pick one canonical language** for the GeoJSON and document it.  
This project chose **Portuguese** (matching the thesis primary language) as canonical.

QGIS projects must reference Portuguese property names. Add a one-line comment to
whichever notebook regenerates this file:

```python
# NOTE: GeoJSON properties use Portuguese names (pt-BR schema). See learnings/.
```

**Longer term:** generate the GeoJSON from a dedicated script (not a notebook side
effect) that always uses a fixed property schema, so EN/pt-BR notebook execution
order cannot silently change the output.

# Why

Both the EN and pt-BR notebooks write to the same output path with different property
name sets derived from their respective Gold schema column names. Whichever notebook
runs last wins. With no enforcement, CI or manual execution can flip the schema
invisibly between commits.
