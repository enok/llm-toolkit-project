---
title: Cloud CLI PERMISSION_DENIED - triage the identity and role first, then send the admin a precise request
category: environment
created: 2026-11-26
tags: [gcloud, cloud-cli, permission-denied, adc, quota-project, iam, admin-request, triage]
---

# Problem
Cloud CLI commands failed with PERMISSION_DENIED or "cannot set quota project". The developer
did not know whether the account lacked a role, the local setup was wrong, or the wrong
identity was active, and the first reaction was to retry write operations (for example saving
a shared knowledge base or vector database to a cloud project) that could not succeed.

# Failed Approaches
- Retrying the same failing command or re-running login: it changes nothing when a role is
  missing.
- Asking an administrator for "access" without detail: the request cannot be acted on.
- Attempting writes to a shared store before knowing who may grant the permission.

# Solution
1. Record which identity is active: the application-default credentials and the CLI account can
   differ; list both.
2. Quote the exact missing role or permission from the error text.
3. Separate "needs an admin grant" (a role is named, the identity is right) from "local
   misconfiguration" (wrong account, wrong project, expired login).
4. Prove what already works with a read-only probe that avoids the quota project, for example
   an identity-token call to a health endpoint with a plain HTTP client.
5. Send the admin a copy-paste request with three items: principal, role, resource.
6. Before writing to a shared knowledge base or vector database, ask who grants write access
   and wait; do not attempt it speculatively.
Leave project ids, service names, emails and URLs out of notes that are shared; use
placeholders.

# Why
The error names the missing role, so the fix is a precise grant, not a retry. Separating the
causes avoids asking an administrator for something a local login fix would solve, and the
read-only probe shows which layer is already healthy. Related:
`terraform-sso-token-refresh-fails-when-cli-works.md`, `skills/environment-diagnose/SKILL.md`.
