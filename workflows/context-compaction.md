---
description: Preserve useful chat or workspace context into durable LLM knowledge and produce a compact future handoff
---

# Context Compaction

Use this workflow when the user asks to preserve useful context, reduce future
context load, save chat/workspace learnings into LLM knowledge, or create a
handoff that another agent can continue from without rereading a long thread.

This workflow is shared toolkit guidance for any user of this toolkit. Keep it
intentionally generic: discover the current project layout from the workspace
you are in, and do not paste machine-specific paths from another chat into
reusable guidance.

If the user asks to save this prompt as a reusable workflow, update this
workflow rather than creating a duplicate. Keep shared text portable; put
ticket, account, dashboard, page, pipeline, or repo-specific facts in the
repo-local docs, learning, or memory note discovered locally.
If the user asks to continue prior work after compaction, finish the save,
verify it, then explicitly resume the previously active task from the compact
handoff rather than restarting from the full raw chat.

## Phase 0 - Stop And Shrink First

If the user explicitly says the current chat is too large, slow, expensive, or
asks you to stop current work and compact first:

1. Stop unrelated task execution immediately.
2. Do not continue implementation, Terraform, deployment, test execution, live
   requests, or external mutations until the compaction save is complete.
3. Preserve the active task only as a compact handoff with objective, dirty
   state, applied/live status, blockers, next validation commands, and manual
   boundaries.
4. Continue later from the compact handoff instead of rereading or replaying the
   full raw chat.

## Phase 1 - Discover Local Knowledge Surfaces

1. Inspect the current workspace and repo instructions:
   - current working directory and git status;
   - `AGENTS.md`, `CLAUDE.md`, `README.md`, `INTENTS.md`, or equivalent;
   - repo-local `docs/llm/`, `learnings/`, memory, workflow, or profile files.
2. Discover durable LLM knowledge locations from current evidence, such as:
   - shared toolkit docs or the consumer repo's `docs/llm/`;
   - repo-local rules, workflows, learnings, or handoff docs;
   - tool-native memory or ad-hoc notes;
   - generated client surfaces that are refreshed from canonical sources.
3. If no durable location exists, create one small local handoff note in the
   most appropriate documentation or memory location already used by the repo.
4. Record dirty git state before editing. Preserve unrelated work.

## Phase 2 - Select What To Save

Save only durable, reusable facts:

- project conventions and ownership boundaries;
- important decisions and rationale;
- current implementation, documentation, deployment, and validation status;
- source-of-truth docs, tickets, dashboards, pipelines, resources, and page IDs;
- validation commands, publish commands, and known-good workflows;
- gotchas, blockers, failed assumptions, and the proven recovery path;
- environment-specific rules, release boundaries, and manual-only steps.

Do not save:

- secrets, tokens, credentials, cookies, auth headers, private keys, or raw PII;
- noisy raw transcript material;
- temporary dead ends unless they prevent a repeated mistake;
- machine-specific paths unless discovered locally and needed for handoff.

## Phase 3 - Write The Handoff

Create a compact handoff that future agents can use directly. Include:

1. Objective and current status.
2. Source-of-truth locations and IDs.
3. What is already applied, live, published, or validated.
4. What is only planned or pending.
5. What must remain untouched.
6. Environments changed and environments that are manual-only.
7. Pipeline/build numbers, approval behavior, and rollout evidence when relevant.
8. Terraform/IaC apply status when relevant.
9. Validation commands and read-back checks.
10. Remaining manual steps or blockers.

Prefer two layers for substantial work:

- append durable reusable lessons to the project or toolkit knowledge file;
- add one short current-thread handoff note for fast future recall.

When the run is an orchestrated one, the durable layer is already defined:
`TASKS_TABLE.md` for the at-a-glance task state and `CONTEXT_STATE.md` for the
narrative resume state, both untracked in the target project's root (see
`tool-subagents/agent-orchestrator.md`). Compact by writing those files and
dropping the narrative — never by summarizing narrative into narrative.

## Phase 4 - Verify The Saved Knowledge

1. Read back every file or memory note you changed.
2. Run `git status` and `git diff` for edited repos.
3. Check that no secrets, local-only clutter, or accidental transcript dumps
   were saved.
4. If shared toolkit workflows, rules, skills, or generated client surfaces were
   changed, run the toolkit validation and sync gates required by that repo.
5. If the user asks to update clients, regenerate the provider/client surfaces
   from the canonical toolkit selection and verify the generated diff.
6. If validation cannot run, state exactly what was not checked and why.

## Phase 5 - Portable Prompt

When the user wants a copyable prompt for another chat or machine, provide this:

```text
Run the context cleanup / context compaction workflow.

Use `workflows/context-compaction.md` if it exists in the current workspace or shared LLM toolkit. If it is not available, follow the same behavior manually.

Goal:
Preserve the useful context from this chat/workspace into durable LLM knowledge and reduce future context load, without saving secrets, noisy transcript content, or machine-specific paths unless they are discovered locally and necessary.

Steps:
1. Inspect the current workspace/repo context, including AGENTS/instructions, README, INTENTS, workflows, learnings, memory notes, repo-local LLM docs, and git status.
2. Discover where this project stores durable LLM knowledge.
3. Save only durable reusable context:
   - Project conventions.
   - Important decisions.
   - Current implementation/documentation/deployment status.
   - Source-of-truth docs, tickets, dashboards, pipelines, resources, and page IDs.
   - Validation commands and known-good workflows.
   - Gotchas, blockers, and proven fixes.
   - Environment rules, release boundaries, and manual-only steps.
4. Create a compact handoff summary future agents can use instead of rereading this whole chat.
5. Preserve unrelated existing edits. Append focused notes instead of rewriting large files.
6. Verify every edited file or memory note with read-back, status, and diff checks.
7. Report:
   - Files or memory locations updated.
   - Key compacted summary.
   - Validation/read-back performed.
   - Anything intentionally not committed, pushed, applied, or changed.
   - Remaining manual steps.
```

## Phase 6 - Report

Close with:

- files or memory locations updated;
- key compacted summary;
- validation and sync commands run;
- anything intentionally paused, not committed, not pushed, not applied, or not
  changed;
- remaining manual steps.
