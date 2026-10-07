# Run record schema (schema 1)

One JSON object per run, stored as one line in a JSON Lines log. The script
`skills/run-retrospective/scripts/run_retro.py` is the source of truth for validation; this page
explains the fields and how to fill them honestly.

## Storage

- Location: `--log PATH` > env `LLM_RUN_LOG` > `~/.llm-toolkit/run-log.jsonl`.
  User-level and cross-project: it accumulates runs from every repository and
  is **never committed**.
- Format: UTF-8, `\n` line endings, one object per line written with sorted
  keys; maximum line length 8 KiB. The record file given to `append` may be
  pretty-printed. Deeply nested, non-encodable, or oversized input is a
  validation error (exit 1), never a crash.
- Append-only: never rewrite or delete earlier lines to improve the numbers.
  A factual slip (a typo, a signature that should have reused an existing
  one) may be corrected in that one line, followed by `validate`.
- Writer: only the root/parent agent, one record per root run (nested
  workflows and lanes hand up `mistake:` lines instead).

## Top-level fields

| Field | Required | Rule |
| --- | --- | --- |
| `schema` | yes | integer `1` |
| `date` | yes | `YYYY-MM-DD`, the day the run ended |
| `workflow` | yes | kebab name of the outermost workflow or skill that owned the run, or `ad-hoc-<shape>` for unrouted work; `^[a-z0-9]+(-[a-z0-9]+)*$`, <= 80 chars. Prefer the routed primary workflow's name; reuse an existing `ad-hoc-*` name from `summary` instead of coining a new one |
| `outcome` | yes | `success`, `partial`, `failed`, `escalated`, or `abandoned` |
| `metrics` | yes | object with the six keys below |
| `mistakes` | yes | list, may be empty |
| `promotions` | yes | list, may be empty |
| `run_id` | no | kebab-case, <= 128 chars; generated as `<date>-<workflow>-<6 hex of sha1(canonical json)>` when absent; must be unique in the log |
| `agent` | no | the coordinating agent, e.g. `agent-orchestrator` |
| `task_shape` | no | <= 120 chars, generic description of the work |
| `notes` | no | <= 500 chars |

Unknown top-level keys are rejected.

## Metrics (all six required, non-negative integers)

| Key | Count | Constraint |
| --- | --- | --- |
| `tasks` | task-table rows; in a single-agent run, deliverables that had acceptance criteria | - |
| `first_pass` | tasks whose first validator verdict was `pass` and that were never reopened by a correction or an escaped defect | `first_pass <= tasks` |
| `iterations` | sum of quality-loop iterations used (the `used` part of each `Loop` cell); a task produced once counts 1 | `iterations >= tasks` when `tasks > 0` |
| `user_corrections` | user messages that corrected output or an assumption; new or changed requirements are not corrections | - |
| `escaped_defects` | defects found by `ci`, `user`, or `post-release` after the task was marked done | - |
| `tool_errors` | tool errors that forced a different approach; identical retries after a transient blip do not count | - |

## Mistake object

| Field | Rule |
| --- | --- |
| `signature` | `<category>/<kebab-slug>`, `^[a-z-]+/[a-z0-9]+(-[a-z0-9]+)*$`, <= 80 chars (naming: `mistake-taxonomy.md`) |
| `category` | must equal the signature prefix; one of the eleven categories |
| `severity` | `low`, `medium`, `high`, or `critical` |
| `source` | `self-review`, `validator`, `ci`, `user`, `tool-error`, or `post-release` |
| `summary` | <= 200 chars: what went wrong, generic |
| `fix` | <= 200 chars: what fixed it in this run; empty string when unfixed |
| `prevented_by` | repo-relative path of the asset that prevents recurrence (existing, or created by this run's promotion), or `null` |

One entry per distinct root cause in the run: list each signature at most
once per record and merge its symptoms into that entry. A duplicate signature
in one record is a validation error.

## Promotion object

| Field | Rule |
| --- | --- |
| `signature` | the signature promoted (normally one of this run's mistakes; a maintenance run may promote a signature recorded earlier) |
| `level` | `learning`, `checklist`, `guard`, or `rule` |
| `asset` | repo-relative path of the landed asset; no `..`, no leading `/`, no drive letter |

Record only promotions that landed and were verified in this run
(`promotion-ladder.md`). Deferred promotions are left out; `candidates` keeps
proposing them. When a mistake recurred although its prevention already
existed but was never recorded, backfill that prevention here at its actual
level, next to the higher level this run lands.

## Under-reporting warnings

`validate` and `append` print non-fatal `warning:` lines on stderr (exit code
unchanged) when a record looks under-reported:

- `escaped_defects > 0` but no mistake has source `ci`, `user`, or
  `post-release`;
- `user_corrections > 0` but no mistake has source `user`;
- `first_pass < tasks` or `tool_errors > 0` while `mistakes` is empty.

Resolve each warning by recording the missing mistake, or explain in `notes`
why the numbers are right (for example a tool error already covered by
another entry's root cause). Never adjust metrics to silence a warning.

## Privacy lint

Any string value that looks like an email address, a cloud access-key ID, a
GitHub or Slack token, a PEM key header, a `password=` / `secret:` / `token=`
style assignment, or a URL containing `?` fails validation. The exact patterns
live in the script. Beyond the lint, keep records free of personal names,
hostnames, account handles, ticket IDs, and project or client names: describe
the mechanism, not the incident.

## Lane return line

Lanes do not write records. They report each self-detected mistake in the
Decisions block of the 4-block return:

```text
mistake: tool-misuse/shell-quoting-breaks-inline-json-filter - inline filter split into several args; switched to native JSON parsing
```

The root adds them to the record, reusing or correcting the signature.

## Durable log and fallback storage

If the log is unreachable (exit 2) or not durable (ephemeral sandbox, CI
runner, a fresh scheduled session whose home is discarded), point
`--log`/`LLM_RUN_LOG` at a durable path, such as a mounted or connected folder
on the user's machine. Otherwise paste the final JSON into the session ledger
and include it in the final report; an exit 0 into a discarded home is not a
record. The next run with a durable log first appends each pending record and
deletes it once `append` prints its run_id (or reports it already exists):

```markdown
### Pending run records

    {"schema": 1, "date": "2026-10-07", "workflow": "ad-hoc-doc-update", ...}
```

## Minimal valid record

```json
{"schema": 1, "date": "2026-10-07", "workflow": "ad-hoc-doc-update",
 "outcome": "success",
 "metrics": {"tasks": 3, "first_pass": 2, "iterations": 4,
             "user_corrections": 0, "escaped_defects": 0, "tool_errors": 1},
 "mistakes": [{"signature": "wrong-assumption/doc-link-target-not-verified",
               "category": "wrong-assumption", "severity": "low",
               "source": "validator",
               "summary": "linked a section heading that had been renamed",
               "fix": "resolved the anchor from the current file before linking",
               "prevented_by": null}],
 "promotions": []}
```

## Complete record

A run that landed a `learning` for a platform quirk and a `guard` for a
high-severity escaped defect:

```json
{"schema": 1,
 "date": "2026-10-07",
 "workflow": "study-repo-to-publication",
 "agent": "agent-orchestrator",
 "task_shape": "multi-language study repo + article + social post",
 "outcome": "success",
 "metrics": {"tasks": 12, "first_pass": 9, "iterations": 17,
             "user_corrections": 2, "escaped_defects": 1, "tool_errors": 5},
 "mistakes": [
   {"signature": "platform-quirk/editor-paste-splits-code-block-at-blank-line",
    "category": "platform-quirk", "severity": "medium", "source": "self-review",
    "summary": "blank lines inside pre split one code listing into several boxes after paste",
    "fix": "replace blank lines inside pre with a single space before paste",
    "prevented_by": "learnings/medium-paste-splits-code-blocks-at-blank-lines.md"},
   {"signature": "validation-gap/rendered-html-not-scanned-for-markdown",
    "category": "validation-gap", "severity": "high", "source": "user",
    "summary": "literal markdown markers reached the draft; the validator only checked the source",
    "fix": "validator scans the rendered HTML for leftover markdown tokens",
    "prevented_by": "skills/medium-publishing/scripts/medium_paste_html.py"}],
 "promotions": [
   {"signature": "platform-quirk/editor-paste-splits-code-block-at-blank-line",
    "level": "learning", "asset": "learnings/medium-paste-splits-code-blocks-at-blank-lines.md"},
   {"signature": "validation-gap/rendered-html-not-scanned-for-markdown",
    "level": "guard", "asset": "skills/medium-publishing/scripts/medium_paste_html.py"}],
 "notes": "escape: the leftover markdown was found by the user after the draft was marked ready"}
```
