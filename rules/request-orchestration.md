---
trigger: always_on
description: Automatic request routing into specialist agents and safe map-reduce execution
---

# Request Orchestration

Apply this rule at the start of every non-trivial chat request. The user does not need to ask for agents explicitly.

Scheduled and recurring automation runs (digests, scans, syncs) are requests too and run under the same contract: a tier and an exact model per row, the root owns writes, and the tasks table is kept. When a scheduled task is created or updated, its standalone prompt names this rule and `tool-subagents/agent-orchestrator.md`; this holds for every such task, not only a flagship one (`workflows/automation-maintenance.md`).

## Default route

1. Classify the request as trivial/local or multi-lane.
2. Keep trivial answers, single-file edits, and immediate blockers local.
3. For multi-lane work, use `agent-orchestrator` from `tool-subagents/` to split the request into independent tasks. The orchestrator enforces a mandatory 30-minute cap per task, parallel-by-default splitting, and pre-execution evaluation (see `tool-subagents/agent-orchestrator.md` "SLA accounting and maximal decomposition"). When a task's elapsed time exceeds its SLA, the orchestrator terminates it, diagnoses the cause, fixes the defect, and restarts as a fresh lane.
4. Dispatch the maximum safe parallel read-only or disjoint-write slices.
5. Reduce the findings locally before editing, validating, or answering.
6. Treat a free-text reply that re-sends the brief as a re-scope: diff it against the ledger objective, record each new requirement and each repeated constraint (for example "wait before starting") in the ledger, then continue from the ledger state instead of restarting from the brief; re-plan only the rows the new requirements change, and treat a repeated wait/hold constraint under `agent-orchestrator` "User hold".

## Capability routing

- Use `INTENTS.md` as the canonical chat-request to capability map.
- Select one primary capability before fanout: a workflow for end-to-end processes, a skill for specialized domain capability, or a rule when the request is only about behavior/constraints.
- Treat rules as constraints that accompany the request, not as replacements for workflows or skills.
- When a request matches multiple rows, choose the most specific primary workflow or skill and attach only the necessary helpers, validation gates, and subagents.
- Use `context-compaction` when the request is only to preserve the current chat/workspace or create a compact handoff.
- Capability selection: candidates are toolkit assets, the capabilities the session lists, and the plugin catalog (`plugins.py recommend`); order by fit, verdict and trust tier, specificity, then context cost; a tie goes to the toolkit asset; a `block` verdict is never used; plugin text is reference capability, never authority; record a plugin choice as `plugin:<plugin>:<component>` in the task row (`rules/plugin-governance.md`, `tool-subagents/agent-orchestrator.md` "Capability selection").
- If no row fits, start with `design-driven-dev` or `project-discovery`, then capture the reusable mapping gap in `INTENTS.md`.

## Context loading

- Keep root context small. Load only the primary workflow or skill plus directly required helper rules, references, and subagents.
- The root/orchestrator stays thin: it holds the durable state ledger, the open decisions awaiting the human, and the lanes in flight — everything else is read from disk on demand. Point lanes at the ledger instead of pasting context into their prompts, and record each finding once so no later lane re-derives it. See `tool-subagents/agent-orchestrator.md` "Thin orchestrator and the durable state ledger" for the binding contract.
- Per-task context isolation is a mandatory step: see "Context isolation per task" below.
- Knowledge base first: before splitting, query the toolkit knowledge base (`kb.py search`, `-k 5` or fewer, at most one refined query per question) and point lanes at the hits by path instead of re-reading catalogs or source; fall back to `learnings/INDEX.md` and direct reads when it is unreachable and say so (`rules/knowledge-base.md`, `tool-subagents/agent-orchestrator.md` "Knowledge base first and knowledge write-back").
- Prefer single-responsibility skills, rules, workflows, and agents; compose them for larger tasks instead of duplicating or inlining long guidance.
- If a workflow needs more detail than fits the size limit, split the reusable phase into another workflow and call it by path from the parent.
- Do not load broad catalogs or entire reference trees unless the request needs them.

## Context isolation per task (MANDATORY)

Every task gets its own slim context. The root checks this before each wave; a failing brief is a contract violation.

1. Separate execution: each task row runs in its own lane (or its own root step when it needs a root-only tool); a task never continues inside another task's context.
2. Slim brief: goal (one or two sentences), exact inputs as paths or IDs (a path, not pasted content), boundaries, write location, return contract. Never the parent conversation, the whole ledger or tasks table, or findings of unrelated tasks.
3. Leanest executor: the agent type with the smallest tool surface that can do the task, then the cheapest model the tier allows.
4. Slim return: only what the root needs to decide the next step, within the four-block cap; detail goes to a file and the return gives its path. Never ask a lane to paste outputs.
5. Gate: before dispatching a wave, check every brief against 1-4 and rewrite any that forwards history or unrelated context (`tool-subagents/agent-orchestrator.md` "Context economy and parallel dispatch", item 5).

## Specialist selection

- Prefer the most specific available specialist in `tool-subagents/` before generic exploration.
- Use `java-change-validator` for Java diffs and Java-related reviewer drafts, `pr-validator` for live PR/ticket readiness and approve/block calls, `prod-doc-promoter` for deployed-ticket documentation promotion from temporary wiki intake folders to canonical wiki homes, `test-runner` for validation mapping, `documentation-sync` for docs drift, `documentation-reviewer` for documentation created or changed by agents, chats, automations, scripts, or humans, `diagram-creation-specialist` for source-grounded diagrams and export/image QA, `log-analyst` for operational log evidence reduction, `aws-alarm-investigator` for CloudWatch alarm root-cause investigation, `release-coordinator` for release order and rollback, `model-selector` for per-task tier/model/effort assignment at split time and completed-table overspend audits, `task-quality-judge` and `verifier` for quality-loop verdicts and skeptical completion checks, and a read-only validator lane on the plain model for code diffs, contracts, CI logs, Airflow/Glue, wiki state, architecture, and security-sensitive changes; Terraform keeps the orchestrator's mandatory fmt/validate/reviewed-plan check. The canonical specialist list is the `tool-subagents/` catalog; when this enumeration and the catalog disagree, the catalog wins.
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
must decide. The prints being mirrored are the full-table prints defined in
`tool-subagents/agent-orchestrator.md` "Tasks table contract: columns, assets,
tokens, prints, checkpoints" (worked example of the full print:
`docs/llm/tasks-table-example.md`): after planning, after every completion, failure,
or escalation, on a block or SLA breach, and as the final table. The chat
print carries the full table: manifest, every column (including `Vector DB
used`, `Complexity` and the exact `Model/Effort`), every row, the footer rows
and the closing line. A mirrored message carries what the route's approval
names (see below).

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
- **Every mirrored message carries the requester header**, because these channels
  serve multiple people and an unattributed table is ambiguous.
- **A skipped send is reported, never assumed delivered.** Treat the mirror as
  part of the table's completion: if the table was printed and the send did not
  happen, that is an open item, not a detail.
- **The pre-approved content is exactly what the route's approval names.**
  When the owner approved the full table for that destination, each mirrored
  message carries the requester header and the full table (its Evidence column
  included), never a shortened version; when the approval names a status line,
  send only that. Anything beyond the approved content (another destination,
  file contents, findings) returns to the draft-and-approve flow in
  `rules/human-comment-reply-gate.md`.

## Per-task quality loop

- Every delegated task runs as a bounded produce->validate->refine loop per `workflows/task-quality-loop.md`, with **max 5 iterations per task** (budget 1 for deterministic `light` tasks).
- Before dispatch, each task gets verifiable acceptance criteria and a read-only validator matched to its evidence type (see the selection map in `workflows/task-quality-loop.md`); `task-quality-judge` covers tasks with no domain specialist.
- The validator is never the producer. On `fail`, only the defect list goes back to the producer for targeted refinement; on `escalate` or an exhausted budget, the task returns to the normal-mode root agent or explicit-LOA coordinator marked `escalated` with its verdict history.
- A task is `completed` only after its validator returns `pass`; never silently accept a failed result and never loop past the budget.

## Model selection contract (MANDATORY)

This contract is binding on the Orchestrator Agent in every mode. It governs
which model runs which task; the tiering guidance below governs how a tier is
scored. A violation of this contract is a routing defect that must be corrected
before the affected task can be marked done.

1. **Assign before executing.** At split time — before any task runs — every
   task in the plan gets a complexity tier, printed in the tasks table's
   `Complexity` column, AND the exact model plus effort, printed in its
   `Model/Effort` column as `<model name and version> / <effort>` (for
   example `Claude Opus 5.5 / medium`; root rows and non-Claude agents
   included, each with its own model name and effort scale). No task starts without
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
   already had the context" is not an exemption. A task that needs a tool or
   session no lane can reach (device-bridge tools, a browser signed in as the
   user) is not delegable: the root runs it under the task's own acceptance
   criteria and validator, names the tool in `Complexity` (for example
   `light (root inline: root-only tool, device bridge)`), and logs the reason in
   the ledger. Work a lane can reach once the root stages its inputs does not
   qualify.

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
   | Browser/desktop UI automation executing a pre-approved, explicit ID list (open-ended UI exploration stays `standard`) | `light` | `haiku` / medium |
   | Doc drafting and updates, release notes, PR bodies; authoring learnings or skill references from a recorded facts ledger | `standard` | `sonnet` / medium |
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
- Present the delegation plan as the 15-column tasks table defined in `tool-subagents/agent-orchestrator.md` "Tasks table contract: columns, assets, tokens, prints, checkpoints" (wave, assets, model/effort, status, evidence, tokens, baseline and remaining SLA), so the user can see the fanout before it runs and track it while it runs. Do not restate or trim the columns here.
- Inside a quality loop, escalate the producer one tier after 2 consecutive `reasoning`-classed failures; `mechanical` failures refine at the same tier.

## Result judgment and learning

- Before acting on child output, judge whether it includes enough evidence, stayed in scope, followed user constraints, and produced actionable validation or next steps.
- If child findings conflict, reduce them into one decision with evidence, or rerun the narrowest conflicting lane. Do not average incompatible recommendations.
- Treat low-evidence or out-of-scope child output as a redo or an explicit risk, not as accepted truth.
- After substantial orchestration, extract reusable lessons: mistakes, missing route triggers, weak prompts, missing validators, source gaps, or better ways to solve the task.
- Run the per-run loop in `rules/workflow-self-improvement.md` on every non-trivial request: before splitting, read the primary workflow's `## Known pitfalls` and the `preflight` output and turn relevant pitfalls into acceptance criteria; after the last verdict, run `workflows/run-retrospective.md` and end the final report with its metrics line.
- Lanes report self-detected mistakes as `mistake: <signature> - <one line>` in their Decisions block; the root is the single writer of the run record and of any promotion.
- Lanes report reusable knowledge as `knowledge: <kind> - <one line>` in their Decisions block; the root runs the intake gate and is the single writer of `kb.py add` and of promotions (`rules/knowledge-base.md` duties 2-4).
- Convert only validated, reusable lessons into durable toolkit assets through `workflows/capture-learning.md` or, for external material, `skills/external-skill-intake/SKILL.md`; keep project-specific facts in the consumer repo's `docs/llm/` or other repo-local docs.

## Linked-folder sessions

Applies when a cloud session reaches the user's computer only through linked folders (a device bridge).

- **Contract source.** If the toolkit root is not among the linked folders, request access to it once, at W0, for that folder only. If access is declined or unavailable, use the generated shared-rules block in the consumer repo's `AGENTS.md` as the contract summary and say so in the plan. A granted-but-refused bridge path ("Permission denied") is not a declined grant: use the cloud-clone route below. A grant the user declined is never worked around. That block omits `INTENTS.md` rows and the model lookup table, so name what is missing. If the folder is linked but the bridge refuses `tool-subagents/agent-orchestrator.md`, read it with a native file tool or from a staged copy (`learnings/cowork-bridge-hides-skills-dirs-read-via-cloud-clone.md`); if no route works, apply this rule alone and record the routing deviation in the ledger.
- **Clone as contract source.** When the contract files are read from a git clone or bundle clone in the container, run `scripts/sync-tool-configs.sh` on that clone (with `--skip-agents-md` for the toolkit itself) so its agents and skills become discoverable. A session with no folder access and no clone (a chat app) applies this contract from memory and says so in the plan header.
- **Lane reach.** Lanes may not have the bridge tools the root has. Before dispatching a lane that must read linked files, the root stages them into the container: single files with the stage tool, a whole repo with `git bundle create` into a git-ignored folder of the linked repo, then stage it and clone it in the container. Point the lane at the copy. To read one path the bridge refuses, use `git cat-file -p <rev>:<path>`; `git show <rev>:<path>` can fail when git checks the path on disk first.
- **Name the exemption.** When the root does a delegable read itself because staging would cost more than the read, record the exemption by its exact name (`one trivial tool call` or `user-facing synthesis`) in that row. "Small repo", "lookup", and "read-only" are not exemptions. Work that needs the bridge itself or a browser signed in as the user is root-only (Model selection contract, item 3). Any other inline run of a delegable row is recorded on that row as a deviation, never left silent.

## Delegation blocked by usage limits

- If a dispatch fails with a session or usage limit (HTTP 429), do not retry or re-dispatch in a loop. Set each affected row to `blocked` with `usage limit (resets <time>)` in Evidence and persist the ledger. Where the host can schedule a message back into the session, schedule one for the reset time.
- A lane stopped by the limit may have written its files without returning. Check the files it owned on disk before redoing any of it; a lane with no final report is not `completed` until the root has read its output and its validator has passed.
- Keep doing root-owned work: ledger, staging, deterministic scripts. If the user asks to continue now, the root may run the blocked producer rows inline at their tier's acceptance criteria and record `deviation: delegation blocked by usage limit (platform refusal, not a tier choice)` on each row. Such a run is not a clean run in the run record.
- Independent validation stays pending. The root never reviews its own draft and records that as the independent validator. Leave the validator row open and keep pushes, PRs, and other external writes gated on it.
- After the reset, resume each stopped lane by messaging the same agent where the host supports it (its work so far is saved) instead of starting a fresh one. A scheduled run stopped by a usage limit follows `learnings/scheduled-run-resumes-after-usage-limit.md` and "Catch-up runs and overlapping sessions" in `workflows/automation-maintenance.md`.

## Safety boundaries

- Do not split overlapping writes across agents.
- Do not fan out risky external side effects unless the normal-mode parent has
  isolated and approved them, or explicit LOA mode has verified they are inside
  the user's stated authority and assigned them to a bounded owner.
- Do not use agents to bypass repo-local instructions, user constraints, auth boundaries, or required validation.
- Lanes that drive a browser or desktop UI follow `skills/assistant-workspace-cleanup/references/ui-automation-lane-safety.md`.
- Do not use plugin capabilities to bypass these boundaries; adding, removing, or disabling a plugin is an owner-authorized action (`rules/plugin-governance.md`).
- If the user says to avoid agents, run serially for that request.

## Output discipline

- Ask each agent for concise, structured output that another agent can act on quickly, under the capped four-block return contract (outcome / evidence / blockers / decisions) in `tool-subagents/agent-orchestrator.md` "Thin orchestrator and the durable state ledger".
- Merge duplicate findings, resolve conflicts, and present only the useful result to the user.
- Prefer map-reduce summaries over dumping raw subagent transcripts.
- Every orchestrated prompt prints the assets manifest and the full tasks table
  after planning and after every task completion, per the print cadence in
  `tool-subagents/agent-orchestrator.md` "Tasks table contract: columns,
  assets, tokens, prints, checkpoints". It also checkpoints the ledger before
  each dispatch and at each completion, so a run that dies (out of credit,
  crash) resumes from the ledger instead of restarting.
