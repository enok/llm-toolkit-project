# Promotion ladder

A lesson climbs from cheap, passive storage toward enforcement each time the
previous level failed to prevent it. The aim is that a mistake costs the
toolkit at most a few occurrences, then becomes impossible to repeat silently.

## Levels

| Level | Trigger | Lands in | Done when |
| --- | --- | --- | --- |
| record | 1st occurrence, `low`/`medium` | the run log only | the record validates |
| `learning` | 1st win that took trial and error | `learnings/<name>.md` + one `learnings/INDEX.md` line + a link to it from the owning asset, via `workflows/capture-learning.md` | quality check and approval gate passed; `tests/test_learning_promotion_coverage.py` passes |
| `checklist` | 2nd run with the signature, not yet promoted to `checklist` or above | one bullet in the owning workflow's or skill's `## Known pitfalls` section, or a preflight / acceptance criterion | bullet present with `(sig: ...)` suffix |
| `guard` | 3rd+ run with the signature, recurrence after a checklist, or any `high` / `critical` / `safety-near-miss`, not yet promoted to `guard` or above | an executable check: script, validator, test, CI gate, lint | the check fails on the original mistake and passes on the fix |
| `rule` | recurrence after a guard, or one pattern seen in 3+ workflows | a `rules/` change through `workflows/toolkit-maintenance.md`, or human escalation when redesign is needed | maintenance validation passed |

`run_retro.py candidates` proposes `checklist`, `guard`, and `rule` from the
log; counts are distinct runs. A count-based rung (`checklist` at 2, `guard`
at 3+) is proposed while the signature is not yet promoted to that level or
above, so a recorded `learning` does not hide a due checklist, and a deferral
keeps showing until a later run records it. `--threshold 1` also proposes
`learning` for single occurrences; otherwise `learning` is decided by the
trial-and-error triggers in `rules/error-driven-learning.md`. Levels can be
skipped upward (a `critical` mistake goes straight to `guard`), never
downward.

**Ineffective prevention:** the signature recurs in a run ordered after the
earliest run that recorded its highest promoted level. Order is ISO date, then
log position, so a later run on the same day counts. A promotion to a higher
level resets the flag until that level fails too. The next promotion is one
level above the highest recorded one (`learning` -> `checklist` -> `guard` ->
`rule`). Never re-promote at the same level.

**Prevention older than the log:** when a mistake recurs although an asset
already prevented it but no record names that promotion, backfill it in this
run's `promotions` at its actual level (for example `learning` for a
`learnings/` file), and also record the higher level you land.

## Routing beyond the owning asset

- **Agent-attributable** (a specialist subagent's recurring miss): also feed
  `workflows/<agent>-evolution.md` (for example
  `workflows/agent-orchestrator-evolution.md`) or
  `workflows/specialist-agent-evolution.md`.
- **`tier-misassignment`**: correct the task-type row of the lookup table in
  `rules/request-orchestration.md` or the `tool-subagents/model-selector.md`
  guidance, via `workflows/model-selector-evolution.md`.
- **CI-detected**: `rules/ci-feedback-loop.md` already demands a prevention
  step; the ladder decides how strong it must be.
- **Project-specific facts** stay in the consumer repo's `docs/llm/`; only
  the generic mechanism is promoted into shared assets.

## The `## Known pitfalls` convention

Checklist promotions live in a section named exactly `## Known pitfalls`,
placed near the end of the owning workflow, `SKILL.md`, or agent definition
(`tool-subagents/<name>.md`, mirrored in its `.toml`), before any "Final Step"
or "Related" section. One bullet per signature:

```markdown
## Known pitfalls

- Replace blank lines inside preformatted blocks with a single space before
  pasting into the editor, then check one code box per listing.
  (sig: platform-quirk/editor-paste-splits-code-block-at-blank-line)
```

- Imperative and checkable: say what to do or verify, not what went wrong.
- The suffix `(sig: <signature>)` is mandatory so recurrence stays traceable
  between the asset and the log.
- A bullet that carries a learning with no run-log signature ends with
  `See learnings/<slug>.md.` instead of the suffix;
  `tests/test_learning_promotion_coverage.py` checks that every learning has such
  a link.
- Preflight reads this section; the orchestrator turns relevant bullets into
  acceptance criteria.
- When a guard lands for the signature, replace the bullet's text with a
  pointer to the guard and keep the suffix, e.g.
  `- Enforced by <script path>. (sig: ...)`.
- Workflow bullets count toward the 12,000-character limit in
  `rules/workflow-authoring.md`. A crowded section is a signal to promote its
  oldest bullets to guards, not to drop them.

## Verification requirement

A promotion is recorded only after it is verified in the same run:

- **guard:** a regression fixture that reproduces the original mistake (for
  example under `tests/fixtures/<name>/`) plus a test asserting the guard
  fails on the fixture and passes on the corrected output. Cite the test
  command and exit code. A check that never failed on the real mistake proves
  nothing.
- **checklist:** bullet present, imperative, suffixed, and the owning file
  still passes its size and index checks.
- **learning:** `workflows/capture-learning.md` quality check and approval, and the owning asset links the file (`tests/test_learning_promotion_coverage.py`).
- **rule:** `workflows/toolkit-maintenance.md` validation phase.

An unverified promotion is a deferral: leave it out of `promotions` and name
it in the final report; `candidates` keeps proposing it.

## Metrics

Computed per workflow by `run_retro.py summary` over a sliding window
(default 5 runs), last window vs the previous one:

| Metric | Definition | Healthy trend |
| --- | --- | --- |
| First-pass yield (FPY) | sum(`first_pass`) / sum(`tasks`) | rising |
| Correction rate | `user_corrections` per run | falling |
| Escape rate | `escaped_defects` per run | falling |
| Rework | (`iterations` - `tasks`) / `tasks` | falling |
| Recurrence | signatures seen in 2+ runs | falling count of unpromoted ones |
| Ineffective prevention | recurrence after the earliest run that recorded the highest promoted level | zero |

The per-run report line (`rules/workflow-self-improvement.md`) carries this
run's FPY, corrections, escapes, promotions landed, and recurrences (this
run's signatures already present in the log).

## Reading trends

- Fewer than 3 runs in a window is noise; report the numbers without a
  verdict.
- Compare a workflow with its own history, not with other workflows; task
  shapes differ.
- FPY rising while escapes also rise means validators are passing work they
  should not: audit the validators before celebrating (Goodhart signal).
- FPY dropping right after a new guard landed can be the guard catching real
  defects; a falling escape rate confirms it.
- Correction rate flat while FPY rises suggests acceptance criteria miss what
  the user cares about: look for `spec-gap` signatures.
- Any ineffective-prevention flag outranks every trend: climb the ladder for
  that signature first.
- Metrics are diagnostic only. Never tune work, validators, or reporting to
  move them (the Goodhart guard in `rules/workflow-self-improvement.md` is
  mandatory).
