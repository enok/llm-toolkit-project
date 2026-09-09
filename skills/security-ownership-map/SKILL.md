---
name: "security-ownership-map"
description: "Analyze git repositories to build a security ownership topology (people-to-file), compute bus factor and sensitive-code ownership, and export CSV/JSON for graph databases and visualization. Trigger only when the user explicitly wants a security-oriented ownership or bus-factor analysis grounded in git history (for example: orphaned sensitive code, security maintainers, CODEOWNERS reality checks for risk, sensitive hotspots, or ownership clusters). Do not trigger for general maintainer lists or non-security ownership questions."
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Security Ownership Map

## Overview

Build a bipartite graph of people and files from git history, then compute ownership risk and export graph artifacts. Also build a file co-change graph (Jaccard similarity on shared commits) to cluster files by how they move together while ignoring large, noisy commits.

## Requirements

- Python 3
- `networkx` (required; community detection is enabled by default)

## Workflow

1. Scope the repo and time window (optional `--since/--until`).
2. Decide sensitivity rules (use defaults or provide a CSV config).
3. Build the ownership map (co-change graph is on by default).
4. Communities are computed by default.
5. Query the outputs for bounded JSON slices.
6. Persist and visualize if needed.

By default, the co-change graph ignores common "glue" files (lockfiles, `.github/*`, editor config) so clusters reflect actual code movement instead of shared infra edits. Dependabot commits are excluded by default.

## Sensitivity Rules

By default, the analysis flags common auth/crypto/secret paths. Override by providing a CSV config file:

```
# pattern,tag,weight
**/auth/**,auth,1.0
**/crypto/**,crypto,1.0
**/*.pem,secrets,1.0
```

## Output Artifacts

The output directory contains:

- `people.csv` (nodes: people)
- `files.csv` (nodes: files)
- `edges.csv` (edges: touches)
- `cochange_edges.csv` (file-to-file co-change edges with Jaccard weight)
- `summary.json` (security ownership findings)
- `commits.jsonl` (optional, if `--emit-commits`)
- `communities.json` (computed from co-change edges; includes `maintainers` per community)

`people.csv` includes timezone detection based on author commit offsets: `primary_tz_offset`, `primary_tz_minutes`, and `timezone_offsets`.

## Basic Security Queries

Run these to answer common security ownership questions:

- **Orphaned sensitive code** (stale + low bus factor)
- **Hidden owners** for sensitive tags
- **Sensitive hotspots** with low bus factor
- **Auth/crypto files** with bus factor <= 1
- **Who is touching sensitive code** the most
- **Co-change neighbors** (cluster hints for ownership drift)
- **Community maintainers** for a cluster

### Summary Format

```json
{
  "orphaned_sensitive_code": [
    {
      "path": "crypto/tls/handshake.rs",
      "last_security_touch": "2023-03-12T18:10:04+00:00",
      "bus_factor": 1
    }
  ],
  "hidden_owners": [
    {
      "person": "alice@corp",
      "controls": "63% of auth code"
    }
  ]
}
```

## Notes

- `bus_factor_hotspots` in `summary.json` lists sensitive files with low bus factor; `orphaned_sensitive_code` is the stale subset.
- If `git log` is too large, narrow with `--since` or `--until`.
- Compare `summary.json` against CODEOWNERS to highlight ownership drift.

## Related Skills

- **security** — general application security principles
- **security-threat-model** — architectural threat modeling
- **owasp-security-review** — codebase findings report
