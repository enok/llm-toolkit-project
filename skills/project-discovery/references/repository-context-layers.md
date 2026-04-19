---
trigger: always_on
description: How to merge toolkit rules with repo-local AGENTS.md, CLAUDE.md, and thin provider compatibility surfaces
---

# Repository context layers

When multiple instruction sources apply (toolkit rules, workflows, repo `AGENTS.md`, optional `CLAUDE.md`, IDE rules):

1. **Merge in memory** during the turn: follow the most complete, **non-conflicting** workflow.
2. Keep the **union** of non-conflicting requirements; where they conflict, **stricter** verification, security, and documentation requirements win unless the user explicitly overrides.
3. **Repo-local** files (`AGENTS.md`, committed `docs/*`, local `skills/` playbooks) are **first-class** for that repository. Do not overwrite them when refreshing shared toolkit symlinks.
4. **Shared toolkit** content (`rules/`, `workflows/`, `skills/`) is the default for generic behavior across projects.
5. Provider skill directories should be thin compatibility symlinks back to the shared catalog, not separate authored copies.
