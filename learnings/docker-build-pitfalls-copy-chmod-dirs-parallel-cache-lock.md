---
title: Docker build pitfalls - COPY --chmod hits directories, parallel builds share a cache lock, registry rate limits
category: build
created: 2026-11-26
tags: [docker, buildkit, copy-chmod, gradle, cache-lock, rate-limit, non-root, mirror]
---

# Problem
Container images built fine but failed only when run or when built in a pipeline:
1. The app failed with "must point to a readable file" under a non-root user.
2. Two `docker build` steps running in parallel timed out on a Gradle lock file.
3. Base-image pulls from a public registry hit rate limits.

# Failed Approaches
- Looking at the application config: the file was present, only its parent directory was not
  traversable.
- Re-running the pipeline: the parallel builds collide again.

# Solution
- `COPY --chmod=0444 src /etc/app/` also gives mode 0444 to directories BuildKit creates, so the
  non-root user cannot enter them. Use a plain `COPY`, or set directory modes in a separate
  step.
- Builds that run in parallel against one BuildKit cache mount share its Gradle lock. Serialize
  the second build behind the first, or give each its own cache.
- For public-registry rate limits, pass the base image through a build argument that points to a
  mirror.
- Read the failing step's log before re-running, and run the built image once before declaring
  the build done.

# Why
A file mode without the execute bit on a directory blocks traversal for every user except root,
and the shared cache directory is one lock domain, so both defects only show up at run time or
under parallelism. Related: `skills/maven-build-troubleshooting/SKILL.md`.
