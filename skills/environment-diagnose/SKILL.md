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

## Known pitfalls

- Treat HTTP 403 on package registries, GitHub web, release downloads, video sites, or Medium from a cloud sandbox as the sandbox's network policy, not a code defect: run best-effort checks there, report them as partial, and run the definitive build and tests on the user's machine. (sig: env-constraint/sandbox-egress-blocks-registries)
- Before saying a local repo or file is unreachable from chat, check the session's connected tools, including a desktop file plugin.
- Do not run `gh pr create` in the cloud container: it failed there with GraphQL blocked and the repository not attached; run `gh` for PR work on the user's machine. See `learnings/gh-graphql-blocked-in-cloud-sandbox.md`. (sig: env-constraint/gh-graphql-blocked-in-cloud-sandbox)
- When `git checkout` on Windows fails with "cannot rmdir ...: Permission denied", check the ReadOnly directory attribute before blaming symlinks or process handles (both were ruled out in the recorded case): remove junctions as links only (no `/s`), clear ReadOnly on the affected directories, then mark link surfaces with `git update-index --skip-worktree`.
- Before reading missing or empty content as a broken clone, check the branch: `git status`, `git log --oneline --graph --all -15`, and `git rev-list --count HEAD..origin/main`; a nonzero behind count means a lagging checkout, not missing content.
- Running or scanning commands through Desktop Commander on a Windows machine has quoting and output pitfalls (PowerShell versus cmd, truncated output, long-running scans). Use the recorded run-and-scan patterns instead of improvising. See `learnings/desktop-commander-powershell-run-and-scan-patterns.md`.
- When a site is "unreachable", separate three causes before changing anything: the sandbox's network policy, the device bridge, and a browser-side filter. Test from each path and report which one blocked. See `learnings/site-unreachable-diagnosis-bridge-and-chrome-filter.md`.
- A cloud CLI that fails with PERMISSION_DENIED or "cannot set quota project": capture which identity is active, name the exact missing role from the error, prove what already works with a read-only probe, and hand the admin a copy-paste request (principal, role, resource) instead of retrying.
- Before blaming a component for a crash, check that the test copies are not derived from the damaged artifact: build fresh from empty, inside and outside the suspect location, changing one variable at a time. (sig: wrong-assumption/cause-inferred-from-contaminated-copy)
