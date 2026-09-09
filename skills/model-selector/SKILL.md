---
name: model-selector
description: "Assign every task a complexity tier, concrete model, effort, and token band before it runs, and audit finished tasks tables for model overspend. Use when splitting a request into tasks, filling a tasks table's Model/Effort column, deciding whether a task needs a stronger model, or checking whether cheap work ran on an expensive model."
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Model Selector

Per-task model assignment is a pre-execution decision, not a retroactive label.
This skill exists because the expensive failure mode is silent: a task that is
never explicitly assigned a model inherits the session's strongest one, and cheap
mechanical work bills at frontier rates while the tasks table records it as if
that were the plan.

## Cheapest capable model

Default DOWN to the least expensive model that can complete the task correctly.
Escalate only on a defined trigger, recorded on the row:

1. Two consecutive `reasoning`-classed validator failures at the current tier.
2. Security-sensitive judgment (auth, secrets, PII, injection surface, permission
   boundaries, security verdicts a human relies on).
3. Cross-file architectural reasoning (service boundaries, contract impact across
   consumers, migration ordering, decisions expensive to reverse).

Escalate one tier per trigger. Importance of the parent request, availability of
a stronger model, critical-path position, and feeding a `deep` reducer are all
invalid escalation reasons.

## Workflow

1. Split the task list so no row bundles different kinds of work — a bundled row
   inflates to the tier of its hardest part and overspends on the rest.
2. Match each row to the lookup table in `tool-subagents/model-selector.md` and
   record the matched row.
3. Apply the escalation triggers; a row above its lookup tier with no named
   trigger is a defect to report, not a preference to honor.
4. Assign a concrete model and effort for the active client from the client model
   map in `tool-subagents/agent-orchestrator.md`, plus a coarse token band
   (`XS`-`XL`).
5. Flag any `light`/`standard` row the root plans to execute inline — that is a
   routing defect unless it is pure conversation, one trivial tool call, or
   user-facing synthesis.
6. Print the assignment in the tasks table's `Model/Effort` column before
   execution, then verify after execution that it matches what actually ran.

Delegate the classification itself to the `model-selector` subagent
(`tool-subagents/model-selector.md`) when the task list is long; it is designed
to run at `light`/`standard` so the audit never costs more than the overspend it
prevents.

## Tier boundaries

- `light` — git operations, file moves, index/table-row edits, running a script
  and reporting pass/fail, mechanical sync, retrieval and mapping.
- `standard` — doc drafting, config/overlay sync review, standard code edits,
  ordinary review, summarization and evidence reduction.
- `deep` — security evaluation, architecture and design, adversarial review,
  conflicting evidence, governance authoring.
- `frontier` — reserved for root-level final synthesis and reasoning that has a
  recorded concrete failure at `deep`. Never assigned to a child at split time.

## Audit mode

Given a completed tasks table, compare the `Model/Effort` column against the
lookup and report each overspend row with the model that should have run. A table
where every row carries the session model is the signature defect: it means
tiering never happened and every task inherited the root.

## Related

- `rules/request-orchestration.md` — the mandatory model-selection contract
- `tool-subagents/agent-orchestrator.md` — client model map and dispatch duty
- `tool-subagents/model-selector.md` — full lookup table and return shape
- `skills/token-efficiency/SKILL.md` — reducing tokens within a chosen model
- `workflows/model-selector-validation.md` — pre-execution assignment gate
- `workflows/model-selector-evolution.md` — fixing stale or mis-tiered lookup rows
- `workflows/task-quality-loop.md` — validator verdicts that justify escalation

## Why escalate on measured failure, not anticipated difficulty

The published routing work splits into two mechanisms: routers that predict
difficulty from the request before anything runs, and cascades that run cheap
first and escalate only when an actual result is scored insufficient. This
toolkit uses the second, because a validator verdict is a measured signal we
already produce, while "this looks hard" is exactly the intuition that produced
the all-frontier tasks table. A router with a bad signal is worse than picking
one model and staying there, so the only failure-based trigger is two
consecutive `reasoning`-classed validator failures — a fact, not a forecast.

Two corollaries worth keeping in mind. First, compare on cost per completed
task, not cost per token: a cheap model that needs four retries is not cheap.
If a `light` assignment keeps failing validation, the lookup row is wrong —
fix the row rather than looping. Second, effort is a real dial independent of
model choice; moving `sonnet` from medium to high effort is often the right
escalation and is cheaper than jumping to `opus`.

## References

Idea-level influences, adapted as original guidance. No code, files, or
dependencies were taken from these sources.

- Anthropic, "Choosing the right model" — <https://platform.claude.com/docs/en/about-claude/models/choosing-a-model>
- Anthropic, "Optimizing for cost and intelligence" (advisor/orchestrator strategies, cost per completed task) — <https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence>
- Chen, Zaharia, Zou (Stanford), "FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance" — <https://arxiv.org/abs/2305.05176>
- Ong et al. (LMSYS / UC Berkeley), "RouteLLM: Learning to Route LLMs with Preference Data", ICLR 2025 — <https://arxiv.org/abs/2406.18665>
- "Hybrid LLM: Cost-Efficient and Quality-Aware Query Routing", ICLR 2024 — <https://openreview.net/forum?id=02f3mUtqnM>
