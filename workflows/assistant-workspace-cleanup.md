---
description: Inventory, classify, approve, execute, and verify a cleanup of an AI-assistant workspace (chats, agent sessions, projects, scheduled tasks, artifacts, orchestration ledgers) with a reversibility-grouped approval gate, ID allow-listed lanes, and live-state verification
---

# Assistant Workspace Cleanup Workflow

Use this when asked to clean up, review, archive, delete, pause, or
consolidate chats, agent sessions, projects, scheduled tasks, or artifacts
("tidy my workspace", "delete the fired one-shots", "merge my daily tasks").
Capability: `skills/assistant-workspace-cleanup/SKILL.md`. Where each item
type lives and its gotchas: `skills/assistant-workspace-cleanup/references/claude-surfaces.md`.
Row actions, keep-rules, and approval groups:
`skills/assistant-workspace-cleanup/references/classification-rubric.md`.
Dispatch prompts: `skills/assistant-workspace-cleanup/references/lane-prompts.md`
(lane names L1-L9 below).

Not for editing a single scheduled task (`workflows/automation-maintenance.md`)
or mining chats for toolkit assets (`skills/chat-knowledge-curation/SKILL.md`).

Contract: nothing changes before the owner approves that group; lanes touch
only IDs on an explicit allow-list; live state is re-read before every
destructive or config step; the root owns the plan, the gate, the ledger, and
the report. Personal details (titles, names, IDs) stay in the run's scratch
files, never in the toolkit.

`<scratch>` is a run folder outside the repository, with `inventory/`,
`results/`, `plan.json`, and `approved.json`.

---

## Phase 0 - Orchestrate and prepare

1. Load `rules/request-orchestration.md` and
   `tool-subagents/agent-orchestrator.md`. Print the tasks table (lane, tier,
   explicit model/effort, wave, validator, status) from the lane table in
   `lane-prompts.md`. Record the start time.
2. Load `rules/ui-automation-lane-safety.md` before any browser lane. If it
   is unreadable, apply the skill's browser-hygiene rule and say so.
3. Scope: default to all five item types; ask only when the request is
   ambiguous. Note the current session ID and any concurrent sessions (they
   are protected).
4. Pre-flight (read-only): is a signed-in browser available, and are the
   trigger and Artifact tools reachable? Never sign in for the owner. If the
   in-app browser redirects to login, ask which browser to use or ask the
   owner to sign in. Browser-less lanes (L1 tools, L3, L7) continue; browser
   lanes wait.
5. If the toolkit or ledger repository checkout is dirty with another
   session's edits, work in a separate `git worktree` from the remote main
   branch. Never stash or touch those files.

## W1 - Inventory (parallel, read-only)

Dispatch in one wave, each with its own model and the shared blocks
(return contract, blocker time limit, concurrency note):

- L1 chats, projects, artifacts (chat-history tools plus Artifact `list`).
- L2 agent sessions via browser (Recents Active and Archived, project pages).
  Chat-history tools never list them.
- L3 scheduled tasks to compact JSON with `include_completed=true`.

Root reduce: counts match each source's own totals; unreadable items are
listed; no lane changed state (tabs it did not open are still open). A lane
that fails validation gets one corrective re-dispatch (light budget 1).

## W2 - Classify and validate against LIVE state

1. Dispatch L4 (standard tier), or the read-only
   `tool-subagents/workspace-hygiene-auditor.md`, on the inventory files and
   the rubric. It writes `<scratch>/plan.json`.
2. Root validation, before anything is shown to the owner:
   - re-read live state for every non-KEEP row and every scheduled task; the
     snapshot may be minutes old and another session may have changed it;
   - re-read sessions touched since the snapshot and apply the keep-rules;
   - resolve duplicate and "Untitled" titles by ID, and build each lane's
     deny-list of look-alikes;
   - run-duration sanity on recurring tasks: compare `last_run` duration to
     the work the prompt requires (a nightly browser-and-file job that
     "succeeds" in seconds is a finding); open the run session before
     recommending;
   - detect overlap: several recurring tasks with similar purpose or
     back-to-back schedules are CONSOLIDATE candidates;
   - override rows that break the rubric; record "n of N overridden".
3. Plan rows get `group` letters per the rubric. Low-confidence rows are
   never DELETE.

## W3 - Approval gate (root)

1. Post the full plan in its own plain message: per group the count and the
   rows (title as shown, short ID, action, reason, confidence), what is kept
   and why, overrides, risks, and the expected duration. Do not combine it
   with the question; text placed before a question widget may not be shown.
2. In a separate turn ask a multi-select question, one option per
   reversibility group (A archive and ledger compaction; B pause; C new or
   changed scheduled tasks; D delete chats and sessions; E delete fired
   one-shots; F delete artifacts; G optional deletes). Nothing is
   pre-selected; skip empty groups.
3. Model choice for any new scheduled task is asked here, not later:
   creation has no model field and falls back to the server default, which
   may be costly. Offer: keep the default, or set a named model after
   creation. Change an existing task's model only if the owner picks that.
4. Write `<scratch>/approved.json` with exact IDs per approved group. The
   owner may edit lists; revalidate edited rows. Unselected groups are
   reported as "not done".

## W4 - Execute approved groups (parallel lanes)

Per group, first re-read live state for that group's IDs and drop any whose
state changed (re-enabled, renamed, new activity, missing). Then dispatch
with explicit allow-list, deny-list, and the concurrency note naming the
other running lanes and their scope:

| Group | Lane | Notes |
| --- | --- | --- |
| A | L5 archive by ID list (browser); root runs ledger compaction | match by URL uuid, never title |
| B | root `update_trigger` enabled=false | reversible |
| C | L8 drafts the combined prompt; root creates the task, then pauses the originals | pause only after the new task exists; do not delete originals yet |
| D | L6 delete chats by ID list (browser) | confirm "Untitled" chats are empty; not pinned |
| E | L7 delete fired one-shots | require enabled=false and ended_reason on a fresh read |
| F | root, one artifact at a time | owner confirms each deletion |
| G | same lane as D, only approved rows | |

Rules: two browser lanes in the same browser profile are either serialized or
told about each other; run reversible groups before irreversible ones when
they touch the same surface; a lane that cannot match an ID skips it and
reports, and never searches by title. Failed IDs get one targeted retry by the
root, not a repeat of the whole list. A lane past twice its typical duration
reports instead of grinding (blocker limits in the lane table).

## W5 - Verify, compact the ledger, report

1. Dispatch L9 on live state. Pass criteria: every approved ID in its target
   state, nothing outside the lists changed (counts differ by exactly the
   approved deltas), the new task exists with the expected schedule, paused
   tasks show enabled=false, and run-duration sanity holds for every
   enabled recurring task including the new one. Fix or report each failure.
2. Ledger compaction (group A). Use the native shell if the bridge shell
   shows unreadable folders. Always dry-run first, show the sections that
   would move, then run it for real:

   ```text
   python scripts/ledger_compact.py --root <dir> --keep <current-session> --dry-run
   python scripts/ledger_compact.py --root <dir> --keep <current-session> [--date YYYY-MM-DD]
   ```

   It archives sections whose remaining-count row is 0 (never by header
   wording), keeps the sections named with `--keep`, appends to the archive
   file, and excludes the archive folder from git.
3. Update the run ledger rows (tasks table and context state per
   `tool-subagents/agent-orchestrator.md`): per lane outcome, evidence, and
   the exact resume action for anything not done.
4. Final report, one message: counts per action and per type, what was kept
   or left unsure, groups not approved, validation overrides, follow-ups
   (delete paused originals after the replacement has run well; remove any
   remaining fired one-shots when a polling loop ends), blockers, elapsed
   time, and the lane table with actual versus typical durations.

Every lane used `workflows/task-quality-loop.md` semantics: acceptance
criteria written before dispatch; light lanes budget 1; max 5 iterations
otherwise.

## Failure handling

| Situation | Action |
| --- | --- |
| Browser redirects to login | Stop browser lanes; ask which browser or ask the owner to sign in; never sign in |
| Lane reports items vanishing | Another lane was not named in its dispatch; add the concurrency note and re-run only that lane |
| ID missing or title differs at execution | Skip and report; never search by title |
| Task state changed since the snapshot | Drop from the lane's list; revalidate and ask again if the action is destructive |
| Bridge shell shows unreadable folders or cannot delete | Switch to the native shell; do not retry in the bridge |
| Lane return over 40 lines or 400 words | One-shot reduction to the four blocks; record the defect |
| Artifact deletion not confirmed | Leave it and report |
| Only chat-history tools available | Treat the inventory as partial: agent sessions and fired one-shots are invisible to them |
