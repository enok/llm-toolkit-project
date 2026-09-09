---
title: Cross-environment MERGE/upsert preview pattern
tags: [sql, merge, upsert, oracle, postgresql, data-copy, idempotent]
---

# MERGE/Upsert Preview Pattern

Generic templates for building an idempotent upsert statement keyed on a
row's natural/composite key, plus a language-agnostic pseudo-skeleton for
the fetch -> preview -> confirm -> write -> verify flow described in
`SKILL.md`. Substitute `<table>`, the key columns, and the non-key column
list for your actual table - nothing here is tied to a specific product or
schema.

## ANSI SQL MERGE

```sql
MERGE INTO <target_schema>.<table> AS t
USING (
  SELECT
    <col1> AS <col1>,
    <col2> AS <col2>
    -- ... one column per source column, aliased to itself
) AS s
ON (t.<key_col1> = s.<key_col1> AND t.<key_col2> = s.<key_col2>)
WHEN MATCHED THEN
  UPDATE SET
    t.<col1> = s.<col1>,
    t.<col2> = s.<col2>
    -- ... every non-key column
WHEN NOT MATCHED THEN
  INSERT (<key_col1>, <key_col2>, <col1>, <col2>)
  VALUES (s.<key_col1>, s.<key_col2>, s.<col1>, s.<col2>);
```

The `ON` clause must use exactly the key columns (never a subset) so the
statement is idempotent: re-running it against the same source row updates
the same target row instead of inserting a duplicate.

## Oracle Variant

Oracle's `MERGE` needs a `FROM dual` on the source side when the source
values come from bind variables or literals rather than another table, and
benefits from explicit `TO_NUMBER`/`TO_DATE` casts so numeric and date
precision survive the round trip:

```sql
MERGE INTO <target_schema>.<table> t
USING (
  SELECT
    :key1                                    AS <key_col1>,
    TO_DATE(:key2, 'YYYY-MM-DD HH24:MI:SS')   AS <key_col2>,
    TO_NUMBER(:val1)                          AS <col1>,
    :val2                                     AS <col2>
  FROM dual
) s
ON (t.<key_col1> = s.<key_col1> AND t.<key_col2> = s.<key_col2>)
WHEN MATCHED THEN UPDATE SET
  t.<col1> = s.<col1>,
  t.<col2> = s.<col2>
WHEN NOT MATCHED THEN INSERT (<key_col1>, <key_col2>, <col1>, <col2>)
VALUES (s.<key_col1>, s.<key_col2>, s.<col1>, s.<col2>);
```

Notes:

- Bind every value (`:name`); build the literal-substituted version only
  for the human-facing preview in Phase 2 of `SKILL.md` - never execute a
  string-concatenated statement.
- Fetch `NUMBER` columns as strings (the driver's `fetchAsString` option or
  equivalent) so large values keep full precision across the read -> write
  round trip.
- Store `DATE`/`TIMESTAMP` values as formatted strings in the snapshot file
  and re-bind them through `TO_DATE`, so the round trip never depends on
  the calling process's local timezone.

## PostgreSQL Variant

PostgreSQL's idiomatic upsert is `INSERT ... ON CONFLICT ... DO UPDATE`,
keyed on a unique constraint or primary key over the key columns (PostgreSQL
15+ also supports a `MERGE` statement shaped like the ANSI template above,
if you prefer that syntax):

```sql
INSERT INTO <target_schema>.<table> (<key_col1>, <key_col2>, <col1>, <col2>)
VALUES ($1, $2, $3, $4)
ON CONFLICT (<key_col1>, <key_col2>)
DO UPDATE SET
  <col1> = EXCLUDED.<col1>,
  <col2> = EXCLUDED.<col2>;
```

`ON CONFLICT` requires a unique index or constraint on exactly the key
columns; create one (in a lower environment, with the user's approval) if
it does not already exist, rather than widening the conflict target to a
different column set.

## Node.js / Python Pseudo-Skeleton

Illustrative only - adapt the driver calls to whatever client library the
project already uses (`pg`, `mysql2`, `oracledb`, `psycopg`, SQLAlchemy, and
so on). The shape - load config, test both connections, read-only fetch,
literal preview, human confirmation, bound-parameter write, verify - is the
part that matters, not the exact API.

```text
# --- config (Prerequisites step 1) ---
function loadConfig(envName):
    path = env.DB_CONFIG_PATH or "~/.config/<tool>/db-connections.json"
    assert file exists at path, else fail("create it from the SKILL.md template")
    config = parseJson(readFile(path))
    entry = config[envName]
    assert entry has user/password/connectString, none containing "REPLACE_ME"
    return entry

# --- connection test (Prerequisites step 2) ---
function testConnectivity(sourceEnv, targetEnv):
    for envName in [sourceEnv, targetEnv]:
        conn = connect(loadConfig(envName))
        run a trivial read (SELECT 1, SELECT now(), a ping, etc.)
        print(envName + ": OK")
        close(conn)

# --- fetch (Phase 1) ---
function fetchOne(sourceEnv, table, keyColumns, rowSelector):
    conn = connect(loadConfig(sourceEnv))          # read-only use of this connection
    rows = conn.query(buildSelect(table, rowSelector))
    if rows.length == 0: fail("NO ROW FOUND for selector: " + rowSelector)
    if rows.length > 1: fail("selector matched " + rows.length + " rows; narrow it")
    snapshot = { table: table, keyColumns: keyColumns, values: rows[0], fetchedAt: now() }
    writeFile(snapshotPath, toJson(snapshot), mode=0o600)
    return snapshot

# --- preview (Phase 2) ---
function renderPreview(snapshot):
    literalSql = buildMerge(snapshot, literal=true)   # human-facing, real values inlined
    print(literalSql)
    return literalSql

# --- confirm (Phase 3) ---
# Handled in conversation, not in code: show renderPreview()'s output and the
# row's key values, then wait for the human's explicit "yes, write it to
# <target>" before calling apply() below.

# --- write (Phase 4) ---
function apply(targetEnv, snapshot, confirmed):
    assert confirmed == true, else fail("apply requires explicit confirmation")
    conn = connect(loadConfig(targetEnv))
    { sql, boundParams } = buildMerge(snapshot, literal=false)   # parameterized
    result = conn.execute(sql, boundParams, { autoCommit: true })
    return result.rowsAffected

# --- verify (Phase 5) ---
function verify(targetEnv, snapshot):
    conn = connect(loadConfig(targetEnv))
    row = conn.query(buildSelectByKey(snapshot.table, snapshot.keyColumns, snapshot.values))
    assert row matches snapshot.values for every non-key column
    return row

# --- report (Phase 6) ---
function report(targetEnv, snapshot, rowsAffected):
    appendLog({ targetEnv: targetEnv, table: snapshot.table,
                keyValues: pick(snapshot.values, snapshot.keyColumns),
                rowsAffected: rowsAffected, at: now() })   # audit trail; never log secrets
    print a human summary: what moved, from where, to where, rows affected, snapshot path
```

## Cross-Platform Notes

- Keep the config path resolvable the same way on Windows, macOS, and Linux
  (a `~`-relative path resolved through the language's home-directory API,
  or an environment variable override) - see `rules/cross-platform-scripts.md`.
- Prefer a small, dependency-light script over a shell one-liner so the
  literal-vs-bound-parameter distinction in Phase 2/4 stays enforced in code
  rather than relying on whoever runs the command to remember it.
