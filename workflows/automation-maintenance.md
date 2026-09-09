---
description: Safely inspect, rename, update, or delete scheduled LLM-tool automations while preserving schedule, status, prompt, and thread binding
---

# Automation Maintenance Workflow

Use this when a user asks to create, rename, update, inspect, pause, resume, or
delete a scheduled automation in an LLM tool (for example a Codex automation or
an equivalent scheduled task).

For automations bound to a specific ticket after implementation is solved,
compose this workflow with `workflows/ticket-pr-validation-loop.md` so the
automation preserves its schedule/thread binding while the run logic validates
the ticket, PR comments, fixes, and CI/CD on the current head.

## Phase 1 - Identify the existing automation

1. Prefer the automation API for view/update/delete operations.
2. If the user refers to "this chat" or "same name as this chat", resolve the
   current thread name from the local session index before choosing a name.
3. Search existing automation records by ID, name, prompt, target thread, and
   schedule before creating a new automation.
4. Prefer updating the matching automation over creating a duplicate.

## Phase 2 - Preserve fields

When updating an existing automation, preserve every field the user did not ask
to change:

- kind and destination;
- schedule;
- status;
- model and reasoning effort;
- prompt;
- target thread;
- workspace and execution environment.

Do not hand-edit automation config files as the primary path. Use direct file
inspection only to identify the correct automation when the API does not expose
enough search context.

## Phase 3 - Mutate and verify

1. Use the automation API update/delete/create operation.
2. Re-read the saved automation after mutation.
3. Verify the intended fields changed and preserved fields stayed unchanged.
4. Report the automation ID, schedule, status, thread binding, and any changed
   fields.

## Failure handling

- If the requested automation cannot be uniquely identified, ask one concise
  clarifying question or list the conflicting candidates.
- If the API rejects the update, report the rejected field and leave the existing
  automation untouched.
- If a recurring task is obsolete, delete it and tell the user why the heartbeat
  stopped.

## Final Step - Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before
closing this workflow.
