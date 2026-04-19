---
trigger: always_on
description: Security principles — PII, injection prevention, auth, secrets
---

# Security Rules

Security principles that apply to any application handling user data.

## Data Sensitivity

- Treat all user data as sensitive by default.
- **PII must never be logged** — no names, SSNs, addresses, DOBs, or identifiers in log output.
- Audit logging required for all data modifications in sensitive domains.
- Comply with relevant standards (e.g., CJIS, HIPAA, SOC2, GDPR) as applicable to the project.

## Permission Checks — Always Required

- Every new endpoint or API must have explicit authorization checks.
- Never bypass permission checks — not even for admin users.
- Default to deny / least-privilege.
- Gate UI features on permissions — don't just hide elements; enforce server-side.

## Authentication

- Use established auth patterns (session-based, JWT, OAuth) — never roll your own crypto.
- Enforce session timeouts for inactivity.
- Use CSRF protection on state-changing operations.
- API tokens for service-to-service communication.

## Data Protection

- Encrypt sensitive fields at rest.
- Use prepared statements / parameterized queries — **never** string-concatenated SQL.
- Sanitize all user inputs before display.
- **Never** store credentials in code or configuration files.
- Use a secret store (e.g., AWS Secrets Manager, Vault) or environment variables for secrets.

## No-Log PII Rule

```python
# WRONG — PII in logs
logger.info("Processing user: id=%s name=%s ssn=%s", user_id, name, ssn)

# CORRECT — log only opaque/internal IDs
logger.info("Processing user: id=%s", user_id)
```

Internal IDs (UUIDs, auto-increment PKs) are acceptable in logs. Never log names, emails, SSNs, phone numbers, addresses, or raw user-submitted data.

## Input Validation

```python
# WRONG — using raw user input without validation
user_id = request.get("user_id")
amount = request.get("amount")  # passed directly to business logic

# CORRECT — validate type and range before use
try:
    user_id = int(request["user_id"])
    amount = float(request["amount"])
    if amount <= 0:
        raise ValueError("amount must be positive")
except (KeyError, ValueError, TypeError) as e:
    raise ValidationError(f"Invalid input: {e}")
```

- Data from external sources (user input, webhooks, message queues) = **untrusted**. Always validate.
- Data from server-side config (env vars, admin-managed settings) = **trusted config** — but still validate format.

## NoSQL Injection Prevention

```python
# CORRECT — use SDK methods (parameterized by design)
table.put_item(Item={"user_id": user_id, "status": status})

# WRONG — never build query expressions via string concatenation
expr = f"user_id = {user_id}"  # injection risk
```

Most NoSQL SDKs (boto3/DynamoDB, MongoDB drivers) are parameterized by design. Never build filter expressions or queries via string concatenation with user-supplied values.

## Dependency Security

- New or updated dependencies may introduce known vulnerabilities.
- Check advisories (Snyk, Dependabot, npm audit, OWASP) when adding dependencies.
- Pin dependency versions in production.

## Fail Securely

- On validation error, raise/throw — do not persist partial or invalid data.
- On external service error, classify and re-raise — never silently swallow and return success.
- Error messages returned to clients should be generic — log detailed errors internally.

## PR Security Checklist

Before approving any PR, verify:

- [ ] No hardcoded secrets, credentials, or API keys
- [ ] All user-controlled inputs validated before use
- [ ] Parameterized queries / SDK builders used (no string concatenation for queries/JSON)
- [ ] Error messages don't leak stack traces or infrastructure details
- [ ] Log messages contain no PII, tokens, or credentials
- [ ] New dependencies checked for CVEs
- [ ] Exception handlers don't swallow errors silently
- [ ] Redirect URLs validated against allowlist (if applicable)

## Red Flags (always block merge)

- Clear injection vectors with user-controlled input.
- Missing or bypassable authentication/authorization on sensitive paths.
- Hardcoded secrets or credentials.
- Unsafe deserialization of external data.
- SSRF or open redirect with user-controlled target/URL.
