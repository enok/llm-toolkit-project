---
title: Externalize Notebook Runtime Configuration
impact: HIGH
impactDescription: notebooks commit output cells, so environment values and credentials can leak through code or printed outputs
tags: python, jupyter, notebook, configuration, credentials, aws, security
---

## Load runtime values from env or local config

Do not hardcode AWS profile names, bucket names, tokens, or environment-specific values in notebooks. Load them from environment variables first, then from a gitignored local config file.

```python
import json
import os

config_path = os.path.join("..", "config", "runtime_config.json")
config = {}
if os.path.exists(config_path):
    with open(config_path, encoding="utf-8") as handle:
        config = json.load(handle)

S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", config.get("aws", {}).get("s3_bucket_name", ""))
AWS_PROFILE = os.environ.get("AWS_PROFILE", config.get("aws", {}).get("profile"))
```

Never print secret or environment values for debugging; notebook outputs are commonly committed.
