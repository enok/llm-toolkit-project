---
trigger: always_on
description: Minimum security gate that must run before opening a PR or merging changes
---

# Security Check Required

A change to code, scripts, `rules/`, `workflows/`, `skills/`, `tool-subagents/`, `integrations/`, `docs/`, `.github/`, `.codex/`, `.cursor/`, `.windsurf/`, linked toolkit paths, or `README.md`/`AGENTS.md`/`CLAUDE.md`/`INTENTS.md` is not complete until the gate has run and its results are reviewed. Prompts and docs are not automatically safe.

## Commands

- `./scripts/security-check-toolkit.sh` (Windows: `./scripts/security-check-toolkit.ps1`, which runs it through Git Bash, not the WSL shim).
- When a skill is added or changed, also `./scripts/validate-skills-with-skillspector.sh` (or `.ps1`) and, when `./scripts/check-new-skill-security.sh --has-work` exits 0, `./scripts/check-new-skill-security.sh`.

## Gate rules

- Secret-scan, unsafe-command, dependency and workflow-security findings block by default; never suppress one without a concrete justification.
- A skipped check (file type absent) is recorded as an intentional skip; a missing tool is installed or recorded as a gap with its risk; a missing optional scanner is not a pass, and a release- or compliance-required scanner fails the gate when unavailable. Verify tools from the shell that runs the gate (PowerShell and Git Bash resolve `PATH` differently).
- Missing scanner credentials or inputs (scanner API token, source URL of an imported skill) block unless the user approves a documented local-only exception.
- `scripts/scan-llm-surface-security.py` blocks override-safety instructions, secret exfiltration, concealed actions, download-and-execute pipes, encoded PowerShell and destructive root deletes in LLM-loaded text. Reword a defensive example so its safe intent is explicit; `llm-surface-security: allow` only with a nearby justification for test or scanner documentation. External scanners supplement this scan; they never replace it.
- Skill scanners run through CLI/API only (not as MCP servers), on explicit `skills/<name>/SKILL.md` files, never whole-machine discovery. SkillSpector runs static `--no-llm` and fails on findings not in `scripts/skillspector-allowlist.json` (keep it narrow and justified). Check an external skill's source URL with a skill trust service before import and proceed only when the returned severity is safe; for a locally authored skill record the URL check as not applicable.

## CI and Terraform identity boundary

- A CI, deployment or Terraform principal must not manage a policy, trust policy, permissions boundary or credential attached to itself; existing self-administration is a finding. IAM bootstrap uses a distinct controlled role or pipeline whose constrained executor cannot change its own policy, trust or boundary, pass arbitrary roles, or reach production outside the approved route; if none exists, fail closed and assign the blocker to its owner.
- One remote authorization object has one Terraform-state owner: search stacks and state routes before an import; a duplicate declaration blocks until one owner is explicitly retired without applying or merging it.

## Windows setup

`winget install Gitleaks.Gitleaks koalaman.shellcheck rhysd.actionlint AquaSecurity.Trivy Google.OSVScanner Anchore.Grype Anchore.Syft hadolint.hadolint Microsoft.PowerShell`; `pip install --user yamllint semgrep checkov cfn-lint pip-audit` plus SkillSpector from its NVIDIA GitHub repository (or `SKILLSPECTOR_BIN`); PSScriptAnalyzer via `Install-Module -Scope CurrentUser`. Restart the shell afterwards. grype and trivy need about 90 MB each of database space.
