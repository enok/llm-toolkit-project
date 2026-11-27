---
description: Reusable per-task produce-validate-refine loop with a hard iteration budget, validator selection map, and tier escalation
---

# Task Quality Loop

Produce->validate->refine loop that `agent-orchestrator` applies to every delegated task; other workflows may call it for any bounded task with verifiable acceptance criteria. Hard limit: **max 5 iterations per task**; deterministic `light` tasks get budget 1. Never loop silently or accept a failed result.

## Before the first iteration

- Write verifiable acceptance criteria, each mandatory or advisory, at least one checkable by evidence. A ticket's ACs are the mandatory criteria; a subtask must also stay aligned with its parent and siblings.
- **Unclear goal gate:** if the goal or ACs cannot become verifiable criteria, ask the user before starting.
- Assign producer + tier and a validator from the map.

## Validator selection map

| Task output type | Validator |
| --- | --- |
| Code change / diff | read-only validator lane on the plain model for behavior and regression risk (+ `test-runner` when tests exist) |
| Test selection / build evidence | `test-runner` |
| Documentation, runbooks, generated LLM surfaces | `documentation-reviewer` |
| CV / career-profile claims | read-only validator lane on the plain model checking each claim, date, and title against its evidence |
| Public article and social post drafts | read-only lane on the publication profile and `rubrics/technical-content.md` if present (shape check of `workflows/study-publication-medium-linkedin.md`); draft stays `NOT POSTED` until the owner approves |
| Java changes | `java-change-validator` |
| Security-sensitive work | read-only validator lane on the plain model with `skills/security-best-practices` |
| Diagrams / exported images | `diagram-creation-specialist` |
| PR / ticket readiness | `pr-validator` |
| Airflow/Glue/ETL | read-only validator lane on the plain model |
| Architecture claims | read-only validator lane on the plain model with `skills/system-architecture-specialist` |
| Log/evidence reduction | `log-analyst` |
| Web research findings | `verifier` at `light`: per-claim PASS / FAIL / UNVERIFIED with a short quote (`skills/credential-evaluation/references/lane-prompts.md`) |
| Alarm RCA / hypotheses | `aws-alarm-investigator` |
| Completion claims, mixed or generic output | `task-quality-judge` or `verifier` |

The validator is a different invocation than the producer, read-only (verdicts and defect lists, never edits), at the minimum sufficient tier, with its model set from the client model map in `tool-subagents/agent-orchestrator.md` like any dispatch.

## Loop

For iteration `i` in 1..budget:

1. **Produce.** After the first pass the producer gets only the task, the criteria, and the last defect list; fix the listed defects, do not restart or widen scope.
2. **Validate.** Verdict `pass` | `fail` | `escalate`, criteria checklist, numbered defects classed `mechanical` or `reasoning`, regressions, loop recommendation. One failed mandatory criterion means `fail`.
3. **Decide.** `pass`: done (first-pass when `i = 1`). `fail` and `i < budget`: refine. `fail` at budget: mark `escalated`, hand the last output and verdict history to the root. `escalate`: stop (mis-scoped task, contradictory criteria, or the same reasoning defect in two consecutive iterations).

After 2 consecutive `fail` verdicts with blocking `reasoning` defects, raise the producer one tier (`light` -> `standard` -> `deep`) through a platform-confirmed mechanism and note it in the task table; `mechanical` defects never raise the tier. A refine re-validation resumes the same validator or gives a fresh one the verdict history.

## Escalated tasks (root agent)

Choose explicitly: **accept-with-risk** (unmet criteria become reported risks), **re-scope** (new row, fresh budget), **reassign**, or **ask the user**.

## Reporting

The task table's Evidence cell shows `iter used/budget`; `Status` gains `validating` and `refining`. Per task, the run record (`workflows/run-retrospective.md`) gets iterations used, the first-pass flag, and one mistake signature per root cause of blocking defects (`skills/run-retrospective/references/mistake-taxonomy.md`); an in-loop tier raise adds `tier-misassignment/...`, and an `escalated` task is never first-pass.
