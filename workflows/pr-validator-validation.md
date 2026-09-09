---
description: Run the PR Validator specialist for live-head PR/ticket readiness, human comments, CI, docs, and approve/block reporting
---

# PR Validator Validation

Use this workflow when a GitHub PR, ticket-bound branch, or recurring PR
automation needs an evidence-backed approve-ready, blocked, or monitor call.

## Phase 1 - Live Scope

1. Establish repo, PR, ticket key, base/head, live head SHA, local checkout
   freshness, dirty-tree ownership, and allowed actions.
2. Load only relevant context: `workflows/ticket-pr-validation-loop.md`,
   `workflows/gh-address-comments.md`, `workflows/gh-fix-ci.md`,
   `rules/human-comment-reply-gate.md`, CI/test logs, PR body, ticket data, and
   linked docs.
3. Stop before edits, pushes, comments, or approvals if freshness, permissions,
   or ownership are unclear.

## Phase 2 - Specialist Pass

1. Invoke or follow `tool-subagents/pr-validator.md`.
2. Provide ticket requirements, PR metadata, full diff, reviews/comments,
   checks, docs, Confluence/diagram evidence, local validation output, and
   prior automated replies.
3. Ask for requirement trace, findings, CI/test gaps, comment handling,
   draft-only replies, decision, and related-specialist handoffs.

## Phase 3 - Reduce And Act

1. Accept only evidence-backed, in-scope findings tied to the live head.
2. Prefer code/test/doc/PR-body fixes over explanatory replies.
3. Do not post, submit, resolve, delete, or send human-facing replies without
   showing the exact draft and receiving explicit approval.
4. Use language, documentation, Confluence, diagram, architecture, security,
   test, CI, or log specialists only when their evidence lane is relevant.

## Phase 4 - Validate

Run the narrowest relevant checks:

- local tests/builds or reports tied to changed risk;
- the changed-code quality gate (`workflows/changed-code-quality-gate.md`) when
  source code changed;
- `git diff --check`;
- `gh pr checks` or equivalent CI evidence;
- docs/index/render/security gates for toolkit or documentation changes.

## Phase 5 - Evolve

If the specialist misses stale-head risk, weak ticket mapping, PR-thread nuance,
CI handoff, claim drift, or token-heavy evidence loading, run
`workflows/pr-validator-evolution.md`.
