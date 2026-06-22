---
trigger: always_on
description: Minimum security gate that must run before opening a PR or merging changes
---

# Security Check Required

Use this rule together with:

- `rules/security.md`
- `rules/command-safety.md`
- `rules/code-rules.md`
- `rules/operational-doc-required.md`

This file defines the minimum security gate for any new or modified content in this repository.

## Mandatory Policy

- Every new or modified code path must receive a security check before the task is considered complete.
- Every new or modified shell script, PowerShell script, batch file, workflow file, rule file, skill file, or operational document must receive the same security check treatment.
- Do not treat prompts, rules, workflows, rubrics, or setup docs as automatically safe. They can introduce insecure commands, secrets exposure, or unsafe operational guidance.

## Required Command

Run:

```bash
./scripts/security-check-toolkit.sh
```

On Windows PowerShell, run the wrapper that invokes the same shell gate through Git Bash:

```powershell
./scripts/security-check-toolkit.ps1
```

For focused agent-skill vetting, run SkillSpector directly across every toolkit skill:

```bash
./scripts/validate-skills-with-skillspector.sh
```

PowerShell:

```powershell
./scripts/validate-skills-with-skillspector.ps1
```

## Minimum Expectations

- Review failures before considering the task done.
- If a check is skipped because the file type is absent, record that as an intentional skip, not as a silent omission.
- If a tool is unavailable in the current environment, install it or explicitly document the gap and the risk.
- Do not suppress findings without a concrete justification.
- Treat secret-scanning failures, unsafe command patterns, dependency findings, and workflow security issues as blocking by default.

## Files In Scope

Apply the mandatory check to changes under:

- `rules/`
- `workflows/`
- `scripts/`
- `.github/`
- `.codex/`
- `.agents/`
- `.cursor/`
- `.windsurf/`
- `integrations/`
- `docs/`
- `README.md`, `AGENTS.md`, `CLAUDE.md`, `INTENTS.md`
- other operational or automation files added later

## Windows Environment Setup

On Windows (Git Bash), install tools before running the security check:

**Binary tools via winget** (no admin required):
```bash
winget install Gitleaks.Gitleaks koalaman.shellcheck rhysd.actionlint AquaSecurity.Trivy Google.OSVScanner Anchore.Grype Anchore.Syft hadolint.hadolint Microsoft.PowerShell --accept-package-agreements
```

**Python tools via pip** (no admin required):
```bash
pip install --user yamllint semgrep checkov cfn-lint pip-audit
pip install --user git+https://github.com/NVIDIA/SkillSpector.git
```

**PSScriptAnalyzer module** (for PowerShell linting):
```bash
pwsh -NoLogo -NoProfile -Command "Install-Module -Name PSScriptAnalyzer -Force -Scope CurrentUser"
```

After installation, restart your shell for PATH updates. Winget tools land in `%LOCALAPPDATA%\Microsoft\WinGet\Packages\`, pip tools in `%APPDATA%\Python\PythonXXX\Scripts`. The PowerShell wrapper looks for Git Bash under the standard Git for Windows install paths and avoids the WSL `bash.exe` shim.

## Known Platform Considerations

- **Python 3.14 + Windows**: semgrep requires `PYTHONUTF8=1` to avoid `cp1252` encoding errors. The script sets this automatically.
- **PSScriptAnalyzer paths**: The script uses relative paths (not POSIX `/c/...` paths) so pwsh can resolve them on Windows.
- **ShellCheck severity**: The script uses `-S warning` to avoid failing on info-level findings (e.g., SC1091 for unresolvable `source` paths, SC2016 for intentional single-quote usage).
- **SkillSpector availability**: If `pip install skillspector` is unavailable, install from the NVIDIA GitHub repository URL shown above. The wrapper invokes the installed Python package, so the console script does not need to be on `PATH`.
- **Disk space**: grype and trivy download vulnerability databases (~90 MB each). Ensure sufficient disk space or these checks will fail.

## Completion Standard

A task that changes in-scope files is not complete until `./scripts/security-check-toolkit.sh` or `./scripts/security-check-toolkit.ps1` has been run and its results have been reviewed.
