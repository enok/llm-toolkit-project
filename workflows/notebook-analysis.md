---
description: Work safely in notebooks while preserving reproducibility and promotion paths into versioned code
---

# Notebook Analysis Workflow

Use when creating or editing notebooks for EDA, statistical analysis, clustering, visualization, or report support.

## Steps

1. Confirm the data prerequisite:
   - which dataset or layer is needed
   - whether a pipeline step must run first
   - how the notebook locates data and credentials
2. Declare notebook inputs near the top: bucket or path, profile, cache choice, seed, and any filters.
3. Keep reusable logic out of cells:
   - move loaders, feature prep, repeated statistics, or plotting helpers into `src/` or scripts
   - keep the notebook focused on orchestration and interpretation
4. Run from a clean kernel and verify the notebook works top to bottom.
5. Add markdown conclusions close to the figures or tables they describe.
6. If the findings influence product, thesis, or operational decisions, reflect them in committed docs or code comments outside the notebook too.
7. If the repo maintains translated analysis surfaces, update the related labels or docs after changing the analytical narrative.

## Exit Criteria

- Notebook can be rerun from a clean state.
- Key logic is not trapped in cells only.
- Findings and limitations are documented where future sessions can find them.
