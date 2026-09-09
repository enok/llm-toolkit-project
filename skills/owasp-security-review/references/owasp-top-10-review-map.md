---
title: OWASP Top 10 review map
tags: [owasp, top-10, appsec, review, classification]
---

# OWASP Top 10 Review Map

Use this map to classify findings without forcing every issue into an OWASP label.

| Category | Review cues |
| --- | --- |
| A01 Broken Access Control | Missing object ownership checks, role bypass, IDOR, unsafe CORS, direct admin route access |
| A02 Cryptographic Failures | Weak TLS assumptions, plaintext secrets, weak key handling, sensitive data in logs or storage |
| A03 Injection | SQL/NoSQL/LDAP/OS/template injection, unsafe deserialization inputs, unparameterized dynamic queries |
| A04 Insecure Design | Missing abuse-case controls, unsafe workflows, authorization only at UI layer, missing rate limits for risky flows |
| A05 Security Misconfiguration | Debug endpoints, default credentials, permissive headers, verbose errors, unsafe deployment defaults |
| A06 Vulnerable Components | Vulnerable direct or transitive dependencies, stale runtimes, unpinned high-risk tooling |
| A07 Identification and Authentication Failures | Weak session lifecycle, password reset gaps, token replay, missing MFA for privileged actions |
| A08 Software and Data Integrity Failures | Unsigned updates, unsafe CI scripts, dependency confusion, untrusted generated artifacts |
| A09 Security Logging and Monitoring Failures | Missing audit events, unredacted sensitive logs, no alertable signal for critical failures |
| A10 Server-Side Request Forgery | User-controlled outbound URLs, metadata service access, weak allowlists, redirect-following fetchers |

Prefer the primary category that best explains the fix. Add secondary mappings only when they change remediation or priority.
