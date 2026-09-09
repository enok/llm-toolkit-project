---
name: local-env-bootstrap
description: >
    Bootstrap or repair a local development environment across one or more repos. Trigger
    when the user asks to set up a project locally, fix onboarding/setup issues, align
    runtime versions, configure secrets/bootstrap steps, or make sibling repos run together.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Local Environment Bootstrap

Use this skill for onboarding, setup repair, and environment alignment.

## When to Apply

- Setting up a project locally for the first time
- Fixing broken local development environment
- Aligning language runtimes, tools, or Docker versions
- Configuring secrets, registries, or auth for local development
- Making multiple sibling repos work together locally

## Workflow

1. **Inventory runtime requirements:**
   - language runtimes and version managers (nvm, pyenv, sdkman, etc.)
   - Docker or container runtime
   - package registries and auth (npm, pip, Maven, Artifactory)
   - secrets/bootstrap tools (vault, env files, config generators)
   - databases, queues, and local services
2. **Identify whether the setup is single-repo or multi-repo.**
3. **Build the minimum viable startup path first:**
   - install dependencies
   - run migrations
   - start backend
   - start frontend
   - smoke test or health check
4. **Capture the most failure-prone branches:**
   - version mismatch (Node, Python, Java, etc.)
   - container startup failure
   - registry auth failure
   - bad local config or env vars
   - stale generated artifacts or caches
5. **Prefer a shortest-good-path bootstrap** over a huge all-at-once setup doc.
6. **Reuse the toolkit bootstrap where it fits.** `scripts/bootstrap-dev.sh` (PowerShell:
   `scripts/bootstrap-dev.ps1`) installs and verifies the shared developer toolchain;
   keep repo-specific steps in the consumer repo instead of forking the shared script.
7. **Document the result** as a README section or local setup guide.

## Output

Return:
- required tools and versions
- ordered setup steps (copy-pastable commands)
- smoke checks to verify the setup works
- troubleshooting branches for common failures

## Non-Goals

- Do not install system-level dependencies without user approval.
- Do not modify global configurations without warning.
- Do not skip verification — a setup isn't done until the smoke check passes.

## Related Skills

- **runbook-authoring** — Formalize the setup as a reusable runbook
- **onboarding** — Broader project onboarding; local-env-bootstrap focuses on the environment
- **shell-scripting** — Setup scripts follow shell best practices
- **llm-toolchain-provisioning** — Installing and verifying the LLM/agent toolchain on a new machine
- **environment-diagnose** — Diagnosing an environment that used to work
