---
description: Add, modify, or troubleshoot bronze-layer ingestion from public data sources (IBGE, Transparency Portal, CGU sanctions, BCB IPCA) with storage-mode selection
---

# Data Source Ingestion Workflow

Use this workflow when adding, modifying, or troubleshooting data ingestion from the project's core sources: IBGE, Transparency Portal, CGU sanctions, or BCB IPCA.

## Storage Backend Configuration

This ingestion pipeline supports **three storage modes**:

| Mode | S3 | Local Filesystem | Use Case |
|------|-----|------------------|----------|
| `s3-only` | ✅ | ❌ | Production, cloud-native, team sharing |
| `local-only` | ❌ | ✅ | Development, offline work, no AWS access |
| `both` | ✅ | ✅ | Backup strategy, hybrid workflows, migration |

### Configuration

Set storage mode via environment variable or config file:

**Option 1: Environment Variable (Recommended)**
```bash
# S3 only (default production)
export STORAGE_MODE=s3-only
export S3_BUCKET=enok-mba-thesis-datalake
export S3_PREFIX=bronze/

# Local only (development/offline)
export STORAGE_MODE=local-only
export LOCAL_DATA_DIR=/home/user/tcc-data

# Both (backup/redundancy)
export STORAGE_MODE=both
export S3_BUCKET=enok-mba-thesis-datalake
export LOCAL_DATA_DIR=/home/user/tcc-data-backup
```

**Option 2: Config File**
```json
// config/storage_config.json
{
  "storage_mode": "local-only",
  "s3": {
    "bucket": "enok-mba-thesis-datalake",
    "prefix": "bronze/",
    "region": "us-east-1"
  },
  "local": {
    "base_dir": "/home/user/tcc-data",
    "create_dirs": true
  },
  "sync": {
    "on_write": false,
    "on_read": false
  }
}
```

### Quick Start by Mode

#### Local-Only Mode
```bash
# Configure
export STORAGE_MODE=local-only
export LOCAL_DATA_DIR=/path/to/local/data

# Run ingestion (no AWS credentials needed)
./scripts/01_bronze_ingestion.sh --local-only

# Data lands in: $LOCAL_DATA_DIR/bronze/{source}/
```

#### S3-Only Mode (Original)
```bash
# Configure
export STORAGE_MODE=s3-only
export AWS_PROFILE=your-profile
export S3_BUCKET=enok-mba-thesis-datalake

# Run ingestion
./scripts/01_bronze_ingestion.sh

# Data lands in: s3://$S3_BUCKET/bronze/{source}/
```

#### Both Mode (Hybrid)
```bash
# Configure
export STORAGE_MODE=both
export LOCAL_DATA_DIR=/home/user/tcc-data
export S3_BUCKET=enok-mba-thesis-datalake

# Run ingestion (writes to both)
./scripts/01_bronze_ingestion.sh

# Data lands in both locations simultaneously
```

## Data Sources Overview

| Source | Type | Update Frequency | Contract File | Client Code |
|--------|------|------------------|---------------|-------------|
| IBGE Census | Static (2010, 2022) | Decadal | `config/ibge_metadata.json` | `src/ingestion/ibge_client.py` |
| Transparency Portal | Monthly (2010-2022) | Historical complete | `config/transparency_metadata.json` | `src/ingestion/transparency_client.py` |
| CGU Sanctions (CEIS, CNEP, CEPIM) | As updated | Periodic | `config/transparency_metadata.json` | `src/ingestion/transparency_client.py` |
| BCB IPCA | Monthly | Monthly | `config/ipca_metadata.json` | `src/ingestion/bcb_client.py` |

## When to Use

- Adding a new data source
- Modifying ingestion logic
- Handling API changes or rate limits
- Troubleshooting failed ingestion
- Adding new variables from existing sources
- Backfilling historical data

## Repository-Specific Steps

### 1. Identify the Data Source and Layer

What are you ingesting and at what medallion layer?

**Bronze Layer (Raw)**
- Preserve source fidelity
- Minimal transformation
- Audit trail of ingestion

**Silver Layer (Normalized)**
- Schema alignment
- Type normalization
- Join key standardization

**Gold Layer (Aggregated)**
- Analysis-ready features
- Municipality-year grain
- Derived metrics

### 2. Check the Contract

Before modifying ingestion:

```bash
# Read the relevant metadata
config/ibge_metadata.json          # IBGE census indicators
config/transparency_metadata.json  # Federal transfers and sanctions
config/ipca_metadata.json          # Inflation series
config/silver_schemas.json         # Silver layer expectations
```

Verify:
- Expected columns match source documentation
- Data types are appropriate
- Temporal coverage is documented
- Primary keys are identified

### 3. Trace the Ingestion Path

**For IBGE:**
1. `src/ingestion/ibge_client.py` — HTTP client
2. `scripts/01_bronze_ingestion.sh` — Orchestration
3. `src/processing/silver_transformer.py` — Normalization

**For Transparency Portal:**
1. `src/ingestion/transparency_client.py` — API client with pagination
2. `scripts/01_bronze_ingestion.sh` — Orchestration
3. `src/processing/silver_transformer.py` — Normalization

**For BCB IPCA:**
1. `src/ingestion/bcb_client.py` — BCB API client
2. `scripts/01_bronze_ingestion.sh` — Orchestration
3. `src/processing/gold_transformer.py` — CPI adjustment

### 4. Implement Changes

**If adding a new variable from existing source:**
1. Update the contract (`config/*.json`)
2. Modify the client to fetch new field
3. Update Silver transformation if normalization needed
4. Update Gold transformation if derived metric needed
5. Update loaders in `src/analysis/`

**If adding a new data source:**
1. Create new client in `src/ingestion/`
2. Add contract in `config/`
3. Add orchestration step in `scripts/01_bronze_ingestion.sh`
4. Create Silver normalization in `src/processing/`
5. Add tests in `tests/`

### 5. Test Ingestion

**Test by Storage Mode:**

```bash
# Local-only mode (no AWS needed)
export STORAGE_MODE=local-only
export LOCAL_DATA_DIR=/tmp/test-data
./scripts/01_bronze_ingestion.sh --source <source_name>

# S3-only mode (requires AWS credentials)
export STORAGE_MODE=s3-only
export S3_BUCKET=test-bucket
./scripts/01_bronze_ingestion.sh --source <source_name>

# Both modes (hybrid)
export STORAGE_MODE=both
export LOCAL_DATA_DIR=/tmp/test-data
export S3_BUCKET=test-bucket
./scripts/01_bronze_ingestion.sh --source <source_name>

# Or run unit tests
pytest tests/ingestion/test_<source>_client.py -v
pytest tests/ingestion/test_storage_backends.py -v  # New: test local/S3/both
```

**Check by Mode:**

| Check | Local | S3 | Both |
|-------|-------|-----|------|
| Data lands in correct path | `ls $LOCAL_DATA_DIR/bronze/` | `aws s3 ls s3://$BUCKET/bronze/` | Both locations |
| Schema matches contract | `head -5 local/file.csv` | `aws s3 cp s3://.../file.csv - \| head -5` | Compare both |
| No data loss | `wc -l local/file.csv` | `aws s3 cp ... \| wc -l` | Compare counts |
| Metadata checkpoint | `cat local/.metadata.json` | `aws s3 cp s3://.../.metadata.json -` | Both updated |
| Error handling | Test without write permissions | Test with invalid bucket | Verify both fail gracefully |

**Quick Verification:**
```bash
# For local-only
find $LOCAL_DATA_DIR/bronze -name "*.csv" -o -name "*.parquet" | head -10

# For S3
aws s3 ls s3://$S3_BUCKET/bronze/ --recursive | head -10

# For both - verify sync
diff <(find $LOCAL_DATA_DIR/bronze -type f | sort) \
     <(aws s3 ls s3://$S3_BUCKET/bronze/ --recursive | awk '{print $4}' | sort)
```

### 6. Validate Downstream Impact

Changes to ingestion may affect:
- Silver transformations (`src/processing/silver_transformer.py`)
- Gold features (`src/processing/gold_transformer.py`)
- Analysis notebooks (loaders may need updates)
- Tests (may need new fixtures)

Run Silver transformation:
```bash
./scripts/02_silver_transformation.sh
```

Verify no regressions:
```bash
pytest tests/processing/ -v
```

### 7. Document Changes

Update:
- `docs/01_BRONZE_LAYER.md` — If ingestion changes
- `docs/02_SILVER_LAYER.md` — If normalization changes
- `docs/03_GOLD_LAYER.md` — If derived features change
- `README.md` — If new data sources added
- `README.pt-BR.md` — Portuguese counterpart

## Source-Specific Guidance

### IBGE Census

- Municipality codes (`codigo_municipio`) are the join key
- 2010 and 2022 have different variable availability
- Handle missing values explicitly (not all municipalities have all indicators)
- Real income requires IPCA adjustment (handled in Gold layer)

### Transparency Portal

- API has rate limits; client implements backoff
- Historical data (2010-2022) is complete; no new fetches needed for thesis
- Municipality codes may need left-padding to 7 digits
- Action codes indicate transfer type (documented in metadata)

### CGU Sanctions

- CEIS: Ineligible companies
- CNEP: National registry of punished companies
- CEPIM: Ineligible municipalities
- Dates matter: sanctions have start and end dates
- Boolean flags should be time-aware (active at reference date)

### BCB IPCA

- Monthly series for inflation adjustment
- Base date matters (thesis uses 2022 BRL as reference)
- Used for real income calculations in Gold layer
- Validate against official BCB published values

## Error Handling Checklist

- [ ] API failures: retry with exponential backoff
- [ ] Partial data: log and continue, don't silently skip
- [ ] Schema drift: fail loudly if source adds/removes columns
- [ ] Missing data: distinguish "no data" from "zero"
- [ ] Date parsing: validate all dates parse correctly
- [ ] Municipality linkage: verify join keys exist in both datasets
- [ ] Storage failures: handle both local and S3 errors gracefully
- [ ] Disk space: verify local storage has sufficient space before ingestion
## Storage Backend Implementation

When the change adds or modifies a storage backend (local, S3, hybrid) instead of a data source, run the **data-source-storage-backend** workflow (`workflows/data-source-storage-backend.md`) in full. It covers the backend module, ingestion-client updates, CLI options, usage examples, and the `01_bronze_ingestion.sh` / environment-variable reference.

## Related Workflows

- `workflows/data-pipeline-change.md` — For pipeline-wide changes
- `pipeline-change.md` — For this repo's specific pipeline
- `workflows/dataset-onboarding.md` — For brand new datasets
