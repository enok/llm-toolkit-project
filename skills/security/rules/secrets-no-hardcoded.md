---
title: Never Hardcode Secrets in Code or Config
impact: CRITICAL
impactDescription: Secrets in source code persist in git history forever and are trivially extractable
tags: security, secrets, credentials, environment-variables, vault
---

## Never Hardcode Secrets

Secrets in source code are visible in git history, CI logs, and to anyone with repo access — forever.

**Incorrect (secret in source code):**

```python
API_KEY = "EXAMPLE_API_KEY_DO_NOT_USE"
db_password = "EXAMPLE_PASSWORD_DO_NOT_USE"
```

**Correct (from environment or secret store):**

```python
API_KEY = os.environ["API_KEY"]

# Or from secret store
import boto3
client = boto3.client("secretsmanager")
secret = client.get_secret_value(SecretId="myapp/api-key")["SecretString"]
```

| Environment | Store |
|-------------|-------|
| Local dev | `.env` file (gitignored) or `direnv` |
| AWS | Secrets Manager, SSM Parameter Store |
| Kubernetes | Kubernetes Secrets (encrypted at rest) |
| CI/CD | GitHub Actions secrets, GitLab CI variables |

- Also never log secrets, tokens, or auth headers
- In notebooks, never print credentials or environment-specific values; output cells are committed artifacts
- Rotate secrets immediately if accidentally committed
