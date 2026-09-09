---
title: Java DTO and shared-library PR review
tags: [java, dto, library, api-contract, jackson, compatibility, pr-review]
---

# Java DTO and Library PR Review

Use this reference when reviewing Java DTOs, shared libraries, generated API
models, or request/response contract packages.

## Contract Surfaces

- Compare public constructors, setters, fluent methods, fields, Jackson
  annotations, equality/hashCode behavior, nullability, and validation against
  the base branch.
- Treat Java source/binary compatibility separately from JSON compatibility.
  Direct Java callers can break even when wire payloads are intentionally
  stricter.
- Match artifact versioning to compatibility. Patch and minor releases should
  preserve deprecated shims unless downstream compile validation and reviewer
  approval explicitly accept the break.
- Make JSON policy explicit with tests for missing required fields, malformed
  values, accepted or rejected legacy payloads, and unknown root properties.
- Align numeric documentation with implementation. If the code parses Java
  `long`, document and test the `Long.MAX_VALUE` boundary; if arbitrary digits
  are allowed, avoid `Long.parseLong`.
- Cross-check consumers with `rules/api-contract-surface.md` and the
  **cross-repo-impact** skill when the artifact is consumed by other repos.

## Review Hygiene

- Keep app-repo diffs free of shared LLM/tooling surfaces when the project has
  moved that configuration to the shared toolkit. Check `.github/copilot-*`,
  `.agents`, `.codex`, `.cursor`, `.windsurf`, `.claude`, `AGENTS.md`,
  `CLAUDE.md`, `docs/llm`, and local sync scripts.
- Keep PR descriptions synchronized with the actual branch diff: current head
  SHA, validation command and version, changed-file table, review-comment
  resolution table, and latest validation evidence.
- For path-heavy PR tables, wrap only display paths with spaced slash
  separators, not machine-readable paths.
- If commits are regrouped after review, prove the final tree hash matches the
  reviewed tree when the rewrite is intended to be history-only.
- For Java 8 projects on Windows, set `JAVA_HOME`, prepend its `bin`, and use a
  Java 8 Maven run when possible. If old coverage tooling cannot run on the
  available JDK, state any coverage-skip fallback explicitly.
- For logging review requests, scan for logger use before changing code. Do not
  add logging churn just to satisfy a requested commit category.
