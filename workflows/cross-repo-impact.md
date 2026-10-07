---
description: Map downstream impact of a shared change across sibling or related repositories
---

# Cross-repo impact workflow

Use when a change may affect multiple repositories, shared packages, or downstream consumers.

## Steps

1. Identify the shared surface: package, contract, generated artifact, workflow, docs, or infrastructure module.
2. Inventory candidate consumer repos from local clones, documentation, and remotes (as available).
3. Once the inventory is known, split **read-only** discovery immediately by default (by repo family or subsystem).
4. Do not pause before internal fanout unless there is a user-visible tradeoff or risky external side effect.
5. Build an impact map: affected repos, files, commands, and validation needed.
6. Only after the map is coherent, decide whether edits should span multiple repos or be deferred as follow-up work.

See `rules/api-contract-surface.md` and `rules/multi-agent-orchestration.md`.

## Known pitfalls

- Before trusting a zero-match search over a local clone, fetch and compare against `origin/main`; when the clone is behind, search the remote ref (`git grep -in "<pattern>" origin/main`). See `learnings/stale-local-clone-false-negative-search.md`.

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
