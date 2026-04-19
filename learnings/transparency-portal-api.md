---
title: Portal da Transparência API — auth, endpoints, and pagination
category: api
created: 2026-04-19
tags: [transparency-portal, api, brazil, cgu, sanctions, ceis, cnep, cepim, transferencias, convenios]
---

# Problem

Knowing which endpoints to call, how to authenticate, and what parameters are required to avoid 401/403 errors when ingesting data from the Brazilian Portal da Transparência API.

# Failed Approaches

1. **Calling `/transferencias` without required query params** — returns 403 (not 400), which looks like an auth error but is actually a missing-parameter error.
2. **Assuming a confirmation email is required** — the API key is shown immediately on the portal page after registration; there is no email confirmation step.
3. **Diagnosing 403 as invalid key** — 401 = no key sent; 403 = key recognized but endpoint rejected the request (wrong params or wrong path).

# Solution

### Authentication
```bash
curl -H "chave-api-dados: <32-char-key>" \
  "https://api.portaldatransparencia.gov.br/api-de-dados/despesas/tipo-transferencia"
```
- Header name: `chave-api-dados`
- Key obtained at: https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email
- OpenAPI spec: `GET https://api.portaldatransparencia.gov.br/v3/api-docs`

### Smoke-test (no params required — good health check)
```
GET /api-de-dados/despesas/tipo-transferencia
→ [{"id":1,"descricao":"Constitucionais e Royalties"}, ...]
```

### Sanções (compliance outcome data — thesis treatment)
| Endpoint | Key params |
|---|---|
| `/api-de-dados/ceis` | `cnpjSancionado`, `nomeSancionado`, `dataInicialSancao`, `dataFinalSancao`, `pagina` |
| `/api-de-dados/cnep` | same as CEIS |
| `/api-de-dados/cepim` | `cnpjEntidade`, `codigoConvenio`, `pagina` |
| `/api-de-dados/ceaf` | `cpf`, `nome`, `pagina` |
| `/api-de-dados/acordos-leniencia` | `cnpjSancionado`, `situacao`, `dataInicialSancao`, `dataFinalSancao`, `pagina` |

### Transferências federais (treatment-side data)
| Endpoint | Key params |
|---|---|
| `/api-de-dados/transferencias` | `dataInicial` (DD/MM/AAAA), `dataFinal`, `codigoFavorecido`, `pagina` |
| `/api-de-dados/transferencias/resumo-por-uf` | `ano`, `uf` |

### Convênios
| Endpoint | Key params |
|---|---|
| `/api-de-dados/convenios` | `dataInicial`, `dataFinal`, `codigoOrgao`, `cnpjFavorecido`, `pagina` |

### Benefícios sociais por município
| Endpoint | Key params |
|---|---|
| `/api-de-dados/novo-bolsa-familia-por-municipio` | `mesAno` (AAAAMM), `codigoIbge`, `pagina` |
| `/api-de-dados/bpc-por-municipio` | `mesAno`, `codigoIbge`, `pagina` |
| `/api-de-dados/auxilio-brasil-por-municipio` | `mesAno`, `codigoIbge`, `pagina` |

### Pagination
All paginated endpoints use `pagina` (1-indexed). Loop until response array length < page size (typically 500).

### Date formats
- `DD/MM/AAAA` — date range filters (`dataInicial`, `dataFinal`, etc.)
- `AAAAMM` — month/year filters (`mesAno`)

### `transparency_client.py` key resolution order
1. AWS Secrets Manager: `mba-thesis/transparency-api-key-dev` → key `TRANSPARENCY_API_KEY`
2. Env var: `TRANSPARENCY_API_KEY`
3. `.env` file fallback

# Why

403 with an empty response body is the API's way of saying "required query parameters missing" — not an auth failure. The smoke-test endpoint (`/despesas/tipo-transferencia`) takes no parameters and is the fastest way to confirm a key is active.
