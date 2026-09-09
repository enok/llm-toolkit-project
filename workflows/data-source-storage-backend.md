---
description: Add or change a storage backend (local, S3, or hybrid) for the bronze ingestion layer, including the backend module, client updates, CLI options, and usage examples
---

# Data Source Storage Backend Implementation

Companion to `workflows/data-source-ingestion.md`. Run this when an ingestion change needs a new or modified storage backend rather than a new source. Return to the parent workflow for testing, downstream validation, and documentation.

## Implementation: Adding Storage Backend Support

To implement the storage mode selection in code:

### 1. Create Storage Backend Module

```python
# src/ingestion/storage_backend.py
import os
from typing import Optional, List
import boto3
from pathlib import Path

class StorageBackend:
    """Abstracts S3 and local filesystem storage."""
    
    def __init__(self, mode: str = None):
        self.mode = mode or os.getenv('STORAGE_MODE', 's3-only')
        self.local_dir = os.getenv('LOCAL_DATA_DIR', './data')
        self.s3_bucket = os.getenv('S3_BUCKET', 'enok-mba-thesis-datalake')
        self.s3_prefix = os.getenv('S3_PREFIX', 'bronze/')
        
        if self.mode == 's3-only':
            self.s3_client = boto3.client('s3')
    
    def write(self, path: str, data: bytes, metadata: dict = None) -> bool:
        """Write data to configured storage(s)."""
        success = True
        
        if self.mode in ('local-only', 'both'):
            local_path = Path(self.local_dir) / path
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(data)
            if metadata:
                (local_path.parent / '.metadata.json').write_text(
                    json.dumps(metadata)
                )
        
        if self.mode in ('s3-only', 'both'):
            s3_key = f"{self.s3_prefix}{path}"
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=data,
                Metadata=metadata or {}
            )
        
        return success
    
    def read(self, path: str) -> bytes:
        """Read data from storage (local preferred if both)."""
        if self.mode in ('local-only', 'both'):
            local_path = Path(self.local_dir) / path
            if local_path.exists():
                return local_path.read_bytes()
        
        if self.mode in ('s3-only', 'both'):
            s3_key = f"{self.s3_prefix}{path}"
            response = self.s3_client.get_object(
                Bucket=self.s3_bucket,
                Key=s3_key
            )
            return response['Body'].read()
        
        raise FileNotFoundError(f"Path not found: {path}")
    
    def exists(self, path: str) -> bool:
        """Check if path exists in storage."""
        if self.mode in ('local-only', 'both'):
            if (Path(self.local_dir) / path).exists():
                return True
        
        if self.mode in ('s3-only', 'both'):
            try:
                s3_key = f"{self.s3_prefix}{path}"
                self.s3_client.head_object(
                    Bucket=self.s3_bucket,
                    Key=s3_key
                )
                return True
            except:
                return False
        
        return False
```

### 2. Update Ingestion Clients

```python
# src/ingestion/ibge_client.py (example)
from .storage_backend import StorageBackend

class IBGEClient:
    def __init__(self, storage_mode: str = None):
        self.storage = StorageBackend(storage_mode)
    
    def fetch_and_store(self, indicator: str, year: int) -> str:
        # Fetch data from API
        data = self._fetch_from_api(indicator, year)
        
        # Store using configured backend
        path = f"ibge/{indicator}_{year}.csv"
        self.storage.write(path, data.encode(), metadata={
            'source': 'IBGE',
            'indicator': indicator,
            'year': str(year),
            'ingested_at': datetime.now().isoformat()
        })
        
        return path
```

### 3. CLI Options for Shell Script

Update `scripts/01_bronze_ingestion.sh`:

```bash
#!/bin/bash

# Parse storage mode from args or env
STORAGE_MODE=${STORAGE_MODE:-s3-only}
LOCAL_DATA_DIR=${LOCAL_DATA_DIR:-./data}
S3_BUCKET=${S3_BUCKET:-enok-mba-thesis-datalake}

# Command line options
for arg in "$@"; do
    case $arg in
        --local-only) STORAGE_MODE=local-only ;;
        --s3-only) STORAGE_MODE=s3-only ;;
        --both) STORAGE_MODE=both ;;
        --local-dir=*) LOCAL_DATA_DIR="${arg#*=}" ;;
        --s3-bucket=*) S3_BUCKET="${arg#*=}" ;;
    esac
done

# Export for Python clients
export STORAGE_MODE
export LOCAL_DATA_DIR
export S3_BUCKET

# Run ingestion
python -m src.ingestion.ibge_client
python -m src.ingestion.transparency_client
# ... etc
```

### 4. Usage Examples

```bash
# Full flexibility via CLI
./scripts/01_bronze_ingestion.sh --local-only --local-dir=/mnt/data
./scripts/01_bronze_ingestion.sh --s3-only --s3-bucket=my-bucket
./scripts/01_bronze_ingestion.sh --both --local-dir=/mnt/data --s3-bucket=my-bucket

# Or via environment
export STORAGE_MODE=local-only
export LOCAL_DATA_DIR=/home/user/tcc-data
./scripts/01_bronze_ingestion.sh

# In Python code
from src.ingestion.storage_backend import StorageBackend

# Explicit mode
storage = StorageBackend(mode='local-only')  # or 's3-only', 'both'
storage.write('bronze/ibge/data.csv', b'...')

# From environment
storage = StorageBackend()  # reads STORAGE_MODE env var
```

## CLI Reference

### 01_bronze_ingestion.sh

| Option | Description | Default |
|--------|-------------|---------|
| `--local-only` | Store data only in local filesystem | Disabled |
| `--s3-only` | Store data only in S3 | **Enabled** |
| `--both` | Store data in both local and S3 | Disabled |
| `--local-dir=PATH` | Local storage directory | `$LOCAL_DATA_DIR` or `./data` |
| `--s3-bucket=NAME` | S3 bucket name | `$S3_BUCKET` or `enok-mba-thesis-datalake` |
| `--only-ibge` | Ingest only IBGE data | All sources |
| `--only-inflation` | Ingest only inflation data | All sources |
| `--only-transparency` | Ingest only Transparency data | All sources |
| `--skip-ibge` | Skip IBGE ingestion | - |
| `--skip-inflation` | Skip inflation ingestion | - |
| `--skip-transparency` | Skip Transparency ingestion | - |

### Environment Variables

| Variable | Description | Required For |
|----------|-------------|------------|
| `STORAGE_MODE` | `local-only`, `s3-only`, or `both` | All modes |
| `LOCAL_DATA_DIR` | Base directory for local storage | `local-only`, `both` |
| `S3_BUCKET` | S3 bucket name | `s3-only`, `both` |
| `S3_PREFIX` | Prefix for S3 keys (e.g., `bronze/`) | `s3-only`, `both` |
| `AWS_PROFILE` | AWS credentials profile | `s3-only`, `both` |
| `AWS_REGION` | AWS region | `s3-only`, `both` |

