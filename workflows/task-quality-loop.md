---
description: Reusable per-task produce-validate-refine loop with a hard iteration budget, validator selection map, and tier escalation
---

# Task Quality Loop

Reusable per-task produce->validate->refine loop for orchestrated delegation. `agent-orchestrator` applies this loop to every delegated task; other workflows may call it by path for any bounded task that has verifiable acceptance criteria.

Hard limit: **max 5 iterations per task.** Never loop indefinitely and never silently accept a failed result.

## Inputs (per task)

- Task objective and scope (from the orchestrator's task table row).
- Acceptance criteria: verifiable, written before the first iteration. Each criterion is mandatory or advisory. At least one criterion must be checkable by evidence (command output, file content, rendered artifact), not by opinion.
  - **Ticket-driven work:** when the task comes from a ticket (Jira or similar), the ticket's acceptance criteria are the mandatory criteria — the loop passes only when every AC is demonstrably met. If the ticket is a subtask, also check the result stays aligned with the parent ticket's goal and does not contradict sibling subtasks; misalignment is a mandatory-criterion failure.
  - **Unclear goal gate:** if the goal or ACs cannot be turned into verifiable criteria (ambiguous wording, missing AC section, conflicting parent/subtask goals), do not start the loop. Ask the user for clarification first — burning iterations against a guessed goal wastes the budget and validates the wrong thing.
- Producer agent + complexity tier (`light`/`standard`/`deep`).
- Validator assignment (see selection map below).
- Loop budget: default 5; deterministic `light` tasks (single command, mechanical edit, exact lookup) get budget 1 — one production pass plus one validation pass, no refinement loop.

## Validator selection map

Match the validator to the task's evidence type; use `task-quality-judge` when no domain specialist fits:

| Task output type | Validator |
| --- | --- |
| Code change / diff | `code-reviewer` (+ `test-runner` when tests exist) |
| Test selection / build evidence | `test-runner` |
| Documentation, runbooks, generated LLM surfaces | `documentation-reviewer` |
| Java changes | `java-change-validator` |
| Security-sensitive work | `security-auditor` or `owasp-security-auditor` |
| Diagrams / exported images | `diagram-creation-specialist` |
| PR / ticket readiness | `pr-validator` |
| Airflow/Glue/ETL | `dag-glue-specialist` |
| Architecture claims | `system-architecture-specialist` |
| Log/evidence reduction | `log-analyst` |
| Alarm RCA / hypotheses | `aws-alarm-investigator` |
| Completion claims, mixed or generic output | `task-quality-judge` or `verifier` |

Rules:

- The validator must be a different agent invocation than the producer. A producer never self-validates.
- Validators are read-only: they return verdicts and defect lists, never edits.
- Run the validator at the minimum sufficient tier (usually `light` or `standard`); the validator tier never needs to match the producer tier. Validator dispatches follow the same mandatory model selection as producer dispatches: set the delegation tool's model parameter from the client model map in `tool-subagents/agent-orchestrator.md` on every call where the platform exposes one.

## Loop procedure

For iteration `i` in 1..budget:

1. **Produce.** The producer executes the task at its assigned tier. On iterations after the first, the producer receives only: the original task, the acceptance criteria, and the previous verdict's defect list. Refinement is targeted — fix listed defects; do not restart from scratch or expand scope.
2. **Validate.** The validator checks every acceptance criterion with evidence and returns the structured verdict (`pass` | `fail` | `escalate`, criteria checklist, numbered defects each classed `mechanical` or `reasoning`, regressions vs previous iteration, loop recommendation).
3. **Decide.**
   - `pass` -> task done. Record iterations used in the task table.
   - `fail` and `i < budget` -> feed the defect list to the producer and continue.
   - `fail` and `i = budget` -> stop; mark the task `escalated` and hand the last output + full verdict history to the root agent.
   - `escalate` (any iteration) -> stop immediately; the task is mis-scoped, criteria are contradictory, or the same reasoning defect survived two consecutive iterations.

## Tier escalation inside the loop

- After 2 consecutive `fail` verdicts whose blocking defects are classed `reasoning`, escalate the producer one tier (`light` -> `standard` -> `deep`) for the next iteration and say so in the task table.
- `mechanical` defects never escalate tier; they indicate instructions, not capability, were the gap.
- Raising effort within the current tier is a cheaper first move than jumping a tier; try it when the defects are borderline.
- Tier escalation follows the standard rule: apply it only through a platform-confirmed mechanism; otherwise continue at platform default and state that.

## Escalation handling (root agent)

When a task arrives `escalated`, the root agent chooses explicitly — never silently:

- **accept-with-risk**: use the best iteration's output and record the unmet criteria as risks in the final report;
- **re-scope**: rewrite the task or its criteria and restart the loop (this is a new task row, fresh budget);
- **reassign**: give the task to a different specialist or take it locally;
- **ask the user**: when the gap is a product/scope decision.

## Anti-patterns

- Re-running the identical prompt hoping for a different result — every iteration must consume the defect list.
- Validator drift — validators judge only the stated criteria; new requirements discovered mid-loop go to the root agent as scope findings, not silent additions.
- Loop inflation — do not apply the full loop to trivial deterministic tasks; budget 1 exists for those.
- Verdict averaging — one failed mandatory criterion means `fail`, regardless of how many others passed.

## Reporting

The orchestrator's task table tracks the loop live: `Loop` column shows `used/budget` (e.g. `2/5`), `Status` gains `validating` and `refining` states, and escalated rows keep their full verdict history available for the root agent's final report. After the run, feed loop statistics (tasks that needed >1 iteration, recurring defect classes, validator misses) into `workflows/self-improvement.md` as evolution signals.
