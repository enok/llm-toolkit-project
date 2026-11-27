---
description: Mandatory security gate before any commit or push: secrets, dependency, static-analysis, and toolkit-surface checks
---

# Security Check Workflow

Procedure behind `rules/security-check-required.md`: checks MUST pass before any commit or push.

1. Confirm the pre-commit and pre-push hooks are executable; if missing, restore a
   pre-commit hook that runs the repository's security script and exits non-zero on failure.
2. Run the repository's security script (in this toolkit `./scripts/security-check-toolkit.sh`
   or `.ps1`; in a consumer repo its own `scripts/security_check_this_repo.sh`; for dev-tools
   work `./scripts/security_check_dev_tools.sh <path-to-toolkit-checkout>`).
3. **FAIL** is blocking: do not commit or push. Fix the root cause (remove and rotate an exposed
   secret, update or justify a vulnerable dependency, refactor an unsafe pattern), re-run, and
   proceed only when every blocking check passes.
4. **SKIP** (tool missing or file type absent) is tracked, not a pass: install the tool or
   document the gap.
5. `--no-verify` only to test the hook itself, or in a documented, approved emergency after a
   manual check.
6. Report: script run, pass/fail/skip counts, failures and their fixes, skipped tools, and any
   bypass with its justification.

Never ignore: hardcoded credentials, tokens or passwords, private keys, `.env` files with real
values, notebook outputs showing credentials, unvalidated input in shell scripts, SQL injection,
or unsafe deserialization.

On Windows, run the bash gate through Git Bash and confirm each scanner resolves in that shell. Command and failure mode: `skills/environment-diagnose/references/device-bridge.md` › "Windows security gate".
