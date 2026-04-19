---
name: environment-diagnose
description: Diagnose local development environment issues across toolchains, auth, Docker, build caches, and project setup; split independent environment surfaces across subagents and synthesize the likeliest root cause. Use when setup, builds, or local services are failing.
---

# Environment Diagnose

Use this skill for local setup and workflow failures.

## When to use
- Builds or tests fail because the environment is misconfigured.
- Local services, containers, auth, or toolchains are broken.
- Repo onboarding or parity with CI needs troubleshooting.

## Parallel fanout
- Once the failing surface is classified, fan out the independent checks immediately by default.
- One subagent inspects build and dependency tooling.
- One subagent inspects Docker, services, and local runtime prerequisites.
- One subagent inspects auth and external integration readiness.
- Keep the final diagnosis and repair plan local.

## Outputs
- Likeliest root cause clusters.
- Concrete repair steps in the safest order.
- Follow-up checks to confirm the fix.
