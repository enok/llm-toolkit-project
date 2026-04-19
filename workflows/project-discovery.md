---
description: Understand a repository, its architecture, and how to work in it
---

# Project discovery workflow

Use when the user asks to understand a repo, get onboarded, map architecture, or document how to work in the codebase. Prefer the **project-discovery** skill when appropriate.

## Steps

1. Identify the destination repo, its stack, and key entry docs or build files.
2. Once scope is known, split independent discovery lanes **immediately by default**:
   - repository structure and entrypoints
   - architecture and request or data flows
   - local run, test, and dependency setup
3. Do not pause before internal fanout unless there is a user-visible tradeoff or risky external side effect.
4. Synthesize a concise overview: key paths, related services or repos, and recommended doc updates.
5. When asked, propose or apply committed docs (for example `README.md`, `docs/architecture.md`).

See `rules/multi-agent-orchestration.md`.
