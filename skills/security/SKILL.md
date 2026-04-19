---
name: security
description: Application security best practices for any project handling user data. This skill should be used when writing, reviewing, or refactoring code that handles authentication, authorization, user input, secrets, or PII. Triggers on tasks involving injection prevention, auth checks, XSS/CSRF/SSRF, secrets management, dependency security, or security review.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Application Security Best Practices

Comprehensive security best practices that apply to any application handling user data. Contains 20+ rules across 7 categories, prioritized by impact.

## When to Apply

Reference these guidelines when:
- Writing endpoints that handle user input
- Implementing authentication or authorization
- Managing secrets, tokens, or credentials
- Reviewing code for security vulnerabilities
- Adding or updating dependencies
- Handling PII or sensitive data
- Evaluating trust boundaries in architecture

## Rule Categories by Priority

| Priority | Category | Impact | Prefix |
|----------|----------|--------|--------|
| 1 | Injection Prevention | CRITICAL | `injection-` |
| 2 | Authentication & Authorization | CRITICAL | `auth-` |
| 3 | Secrets Management | CRITICAL | `secrets-` |
| 4 | Web Security (XSS/CSRF/SSRF) | HIGH | `web-` |
| 5 | Data Privacy & PII | HIGH | `pii-` |
| 6 | Dependency Security | MEDIUM | `deps-` |
| 7 | Threat Modeling & Trust Boundaries | MEDIUM | `threat-` |

## Quick Reference

### 1. Injection Prevention (CRITICAL)

- `injection-sql` - Parameterized queries only. Never concatenate user input into SQL.
- `injection-command` - Never pass user input to shell commands. Use safe APIs.
- `injection-template` - Escape all user input in templates. No raw HTML insertion.
- `injection-deserialization` - Never deserialize untrusted data with APIs that can execute code.
- `injection-path-traversal` - Validate file paths. Block ../ and absolute paths.

### 2. Authentication & Authorization (CRITICAL)

- `auth-every-endpoint` - Every endpoint must have explicit authorization checks.
- `auth-server-side` - Never rely on client-side permission checks alone.
- `auth-least-privilege` - Default to deny. Grant minimum permissions required.
- `auth-established-patterns` - Use proven auth (JWT, OAuth, sessions). Never roll your own crypto.

### 3. Secrets Management (CRITICAL)

- `secrets-no-hardcoded` - Never embed secrets in code or config files.
- `secrets-no-logging` - Tokens and secrets must never appear in logs or URLs.
- `secrets-store` - Use a secret store (Vault, AWS Secrets Manager) or environment variables.

### 4. Web Security (HIGH)

- `web-xss` - Escape user-controlled data in HTML/JS. No innerHTML with user data.
- `web-csrf` - CSRF protection on state-changing operations.
- `web-ssrf` - Validate and constrain outbound URLs. No user-controlled targets to internal endpoints.
- `web-redirect` - Allowlist redirect URLs. No open redirects.

### 5. Data Privacy & PII (HIGH)

- `pii-no-logging` - Never log names, SSNs, addresses, DOBs, or identifiers.
- `pii-minimization` - Collect only what you need. Don't store PII unnecessarily.
- `pii-audit` - Audit logging required for all data modifications in sensitive domains.

### 6. Dependency Security (MEDIUM)

- `deps-check-advisories` - Check Snyk, Dependabot, npm audit when adding/updating dependencies.
- `deps-pin-versions` - Pin dependency versions in production.

### 7. Threat Modeling (MEDIUM)

- `threat-trust-boundaries` - Extra scrutiny where data crosses trust boundaries.
- `threat-sensitive-ops` - Deletes, bulk updates, role changes need checks and audit trails.

## Red Flags (always block merge)

- Clear injection vectors with user-controlled input
- Missing or bypassable authentication/authorization on sensitive paths
- Hardcoded secrets or credentials
- Unsafe deserialization of external data
- SSRF or open redirect with user-controlled target/URL

## How to Use

Read individual rule files for detailed explanations and code examples:

```
rules/injection-sql.md
rules/secrets-no-hardcoded.md
```

Each rule file contains:
- Brief explanation of why it matters
- Incorrect code example with explanation
- Correct code example with explanation
- Additional context and key rules

## Related Skills

This skill provides **cross-cutting security rules**. Pair it with technology-specific skills:

- **nodejs** — Node.js-specific hardening: helmet(), rate limiting, CORS allowlist, secure cookies, trust proxy
- **cloudformation** — AWS infrastructure security: least-privilege IAM, no hardcoded secrets in templates, encryption at rest
- **terraform** — IaC security scanning (trivy, checkov), state security, least-privilege
- **shell-scripting** — Script security: no eval, mktemp for temp files, input validation
- **java-best-practices** / **python-best-practices** / **js-ts-best-practices** — Language-specific error handling and input validation patterns
- **best-practices** — Defensive programming, fail-fast validation, immutability (foundations that security builds on)

## Full Compiled Document

For the complete guide with all rules expanded: `AGENTS.md`
