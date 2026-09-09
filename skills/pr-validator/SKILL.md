---
name: pr-validator
description: Read-only PR validator specialist for Jira-bound or GitHub PR readiness, live head freshness, full diff review, human review threads, CI checks, docs, Confluence, diagrams, test evidence, claim drift, draft-only replies, and approve-ready/blocked/monitor reporting. Use whenever validating a PR, a solved ticket, reviewer comments, a CI outcome, or a recurring PR automation cycle.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.0.0"
---

# PR Validator

Route PR and ticket readiness work through the read-only PR Validator
specialist so that every approve-ready, blocked, or monitor call is tied to the
live PR head and backed by evidence rather than by stale review state or a
previous green check.

## When to Use

- "validate this PR", "is PR #123 ready", "approve or block this PR"
- A solved ticket (`ABC-123`) needs its PR checked before review or merge
- Reviewer comments, bot findings, or CI results need evidence-based triage
- A recurring PR automation cycle needs a current, defensible decision

## Workflow

1. Load `workflows/pr-validator-validation.md`.
2. Invoke or follow `tool-subagents/pr-validator.md` as a read-only specialist.
3. Keep root-agent ownership for edits, local validation, commits, pushes, PR
   actions, Jira/GitHub/Confluence writes, and user-facing communication.
4. Apply `rules/human-comment-reply-gate.md` before any human-facing reply:
   exact drafts only (`Posting status: NOT POSTED`) until the user approves the
   exact text and target.
5. Compose with `workflows/ticket-pr-validation-loop.md`,
   `workflows/gh-address-comments.md`, `workflows/gh-fix-ci.md`, and the
   `java-change-validator`, `documentation-reviewer`,
   `confluence-documentation-specialist`, `diagram-creation-specialist`,
   `system-architecture-specialist`, CI, test, security, and log specialists
   only when their evidence lanes are relevant.
6. If the specialist misses a reusable pattern, run
   `workflows/pr-validator-evolution.md`.

## Required Context

- Repo, PR number/URL, ticket key, base/head refs, live head SHA, and whether
  the local checkout matches the PR head.
- Ticket requirements and acceptance criteria, PR body, full diff against the
  base branch, review threads, CI checks, test reports, and linked docs or
  diagrams.
- The user's policy for commenting, resolving, pushing, approving, or only
  reporting.

## Expected Output

A requirement trace table, evidence-backed findings with exact implementer
actions, CI/test gaps, a full-thread comment audit with draft-only replies,
claim drift across code/tests/docs/PR body/ticket, one decision
(approve-ready, blocked, or monitor) tied to the live head SHA,
related-specialist handoffs, and a learning/token-efficiency note.
