---
title: GitHub Actions migration security
tags: [ci, github-actions, security, secrets, oidc, runners]
---

# GitHub Actions Migration Security

Use this when a Jenkins migration touches credentials, deploys, runners, fork PRs, or third-party actions.

## Credential Migration

- Inventory every Jenkins credential by consumer, scope, rotation owner, and runtime environment before creating GitHub secrets.
- Prefer GitHub environment secrets for deployment credentials that require human approval.
- Prefer OIDC or cloud workload federation over long-lived cloud keys when the cloud provider and organization policy allow it.
- Use deploy keys, service accounts, or fine-grained tokens instead of personal credentials.
- Grant the minimum scopes needed. Remove Jenkins-era broad admin tokens during the migration instead of moving them as-is.
- Never commit secret values, rendered credentials, `.npmrc` tokens, Maven settings with passwords, kubeconfigs, or cloud keys.

## Workflow Permissions

- Set explicit top-level `permissions:` and override per job only when needed.
- Keep `contents: read` for build/test jobs unless they actually write releases, packages, deployments, checks, or pull requests.
- Grant `id-token: write` only to jobs that request OIDC tokens.
- Avoid `pull_request_target` unless the workflow is specifically designed for untrusted code. Never check out or run fork code with write tokens or secrets.

## Third-Party Actions

- Prefer official actions or organization-approved actions.
- Pin third-party actions according to repository policy. For high-trust or deployment workflows, pin to a full commit SHA when practical.
- Review action source, permissions, and network behavior before introducing it into a secrets-bearing job.
- Do not pass secrets to actions that do not explicitly need them.

## Script Injection And Logs

- Treat PR titles, branch names, commit messages, issue text, and workflow inputs as untrusted.
- Pass untrusted expressions through environment variables or action inputs; avoid directly interpolating them into shell scripts.
- Mask generated sensitive values with `::add-mask::` before they can appear in logs.
- Review logs from both success and failure paths before declaring parity; failure output often leaks command lines or environment details.

## Runner Boundaries

- Use self-hosted runners only when required for private network access, licensed tools, large hardware, or persistent caches.
- Keep self-hosted runner groups scoped to the smallest repository or organization set that needs them.
- Do not run untrusted fork PR code on privileged self-hosted runners.
- Recreate Jenkins network assumptions explicitly: VPC access, proxy settings, DNS, certificate stores, Docker daemon access, and artifact repository allowlists.
