---
description: Validate capability-first agent orchestration, per-task model selection, SLA accounting, and explicit LOA mode handoffs
---

# Agent Orchestrator Validation

Use this workflow to validate coordinator routing, task tables, async handoffs,
or explicit LOA-mode results before they are presented as final.

## Steps

1. Establish explicit mode selection, user authority, platform capabilities,
   repo/worktree ownership, task acceptance criteria, and external-action gates.
2. Confirm every task has a non-overlapping owner, requested/confirmed
   model+reasoning, separate read-only validator, loop budget, wave, and SLA.
   Model selection is mandatory: verify each dispatch actually set the
   platform's model/effort parameter from the client model map in
   `tool-subagents/agent-orchestrator.md` (Claude Code: `light` -> `haiku`,
   `standard` -> `sonnet`, `deep` -> `opus`). A row whose confirmed model is
   the session default without a recorded tier-escalation justification is a
   defect — fail the row until the dispatch is corrected; accept
   `platform default / unconfirmed` only where the platform exposes no
   per-task mechanism.
3. Check the tasks table against "Tasks table contract: columns, assets,
   tokens, prints, checkpoints" in `tool-subagents/agent-orchestrator.md`:
   - Every normal-mode chat print (and `TASKS_TABLE.md`) carries all 13 columns in order (`#`, `Wave`, `Task`,
     `Assets`, `Model/Effort`, `Status`, `Evidence`, `PR link(s)`, `CI/CD run
     link(s)`, `Tokens`, `% Complete`, `SLA`, `Remaining SLA`) and the three
     footer rows (`Total (all tasks)`, `Total (remaining/not completed)`,
     `Remaining SLA to complete all tasks (critical path)`); a dropped or
     merged column is a defect even when its cells are empty.
   - `Tokens` is filled for every completed row (host-reported, or marked
     `~` when estimated) and `Total (all tasks)` sums it; the assets manifest
     (route, rules in force, agents, helpers) is present above the table and
     the `Assets` column names nothing the manifest lacks.
   - The full table was printed after planning and after every completion,
     failure, or escalation, and immediately on a block or breach, not a
     delta or partial table; the printed values match `TASKS_TABLE.md`.
   - Checkpoint evidence exists: the ledger was written before the first
     dispatch and at each dispatch (dispatch time and expected output path in
     Evidence), and completed rows cite durable artifact paths (project tree,
     pushed or bundled branch, run folder), not a sandbox or `/tmp`. A
     resumed run starts from the open ledger section and is headed
     `resumed from <timestamp>`.
   - SLA accounting: every row's baseline `SLA` is <= 00:30 (a larger row
     should have been split before dispatch) and not edited after dispatch,
     the critical path is stated, the `Wave` column makes parallelism
     visible, and `Remaining SLA` and its total are recalculated rather than
     carried forward. A task whose elapsed time exceeded its `SLA` baseline
     must show a termination, a diagnosed cause, and a fresh restarted lane,
     never a silently extended budget.
4. Enforce the mandatory CSCI/UID lifecycle: every created or updated code,
   script, configuration, or infrastructure artifact has explicit unit-test,
   integration-test, and documentation tasks (page text and diagrams in the
   project's wiki or docs site); the target project's `README.md` links the
   application's documentation page (ask the user for the location if absent —
   never invent one); and documentation tasks sit in the final wave, after the
   application is validated.
5. For LOA, independently verify milestone-only progress (`0/25/50/75/100`),
   every row's baseline and remaining SLA in h/min, baseline-SLA weighted
   rollup rounded to 5%, critical-path remaining SLA, and that external
   variance is a range.
6. After each validator pass, inspect the target project's untracked,
   uncommitted `LLM-STATE.md`: timezone timestamp, task table, branch/SHA/
   worktree, command evidence, live PR/check/thread state, agents/models,
   risks, resume action, and notification-mirror status. Verify it is excluded
   before each commit/push. Verify the same for `TASKS_TABLE.md` and
   `CONTEXT_STATE.md` when the run persists them.
7. Where the consumer repo configures a notification route, confirm a send has
   human-gate or standing-approval evidence and targets that configured
   destination without mass mentions. Use
   `Notification mirror: unavailable (no write capability)` only when the write
   tool is absent; otherwise distinguish authentication missing, destination
   missing, or pending approval. Every unavailable state is nonblocking. With
   no configured route, confirm the table was printed and the mirror correctly
   skipped.
8. Validate the narrowest relevant produced artifacts and report only
   evidence-backed defects. A producer never validates itself.
9. Confirm the four-block return contract held for each lane (outcome /
   evidence / blockers / decisions, capped at 40 lines or 400 words excluding
   fenced evidence) and that over-cap returns were sent back for reduction
   rather than absorbed into the root context.
10. Confirm learning output records capability inventory, selected token-saving
    tools, reused evidence, and duplicate exploration avoided.

## Evolution

For a validated routing, model, SLA, state, notification, or token-efficiency
miss, run `workflows/agent-orchestrator-evolution.md`.
