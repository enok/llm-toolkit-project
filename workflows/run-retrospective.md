---
description: Per-run retrospective for any LLM or agent workflow - collect mistake signals, classify them by signature, find the missing guard, record the run, promote recurring lessons up the ladder, verify the promotion, and report trend metrics
---

# Run Retrospective

The per-run entry point of the loop required by `rules/workflow-self-improvement.md`. Run it at the end of every non-trivial workflow run, skill-driven task, orchestrated lane set, or scheduled/automated run: after the last validator verdict, before the final report. For the broader harvest (subagent evidence, new capabilities, external skills) continue with Phase 1 of `workflows/self-improvement.md`.

**One record per root run:** the outermost workflow, or the orchestrator root, runs this retrospective once, at its very end, under the outermost (routed primary) workflow's name, never the agent's name. A nested workflow's `Final Step — Self-improvement`, a lane, and any workflow invoked by this retrospective (`capture-learning`, `toolkit-maintenance`) skip `workflows/self-improvement.md` entirely (its Phase 0 retrospective and the harvest) and hand their signals up as `mistake:` lines; the root's single pass covers them.

- **Trivial run** (fewer than 3 steps, zero signals): no record; say "no retrospective signals" and stop.
- **Clean run** (3+ steps, zero signals): skip Phases 2-3 and 5-6 and the dry run; append a record with empty `mistakes` and `promotions` and print the metrics line. Recording clean runs keeps FPY honest.

Script: `skills/run-retrospective/scripts/run_retro.py` (Python 3.9+, stdlib only). Commands, log location, and the copy-paste dry run: `skills/run-retrospective/SKILL.md`.

## Phase 1 - Collect signals

Gather every signal of this run from evidence, not memory:

| Source | Where to find it | `source` value |
| --- | --- | --- |
| Validator verdicts, defect lists, iteration counts | verdict history (`workflows/task-quality-loop.md`), tasks table `Loop` / Evidence | `validator` |
| Tool errors that forced another approach | session ledger (`CONTEXT_STATE.md`) | `tool-error` |
| User corrections | the conversation | `user` |
| CI failures | CI run logs (see also `rules/ci-feedback-loop.md`) | `ci` |
| Post-release findings | reviews, monitoring, follow-ups | `post-release` |
| Lane and nested-workflow `mistake: <signature> - <line>` reports | Decisions blocks, nested final steps | as reported |
| Tier escalations | tasks-table rows with an escalation trigger | `validator` |
| Self-detected misses | your own review of the result | `self-review` |

Count the six metrics (`tasks`, `first_pass`, `iterations`, `user_corrections`, `escaped_defects`, `tool_errors`) while collecting, per the counting rules in `skills/run-retrospective/references/run-record-schema.md`; a task later reopened is not first-pass.

## Phase 2 - Classify

For each distinct root cause (several symptoms of one cause are one mistake; each signature appears at most once per record):

1. **Category** from the closed set of eleven in `skills/run-retrospective/references/mistake-taxonomy.md`.
2. **Signature** `<category>/<kebab-slug>`, naming the mechanism, not the symptom or the project. Before inventing one, list every recorded signature with `run_retro.py signatures` (all workflows, with counts and highest promoted level); when one has the same root cause, copy it exactly, because recurrence counting depends on stable signatures. `preflight` and `summary` show only recurring or top signatures, so they are not a substitute.
3. **Severity** `low | medium | high | critical` (guidance in the taxonomy). `high`, `critical`, and every `safety-near-miss` are promoted to a guard at first occurrence.
4. **Source** from the table above. A mistake is an **escaped defect** when its source is `ci`, `user`, or `post-release` and the task was already marked done; count it in `escaped_defects`.

## Phase 3 - Root cause

Answer two questions per mistake, each in one line:

1. **Why did it happen?** The mechanism (wrong flag, unverified belief, platform behaviour, missing criterion).
2. **Why was it not caught earlier?** Which preflight item, acceptance criterion, validator, or test should have stopped it. The second answer usually names the missing guard and becomes the promotion target.

Write the fix applied in this run to `fix`. Set `prevented_by` to the asset that prevents recurrence: the existing one that should have caught it, the one this run's promotion creates, or `null` when none exists yet. If the mistake happened although its `prevented_by` asset already existed, that prevention was ineffective: climb one level in Phase 5. When that existing prevention was never recorded in the log, backfill it in this record's `promotions` at its actual level (for example `learning` for a `learnings/` file), and also record the higher level you land.

## Phase 4 - Record (draft and dry run)

Build the record as one JSON object in a scratch file outside the repository (pretty-printing is fine; the script writes one line). Keep summaries generic (privacy rules in the schema reference).

```json
{"schema": 1, "date": "2026-10-07", "workflow": "study-repo-to-publication",
 "agent": "agent-orchestrator", "outcome": "success",
 "metrics": {"tasks": 12, "first_pass": 9, "iterations": 17,
             "user_corrections": 2, "escaped_defects": 1, "tool_errors": 5},
 "mistakes": [
   {"signature": "validation-gap/rendered-html-not-scanned-for-markdown",
    "category": "validation-gap", "severity": "high", "source": "user",
    "summary": "literal markdown markers reached the draft; the validator only checked the source",
    "fix": "validator scans the rendered HTML for leftover markdown tokens",
    "prevented_by": "skills/medium-publishing/scripts/medium_paste_html.py"}],
 "promotions": [
   {"signature": "validation-gap/rendered-html-not-scanned-for-markdown",
    "level": "guard", "asset": "skills/medium-publishing/scripts/medium_paste_html.py"}]}
```

The example shows the final state (a fuller one is in the schema reference); in the draft leave `promotions` empty. Dry-run the draft with `append --log <scratch>/retro-draft.jsonl` against a fresh scratch copy of the log (commands in the SKILL.md "Dry run" section): this validates the record (schema, privacy lint, run_id uniqueness) and counts it without touching the real log. Exit 1 prints the failing field; fix and repeat (nothing was written). `warning:` lines on stderr flag likely under-reporting: resolve the warnings `append` prints for this record, or explain in `notes`; `validate` repeats them per earlier line (`warning: line N:`) as information only.

## Phase 5 - Promote

Run `run_retro.py candidates --log <scratch>/retro-draft.jsonl`. It lists each signature needing promotion with the proposed level, counting this run: a count-based rung (`checklist` at 2 runs, `guard` at 3+) is proposed while the signature is not yet promoted to that level or above, so a deferral or a skipped rung keeps showing. Add `learning` yourself when a fix took trial and error. Land each promotion at the smallest durable surface (details: `skills/run-retrospective/references/promotion-ladder.md`):

| Level | Lands in | Through |
| --- | --- | --- |
| `learning` | `learnings/<name>.md` + `learnings/INDEX.md` line + a link from the owning asset | `workflows/capture-learning.md` |
| `checklist` | one bullet in the owning workflow's or skill's `## Known pitfalls` section ending `(sig: <signature>)`, or a preflight/acceptance criterion | direct edit of the owning asset |
| `guard` | script, validator, test, CI gate, or lint that fails on the original mistake | the owning skill or script plus its tests |
| `rule` | a `rules/` change, or human escalation when redesign is needed | `workflows/toolkit-maintenance.md` |

Routing extras:

- **Agent-attributable** (a specialist's recurring miss): also update `workflows/<agent>-evolution.md`, for example `workflows/agent-orchestrator-evolution.md`, or `workflows/specialist-agent-evolution.md` when no agent-specific one exists.
- **`tier-misassignment`**: correct the task-type row in the lookup table of `rules/request-orchestration.md` or the guidance in `tool-subagents/model-selector.md` (via `workflows/model-selector-evolution.md`).
- **Ineffective prevention** (recurrence after the earliest run that recorded the signature's highest promoted level): promote one level above that highest level; never re-promote at the same level.

Workflows invoked here (`capture-learning`, `toolkit-maintenance`) skip their own retrospective and hand signals back to this one. Add each landed promotion to the record's `promotions` list (`signature`, `level`, `asset`). A promotion you cannot land in this run stays out of the list; `candidates` keeps proposing it until a later run records it. Name each deferral in the final report.

## Phase 6 - Verify the promotion, then append

1. **Guard:** add a regression fixture that reproduces the original mistake (for example under `tests/fixtures/<name>/`) and a test asserting the guard fails on it and passes on the fixed output. Run the test; cite command and exit code. Without a failing-first test it is not a guard: record the level that actually landed, or defer it.
2. **Checklist:** the bullet is an imperative check, sits in `## Known pitfalls`, and ends with `(sig: <signature>)`; workflows stay within the size limit in `rules/workflow-authoring.md`.
3. **Learning:** passes the quality check and approval gate of `workflows/capture-learning.md`, and the owning asset links the file (`tests/test_learning_promotion_coverage.py`).
4. **Rule:** passes the validation phase of `workflows/toolkit-maintenance.md`.

Then append the final record to the real log and confirm the log is valid:

```bash
python3 skills/run-retrospective/scripts/run_retro.py append --record <scratch>/run.json
python3 skills/run-retrospective/scripts/run_retro.py validate
```

`append` prints the run_id. If the log is unreachable (exit 2) or not durable (ephemeral sandbox, CI runner, a fresh scheduled session whose home is discarded), point `--log`/`LLM_RUN_LOG` at a durable path, such as a mounted or connected folder on the user's machine. Otherwise paste the final JSON under `### Pending run records` in `CONTEXT_STATE.md` and include it in the final report. An exit 0 into a discarded home is not a record. The next run with a durable log appends pending records first; committed promotions never wait on the log.

## Phase 7 - Measure and report

Run `run_retro.py summary --workflow <name>` and `run_retro.py candidates`.

- Read the trend as last window vs previous window (default 5 runs): FPY rising, correction and escape rates falling means the loop works. How to read noisy or contradictory trends: `skills/run-retrospective/references/promotion-ladder.md`.
- A signature flagged ineffective means its prevention failed: climb one level now or name it as a deferral.
- `candidates` on the real log should list none of this run's signatures except the deferrals named above. Older entries are backlog: land them only if in scope; otherwise leave them for `toolkit-maintenance`.

End the final report with the metrics line from `rules/workflow-self-improvement.md`:

```text
Self-improvement: FPY 9/12, corrections 2, escapes 1, promotions 1, recurrences 0
```

`recurrences` counts this run's signatures that were already in the log before this run. Metrics are diagnostic only; the Goodhart guard in the rule is mandatory.
