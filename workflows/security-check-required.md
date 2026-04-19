---
description: Run mandatory security checks on toolkit changes
---

# Security Check Workflow

Use this workflow with:

- `workflows/security-report.md`
- `workflows/ticket-review.md`
- `workflows/pre-pr-check.md`

## Steps

1. Identify whether the change touches code, scripts, workflows, rules, skills, integrations, or operational documentation.
2. Verify security tools are installed. On Windows, see `rules/security-check-required.md § Windows Environment Setup` for installation commands via winget + pip.
3. If on Windows (Git Bash) and tools were just installed, ensure PATH includes the winget and pip install directories (or restart the shell).
4. Run:
   - `./scripts/security-check-toolkit.sh`
5. Review every failure and blocking finding before considering the task complete.
6. If a check is skipped because the file type is absent, leave it skipped; do not fake coverage.
7. If a needed tool is missing, install it or document the gap and residual risk explicitly.
8. Treat secret leaks, unsafe command patterns, workflow security issues, and dependency findings as blocking unless there is a specific reviewed exception.

## Reporting Expectations

- Summarize that `./scripts/security-check-toolkit.sh` was run.
- Summarize passed, failed, and skipped counts.
- Summarize failed checks and whether they were fixed or intentionally deferred.
- Call out skipped checks that reflect tooling or environment gaps rather than absent file types.
- Note any platform-specific workarounds applied (see `rules/security-check-required.md § Known Platform Considerations`).
