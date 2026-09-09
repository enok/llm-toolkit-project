---
name: cross-env-data-copy
description: Copy a single record from a source environment (for example production) into a target environment (for example stage or dev) to reproduce a bug or seed a test fixture, with a read-only source fetch, an idempotent MERGE/upsert preview, and mandatory human confirmation before any write. Use when the user asks to "copy a row from prod to stage," "seed stage with a production record," "prep an environment for testing," "replicate one record across environments," or "pull one row down from production." Not for bulk data loads, schema migrations, or multi-row syncs.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.0.0"
---

# Cross-Environment Data Copy

Automate the common one-off runbook of pulling a single record from an
upstream environment (typically production) and loading it into a
downstream environment (typically stage or dev) so a report, job, feature,
or bug can be tested against production-shaped data - without ever writing
to the source, and without ever writing to the target without an explicit,
in-conversation human confirmation.

This skill holds the *method* only. The source/target environment names,
the table or collection, the key columns, and the row selector all come
from the user's request or a documented runbook in the consumer repo (for
example its `docs/llm/`, or a project-specific `docs/` page) - never
hardcoded here.

## When To Apply

- The user wants to copy, seed, or replicate **one** record from one
  environment to another (prod -> stage, stage -> dev, etc.) so a feature,
  report, or scheduled job can be exercised against realistic data.
- The user wants to reproduce a production bug in a lower environment using
  a real row.
- The user needs a single fixture row in a lower environment to unblock
  manual or automated testing.
- **Not** for bulk data loads, schema migrations, backfills, or multi-row
  syncs - this skill is intentionally single-row and narrow-scope. For
  anything wider, treat it as a data migration and get it reviewed like one
  (see `rules/external-write-authorization.md`).

## Prerequisites (check before running)

1. **Credentials come only from a local config file, never from chat.**
   Use a per-tool convention such as `~/.config/<tool>/db-connections.json`
   (check whether the project already has an established credentials-file
   convention and reuse it instead of inventing a new one). The file should
   hold one entry per named environment (connection string/host, user,
   password or secret reference), must never be committed to git, and
   should be created with restrictive permissions (`chmod 600` on
   Linux/macOS). If the file is missing or still holds placeholder values,
   stop and ask the user to fill it in themselves - never ask the user to
   paste credentials into the chat, and never write a credential into a
   script, log, or commit.
2. **Reachability.** Confirm the machine can reach both the source and
   target endpoints (VPN, SSH tunnel, IP allowlist, security group, or
   equivalent). Run a lightweight connectivity/auth check against both
   environments before the real fetch - see the connection-test step in
   `references/merge-preview-pattern.md`. If it fails, tell the user to
   check VPN/tunnel/allowlist status rather than retrying blindly.
3. **Confirm scope.** Make sure the table/collection, the key column(s),
   and the row selector (the filter that picks exactly one row) are known -
   from the user's request or a documented runbook. If any of these is
   ambiguous, ask; never guess which row to copy.

## Parameters

Every value below is supplied by the request or a project runbook - none of
them are hardcoded in this skill.

| Parameter | Meaning |
|-----------|---------|
| Source env | Name of the environment to read from (for example `prod`) |
| Target env | Name of the environment to write to (for example `stage`) |
| Table | Fully qualified table/collection name (`schema.table`) |
| Key columns | Column(s) that uniquely identify the row - used both as the `MERGE`/upsert match condition and to make re-runs idempotent |
| Row selector | The filter that picks exactly **one** source row (a date, a natural key, an ID plus a type, etc.) |
| Column allow/deny list (optional) | Columns that must never leave the source (for example free-text PII fields), when the table carries data the target environment should not receive |

## Phases

1. **Read-only fetch from source.** Run only a `SELECT` (or read) against
   the source; the source connection is never used for a write in this
   skill. Fail loudly - do not fall back to a guessed row - if the selector
   matches zero rows or more than one row. Save the fetched row (with
   column type metadata) to a local snapshot file so the preview and the
   later write use the exact same data; never print full row contents to a
   shared or committed log if any column may carry sensitive data.
2. **Render an idempotent MERGE/upsert preview.** Build a `MERGE` (or
   equivalent upsert) statement keyed on the key columns, so re-running the
   copy updates the existing target row instead of duplicating it. Show the
   user the literal statement with real values substituted, even though the
   actual execution in step 4 uses bound parameters - the literal preview
   is what the human confirms against. See
   `references/merge-preview-pattern.md` for ANSI, Oracle, and PostgreSQL
   templates.
3. **Explicit human confirmation.** Show the row's key values and the full
   preview, then ask whether to apply it to the target. Never skip this
   step, even if the user seems to be in a hurry or has asked for the copy
   before - the write always requires explicit confirmation in this
   conversation, naming the target environment.
4. **Execute.** Only after confirmation, run the upsert against the target
   using bound parameters (not the literal preview text). Gate the write
   behind an explicit flag or argument (for example `--confirm-target-write`)
   that only gets passed after the human confirmed in step 3 - this is a
   safety gate against an accidental direct re-run, not a substitute for
   asking.
5. **Read back and verify.** Re-fetch the row from the target using the key
   columns and compare it against the source snapshot from step 1. Report
   any mismatch instead of assuming the write succeeded because the
   statement returned no error.
6. **Report.** Tell the user which row moved, from which source to which
   target, the rows-affected count, and where the local snapshot file is.
   Never include secret values in the report.

## Safety Rules

- **Never write without confirmation.** The write step never runs
  unattended; it requires an explicit, in-conversation "yes, write it to
  `<target>`" for that specific row and target.
- **Never widen scope without separate approval.** Copying more than one
  row, more than one table, or looping this skill over a list is a
  different, riskier operation - treat it as a data migration, get explicit
  approval for the wider scope first, and prefer a reviewed script or the
  project's normal migration path over repeating this skill in a loop.
- **Never write to the source.** The source connection is read-only for the
  life of this skill; a request for two-way sync is a different task.
- **Redact secrets everywhere.** Never print, log, or commit a password,
  token, or connection secret; load them only from the local credentials
  file described in Prerequisites.
- **Log what was written.** Keep a record (even a simple local file) of
  target environment, table, key values, timestamp, and rows-affected for
  every executed write, so there is an audit trail independent of the chat
  transcript.
- **Treat the target as a real environment.** Do not assume a "lower"
  environment is disposable - confirm with the user before overwriting a
  row that already exists there, and state in the confirmation step whether
  the target row already exists (update) or will be newly inserted.

## References

- `references/merge-preview-pattern.md` - generic SQL `MERGE`/upsert
  templates (ANSI, Oracle, PostgreSQL) and a Node.js/Python pseudo-skeleton
  covering config loading, connection test, fetch, preview, confirm, write,
  and verify.

## Related Toolkit Capabilities

- `rules/command-safety.md` - safety expectations for any command that can
  mutate shared state.
- `rules/external-write-authorization.md` - the broader confirmation gate
  this skill's write step follows.
- `rules/cross-platform-scripts.md` - write any accompanying script so it
  runs the same way on Windows, macOS, and Linux.
- `skills/data-governance/SKILL.md` - when the row being copied carries
  regulated or sensitive data and needs a governance check before it moves
  environments.
