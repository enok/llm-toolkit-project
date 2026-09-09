---
description: Assign and verify per-task complexity tier, model, effort, and token band before execution, and audit a finished tasks table for overspend
---

# Model Selector Validation

Use this workflow when a request is being split into tasks and each task needs a
tier plus a concrete model/effort before execution, or when a completed tasks
table should be audited for model overspend.

## Steps

1. Establish the task list, the active client, whether that client exposes a
   per-task model/effort mechanism, and any user constraint on model choice.
2. Split bundled tasks first: a row mixing mechanical and reasoning work inflates
   to the tier of its hardest part and overspends on the rest.
3. Invoke or follow `tool-subagents/model-selector.md` to assign every task a
   tier, model, effort, estimated token band, and rationale naming the matched
   lookup row or the escalation trigger.
4. Check the assignment against the model selection contract in
   `rules/request-orchestration.md`: cheapest capable model, escalation only on a
   recorded trigger, effort raised before a model tier is jumped, and no child
   assigned the session frontier model at split time.
5. Flag routing defects: rows above their lookup tier with no named trigger, and
   `light`/`standard` rows the root plans to run inline without qualifying for the
   conversation, single-trivial-tool-call, or user-facing-synthesis exemption.
6. Print the assignment in the tasks table's `Model/Effort` column before any
   task runs; after execution verify each value against the model parameter the
   dispatch actually accepted.
7. In audit mode, report per-row overspend with the model that should have run.
   A table carrying one model on every row means tiering never happened.
8. Report the assignment table, flags, corrections applied, and reusable lookup
   lessons.

---

## Evolution

If the selector mis-tiers a recurring task type or its lookup goes stale, run
`workflows/model-selector-evolution.md`.
