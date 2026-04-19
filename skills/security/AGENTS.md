# Application Security Best Practices

Comprehensive security best practices that apply to any application handling user data. Merged from rules/security.md and rubrics/security.md into a unified guide with detailed code examples.

## Injection Prevention

### SQL / NoSQL Injection

User or external input must never be concatenated into queries. Always use parameterized queries.

```java
// WRONG — string concatenation, trivially exploitable
String sql = "SELECT * FROM users WHERE name = '" + name + "'";
// Input: name = "'; DROP TABLE users; --"

// CORRECT — parameterized query
PreparedStatement stmt = conn.prepareStatement("SELECT * FROM users WHERE name = ?");
stmt.setString(1, name);
```

```python
# WRONG — f-string in query
cursor.execute(f"SELECT * FROM orders WHERE id = '{order_id}'")

# CORRECT — parameterized
cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
```

```typescript
// WRONG — template literal in SQL
const result = await db.query(`SELECT * FROM users WHERE email = '${email}'`);

// CORRECT — parameterized
const result = await db.query("SELECT * FROM users WHERE email = $1", [email]);
```

### Command Injection

Never pass user input to shell commands. Use safe APIs with argument arrays.

```python
# WRONG — shell=True with user input
import subprocess
subprocess.run(f"convert {user_filename} output.png", shell=True)  # rm -rf / via filename

# CORRECT — argument array, no shell
subprocess.run(["convert", user_filename, "output.png"], shell=False)
```

### Template Injection / XSS

```tsx
// WRONG — dangerouslySetInnerHTML with user data
<div dangerouslySetInnerHTML={{ __html: userComment }} />

// CORRECT — framework auto-escaping
<div>{userComment}</div>

// CORRECT — if raw HTML needed, sanitize first
import DOMPurify from "dompurify";
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userComment) }} />
```

### Path Traversal

```python
# WRONG — user controls the file path
file_path = f"/uploads/{user_provided_filename}"
with open(file_path) as f:  # ../../../etc/passwd

# CORRECT — resolve and verify within allowed directory
import os
base_dir = os.path.realpath("/uploads")
requested = os.path.realpath(os.path.join(base_dir, user_provided_filename))
if not requested.startswith(base_dir):
    raise SecurityError("Path traversal detected")
with open(requested) as f:
    ...
```

### Unsafe Deserialization

```java
// WRONG — deserializing untrusted data can execute arbitrary code
ObjectInputStream ois = new ObjectInputStream(untrustedStream);
Object obj = ois.readObject();  // can execute arbitrary code via crafted payload

// CORRECT — use safe formats (JSON) with schema validation
ObjectMapper mapper = new ObjectMapper();
OrderRequest request = mapper.readValue(jsonString, OrderRequest.class);
// Only known fields are deserialized into a typed object
```

## Authentication & Authorization

### Every Endpoint Needs Auth Checks

```java
// WRONG — no authorization check
@GetMapping("/admin/users")
List<User> listUsers() {
    return userRepository.findAll();  // anyone can access admin data
}

// CORRECT — explicit authorization
@GetMapping("/admin/users")
@PreAuthorize("hasRole('ADMIN')")
List<User> listUsers() {
    return userRepository.findAll();
}
```

### Server-Side Enforcement

```typescript
// WRONG — client-side only permission check
function AdminPanel() {
  const { isAdmin } = useAuth();
  if (!isAdmin) return null;  // can be bypassed by modifying JS
  return <UserManagement />;
}

// CORRECT — server-side enforcement (client-side is just UX)
// API endpoint enforces authorization regardless of client
app.get("/api/admin/users", requireRole("admin"), async (req, res) => {
  const users = await userService.listAll();
  res.json(users);
});

// Client-side hides UI for non-admins (UX only, not security)
function AdminPanel() {
  const { isAdmin } = useAuth();
  if (!isAdmin) return null;
  return <UserManagement />;
}
```

### Least Privilege — Default Deny

- Every new endpoint: deny by default, require explicit grant.
- Never bypass checks for admin users — admins get explicit admin permissions.
- Gate UI features on permissions, but always enforce server-side.
- Use established auth patterns (JWT, OAuth, sessions) — never roll your own crypto.

## Secrets Management

### Never Hardcode Secrets

```python
# WRONG — secret in source code
API_KEY = "EXAMPLE_API_KEY_DO_NOT_USE"  # visible in git history forever
db_password = "EXAMPLE_PASSWORD_DO_NOT_USE"

# CORRECT — from environment
API_KEY = os.environ["API_KEY"]

# CORRECT — from secret store
import boto3
client = boto3.client("secretsmanager")
secret = client.get_secret_value(SecretId="myapp/api-key")["SecretString"]
```

### Never Log Secrets or Tokens

```java
// WRONG — token in logs
log.info("Request headers: {}", request.getHeaders());  // includes Authorization header
log.debug("API response: {}", response.getBody());      // may contain tokens

// CORRECT — log only safe fields
log.info("Request: method={}, path={}, user={}", method, path, userId);
```

### Use Secret Stores

| Environment | Store |
|-------------|-------|
| Local dev | `.env` file (gitignored) or `direnv` |
| AWS | Secrets Manager, SSM Parameter Store |
| Kubernetes | Kubernetes Secrets (encrypted at rest) |
| CI/CD | GitHub Actions secrets, GitLab CI variables |
| Generic | HashiCorp Vault |

## Web Security

### Cross-Site Scripting (XSS)

- Use framework auto-escaping (React JSX, template engines with escaping).
- Don't use `dangerouslySetInnerHTML`, `v-html`, or raw HTML insertion without sanitization.
- Configure Content Security Policy (CSP) headers.
- Sanitize before rendering user-provided HTML (DOMPurify, bleach).

### Cross-Site Request Forgery (CSRF)

- Use CSRF tokens on all state-changing operations (POST, PUT, DELETE).
- Use `SameSite=Strict` or `SameSite=Lax` on cookies.
- Verify `Origin` or `Referer` headers on sensitive endpoints.

### Server-Side Request Forgery (SSRF)

```python
# WRONG — user controls the URL, can reach internal services
url = request.args.get("url")
response = requests.get(url)  # http://169.254.169.254/latest/meta-data/

# CORRECT — allowlist of allowed domains
ALLOWED_HOSTS = {"api.example.com", "cdn.example.com"}
parsed = urllib.parse.urlparse(url)
if parsed.hostname not in ALLOWED_HOSTS:
    raise SecurityError("URL not in allowlist")
response = requests.get(url)
```

### Open Redirects

```typescript
// WRONG — user-controlled redirect, can phish users
res.redirect(req.query.next);  // https://evil.com/login

// CORRECT — allowlist or relative-path only
const next = req.query.next as string;
if (!next.startsWith("/") || next.startsWith("//")) {
  return res.redirect("/");  // safe default
}
res.redirect(next);
```

## Data Privacy & PII

### No PII in Logs

```java
// WRONG — PII in logs
log.info("Processing person: name={}, ssn={}, dob={}", 
    person.getName(), person.getSsn(), person.getDob());

// CORRECT — log only IDs, never PII
log.info("Processing person: id={}", person.getId());
```

- Treat all user data as sensitive by default.
- PII includes: names, SSNs, addresses, DOBs, emails, phone numbers, IPs (in some jurisdictions).
- Audit logging required for all data modifications in sensitive domains.
- Comply with relevant standards (CJIS, HIPAA, SOC2, GDPR) as applicable.

### Data Minimization

- Collect only what you need for the current feature.
- Don't store PII unnecessarily "just in case."
- Implement retention policies — delete data when no longer needed.
- Encrypt sensitive fields at rest.

## Dependency Security

- Check advisories (Snyk, Dependabot, `npm audit`, `pip audit`) when adding/updating dependencies.
- Pin dependency versions in production — use lock files (`package-lock.json`, `poetry.lock`).
- Review new transitive dependencies — they expand your attack surface.
- Run automated dependency scanning in CI.

## Threat Modeling

### Trust Boundaries

Consider where data crosses trust boundaries — these transitions deserve extra scrutiny:

| Boundary | Risks |
|----------|-------|
| **User → Application** | Injection, XSS, CSRF, input validation |
| **Application → Database** | SQL injection, excessive permissions |
| **Application → External Service** | SSRF, data leakage, credential exposure |
| **Service → Service** | AuthN/AuthZ bypass, token leakage |
| **Application → Logs/Monitoring** | PII exposure, secret leakage |

### Sensitive Operations Checklist

Deletes, bulk updates, role changes, and access to sensitive resources should have:
- [ ] Explicit authorization check
- [ ] Audit trail (who did what, when)
- [ ] Confirmation step for destructive actions
- [ ] Rate limiting to prevent abuse

## PR Security Checklist

Before approving any PR, verify:

- [ ] No hardcoded secrets, credentials, or API keys
- [ ] All user-controlled inputs validated before use
- [ ] Parameterized queries / SDK builders used (no string concatenation)
- [ ] Error messages don't leak stack traces or infrastructure details
- [ ] Log messages contain no PII, tokens, or credentials
- [ ] New dependencies checked for CVEs
- [ ] Exception handlers don't swallow errors silently
- [ ] Redirect URLs validated against allowlist (if applicable)

## Red Flags (always block merge)

- Clear injection vectors with user-controlled input
- Missing or bypassable authentication/authorization on sensitive paths
- Hardcoded secrets or credentials
- Unsafe deserialization of external data
- SSRF or open redirect with user-controlled target/URL

## Related Skills

This skill provides **cross-cutting security rules**. Pair it with technology-specific skills:

- **nodejs** — Node.js-specific hardening: helmet(), rate limiting, CORS allowlist, secure cookies, trust proxy
- **cloudformation** — AWS infrastructure security: least-privilege IAM, no hardcoded secrets in templates, encryption at rest
- **terraform** — IaC security scanning (trivy, checkov), state encryption, least-privilege
- **shell-scripting** — Script security: no eval, mktemp for temp files, input validation, no secrets in scripts
- **java-best-practices** / **python-best-practices** / **js-ts-best-practices** — Language-specific error handling and input validation patterns
- **best-practices** — Defensive programming, fail-fast validation, immutability (foundations that security builds on)
