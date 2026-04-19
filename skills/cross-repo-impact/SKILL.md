---
name: cross-repo-impact
description: Analyze how a shared package, contract, workflow, or infrastructure change affects sibling repos and clones; split repo scanning across subagents and synthesize the impact into a concrete action map. Use when a change may affect more than one repository.
---

# Cross-Repo Impact

Use this skill when changes cross repository boundaries.

## When to use
- The task touches shared packages, contracts, docs, workflows, or infra.
- A monorepo split means consumers may live in other repos.
- You need to identify follow-up work across sibling repos or clone families.

## Parallel fanout
- Once the shared surface is identified, split read-only discovery immediately by default.
- Split inventory by repo family or subsystem.
- Keep one local aggregator that merges findings into a single impact map.
- Prefer read-only parallel discovery before any multi-repo edits.

## Outputs
- Affected repos and why they are affected.
- Likely file or module hotspots per repo.
- Suggested execution order and validation strategy.
