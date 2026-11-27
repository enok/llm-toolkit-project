---
description: Run a mandatory static-analysis gate against only code added or modified in the current Git change set
---

# Changed-code quality gate workflow

Mandatory for changed source code per `rules/changed-code-quality-gate-required.md`
(scope and blocking policy live there); not needed for docs- or config-only changes.

1. Pick the base: local uncommitted work omits `--base`; branch/pre-PR passes the
   trusted target branch or base SHA; CI PR passes base and head SHAs with
   `--event pull_request`; CI push passes `before`/`after` with `--event push`
   (a new branch passes this toolkit's trunk, `main`).
2. Run the repository's `scripts/changed_code_quality_gate.py` with the platform's
   Python launcher, e.g. `--base origin/main`. `--scope-only` is not coverage.
3. Exit codes: 0 pass or nothing applicable; 1 findings; 2 Git scope/config error;
   3 analyzer or coverage unavailable; 4 analyzer or report failure. Stop on 1-4.
4. Tests, build, dependency, docs, and security gates still run; this replaces none.

Never put secrets on the command line. CI wiring:
`.github/workflows/changed-code-quality-gate.yml` (runs the gate from a protected revision).
