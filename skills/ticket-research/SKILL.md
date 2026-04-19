---
name: ticket-research
description: Research a ticket across local code, local docs, and available Jira, Confluence, and GitHub context; split evidence gathering across subagents and synthesize a grounded implementation brief. Use when starting work on a ticket or when requirements are unclear.
---

# Ticket Research

Use this skill to gather task context deeply before implementation.

## When to use
- The user asks to research a ticket before coding.
- Requirements, acceptance criteria, or linked context are unclear.
- The task may span multiple repos or shared packages.

## Context order
1. Prefer Jira, Confluence, GitHub PRs/issues, and linked docs when authenticated and available.
2. Fall back to local ticket artifacts (for example `docs/tickets/`, other committed task-artifact directories, READMEs, architecture docs, branch names, commit messages) when private systems are unavailable.
3. Always ground conclusions in actual code and repository structure.

## Parallel fanout
- Once the ticket and repo scope are known, fan out the independent discovery lanes immediately by default.
- One subagent for ticket and doc context.
- One subagent for codebase pattern discovery.
- One subagent for cross-repo impact when shared packages or APIs are involved.
- Keep synthesis local so the final brief is coherent and de-duplicated.
- Only pause before posting questions or updates to external systems, not before internal research fanout.

## Merge Applicable Guidance
- Do not treat overlapping skills or instruction sources as mutually exclusive.
- Merge applicable requirements from system/developer instructions, repo guides (`AGENTS.md`, `CLAUDE.md`, nearest subdirectory `CLAUDE.md`), this skill, and any other clearly relevant skill.
- When two sources overlap, use the most complete non-conflicting workflow and preserve stricter requirements for artifacts, diagrams, verification, documentation, and follow-up outputs.

## Outputs
- Task summary and likely acceptance criteria.
- Concrete files or modules likely to change.
- Risks, unknowns, and follow-up questions.
- Suggested implementation order and test plan.

## Committed Artifacts
- When the repo or active instructions expect committed ticket research artifacts, the work is not complete until they are written to the repo's ticket-artifact convention.
- Shared default when no repo convention is known: `docs/tickets/<TICKET>/`.
- If repo instructions or existing committed artifacts use another convention, follow that convention instead.
- Always create the directory if it does not exist.
- Always write these two files when a ticket key is known:
  - `<ARTIFACT_ROOT>/README.md` — the main research brief with task summary, acceptance criteria, likely code areas, risks, implementation order, and test plan.
  - `<ARTIFACT_ROOT>/diagrams.md` — one or more Mermaid diagrams that make the research easier to review quickly. Prefer at least a current-state flow and, when there is a concrete hypothesis, a failure-path or proposed-fix flow.
- Infer `<TICKET>` from the user request, branch name, or Jira context. If no ticket key exists, write to the repo's research fallback path, such as `docs/tickets/research/` or the repo's equivalent.
- If writing under the committed ticket-artifact path is blocked by sandboxing or path permissions, retry with the minimum required escalation instead of silently skipping the artifacts.
- The final response should link to the committed artifacts and summarize the highest-signal findings.
