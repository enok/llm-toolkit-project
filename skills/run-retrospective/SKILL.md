---
name: run-retrospective
description: Use when a non-trivial LLM or agent run (workflow, skill-driven task, orchestrated lane set, scheduled automation) ends and its mistakes must be classified by signature, recorded in the run log, promoted to learnings, checklists, guards, or rules, and measured over time; also use before starting a workflow to read its known pitfalls, or when asked about first-pass yield, recurring mistakes, or promotion candidates.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Run Retrospective

Tooling for the always-on loop in `rules/workflow-self-improvement.md`:
preflight -> capture -> retrospective + record -> promote -> verify -> measure.
The procedure is `workflows/run-retrospective.md`; this skill is the quick
start and the reference set.

## When to use

- **Before a run:** append any pending records (only when the log is durable), then list the workflow's
  known pitfalls and fold them into the plan and acceptance criteria
  (`preflight`).
- **After a non-trivial run:** 3+ steps, or any validator `fail`, tool error
  that forced another approach, user correction, or escaped defect. Look up
  existing signatures, classify, record, promote (`signatures`, `append`,
  `candidates`).
- **Periodic review:** trend per workflow, recurring signatures, and the
  promotion backlog (`summary`, `candidates`), as in the self-improvement
  review step of `workflows/toolkit-maintenance.md`.
- **Log hygiene:** check every stored record (`validate`).

One record per root run, written by the root/parent agent. Lanes, nested
workflows, and workflows invoked by the retrospective report
`mistake: <signature> - <one line>` instead.

## Quick start

Run from the toolkit root (use `py -3` on Windows when `python3` is not on
PATH). Every subcommand accepts `--log PATH` after the subcommand name.

Log location, first match wins:

1. `--log PATH`
2. environment variable `LLM_RUN_LOG`
3. `~/.llm-toolkit/run-log.jsonl` (user-level, cross-project, never committed;
   parent folders are created on first append)

```bash
S=skills/run-retrospective/scripts/run_retro.py
# [brackets] mark optional flags; the values shown are the defaults

# Before a run: ranked pitfalls (count, last seen, latest fix, prevented_by)
python3 $S preflight --workflow <name> [--limit 5] [--include-global]

# Before inventing a signature: every recorded one, all workflows, with count
# (distinct runs), workflows, last seen, highest promoted level
python3 $S signatures [--workflow <name>] [--json]

# After a run: validate + append one record (file or stdin); prints the run_id
python3 $S append --record run.json
python3 $S append --record - < run.json

# Signatures that need promotion, with the proposed next level
# (--threshold 1 also proposes `learning` for single occurrences)
python3 $S candidates [--threshold 2] [--json]

# Trend per workflow: FPY last vs previous window, correction/escape rates,
# rework, top recurring signatures with promoted level and ineffective flag
python3 $S summary [--workflow <name>] [--window 5] [--json]

# Check every stored line; prints "ok: N records" or "line N: <error>"
python3 $S validate
```

```powershell
$env:LLM_RUN_LOG = "<path>/run-log.jsonl"   # optional override of the default
py -3 skills/run-retrospective/scripts/run_retro.py preflight --workflow <name>
py -3 skills/run-retrospective/scripts/run_retro.py append --record run.json
```

In Windows PowerShell prefer `--record <file>` over piping into `--record -`:
piping text to a native command re-encodes it and can mangle non-ASCII
characters.

Exit codes: `0` ok, `1` validation failed (nothing appended), `2` usage or IO
error. A missing log is not an error: `validate` prints `ok: 0 records`,
`preflight` prints `no known pitfalls for <name>`, `candidates` prints
`no candidates`, `signatures` prints `no signatures recorded`. `validate` and
`append` may print non-fatal `warning:` lines on stderr for likely
under-reporting (exit code unchanged): resolve the warnings `append` prints for
this record, or explain in `notes`; `validate` repeats them per earlier line
(`warning: line N:`) as information only.

## Dry run (before promoting)

Validate and count a draft record without touching the real log: append it to
a fresh scratch copy, then ask for candidates against that copy.

```bash
S=skills/run-retrospective/scripts/run_retro.py
LOG="${LLM_RUN_LOG:-$HOME/.llm-toolkit/run-log.jsonl}"
rm -f <scratch>/retro-draft.jsonl; [ -f "$LOG" ] && cp "$LOG" <scratch>/retro-draft.jsonl
python3 $S append --log <scratch>/retro-draft.jsonl --record <scratch>/run.json
python3 $S candidates --log <scratch>/retro-draft.jsonl
```

```powershell
$log = if ($env:LLM_RUN_LOG) { $env:LLM_RUN_LOG } else { "$HOME/.llm-toolkit/run-log.jsonl" }
Remove-Item <scratch>/retro-draft.jsonl -ErrorAction Ignore; if (Test-Path $log) { Copy-Item $log <scratch>/retro-draft.jsonl }
py -3 skills/run-retrospective/scripts/run_retro.py append --log <scratch>/retro-draft.jsonl --record <scratch>/run.json
py -3 skills/run-retrospective/scripts/run_retro.py candidates --log <scratch>/retro-draft.jsonl
```

## Durable log and pending records

If the log is unreachable (exit 2) or not durable (ephemeral sandbox, CI
runner, a fresh scheduled session whose home is discarded), point
`--log`/`LLM_RUN_LOG` at a durable path, such as a mounted or connected folder
on the user's machine. Otherwise paste the final JSON under
`### Pending run records` in `CONTEXT_STATE.md` and include it in the final
report; an exit 0 into a discarded home is not a record. At the next preflight
whose log is durable, first append any `### Pending run records` from
`CONTEXT_STATE.md`, and delete each one once `append` prints its run_id (or
reports it already exists); in a discarded home leave them pending. Promotions
into committed assets never wait on the log.

## Record in one minute

One JSON object per run: `schema` 1, `date`, `workflow`, `outcome`, six
`metrics`, `mistakes` (signature, category, severity, source, summary, fix,
prevented_by), `promotions` (signature, level, asset). `workflow` is the
kebab name of the owning workflow (<= 80 chars). Signatures are
`<category>/<kebab-slug>`, at most once per record; reuse an existing one
(`signatures`) when the root cause matches.
Full field rules and a complete example: `references/run-record-schema.md`.

## Rules that keep the numbers honest

- Metrics are diagnostic only (Goodhart guard in
  `rules/workflow-self-improvement.md`). Under-reporting a mistake is itself a
  `validation-gap` mistake.
- Records stay generic; the script rejects emails, credential-like strings,
  key headers, and URLs with query strings. Names, hostnames, handles, and
  ticket IDs are not linted: keep them out yourself.
- A promotion counts only after it is verified: a guard must fail on the
  original mistake (`references/promotion-ladder.md`).

## References

- `references/run-record-schema.md` - fields, metric counting rules, validation, privacy lint, fallback storage.
- `references/mistake-taxonomy.md` - the eleven categories with examples, signature naming, severity, source.
- `references/promotion-ladder.md` - levels, triggers, landing places, `## Known pitfalls` convention, verification, metrics and trend reading.

## Related

- `workflows/run-retrospective.md` - the seven-phase per-run procedure.
- `workflows/self-improvement.md` - broader harvest across sessions.
- `rules/error-driven-learning.md` and `workflows/capture-learning.md` - the `learning` rung.
- `workflows/task-quality-loop.md` - per-task iterations, first-pass flags, defect lists.
