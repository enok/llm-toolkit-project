# LLM Toolkit -- Global Orchestration Directive

The shared LLM toolkit lives at `{{TOOLKIT_ROOT}}`. Its skills, subagents,
rules, and workflows are installed at the user level and are the default
for every session on this machine, in every project.

## At session start

Read `{{TOOLKIT_ROOT}}/AGENTS.md` before doing anything else.

## Route every non-trivial prompt

Process every non-trivial prompt through:

1. `{{TOOLKIT_ROOT}}/rules/request-orchestration.md`
2. `{{TOOLKIT_ROOT}}/tool-subagents/agent-orchestrator.md`

Together they require you to:

- Classify the request (trivial/local vs. multi-lane) before acting.
- For multi-lane work, produce a wave-ordered task table (agent, task,
  tier, model, validator, status) before any task runs.
- Give every task a complexity tier AND an explicit model -- never left to
  inherit the session default: `light` -> the cheapest capable model,
  `standard` -> the mid-tier model, `deep` -> the strongest model
  available (e.g. Claude Code: haiku / sonnet / opus).
- Run every delegated task as a bounded produce -> validate -> refine
  loop, max 5 iterations, escalating to the root agent instead of
  silently accepting a failed result.
- Keep a durable state ledger in the project root: `TASKS_TABLE.md` (the
  task table) and `CONTEXT_STATE.md` (decided facts, blockers, resume
  point).
- Let the root agent -- not a delegated task -- own file writes, commits,
  pushes, and replies to the human.

Use `{{TOOLKIT_ROOT}}/INTENTS.md` to route each ask to its primary skill,
workflow, or rule before fanning out to specialists.

## Layering with repo-local instructions

Skills and subagents are installed once at the user level and apply
across every repository. A repository's own `AGENTS.md` / `CLAUDE.md`
layers on top of this directive per
`{{TOOLKIT_ROOT}}/rules/repository-context-layers.md`: repo-local
instructions are first-class for that repository and are never
overridden by this global directive.

## Trivial exceptions

One-line answers, single-file edits or lookups, and other genuinely trivial
requests stay inline -- no task table, no delegation.
