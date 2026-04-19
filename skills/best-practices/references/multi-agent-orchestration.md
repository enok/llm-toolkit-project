---
trigger: always_on
description: Parallel subagents, safe fanout, and when to serialize work
---

# Multi-Agent Orchestration

When a selected workflow has independent lanes, use parallel agents (Cursor subagents, Task tool, or IDE fanout) by default. Do not pause to ask for permission first unless there is a user-visible tradeoff, risky external side effect, or overlapping write ownership that needs a decision.

## Default fanout

- Launch the maximum safe parallel slices once scope is known.
- Keep the immediate blocking step local so the critical path keeps moving.
- Split only independent work: different subsystems, different files, different evidence sources.
- Do not assign overlapping write ownership to more than one agent.
- Use specialized agents for sidecar analysis, test mapping, docs drift, risk review, and other bounded tasks.
- Merge findings locally before implementing broad fixes.

## Typical parallel slices

- Ticket and doc context
- Diff or risk review
- Test coverage and validation planning
- Docs drift and release-note impact
- Cross-repo or downstream consumer impact
- CI failure log inspection and local repro mapping

## When to pause instead of fan out

- The user must choose between non-obvious product or design options
- A command or change has risky external side effects
- The write set cannot be split cleanly

## Finish locally

- Reconcile duplicate findings.
- Make the final implementation decisions.
- Run final verification locally.
- Summarize what changed, what was verified, and what remains risky.

## Workflows that should fan out when lanes are independent

When the active workflow has separate read-only or non-overlapping write lanes, parallelize by default (see each workflow’s steps): **review**, **ticket-review-and-fix**, **pre-pr-check**, **project-discovery**, **run-tests**, **ticket-research**, **gh-fix-ci**, **gh-address-comments**, **environment-diagnose**, **security-report**, **update-docs**, **cross-repo-impact**, **dependency-upgrade**, and **document-creation** (when phases are independent). **Enable Max Mode** (or equivalent) in the IDE so subagents using `model: inherit` run at full capability.

## Tool mapping

- **Cursor**: project subagents live in `.cursor/agents/` (see `.cursor/README.md`). Prefer `/agent-name` or natural-language delegation; combine with rules in `.cursor/rules/`.
- **Claude / Codex**: use `.claude/agents/` for shared agent files. Keep `AGENTS.md` as the primary repo-level surface, and expose shared skills through the thin `.codex/skills` compatibility symlink when needed.
- **Windsurf / generic**: follow the same principles using the IDE’s task or multi-chat capabilities.
