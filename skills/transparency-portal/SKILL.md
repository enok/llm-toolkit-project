---
name: transparency-portal
description: |
  Work with Brazilian Portal da Transparência (CGU) public API — federal transfers
  to municipalities, public sanctions (CEIS/CNEP/CEPIM), and government spending.
  Use for ingesting federal spending data, sanction datasets, paginated API access,
  API key handling, and compliance analysis joining transfer data with outcomes.
license: MIT
---

# Portal da Transparência (CGU)

Brazilian Federal Government Transparency Portal — federal spending and sanctions data.

> **Reference**: See `learnings/transparency-portal-api.md` for the endpoint catalog, auth, and pagination notes.

## Quick Reference

### Authentication
- Requires **API token** — register at https://api.portaldatransparencia.gov.br/
- Header: `chave-api-dados: YOUR_TOKEN`
- **NEVER hardcode** — load from `.env` / `TRANSPARENCY_API_KEY`
- Rate limit: **30 req/min** (weekdays 06:00–23:59), **180 req/min** (nights/weekends)

### Key Endpoints for Thesis (Federal Transfers → Compliance)

| Dataset | Endpoint | Use Case |
|---------|----------|----------|
| Transferências da União | `/api-de-dados/transferencias` | Federal transfers by municipality (treatment variable) |
| CEIS | `/api-de-dados/ceis` | Inidôneas/suspensas (compliance outcome) |
| CNEP | `/api-de-dados/cnep` | Empresas punidas (compliance outcome) |
| CEPIM | `/api-de-dados/cepim` | Entidades impedidas (compliance outcome) |
| Convênios | `/api-de-dados/convenios` | Federal agreement spending |
| Servidores | `/api-de-dados/servidores` | Federal payroll (PII sensitive) |

### Pagination Pattern
```python
def fetch_all_pages(endpoint: str, params: dict, api_key: str, max_pages: int = None):
    """
    Portal uses 1-indexed 'pagina' query param. 15 records per page default.
    Stop when response array is empty.
    """
    headers = {"chave-api-dados": api_key, "Accept": "application/json"}
    all_records = []
    page = 1
    while True:
        r = requests.get(
            f"https://api.portaldatransparencia.gov.br{endpoint}",
            headers=headers,
            params={**params, "pagina": page},
            timeout=30,
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        all_records.extend(batch)
        page += 1
        if max_pages and page > max_pages:
            break
        time.sleep(2)  # rate limit guard
    return all_records
```

### Checkpoint/Resume Pattern
- Store last successful `(endpoint, params, page)` in Bronze metadata
- On re-run, read checkpoint and resume from `page + 1`
- Tag files by ingestion date: `bronze/transferencias/year=2023/month=03/`

### Municipality Join
- Transferencias returns `codigoIbge` — use this as 7-digit IBGE code
- For Sanctions (CEIS/CNEP/CEPIM) — entity-level, not municipal; joined by `municipio` name (less reliable) or `cnpj`

## When to Apply

- Ingesting federal transfer data for treatment analysis
- Fetching sanction datasets for compliance outcome measurement
- Implementing paginated ingestion with rate-limit backoff
- Building checkpointed Bronze ingestion
- Validating API key is loaded from environment (never hardcoded)

## Security Considerations

- **API key is sensitive** — gitignore `.env`, commit only `.env.example`
- Log request URLs **without** the API key header
- Some endpoints return **PII** (CPF, CNPJ, addresses) — apply retention/masking per LGPD
- **LGPD Art. 26** — public administration data has legal basis but still requires proportionality

## Common Pitfalls

- **Rate limits change by time of day** — design for weekday limit even if running at night
- **"Sem registros" responses** — not always empty list; check for `{"message": "..."}` HTTP 200
- **`codigoIbge` may be null** — entity not localized; log and skip
- **Historical data gaps** — pre-2013 coverage sparse
- **Timezone**: all dates are Brasilia time (America/Sao_Paulo)

## Related

- `skills/ibge-datasets/` — Municipality master data (join key)
- `skills/data-pipeline/` — Bronze/Silver/Gold patterns
- `skills/security/` — Secrets handling, PII review
- `workflows/data-source-ingestion.md` — Ingestion workflow

## References

- [API Portal da Transparência](https://api.portaldatransparencia.gov.br/)
- [Swagger UI](https://api.portaldatransparencia.gov.br/swagger-ui.html)
- [LGPD Art. 26](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
