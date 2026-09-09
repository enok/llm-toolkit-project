---
trigger: always_on
description: Automatic request routing into specialist agents and safe map-reduce execution
---

# Request Orchestration

Apply this rule at the start of every non-trivial chat request. The user does not need to ask for agents explicitly.

## Default route

1. Classify the request as trivial/local or multi-lane.
2. Keep trivial answers, single-file edits, and immediate blockers local.
3. For multi-lane work, use `agent-orchestrator` from `tool-subagents/` to split the request into independent tasks. The orchestrator enforces a mandatory 30-minute cap per task, parallel-by-default splitting, and pre-execution evaluation (see `tool-subagents/agent-orchestrator.md` "SLA accounting and maximal decomposition"). When a task's elapsed time exceeds its SLA, the orchestrator terminates it, diagnoses the cause, fixes the defect, and restarts as a fresh lane.
4. Dispatch the maximum safe parallel read-only or disjoint-write slices.
5. Reduce the findings locally before editing, validating, or answering.

## Capability routing

- Use `INTENTS.md` as the canonical chat-request to capability map.
- Select one primary capability before fanout: a workflow for end-to-end processes, a skill for specialized domain capability, or a rule when the request is only about behavior/constraints.
- Treat rules as constraints that accompany the request, not as replacements for workflows or skills.
- When a request matches multiple rows, choose the most specific primary workflow or skill and attach only the necessary helpers, validation gates, and subagents.
- Use `chat-knowledge-curation` when the request is primarily to mine chats, memory, rollout summaries, automation runs, or learnings into durable LLM assets.
- Use `context-compaction` when the request is only to preserve the current chat/workspace or create a compact handoff; use `chat-knowledge-curation` for broader history mining or promotion of repeated, cross-source lessons into shared toolkit assets.
- If no row fits, start with `design-driven-dev` or `project-discovery`, then capture a reusable mapping gap through `toolkit-maintenance`.

## Context loading

- Keep root context small. Load only the primary workflow or skill plus directly required helper rules, references, and subagents.
- The root/orchestrator stays thin: it holds the durable state ledger, the open decisions awaiting the human, and the lanes in flight — everything else is read from disk on demand. Point lanes at the ledger instead of pasting context into their prompts, and record each finding once so no later lane re-derives it. See `tool-subagents/agent-orchestrator.md` "Thin orchestrator and the durable state ledger" for the binding contract.
- Prefer single-responsibility skills, rules, workflows, and agents; compose them for larger tasks instead of duplicating or inlining long guidance.
- If a workflow needs more detail than fits the size limit, split the reusable phase into another workflow and call it by path from the parent.
- Do not load broad catalogs or entire reference trees unless the request needs them.

## Specialist selection

- Prefer the most specific available specialist in `tool-subagents/` before generic exploration.
- Use `parallel-explorer` for broad repo maps, `cross-repo-analyst` for multi-repo context, `code-reviewer` for implementation risk, `java-change-validator` for Java diffs and Java-related reviewer drafts, `pr-validator` for live PR/ticket readiness and approve/block calls, `dag-glue-specialist` for Airflow DAG, MWAA, AWS Glue job, crawler, Data Catalog, and ETL pipeline validation, `prod-doc-promoter` for deployed-ticket documentation promotion from temporary wiki intake folders to canonical wiki homes, `test-runner` for validation mapping, `documentation-sync` for docs drift, `documentation-reviewer` for documentation created or changed by agents, chats, automations, scripts, or humans, `confluence-documentation-specialist` for wiki page state and hierarchy, `diagram-creation-specialist` for source-grounded diagrams and export/image QA, `system-architecture-specialist` for application architecture, service boundaries, data flows, integrations, and quality attributes, `log-analyst` for operational log evidence reduction, `aws-alarm-investigator` for CloudWatch alarm root-cause investigation, `ci-triage` for CI failure logs, `contract-analyzer` for API/schema/event and downstream-consumer impact, `release-coordinator` for release order and rollback, `model-selector` for per-task tier/model/effort assignment at split time and completed-table overspend audits, `task-quality-judge` and `verifier` for quality-loop verdicts and skeptical completion checks, and security agents for security-sensitive changes. The canonical specialist list is the `tool-subagents/` catalog; when this enumeration and the catalog disagree, the catalog wins.
- If no specialist fits, keep the task in the parent agent and note the missing reusable capability only when it would be useful to add later.

## Hierarchical delegation

- In normal mode, the root agent owns user communication, final decisions,
  edits, validation, and push/PR actions.
- Coordinator agents may call other agents when their task has independently verifiable subparts.
- Leaf agents should not recursively delegate unless their prompt or manifest explicitly allows it.
- Keep delegation depth shallow: root -> coordinator -> specialist is the normal maximum.
- A child agent returns evidence, paths, commands, risks, and recommended next steps; it does not claim final completion for the whole user request.

## Explicit LOA mode

Only when the user explicitly asks for LOA mode or long-running autonomous
orchestration, route to the LOA mode in `tool-subagents/agent-orchestrator.md`.
Then the parent chat is reconciliation/final-results checker only and separated
async workers own authorized implementation, restacks, pushes, PR/release/
CI actions, and independent validation. Require its milestone/SLA table,
excluded project-root `LLM-STATE.md` checkpoint, and capability-gated chat
mirror; normal root-owned execution remains the default.

## Tasks-table notification cadence (MANDATORY when configured)

Printing the tasks table and mirroring it to the team's channel are one action,
not two. Whenever a consumer has a configured notification route and a standing
authorization covering it, every print of the table is also sent to the matching
channel — first table, after each task completion, and immediately when a task
becomes blocked, with the blocked send naming what is blocked and what the user
must decide.

- **The route and its authorization are configuration, not defaults.** They live
  with the consumer as a consumer-configured notification route (for example
  `docs/llm/notification-routing.md` in the consumer repo), which names the
  channel per scope and records the standing authorization. Never hardcode a
  channel or assume a send is authorized: with no configured route, or no
  standing approval covering it, print the table and treat the send as an
  unapproved external write under `rules/external-write-authorization.md` —
  prepare it, label it `NOT POSTED`, and ask.
- **Capability is not authorization.** A reachable chat tool (Slack, Teams, or
  similar) does not by itself permit posting; the standing authorization does.
  Equally, a standing authorization does not survive a missing connection — when
  the transport is unavailable, say the mirror was skipped and why rather than
  silently dropping it.
- **Every mirrored table carries the requester header**, because these channels
  serve multiple people and an unattributed table is ambiguous.
- **A skipped send is reported, never assumed delivered.** Treat the mirror as
  part of the table's completion: if the table was printed and the send did not
  happen, that is an open item, not a detail.
- **The pre-approved format is narrow.** Each mirrored message carries only the
  status-line format approved with the route (agent, one-line result, complexity
  tier); anything else returns to the draft-and-approve flow in
  `rules/human-comment-reply-gate.md`.

## Per-task quality loop

- Every delegated task runs as a bounded produce->validate->refine loop per `workflows/task-quality-loop.md`, with **max 5 iterations per task** (budget 1 for deterministic `light` tasks).
- Before dispatch, each task gets verifiable acceptance criteria and a read-only validator matched to its evidence type (see the selection map in `workflows/task-quality-loop.md`); `task-quality-judge` covers tasks with no domain specialist.
- The validator is never the producer. On `fail`, only the defect list goes back to the producer for targeted refinement; on `escalate` or an exhausted budget, the task returns to the normal-mode root agent or explicit-LOA coordinator marked `escalated` with its verdict history.
- A task is `done` only after its validator returns `pass`; never silently accept a failed result and never loop past the budget.

## Model selection contract (MANDATORY)

This contract is binding on the Orchestrator Agent in every mode. It governs
which model runs which task; the tiering guidance below governs how a tier is
scored. A violation of this contract is a routing defect that must be corrected
before the affected task can be marked done.

1. **Assign before executing.** At split time — before any task runs — every
   task in the plan gets a complexity tier AND a concrete model plus effort,
   printed in the tasks table's `Model/Effort` column. No task starts without
   its assignment. The column is never filled retroactively from what happened;
   it is the dispatch decision, written first and then verified against what
   actually ran. Use `model-selector` from `tool-subagents/` to produce the
   assignment table when the task list is long or the tiers are contested.
2. **Cheapest capable model.** Default DOWN: assign the least expensive model
   that can complete the task correctly, then escalate only on a trigger below.
   Escalation triggers, each recorded on the row:
   - two consecutive `reasoning`-classed validator failures at the current tier;
   - security-sensitive judgment (auth, secrets, PII, injection surface,
     permission boundaries, or a security verdict a human will rely on);
   - cross-file architectural reasoning (service boundaries, contract impact
     across consumers, migration ordering, decisions expensive to reverse).
   Escalate one tier per trigger. These are NOT escalation reasons: the parent
   request is important or production-sensitive, a stronger model is available,
   the user asked for the orchestrator, the task is on the critical path, or the
   task feeds a `deep` reducer. Escalation is driven by a measured signal — a
   validator verdict or a named security/architecture property of the task — not
   by a forecast that the task looks hard. Raising effort within the assigned
   model (e.g. `sonnet` medium -> high) is the first escalation step and is
   preferred over jumping a model tier. Judge cost per completed task, not per
   token: if a `light` row keeps failing validation, its lookup row was wrong —
   correct the assignment instead of looping at the wrong tier.
3. **No silent inheritance.** A task never runs on the session/root model merely
   because nobody set a parameter. Inline execution by the root of a task classed
   `light` or `standard` is a routing defect unless it is pure conversation, a
   single trivial tool call, or user-facing synthesis. Executing a delegable task
   inline does not exempt it from this contract: if the root does the work
   itself, the task's tier still applies and the root must either delegate it at
   its tier or record why one of the three exemptions covers it. "The root
   already had the context" is not an exemption.

   **The session model is not a ceiling.** Tier assignment is a property of the
   task, decided independently of what the session happens to be running. When
   the session is set to a cheaper model and a task's row in the lookup calls
   for a stronger one, dispatch that task at its own tier and set the model
   parameter explicitly — a `deep` task does not become a `standard` task
   because the operator chose a cheaper session default. The converse holds and
   matters more often: an expensive session model never promotes `light` work,
   which is dispatched at `haiku` regardless of what the root is running.
   Inheritance in either direction is the defect this contract exists to
   prevent, and per-task assignment is the orchestrator's own responsibility —
   not something it defers to the session setting or to the operator.
4. **Task-type to tier lookup.** Assign from this table; a recorded escalation
   trigger is the only thing that moves a row above it.

   | Task type | Tier | Claude Code model / effort |
   | --- | --- | --- |
   | Git commit/push/branch, file moves, index-line or table-row edits | `light` | `haiku` / low |
   | Running a validation script or test and reporting pass/fail | `light` | `haiku` / low |
   | Path/name sync, formatting, mechanical find-and-replace | `light` | `haiku` / low |
   | Retrieval, file/symbol mapping, scanning output for a known pattern | `light` | `haiku` / medium |
   | Doc drafting and updates, release notes, PR bodies | `standard` | `sonnet` / medium |
   | Config/overlay sync review, generated-surface drift check | `standard` | `sonnet` / medium |
   | Standard code edits, ordinary bug fixes, ordinary code review | `standard` | `sonnet` / medium |
   | Summarization and evidence reduction, test selection and triage | `standard` | `sonnet` / medium |
   | Security evaluation, threat modeling, security verdicts | `deep` | `opus` / high |
   | Architecture/design, contract impact across consumers, migration ordering | `deep` | `opus` / high |
   | Adversarial review, conflicting-evidence reconciliation, release go-no-go | `deep` | `opus` / high |
   | Governance authoring (rules, mandatory contracts, policy other agents obey) | `deep` | `opus` / high |
   | Root-level final synthesis; reasoning with a recorded failure at `deep` | `frontier` | session frontier model / high |

   `frontier` is reserved for the root's own synthesis and for a task with a
   concrete recorded failure at `deep`/high. It is never assigned to a child task
   at split time because the task looks hard in advance.
5. **Verify the column.** The `Model/Effort` value is the assigned dispatch
   model, and after execution it must match what actually ran (the accepted
   model parameter on the tool call). A row whose value is the session default
   without a recorded task-specific escalation justification is a routing defect:
   flag it, correct the dispatch, and do not mark the row done. A whole table
   carrying one model on every row is prima facie evidence that tiering never
   happened — re-run the assignment through `model-selector` before reporting.

6. **Assign row by row, before printing.** Walk the task list one row at a time
   against the lookup in (4) and write each row's tier from the task type in
   front of you. Assigning a tier to the plan as a whole, or copying the
   previous row's value down the column, is the failure this step prevents — it
   produces a uniform column that looks deliberate and is not.

   Then run these checks on the assembled table and fix what they catch before
   the table is shown to anyone:

   - **Distinct-value check.** A table of three or more rows whose
     `Model/Effort` column holds a single distinct value fails. Real task lists
     mix mechanical and reasoning work, so a uniform column means the lookup
     was never consulted. Re-assign from (4) row by row.
   - **Floor check.** Every row that is a commit, push, file move, index-line
     edit, script run, or pattern scan reads `haiku`. If no row in a table
     containing such work reads `haiku`, the column was inherited rather than
     assigned.
   - **Justification check.** Every row above `standard` names the trigger from
     (2) or the lookup row that put it there. A `deep` row with no stated
     reason is an unjustified escalation, and "the overall request is
     important" is explicitly not a reason.

   These checks are cheap and run every time the table is refreshed, not only
   at first authoring. When one fires, correct the assignment and say so in the
   response rather than silently rewriting the column.

## Complexity-tiered delegation

- When `agent-orchestrator` splits a request, it scores each child task's reasoning demand as `light`, `standard`, or `deep` (see `tool-subagents/agent-orchestrator.md`) instead of naming a vendor model.
- **Applying the tier is mandatory whenever the platform exposes a per-task mechanism** (a model/effort parameter on the delegation tool, an IDE model picker, a per-agent override): every dispatch must set the model explicitly from the client model map in `tool-subagents/agent-orchestrator.md` (Claude Code Agent tool: `light` -> `haiku`, `standard` -> `sonnet`, `deep` -> `opus`). Omitting an available model parameter so the child inherits the session default is a routing defect, not a neutral default. Only a platform with genuinely no mechanism runs at the platform default, stated as `platform default / unconfirmed`; never claim a model switch that did not happen.
- In normal mode the root stays on the strongest available model. In explicit
  LOA mode the parent remains a reconciliation/final checker while each async
  task uses the coordinator's economical, platform-confirmed tier mapping.
- Present the delegation plan as a table (agent, task, complexity tier, validator, loop budget, rough time estimate, which wave/parallel group it runs in, and a status column updated as tasks move through pending/running/validating/refining/done/escalated) so the user can see the fanout before it runs and track it while it runs.
- Inside a quality loop, escalate the producer one tier after 2 consecutive `reasoning`-classed failures; `mechanical` failures refine at the same tier.

## Result judgment and learning

- Before acting on child output, judge whether it includes enough evidence, stayed in scope, followed user constraints, and produced actionable validation or next steps.
- If child findings conflict, reduce them into one decision with evidence, or rerun the narrowest conflicting lane. Do not average incompatible recommendations.
- Treat low-evidence or out-of-scope child output as a redo or an explicit risk, not as accepted truth.
- After substantial orchestration, extract reusable lessons: mistakes, missing route triggers, weak prompts, missing validators, source gaps, or better ways to solve the task.
- Convert only validated, reusable lessons into durable toolkit assets through `workflows/self-improvement.md`, `workflows/toolkit-maintenance.md`, or `skills/external-skill-intake/SKILL.md`; keep project-specific facts in the consumer repo's `docs/llm/` or other repo-local docs.

## Safety boundaries

- Do not split overlapping writes across agents.
- Do not fan out risky external side effects unless the normal-mode parent has
  isolated and approved them, or explicit LOA mode has verified they are inside
  the user's stated authority and assigned them to a bounded owner.
- Do not use agents to bypass repo-local instructions, user constraints, auth boundaries, or required validation.
- If the user says to avoid agents, run serially for that request.

## Output discipline

- Ask each agent for concise, structured output that another agent can act on quickly, under the capped four-block return contract (outcome / evidence / blockers / decisions) in `tool-subagents/agent-orchestrator.md` "Thin orchestrator and the durable state ledger".
- Merge duplicate findings, resolve conflicts, and present only the useful result to the user.
- Prefer map-reduce summaries over dumping raw subagent transcripts.
