# Data Science Project Overview (Template)

> **This is a template.** Copy it and replace the placeholders with your project details.

## Project

**Name:** [project name]  
**Objective:** [research question, product goal, or analytical decision]  
**Primary Stakeholders:** [team, business owner, advisor, or consumers]

## Data Scope

- **Primary data sources:** [APIs, files, warehouses, public datasets]
- **Refresh cadence:** [batch, daily, event-driven, one-time snapshot]
- **Storage layers:** [raw, bronze, silver, gold, feature store, marts]
- **Governance notes:** [privacy, licensing, public-sector, regulated-domain notes]

## Tech Stack

| Area | Technology |
|------|------------|
| Language | [Python, R, SQL, Scala, etc.] |
| Storage | [S3, warehouse, lakehouse, local files] |
| Orchestration | [Airflow, Dagster, cron, scripts] |
| Analysis | [pandas, notebooks, BI, stats packages] |
| ML | [scikit-learn, XGBoost, PyTorch, managed ML platforms, etc.] |
| Infra | [Terraform, Docker, cloud services] |
| Testing | [pytest, Great Expectations, dbt tests, custom validators] |

## Repository Layout

```text
project/
|-- config/        # metadata, schemas, feature definitions, env templates
|-- src/           # ingestion, transforms, analysis, reusable utilities
|-- notebooks/     # EDA, stats, model exploration
|-- scripts/       # operational entrypoints and validation commands
|-- tests/         # unit, integration, data validation, notebook tests
|-- docs/          # architecture, runbooks, findings, bilingual docs
|-- infra/         # cloud and infrastructure as code
```

## Data Contracts

- **Authoritative metadata files:** [list the files or folders]
- **Schema definitions:** [list the files or folders]
- **Translation or glossary maps:** [if applicable]
- **Evidence artifacts:** [logs, validation reports, audit files]

## Working Conventions

- Keep technical LLM config in English.
- Treat schemas, keys, and storage paths as contracts.
- Keep notebooks reproducible and extract reusable logic into code.
- Update localized docs in the same change when they are meant to stay aligned.

## Core Commands

```bash
[environment setup command]
[run tests command]
[run pipeline command]
[run notebook or analysis command]
```
