---
trigger: always_on
description: Parallel subagents, safe fanout, and when to serialize work
---

# Multi-Agent Orchestration

When `rules/request-orchestration.md` selects a multi-lane route, fan out without asking unless a user-visible tradeoff, risky side effect or overlapping write set needs a decision.

- Run in parallel only work with no dependency between lanes. A lane that consumes another lane's output (an interface, module, schema or generated file) runs in a later wave, after that output is validated; never alongside it.
- Give each file one writer. UI-driving lanes also follow `skills/assistant-workspace-cleanup/references/ui-automation-lane-safety.md`.
- Every dispatch carries its tier and sets the model parameter from the client map whenever the platform exposes one (Claude Code: `light` -> `haiku`, `standard` -> `sonnet`, `deep` -> `opus`); only a platform without one runs at its stated default.
- Every lane carries acceptance criteria, a validator and a loop budget per `workflows/task-quality-loop.md`; it is done when its validator returns `pass`, and escalated lanes return to the root with their verdict history.
- The root reconciles findings, decides, and runs final verification itself.
