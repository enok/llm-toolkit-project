---
name: ibge-datasets
description: |
  Work with Brazilian IBGE (Instituto Brasileiro de Geografia e Estatística) public
  datasets — municipality codes, population estimates, Censo Demográfico, PNAD,
  PIB municipal, and geographic boundaries. Use for municipality-level analysis,
  joining IBGE data with other public datasets, handling IBGE 7-digit codes,
  or accessing IBGE REST APIs (Sidra, Servicodados).
license: MIT
---

# IBGE Datasets (Brazil)

Brazilian statistical office datasets for municipal-level analysis.

> **Reference**: See `references/ibge-apis.md` for full API specs.

## Quick Reference

### Municipality Code (the universal join key)
- **7-digit code** (IBGE): e.g., `3550308` = São Paulo/SP
  - First 2 digits: state (35 = SP)
  - Next 5 digits: municipality within state
- **6-digit code** (legacy): older datasets may use this; multiply by 10 and add check digit
- **Always store as string** to preserve leading zeros

### Key IBGE Datasets for Municipal Compliance Analysis

| Dataset | Content | API Endpoint |
|---------|---------|--------------|
| Municípios | Full list with names, states, region | `servicodados.ibge.gov.br/api/v1/localidades/municipios` |
| População (estimativa) | Annual population estimates | `servicodados.ibge.gov.br/api/v3/agregados/6579` |
| Censo Demográfico | Decennial census | `servicodados.ibge.gov.br/api/v3/agregados/` (multiple tables) |
| PIB dos Municípios | Municipal GDP | `servicodados.ibge.gov.br/api/v3/agregados/5938` |
| Malhas geográficas | Shapefiles/GeoJSON | `servicodados.ibge.gov.br/api/v3/malhas/` |

### Sidra vs Servicodados
- **Sidra** (`apisidra.ibge.gov.br`) — older SDMX-like queries, comprehensive
- **Servicodados** (`servicodados.ibge.gov.br`) — modern REST JSON, preferred for new code

### Typical Query Pattern
```python
import requests

def fetch_ibge_aggregate(aggregate_id: int, period: str, variable: str = "allxp"):
    """
    aggregate_id: IBGE table ID (e.g. 6579 for population)
    period: 'YYYY' or 'YYYY-YYYY' range
    variable: variable code or 'allxp' for all
    """
    url = (
        f"https://servicodados.ibge.gov.br/api/v3/agregados/{aggregate_id}"
        f"/periodos/{period}/variaveis/{variable}"
        "?localidades=N6[all]"  # N6 = municipality level
    )
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()
```

### Data Hygiene
- **5570 municipalities** in Brazil (as of 2023) — use this as sanity check
- **Null handling**: IBGE uses `-` or `...` or `..` for "not applicable" / "data unavailable"; treat as NaN
- **Year coverage**: varies per dataset; always check `Nivel territorial` and `periodo` fields

## When to Apply

- Loading municipality master data
- Joining federal transfers with population/GDP
- Computing per-capita or intensity metrics
- Creating municipality-level choropleth maps
- Validating that municipality codes are well-formed (7 digits, valid state prefix)

## Common Pitfalls

- **Coding changes over time**: some municipalities created/split; check creation year
- **Accent-stripped names don't match**: always join by code, never by name
- **Territorial levels**: N1=Brazil, N2=region, N3=state, N6=municipality; filter carefully
- **API rate limits**: ~20 requests/sec; use backoff for bulk ingestion

## Related

- `skills/data-pipeline/` — Bronze/Silver/Gold pipeline patterns
- `skills/transparency-portal/` — Complementary federal spending API
- `workflows/dataset-onboarding.md` — Onboard new datasets
- `workflows/data-source-ingestion.md` — Ingestion discipline

## References

- [IBGE Servicodados API](https://servicodados.ibge.gov.br/api/docs)
- [Sidra Documentation](https://apisidra.ibge.gov.br/)
- [Brazilian municipality evolution](https://www.ibge.gov.br/geociencias/organizacao-do-territorio/estrutura-territorial/)
