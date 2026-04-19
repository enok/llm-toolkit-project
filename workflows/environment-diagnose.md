---
description: Diagnose local environment, auth, dependency, and container issues safely
---

# Environment diagnose workflow

Use for local setup failures, broken builds, missing auth, or service boot issues.

## Steps

1. Classify the failure surface: toolchain, auth, containers or local services, dependency install, build cache, or repo-specific setup.
2. Gather concrete evidence first: command output, config presence, running services, and expected versions.
3. Once the failure surface is known, split independent environment checks **immediately by default**.
4. Do not pause before internal fanout unless there is a user-visible tradeoff or risky external side effect.
5. Cluster likely causes and test the lowest-risk fixes first.
6. Re-run the failing workflow and confirm the environment is healthy before stopping.

See `rules/multi-agent-orchestration.md`.
