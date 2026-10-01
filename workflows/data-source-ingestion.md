---
description: Add, modify, or troubleshoot bronze-layer ingestion from public data sources (statistical agencies, public-data APIs, registries, price indexes) with storage-mode selection
---

# Data Source Ingestion Workflow

Use this workflow when adding, modifying, or troubleshooting data ingestion from the project's core sources (for example a statistical agency, a public-data API, a registry, or a price-index series).

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
export S3_BUCKET=<your-bucket>
export S3_PREFIX=bronze/

# Local only (development/offline)
export STORAGE_MODE=local-only
export LOCAL_DATA_DIR=/home/user/project-data

# Both (backup/redundancy)
export STORAGE_MODE=both
export S3_BUCKET=<your-bucket>
export LOCAL_DATA_DIR=/home/user/project-data-backup
```

**Option 2: Config File**
```json
// config/storage_config.json
{
  "storage_mode": "local-only",
  "s3": {
    "bucket": "<your-bucket>",
    "prefix": "bronze/",
    "region": "us-east-1"
  },
  "local": {
    "base_dir": "/home/user/project-data",
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
export S3_BUCKET=<your-bucket>

# Run ingestion
./scripts/01_bronze_ingestion.sh

# Data lands in: s3://$S3_BUCKET/bronze/{source}/
```

#### Both Mode (Hybrid)
```bash
# Configure
export STORAGE_MODE=both
export LOCAL_DATA_DIR=/home/user/project-data
export S3_BUCKET=<your-bucket>

# Run ingestion (writes to both)
./scripts/01_bronze_ingestion.sh

# Data lands in both locations simultaneously
```

## Data Sources Overview

| Source | Type | Update Frequency | Contract File | Client Code |
|--------|------|------------------|---------------|-------------|
| Census / survey | Static snapshots | Per release | `config/<census>_metadata.json` | `src/ingestion/<census>_client.py` |
| Public Data API | Monthly | Historical complete | `config/<api>_metadata.json` | `src/ingestion/<api>_client.py` |
| Registry | As updated | Periodic | `config/<registry>_metadata.json` | `src/ingestion/<registry>_client.py` |
| Price index | Monthly | Monthly | `config/<index>_metadata.json` | `src/ingestion/<index>_client.py` |

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
config/<source>_metadata.json      # One contract per source
config/silver_schemas.json         # Silver layer expectations
```

Verify:
- Expected columns match source documentation
- Data types are appropriate
- Temporal coverage is documented
- Primary keys are identified

### 3. Trace the Ingestion Path

**For a census / survey source:**
1. `src/ingestion/<census>_client.py` — HTTP client
2. `scripts/01_bronze_ingestion.sh` — Orchestration
3. `src/processing/silver_transformer.py` — Normalization

**For a public-data API:**
1. `src/ingestion/<api>_client.py` — API client with pagination
2. `scripts/01_bronze_ingestion.sh` — Orchestration
3. `src/processing/silver_transformer.py` — Normalization

**For a price-index series:**
1. `src/ingestion/<index>_client.py` — Series API client
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

### Census / survey sources

- Use the official geographic code as the join key
- Different census years can have different variable availability
- Handle missing values explicitly (not every unit has every indicator)
- Real (inflation-adjusted) values are computed in the Gold layer

### Public-data APIs

- APIs have rate limits; the client implements backoff
- When historical data is complete, still keep data freshness checks in place
- Geographic codes may need left-padding to their fixed width
- Document coded fields (categories, action codes) in the metadata contract

### Registries

- Dates matter: registry entries have start and end dates
- Boolean flags should be time-aware (active at reference date)

### Price-index series

- Monthly series for inflation adjustment
- Base date matters (state the reference currency and year)
- Used for real-value calculations in the Gold layer
- Validate against the official published values

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
