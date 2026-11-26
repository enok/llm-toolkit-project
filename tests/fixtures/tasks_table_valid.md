## Session: demo-run-01 (2026-01-15 09:00 UTC) — synthetic ledger used as a test fixture (in progress)
Requested by: a user · Route: `INTENTS` row "build feature" → skill `example-skill` + workflow `example-workflow` · Rules in force: `example-rule` · Agents: `example-agent` (reviewer lane, large model), root (small model) · Helpers: `scripts/example_check.py`

| # | Wave | Task | Assets | Vector DB used | Complexity | Model/Effort | Status | Evidence | PR link(s) | CI/CD run link(s) | Tokens | % Complete | SLA | Remaining SLA |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | W0 | Route the request and load the contract | INTENTS · rule:example-rule | yes - 2 searches; prior plan for this route | light (root inline) | Claude Haiku 5.5 / low | completed | first-pass; plan in notes/plan.md | — | — | 12.4K | 100 | 00:05 | 00:00 |
| 2 | W0 | Survey the files the change touches | workflow:example-workflow | no | light (root inline) | Claude Haiku 5.5 / low | completed | first-pass; 6 files listed in notes/survey.md | — | — | ~3.1K | 100 | 00:05 | 00:00 |
| 3 | W1 | Implement module A | skill:example-skill · script:scripts/example_check.py | no | standard | Claude Sonnet 5.5 / medium | completed | refined once; src/module_a.txt; example_check exit 0 | — | — | 48.7K | 100 | 00:20 | 00:00 |
| 4 | W1 | Implement module B | skill:example-skill | no | standard | Claude Sonnet 5.5 / medium | running (dispatched 10:05) | expected output: src/module_b.txt | — | — | — | 40 | 00:20 | 00:12 |
| 5 | W1 | Draft tests for module A | agent:example-agent | no | standard | Claude Sonnet 5.5 / medium | validating | tests/draft_a.txt written; review pending | — | — | 22.0K | 80 | 00:15 | 00:04 |
| 6 | W2 | Independent review of modules A and B | agent:example-agent · rule:example-rule | no | deep (validator is not the producer) | Claude Opus 5.5 / high | pending | — | — | — | est. 30-50K | 0 | 00:10 | 00:10 |
| 7 | W2 | Run validators and the test suite | script:scripts/example_check.py | no | light (root inline) | Claude Haiku 5.5 / low | pending | — | — | — | — | 0 | 00:05 | 00:05 |
| 8 | W2 | Final table and ledger close | none (inline) | no | light (root inline) | Claude Haiku 5.5 / low | blocked (waiting for a human decision) | — | — | — | — | 0 | 00:05 | 00:05 |
| **Total (all tasks)** |  | 8 |  | | |  |  |  |  |  | ~86.2K |  | 01:25 |  |
| **Total (remaining/not completed)** |  | 5 |  | | |  |  |  |  |  |  |  |  | 00:36 |
| **Remaining SLA to complete all tasks (critical path)** |  | 4 → 6 → 7 → 8 |  | | |  |  |  |  |  |  |  |  | 00:32 |

Tokens: root rows use the session token counter, or a ~ estimate where the host exposes none (row 2); delegated rows are the usage reported by the dispatch tool; the total is marked ~ because it sums an estimate. Row 6 shows its planned band until it runs.
