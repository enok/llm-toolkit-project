---
trigger: always_on
description: Close a measurable learn-from-mistakes loop on every non-trivial LLM or agent run - preflight known pitfalls, capture mistakes by signature, record the run, promote recurring lessons to verified guards, and report trend metrics
---

# Workflow Self-Improvement

Run this loop on every non-trivial run; the user never has to ask, and no workflow needs a retrospective phase of its own.

## Scope

Every non-trivial workflow run, skill-driven task, orchestrated lane set, and scheduled or automated agent run: 3+ steps, or any validator `fail`, tool error that forced a different approach, user correction, or escaped defect. A trivial run with zero signals needs no record.

One record per root run: the outermost workflow, or the orchestrator root, runs the retrospective once, at its very end, under the outermost (routed primary) workflow's name, never the agent's name. A nested workflow's `Final Step — Self-improvement`, a lane, and any workflow invoked by the retrospective itself (`capture-learning`, `toolkit-maintenance`) skip `workflows/self-improvement.md` entirely (its Phase 0 retrospective and the harvest) and hand their signals up as `mistake:` lines; the root's single pass covers them.

## The loop

1. **Preflight (before planning).** First, if `CONTEXT_STATE.md` has `### Pending run records` and the log is durable (see Non-blocking), append each one and delete it once `append` prints its run_id or reports that it already exists; in a discarded home leave them pending. Then run `skills/run-retrospective/scripts/run_retro.py preflight --workflow <name>` (`skills/run-retrospective/SKILL.md`), read the owning workflow's or skill's `## Known pitfalls`, and scan `learnings/INDEX.md` per `rules/error-driven-learning.md`. Fold every relevant pitfall into the plan and the acceptance criteria. When the script is unavailable (e.g. a chat app without the repo), skip it and say so.
2. **Capture (during).** Note each signal when it happens in the session ledger (`CONTEXT_STATE.md`): validator defects (`workflows/task-quality-loop.md`), tool errors that forced another approach, user corrections, tier escalations, CI failures. Lanes never write records; each lane lists `mistake: <signature> - <one line>` in its Decisions block. The root is the single writer.
3. **Retrospective + record (after).** Run `workflows/run-retrospective.md`: classify each mistake as `<category>/<slug>` (reuse recorded signatures), answer why it happened and why it was not caught earlier, and append one run record. A clean run still gets a record with empty `mistakes`; recording clean runs keeps FPY honest.
4. **Promote.** Climb `skills/run-retrospective/references/promotion-ladder.md`: record -> `learning` -> `checklist` (2nd occurrence) -> `guard` (3rd, or recurrence after a checklist) -> `rule` (recurrence after a guard, or 3+ workflows). Any `high`/`critical` mistake and every `safety-near-miss` becomes a guard at first occurrence.
5. **Verify.** A guard counts only when it fails on the original mistake (regression fixture or test) and passes on the fixed output. Checklist bullets end with `(sig: <signature>)`.
6. **Measure.** End the final report with one line: `Self-improvement: FPY <first_pass>/<tasks>, corrections <n>, escapes <n>, promotions <n>, recurrences <n>`. A signature that recurs after its highest promotion means that fix failed: climb one level.

## Goodhart guard (MANDATORY)

Metrics are diagnostic only, never a target. Never skip or weaken a validator, lower acceptance criteria, split work to inflate first-pass counts, or under-report a mistake to improve numbers. Under-reporting is itself a `validation-gap` mistake and is recorded as one.

## Non-blocking

The log must be durable. If it is unreachable, or lives in a home that is discarded (ephemeral sandbox, CI runner, fresh scheduled session), point `--log`/`LLM_RUN_LOG` at durable storage or keep the record under `### Pending run records` in `CONTEXT_STATE.md`; an exit 0 into a discarded home is not a record. Promotions into committed assets never wait on the log. If the retrospective cannot finish, deliver the result and report it as an open item.

## Privacy and genericity

Records hold generic summaries only; the script rejects emails, credential-like strings, key headers, and URLs with query strings. Names, hostnames, handles, and ticket IDs are not linted: keep them out yourself. The run log is user-level and never committed. Promoted assets follow the genericity rules in `rules/error-driven-learning.md`.
