---
trigger: always_on
description: Explicit deploy order, verification, and rollback planning for release work
---

# Release safety

Before proposing or executing a release:

1. Identify migrations, backwards-compatibility risks, and config or secrets changes.
2. Define the deploy order explicitly across repos and services.
3. Define verification **before** rollout begins.
4. Define rollback **before** production action begins.
5. If multiple repos or environments are involved, treat this as **release coordination**, not a single-repo change.
