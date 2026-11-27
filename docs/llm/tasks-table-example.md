# Canonical tasks table: the most complete form, every print

Every tasks table print of the agent-orchestrator is this complete, in the chat and in any notification mirror: never a reduced table, a delta, or a summary line. The binding contract is "Tasks table contract: columns, assets, tokens, prints, checkpoints" in `tool-subagents/agent-orchestrator.md`; this document is a worked example of the shape to copy. The task, pull request and CI links below are made up.

## When to use this example

- Before printing a table, to check the print against a known-good shape.
- When a user says "print it the way I showed you in the other chat" and that chat cannot be opened (private link, other account): take the format from this example, say so, and offer to match a pasted sample if one differs.
- When a consumer repository needs a pointer for its directive: link here instead of restating the format.

## Required parts of every print

1. **Header line:** session name, print number, timestamp with timezone, and what triggered the print (`planning`, `row 4 completed`, `row 6 blocked`, `final`, `resumed from <timestamp>`).
2. **Manifest, five lines:** `Route`, `Rules in force`, `Agents` (each with its model), `Helpers`, and `Mirror` (the notification channel and whether the send succeeded; `none configured` when there is no mirror).
3. **Table with all 15 columns, none dropped:** `# | Wave | Task | Assets | Vector DB used | Complexity | Model/Effort | Status | Evidence | PR link(s) | CI/CD run link(s) | Tokens | % Complete | SLA | Remaining SLA`. Empty cells read `—`.
4. **Complexity cell:** the tier (`light`, `standard`, `deep`), then the trigger in italics for rows above the standard tier (`*(trigger: ...)*`) and the exemption in italics on root-inline rows (`*(exempt: ...)*`).
5. **Model/Effort cell:** the exact model that runs the row and its effort, `<model name and version> / <effort>`; never a tier word, family alias or role.
6. **Failed or re-split rows stay in the table** with their cause in Evidence; the replacement rows are added, not substituted, and the failed row shows Remaining SLA `00:00`.
7. **Three footer rows**, in this order: `Total (all tasks)`, `Total (remaining/not completed)`, `Remaining SLA to complete all tasks (critical path)`.
8. **Closing line** under the footer rows: how many tasks used the project's vector knowledge base, out of all tasks, and the searches made.

## Example (mid-run snapshot)

**Tasks table: session `s3-retry` · print #9 · 2026-11-26 12:05 UTC (UTC+00:00) · trigger: row 11 entered validating**

**Route:** `INTENTS.md` → "implement a ticket" → primary `workflow:ticket-implementation` (helpers: `skill:best-practices`, `skill:pre-pr-check`)
**Rules in force:** `rule:request-orchestration`, `rule:external-write-authorization`, `rule:human-comment-reply-gate`, `workflow:task-quality-loop`
**Agents:** `agent-orchestrator` (root, Claude Opus 5.5), `parallel-explorer` (Claude Haiku 5.5), `java-change-validator` (Claude Sonnet 5.5), `test-runner` (Claude Haiku 5.5), `code-reviewer` (Claude Sonnet 5.5), `pr-validator` (Claude Haiku 5.5), `task-quality-judge` (Claude Opus 5.5)
**Helpers:** `script:check_tasks_table.py`, `script:mvn verify`, `script:gh pr checks`, `skill:run-tests`
**Mirror:** `<notification-channel>`, send succeeded

| # | Wave | Task | Assets | Vector DB used | Complexity | Model/Effort | Status | Evidence | PR link(s) | CI/CD run link(s) | Tokens | % Complete | SLA | Remaining SLA |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | W1 | Read `learnings/INDEX.md`, map uploader call sites | `agent:parallel-explorer` · `rule:request-orchestration` | yes - 2 searches; call-site map from past uploads | light | Claude Haiku 5.5 / low | completed | `CONTEXT_STATE.md#recon` (14 call sites) | — | — | 8.2K | 100% | 00:10 | 00:00 |
| 2 | W1 | Pull current SDK retry documentation | `skill:run-tests` | no | light | Claude Haiku 5.5 / low | completed | `notes/sdk-retry.md` | — | — | 6.4K | 100% | 00:10 | 00:00 |
| 3 | W2 | Design retry policy (backoff with jitter, idempotency) | `agent:task-quality-judge` · `workflow:task-quality-loop` | yes - via row 1 | deep *(trigger: ambiguous idempotency contract)* | Claude Opus 5.5 / high | completed | `docs/retry-policy.md`; judge pass on iteration 2 of 5 | — | — | 41.7K | 100% | 00:25 | 00:00 |
| 4 | W3 | Implement retrying uploader and config | `skill:best-practices` · `agent:java-change-validator` | no | standard | Claude Sonnet 5.5 / medium | failed | breached (cause: scope too large), re-split into #5 and #6; `feat/retry@a1b2c3d` partial | — | — | 52.3K | 50% | 00:30 | 00:00 |
| 5 | W3 | `RetryingUploader` class and unit tests | `skill:best-practices` · `agent:java-change-validator` | no | standard | Claude Sonnet 5.5 / medium | completed | `feat/retry@d4e5f6a`; 18 tests green | — | — | 22.9K | 100% | 00:20 | 00:00 |
| 6 | W3 | Wire config properties and the Spring bean | `agent:java-change-validator` | no | light | Claude Haiku 5.5 / low | completed | `feat/retry@9f8e7d6` | — | — | 9.1K | 100% | 00:15 | 00:00 |
| 7 | W4 | Full test suite and failure triage | `agent:test-runner` · `script:mvn verify` | no | light | Claude Haiku 5.5 / low | completed | `mvn verify` 412 of 412 pass | — | — | 11.8K | 100% | 00:15 | 00:00 |
| 8 | W4 | Diff code review | `agent:code-reviewer` | no | standard | Claude Sonnet 5.5 / medium | completed | 0 blockers, 2 nits fixed | — | — | 27.5K | 100% | 00:20 | 00:00 |
| 9 | W5 | Push branch and open PR | `rule:external-write-authorization` · `skill:pre-pr-check` | no | standard *(exempt: root-only write)* | Claude Opus 5.5 / medium | completed | push approved 11:48 | [#42](https://github.com/example-org/upload-service/pull/42) | — | 5.3K | 100% | 00:10 | 00:00 |
| 10 | W6 | Watch CI and PR readiness | `agent:pr-validator` · `script:gh pr checks` | no | light | Claude Haiku 5.5 / low | running | 3 of 5 checks green | [#42](https://github.com/example-org/upload-service/pull/42) | [run 9183](https://github.com/example-org/upload-service/actions/runs/9183) | 3.1K | 25% | 00:20 | 00:12 |
| 11 | W6 | CHANGELOG and README retry section | `agent:task-quality-judge` | no | light | Claude Haiku 5.5 / low | validating | `CHANGELOG.md`, `README.md` diff | [#42](https://github.com/example-org/upload-service/pull/42) | — | 6.2K | 75% | 00:15 | 00:04 |
| 12 | W7 | Final validation and ledger compaction | `script:check_tasks_table.py` | no | standard | Claude Sonnet 5.5 / medium | pending | — | — | — | est. 10-15K | 0% | 00:10 | 00:10 |
| **Total (all tasks)** | | **12** | | | | | | | | | **194.5K** | | **03:20** | |
| **Total (remaining/not completed)** | | **4** | | | | | | #4 (failed), #10, #11, #12 | | | | | | **00:26** |
| **Remaining SLA to complete all tasks (critical path)** | | #10 (longest W6 lane) → #12 | | | | | | | | | | | | **00:22** |

Vector DB: 2 of 12 tasks used it (2 searches: rows 1 and 3 via row 1).

## Notes on the example

- Statuses shown: completed, failed, running, validating, pending. A real run can also show `blocked`, `paused`, `refining` and `escalated`.
- Every finished or failed row has a real token number; only a pending row shows `—` or a planned band (`est. ...`), and a band is never summed into the total.
- No row's SLA is over 00:30. The critical path is the longest chain of dependent rows, never the sum of the parallel lanes of a wave.
- The failed row #4 keeps its place with the cause; rows #5 and #6 replace its remaining work.
- In the footer rows the Task cell holds the bare count (a number only); the row numbers behind it go in Evidence.
- Check any table before sending it: `python3 scripts/check_tasks_table.py <file>`.
