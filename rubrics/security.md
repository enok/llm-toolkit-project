# Security Rubric

Evaluate security posture during code review. Use together with `rules/security.md`. Every item marked Blocker must be fixed before merge.

---

## Injection

| Signal | Severity |
|--------|----------|
| User-controlled input concatenated into SQL / NoSQL query | Blocker |
| User-controlled input concatenated into shell command | Blocker |
| User-controlled input used in file path without sanitization | Blocker |
| User-controlled input rendered as HTML without escaping (XSS) | Blocker |
| Parameterized queries / SDK builders used correctly | — (pass) |

## Authentication & Authorization

| Signal | Severity |
|--------|----------|
| New endpoint/action with no authorization check | Blocker |
| Authorization check bypassable (e.g., client-supplied role) | Blocker |
| Missing ownership check (user can read/write other users' data) | Blocker |
| Admin-only path reachable without role verification | Blocker |
| Session not invalidated on logout or password change | Blocker |
| CSRF protection missing on state-changing form/endpoint | Blocker |

## Secrets & Credentials

| Signal | Severity |
|--------|----------|
| Hardcoded API key, password, or token in source code | Blocker |
| Secret committed to `.env`, config file tracked by git | Blocker |
| Secret logged (even at DEBUG level) | Blocker |
| Secret passed as CLI argument (visible in `ps` output) | Blocker |
| Secrets loaded from env vars or secret store | — (pass) |

## Cryptography

| Signal | Severity |
|--------|----------|
| Weak or broken algorithm (MD5, SHA-1 for integrity, DES, RC4) | Blocker |
| Custom / homebrew crypto implementation | Blocker |
| Hardcoded IV or salt | Blocker |
| Random used for security purposes without `secrets` / `os.urandom` | Blocker |

## PII & Data Exposure

| Signal | Severity |
|--------|----------|
| PII in log messages (name, email, SSN, phone, address) | Blocker |
| PII in error responses returned to client | Blocker |
| PII stored without encryption at rest where required | Blocker |
| Stack trace or internal path leaked in HTTP error response | Blocker |
| Raw exception message returned to client | Suggestion |

## Web Security (HTTP APIs)

| Signal | Severity |
|--------|----------|
| SSRF: user-controlled URL fetched server-side without allowlist | Blocker |
| Open redirect with user-controlled destination | Blocker |
| Missing `Content-Security-Policy` / `X-Frame-Options` on new pages | Suggestion |
| File upload without MIME-type and size validation | Blocker |
| Insecure deserialization of untrusted data | Blocker |

## Dependencies

| Signal | Severity |
|--------|----------|
| New dependency with known critical CVE | Blocker |
| Dependency version unpinned in production lock file | Suggestion |
| Transitive dependency pulled from untrusted registry | Blocker |

## Error Handling & Observability

| Signal | Severity |
|--------|----------|
| Exception swallowed silently (empty `except` / `catch`) | Blocker |
| Security-sensitive operation not audit-logged | Suggestion |
| Failed auth/authz attempt not logged | Suggestion |

---

## Threat Model Shortcuts

When reviewing a new endpoint or service boundary, quickly check:

1. **Who can call it?** — authenticated + authorized?
2. **What inputs flow in?** — validated, typed, bounded?
3. **What secrets does it touch?** — injected, not hardcoded?
4. **What does it return?** — no PII, no stack traces?
5. **What does it write?** — idempotent, audit-logged?

Any "no" without justification = Blocker.
