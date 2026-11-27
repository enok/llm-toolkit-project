---
name: assistant-workspace-cleanup
description: Inventory, classify, and safely clean up an AI-assistant workspace - regular chats, agent or Cowork sessions, projects, scheduled tasks (including fired one-shots), artifacts, and orchestration ledgers - behind a human approval gate grouped by reversibility, with ID allow-listed execution lanes and live-state verification. Use whenever the user asks to clean up, tidy, review, archive, delete, pause, or consolidate chats, sessions, projects, scheduled tasks, or artifacts; when a polling loop left fired one-shots, overlapping daily automations need merging, a task reports success but ran suspiciously fast, or a tasks ledger grew too large. Not for repo branches or files, or for editing one scheduled task.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.2.0"
---

# Assistant workspace cleanup

Reusable engine for tidying an assistant workspace that has accumulated chats,
agent sessions, scheduled tasks, and artifacts. The skill holds the procedure
and the safety contract. Everything specific to one owner (titles, names,
IDs, which items matter) lives only in that run's live inventory and plan,
never in this skill or in the toolkit.

- Run procedure: `workflows/assistant-workspace-cleanup.md` (five waves).
- Read `references/claude-surfaces.md` (tool-by-tool listing, archive, delete, pause notes) when a lane must list, archive, delete,
  or pause a given item type, or a tool behaves unexpectedly.
- Read `references/classification-rubric.md` when classifying, validating the
  plan, or building the approval groups.
- Read `references/lane-prompts.md` when dispatching a lane; it holds
  copy-ready prompts with tier, acceptance criteria, and return contract.
- Read-only classifier specialist: `tool-subagents/workspace-hygiene-auditor.md`.
- Browser-lane safety: `skills/assistant-workspace-cleanup/references/ui-automation-lane-safety.md` (read when dispatching any lane that drives a browser or desktop UI).
- Ledger compaction: `scripts/ledger_compact.py`.
- Learnings behind the rules: `learnings/scheduled-task-listing-hides-fired-one-shots.md`, `learnings/scheduled-task-create-cannot-set-model.md`, `learnings/short-succeeded-run-is-not-evidence-of-work.md`, `learnings/inventory-snapshot-goes-stale-before-destructive-steps.md`, `learnings/chat-history-tools-exclude-agent-sessions.md`, `learnings/many-daily-automations-exhaust-usage-limits.md`, `learnings/dirty-shared-checkout-use-a-worktree.md`, `learnings/cloud-session-device-bridge-file-io.md`.
- Related, not duplicated: `workflows/automation-maintenance.md` (edit one
  scheduled task), `workflows/task-quality-loop.md` (per-lane
  produce-validate-refine), `skills/chat-knowledge-curation/SKILL.md` (mine
  chats for toolkit assets before deleting them).

Hand off instead of using this skill for repository branches or files (`skills/git-conventions/SKILL.md`) and for editing one scheduled task (`workflows/automation-maintenance.md`).

## The five waves

| Wave | Work | Lane tier | Owner of writes |
| --- | --- | --- | --- |
| W1 Inventory | Parallel read-only listing of every surface, compact JSON out | light | none |
| W2 Classify | One classifier lane, then root validation against LIVE state | standard, then root | root |
| W3 Approval gate | Plan in its own plain message, then a multi-select question grouped by reversibility | root | root |
| W4 Execute | Approved groups in parallel lanes, each with an explicit ID allow-list | light (standard for prompt drafting) | lanes, within the list |
| W5 Verify | Re-read live state, run-duration sanity, ledger compaction, report | light, then root | root |

## Safety rules

Most of these are hard boundaries because workspace deletions are permanent
and the cost of a wrong guess falls on the owner, not on the agent.

1. **Approval is per group and per list.** Archive, delete, pause, create, and
   reconfigure only after the owner approved that group; a lane touches only
   IDs on its approved allow-list. This keeps a safe approval from covering a
   destructive step. If the owner edits a list, revalidate the edited rows. Run ledger
   compaction with `--dry-run` first and show what would move.
2. **Plan, then question.** Show the full plan in its own plain message, then
   ask the multi-select question in a separate turn, because text placed
   before a question widget may not be visible to the owner.
3. **Live state beats the snapshot.** Re-read live state when validating the
   plan and again right before each destructive or config step; drop any ID
   whose state changed and report it. Another session can change an item in
   the minutes between inventory and execution.
4. **Use stable IDs, not titles.** Duplicate and "Untitled" titles exist, so
   give every destructive lane the allow-list plus a deny-list of look-alikes.
5. **Reversible before irreversible.** With title-only evidence prefer KEEP or
   ARCHIVE over DELETE. Pause replaced scheduled tasks and delete them only
   after the replacement has proven itself.
6. **Do not sign in for the owner.** If a browser is not signed in, stop the
   browser lanes and ask which browser to use or ask the owner to sign in;
   credentials entry is the owner's act.
7. **Keep browser use tidy.** A lane closes only tabs it opened and reuses no
   other lane's tab, so concurrent lanes do not break each other. Tell each
   lane which lanes run concurrently and on what scope.
8. **Protect active items.** Leave the current session, pinned items, anything
   touched in the last 3 days, and live processes alone unless the owner
   approves that item explicitly; they are the ones likely to be in use.
9. **Models are the owner's call.** Creating a scheduled task has no model
   field, so it runs on the server default (often the costliest). Ask the
   model question inside the gate, and change an existing task's model only on
   explicit request.
10. **Treat status as a claim, not evidence.** A run marked successful but far
    shorter than its work needs is a finding: compare duration with expected
    work and open the run session.
11. **Delete artifacts one at a time** with the owner's confirmation each
    time, even after group approval, and keep that step with the root rather
    than an execution lane; artifact deletion cannot be undone.
12. **The root owns plan, approvals, ledger, and synthesis.** Lanes return the
    four-block contract (Outcome, Evidence, Blockers, Decisions; at most 40
    lines or 400 words) and surface a blocker within their stated time limit,
    so the root can re-plan instead of waiting.

## Model routing

| Work | Tier | Model (Claude Code) |
| --- | --- | --- |
| List/scan inventory, execution against a pre-approved ID list, verification | light | haiku, medium |
| Classification, consolidated-prompt drafting | standard | sonnet, medium |
| Plan validation against live state, approval gate, synthesis | root | session model |

Record on each root row why it stays at the root, normally "root owns
writes". Name the model for light work explicitly; an inherited expensive
model burns tokens silently. Keep the critical job (the approval gate, the
live-state re-read, the root's writes) apart from bulk jobs: bulk archive and
delete lanes run separately with their own allow-lists, so a long bulk run
does not delay or block the gate.

## Environment notes

- Do toolkit or ledger edits from a separate `git worktree` when the main
  checkout is dirty; never stash or touch another session's files.
- If a bridge shell shows unreadable folders or cannot delete, switch to the
  host's native shell instead of retrying (details in
  `references/claude-surfaces.md`).

## Outputs

Write in the run's scratch folder: `inventory/*.json` (compact), `plan.json`,
`approved.json`. Plan rows follow the schema in
`references/classification-rubric.md`. End with one report in this shape:

```
# Workspace cleanup report
## Counts per action   (archived / deleted / paused / consolidated / kept)
## Not done            (unselected groups, skipped changed items, with IDs)
## Follow-ups          (new tasks to prove, items to re-check)
## Blockers
## Elapsed time        (per wave)
```

Example: a polling loop left 40 fired, disabled one-shots with one name
pattern and one still-enabled sibling with a future run time. The plan puts
the 40 in group E (delete, fired one-shots) with a deny-list holding the live
sibling, flags `stale-risk` on the sibling, and defers that group until the
loop is confirmed stopped.
