---
description: Keep English and Portuguese notebook pairs synchronized after edits (cells, outputs, narrative, translations)
---

# Bilingual Notebook Sync Workflow

Use this workflow when modifying notebooks that exist in both English (`notebooks/`) and Portuguese (`notebooks/pt-BR/`) versions.

## When to Use

- Adding new analysis to existing notebooks
- Updating visualization or output sections
- Refactoring code across notebook pairs
- Fixing bugs that affect both language versions

## Repository-Specific Steps

### 1. Identify the Notebook Pair

Find the corresponding notebook in both languages:
- English: `notebooks/<analysis>_<topic>.ipynb`
- Portuguese: `notebooks/pt-BR/<analysis>_<topic>.ipynb`

Examples:
- `notebooks/01_statistical_analysis.ipynb` ↔ `notebooks/pt-BR/01_statistical_analysis.ipynb`
- `notebooks/02_regression_models.ipynb` ↔ `notebooks/pt-BR/02_regression_models.ipynb`

### 2. Determine Change Scope

What type of change are you making?

| Change Type | English First | Portuguese Sync | Notes |
|-------------|---------------|-----------------|-------|
| Code/algorithm | ✓ | Mirror exactly | Code should be identical |
| Markdown narrative | ✓ | Translate | Keep technical terms consistent |
| Output cells | Regenerate | Regenerate | Ensure reproducibility |
| Variable names | ✓ | Mirror exactly | Do not translate variable names |
| Dataset references | ✓ | Mirror exactly | Paths and keys stay in English |

### 3. Apply Changes

**Always modify the English version first**, then mirror to Portuguese:

1. Make changes to the English notebook
2. Run the English notebook to verify outputs
3. Apply the same code changes to the Portuguese notebook
4. Translate markdown narrative while keeping:
   - Code identical
   - Variable names unchanged
   - Dataset paths unchanged
   - Technical terms consistent with the course materials

### 4. Validate Synchronization

Check that both notebooks:
- [ ] Have identical code cells (except markdown content)
- [ ] Use the same variable names and data paths
- [ ] Reference the same dataset versions
- [ ] Produce equivalent outputs (allowing for randomness if seeds are set)
- [ ] Have parallel section structures

### 5. Test Execution

- [ ] English notebook runs without errors: `jupyter nbconvert --execute notebooks/<name>.ipynb`
- [ ] Portuguese notebook runs without errors: `jupyter nbconvert --execute notebooks/pt-BR/<name>.ipynb`
- [ ] Outputs are reproducible (re-run produces same results)

### 6. Commit Strategy

Commit both notebooks together:
```
ABC-123: Update <analysis> notebooks (EN + pt-BR)

- Changes: <brief description>
- English: notebooks/<name>.ipynb
- Portuguese: notebooks/pt-BR/<name>.ipynb
```

## Translation Guidelines

### Keep in English
- Code (variable names, functions, class names)
- Dataset column names when referencing code
- File paths and S3 keys
- Python package names
- Configuration keys

### Translate to Portuguese
- Narrative explanations
- Section titles and headers
- Figure captions
- Interpretation of results
- Warnings and notes to readers

### Technical Terminology
Use consistent translations for domain terms:
| English | Portuguese |
|---------|------------|
| Municipalities | Municípios |
| Clustering | Clusterização |
| Outliers | Outliers (keep) or Valores atípicos |
| Income per capita | Renda per capita |

## Known pitfalls

- **Translating variable names**: `df_municipios` should stay `df_municipios`, not become `df_municipios_pt`
- **Different random seeds**: Ensure both notebooks use the same seeds for reproducibility
- **Path differences**: Both should reference the same data sources, not language-specific copies
- **Output drift**: Clear outputs before committing; regenerate in both languages
- Verify the exact cell text in the target pt-BR notebook before writing a patch anchor: pt-BR cells can keep English strings (for example `print()` or `except` messages never localised), so a translated or assumed anchor can miss. Make the patch script count replacements and fail on zero instead of printing a warning. See learnings/notebook-patch-anchor-mismatch-ptbr.md.
- When both language notebooks write the same output file (for example a GeoJSON), pick one canonical language for its property names, document it in the notebook that regenerates it, and re-check the file after running either notebook: whichever runs last silently rewrites the schema and breaks consumers such as QGIS projects. Prefer generating the file from a dedicated script with a fixed property schema. See learnings/geojson-property-language-drift.md.

## Related Resources

- `workflows/bilingual-doc-sync.md` — For README and documentation files
- `workflows/notebook-analysis.md` — For notebook quality checks
