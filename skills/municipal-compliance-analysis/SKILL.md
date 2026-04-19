---
name: municipal-compliance-analysis
description: |
  Analyze relationships between federal transfer spending (treatment) and municipal
  compliance outcomes (sanctions, audit findings) in Brazil. Use for correlation/causal
  inference on Brazilian municipal panel data, building treatment-outcome joins,
  handling confounders (population, GDP, region), and interpreting results in the
  context of Brazilian federalism and LGPD constraints.
license: MIT
---

# Municipal Compliance Analysis (Brazilian Public Sector)

Treatment ↔ outcome analysis for federal transfers vs compliance in Brazilian municipalities.

> **Reference**: See `references/methodology.md` for full analytical approach and limitations.

## Quick Reference

### The Core Question
> Do federal transfers (treatment) correlate with compliance outcomes (outcome) in Brazilian municipalities, controlling for confounders?

### Treatment Variables (from Transparency Portal)
- **Total federal transfers per municipality per year** (BRL)
- **Transfer diversity** (# of distinct programs)
- **Per-capita transfer** (normalized by IBGE population)
- **Transfer concentration** (Gini within municipality)

### Outcome Variables (compliance)
- **Sanction count** (CEIS/CNEP/CEPIM entries for municipality)
- **Sanction severity** (weighted by sanction type duration/amount)
- **TCU audit findings** (if linked)

### Key Confounders (MUST control for)
- **Population size** (IBGE) — larger municipalities have more of everything
- **GDP per capita** (IBGE) — economic capacity affects both transfer allocation and compliance infrastructure
- **Region** (N/NE/SE/S/CO) — historical/institutional variation
- **HDI** (municipal HDI if available) — composite governance capacity proxy
- **Political alignment** (if dataset permits) — known confounder in federal transfer allocation

### Typical Analytical Pipeline

```python
# 1. Build panel: (municipality, year) → treatment, outcome, confounders
panel = join_all([
    transfers_df,            # treatment
    sanctions_df,            # outcome
    population_df,           # confounder
    gdp_df,                  # confounder
    region_master,           # confounder
], on=["municipality_code", "year"])

# 2. Validate coverage
assert panel["municipality_code"].nunique() > 5000  # of ~5570 Brazilian municipalities
assert panel["year"].nunique() >= 5  # multi-year for panel effects

# 3. Fit model (examples in order of complexity)
# Simple: log-log OLS with region/year fixed effects
# Intermediate: negative binomial (count outcomes), clustered SE
# Advanced: two-way FE panel, IV if instrument exists, DiD if quasi-experiment
```

### Clustering for Segmentation
- **Features**: population size, GDP/capita, region, HDI
- **Algorithm**: k-means (k=4-6) or hierarchical (Ward) for interpretability
- **Validation**: silhouette score, domain-meaningful cluster profiles

## When to Apply

- Building the thesis panel dataset (treatment + outcome + confounders)
- Interpreting regression/model results for compliance outcomes
- Selecting appropriate statistical methods (OLS vs GLM vs panel)
- Validating that municipality code joins are sound
- Writing the methodology/results chapters with Brazilian context

## Limitations to Disclose (thesis requirement)

- **Sanctions are lagging indicators** — compliance violations discovered years after
- **Selection bias** — only detected violations appear in registries
- **Reverse causality** — already-violating municipalities may receive less/different transfers
- **Unobserved political economy** — coalition/alignment variables rarely public
- **LGPD** limits — some fine-grained data (individuals) not ethically usable
- **External validity** — Brazilian findings may not generalize to other federal systems

## Domain Terms

- **Transferência voluntária** — discretionary federal transfer (convênios)
- **Transferência obrigatória** — constitutional/legal mandatory transfer (FPM, FPE)
- **SIAFI** — federal financial system (some datasets sourced here)
- **TCU** — Tribunal de Contas da União (federal audit court)
- **CGU** — Controladoria-Geral da União (runs Transparency Portal)

## Related

- `skills/transparency-portal/` — Treatment variable ingestion
- `skills/ibge-datasets/` — Confounder ingestion
- `skills/ml-experiment/` — Model training discipline
- `skills/research-thesis-support/` — Research rigor
- `skills/data-governance/` — LGPD/ethics
- `workflows/research-analysis-cycle.md` — Evidence cycle

## References

- Arretche, M. (2012) — Democracia, Federalismo e Centralização no Brasil
- Bucciferro, J. R. (2017) — Transferências intergovernamentais e accountability
- LGPD (Lei 13.709/2018) — data protection bounds
