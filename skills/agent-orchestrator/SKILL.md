---
name: agent-orchestrator
description: Use when a non-trivial request needs capability-first routing, safe parallel delegation, per-task model tiering, bounded independent validation, durable resume state, or explicit LOA long-running autonomous orchestration.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Agent Orchestrator

Route non-trivial work through the coordinator. Default mode preserves normal
parent-owned execution; use LOA (long-running autonomous orchestration) only
after the user explicitly requests it.

## Mandatory duties

Any LLM tool loading only this skill still owes all of these duty sets from
`tool-subagents/agent-orchestrator.md`:

- **Context economy + parallel dispatch** — sweep no-longer-load-bearing
  context the moment each task completes; start every dependency-free task
  in parallel, each in its own separate agent/chat context; pass each
  dispatch minimal context in and pull back only structured results,
  verdicts, and evidence pointers, never transcripts or raw dumps.
- **Thin orchestrator + durable state ledger** — keep the root's resident
  context to three things only (the ledger, the open decisions awaiting the
  human, the lanes in flight); treat `CONTEXT_STATE.md` + `TASKS_TABLE.md` as
  the single source of truth and **point** lanes at it instead of pasting it
  into their prompts; send only four things outbound (the task, verifiable
  acceptance criteria, the constraints that lane could breach, the ledger
  path); require the four-block return (outcome / evidence / blockers /
  decisions) capped at 40 lines or 400 words excluding fenced evidence, and
  send an over-cap return back for reduction; distil every judged result —
  root causes with their workarounds — into the ledger once, so no later lane
  rediscovers it; compact by writing the ledger and dropping the narrative,
  never by summarizing narrative into narrative.
- **Per-task model selection, independent of the session** — assign every task
  a tier and a concrete model/effort row by row from the lookup in
  `rules/request-orchestration.md`, before anything runs; the session model is
  neither a ceiling nor a floor, so escalate a task above a cheap session
  default when its row calls for it and keep `light` work on `haiku` under an
  expensive one. Before showing the table, run the distinct-value, floor, and
  justification checks from that rule — a uniform `Model/Effort` column across
  three or more rows means the lookup was never consulted; correct it and say
  so.
- **Tasks-table notification cadence (opt-in)** — where the consumer repo
  configures a notification route, printing the table and mirroring it to that
  route are one action: first table, each completion, and immediately on a
  block. Look the route and its standing approval up in the consumer repo's
  `docs/llm/` (for example `docs/llm/notification-routing.md`); never assume a
  destination, never treat capability as authorization, and never let an
  unavailable transport become a silent skip. With no configured route, print
  the table and skip the mirror.
- **SLA accounting + maximal decomposition** — enforce the mandatory
  30-minute cap per task (any task SLA > 00:30 is a violation; split before
  dispatch); split to the smallest independently executable units; always
  split for parallel where dependencies allow; optimize jointly for fewest
  tokens, highest quality, shortest wall-clock; pre-execution evaluation of
  the plan as a whole (every row <= 00:30, critical-path stated, parallel
  visible in the Wave column); recalculate each row's SLA to the realistic
  remaining allotment on every refresh; report both the remaining-SLA sum
  and the critical-path wall-clock; re-split when the critical path exceeds 1
  hour; record the actual model/effort that ran per task in the tasks table
  (never the session default by silent inheritance); when a task's elapsed
  time exceeds its SLA, terminate it, diagnose the cause (wrong path/branch,
  silent blocker grinding, scope too large, loop without progress), fix the
  defect, and restart as a fresh lane — every dispatch must include a
  bounded-time blocker-reporting instruction so lanes surface blockers early.
- **Regression safety** — post-change verification re-verifies the
  previously-working surfaces a change touches, not just what it added;
  multi-part cutovers (for example an infrastructure rename plus an app
  deploy) ship as one atomic delivery or with an explicit bridge, never
  half-applied; a discovered regression drops everything for an evidence-first
  fix; every regression or near-miss gets an automated in-repo prevention
  guard, and testing before push is mandatory for any code change.
- **State persistence for resume** — per the "General tasks table
  persistence" and "Context state persistence" mandates in
  `tool-subagents/agent-orchestrator.md`: write/refresh `TASKS_TABLE.md`
  (at-a-glance task table) and `CONTEXT_STATE.md` (detailed narrative/resume
  state) in the target project's root after the initial analysis and again
  after EVERY task completion — both untracked and never committed. Purpose:
  if the session runs out of tokens or the user switches to another chat,
  machine, or LLM tool, loading the project and reading these two files must
  be sufficient to resume exactly where work stopped.

## Workflow

1. Load `workflows/agent-orchestrator-validation.md` and follow
   `tool-subagents/agent-orchestrator.md`.
2. Inventory available tools, skills, and platform model controls before
   dispatch. Per-task model selection is mandatory and governed by the model
   selection contract in `rules/request-orchestration.md`: assign every task a
   tier AND a concrete model/effort at split time, before execution, printed in
   the tasks table; apply the cheapest capable model and escalate only on a
   recorded trigger; every dispatch sets the delegation tool's model/effort
   parameter from the client model map in `tool-subagents/agent-orchestrator.md`
   (Claude Code Agent tool: `light` -> `haiku`, `standard` -> `sonnet`,
   `deep` -> `opus`); never let a child silently inherit the session default,
   and never run a delegable `light`/`standard` task inline instead. Use
   `model-selector` for the assignment table and for overspend audits. The
   skill inventory is the union of the toolkit catalog (`INTENTS.md` /
   `skills/`) and any client-installed skills the session exposes (plugin,
   marketplace, or user skills); plan with both, invoking installed skills by
   their exact listed names. Use the most specific capability with progressive
   disclosure, reuse evidence, and forbid duplicate exploration.
3. Use independent producers and read-only validators with the bounded loop in
   `workflows/task-quality-loop.md`; do not assign overlapping writes.
4. Enforce the mandatory CSCI/UID lifecycle from
   `tool-subagents/agent-orchestrator.md`: every created or updated
   code/script/configuration/infrastructure artifact gets explicit unit-test,
   integration-test, and documentation tasks (page text and diagrams in the
   project's wiki or docs site); the target `README.md` links the
   application's documentation page (ask for the location if absent, never
   invent one); documentation tasks run last, after validation.
5. In explicit LOA mode, keep the parent as final-results reconciler only;
   separate asynchronous workers perform user-authorized execution and LOA owns
   the excluded target-project `LLM-STATE.md` checkpoint as its sole writer.
   Sending a notification still requires the human-facing gate in
   `rules/human-comment-reply-gate.md` or an exact standing approval;
   capability alone is not authorization.
6. If the coordinator misses a reusable routing, SLA, state, or efficiency
   pattern, run `workflows/agent-orchestrator-evolution.md`.

## Related

- `rules/request-orchestration.md` — the binding orchestration and model-selection contract
- `rules/multi-agent-orchestration.md` — parallel fanout and reduction discipline
- `skills/model-selector/SKILL.md` — per-task tier assignment and overspend audit
- `skills/token-efficiency/SKILL.md` — reducing tokens within a chosen model
- `workflows/context-compaction.md` — preserving context into a durable handoff
