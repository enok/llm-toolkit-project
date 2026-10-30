---
title: Windows security gates - Store Python alias is skipped, pip --user tools are off PATH, and committed skills are not scanned
category: toolchain
created: 2026-10-30
tags: [windows, python, windowsapps, git-bash, security-check, skillspector, semgrep, powershell, shim]
---

# Problem
On a Windows PC whose only Python is the Microsoft Store install, the pre-commit gates for a toolkit
change did not run as intended: `validate-toolkit-indexes.ps1` failed with "python3 or python is
required to validate workflow character counts", `security-check-toolkit.ps1` failed with "Python is
required for the LLM surface prompt-injection scan", and after the new skill was committed the
skill scans printed "SKIP: no new or modified skill files detected".

# Failed Approaches
- Relying on `python` / `python3` from PATH: both resolve to the `...\AppData\Local\Microsoft\WindowsApps\`
  app-execution aliases, and `find_python_cmd` in `scripts/security-check-toolkit.sh` and
  `scripts/check-new-skill-security.sh` deliberately skips any `*/WindowsApps/*` candidate.
- Trusting installed tools: semgrep and skillspector were installed but skipped ("not installed
  or is not executable from this shell"). `pip --user` put them in the Store package's
  `...\AppData\Local\Packages\PythonSoftwareFoundation.Python.<X.Y>_<id>\LocalCache\local-packages\<PythonXY>\Scripts`,
  which is not on PATH.
- Running `./scripts/security-check-toolkit.ps1` from Windows PowerShell 5.1: it aborted at "Semgrep auto
  scan" with an empty `bash.exe :` NativeCommandError (native stderr became an error record), exit 1, log truncated.
- Scanning after committing: `has_changed_skill_files` reads only `git diff HEAD`, `git diff --cached HEAD`
  and untracked files, so a committed skill looks unchanged and both changed-skill scans skip.

# Solution
- Create a shim folder outside WindowsApps (for example `%TEMP%\pyshim`, `/tmp/pyshim` in Git Bash) with two
  files, `python3` and `python`, each `#!/bin/sh` then
  `exec /c/Users/<user>/AppData/Local/Microsoft/WindowsApps/python.exe "$@"`. Prepend it to PATH;
  `command -v python3` then returns the shim and the scripts accept it.
- Also prepend the Store package `...\LocalCache\local-packages\<PythonXY>\Scripts` folder so semgrep and
  skillspector run instead of being skipped (`pytest.exe` lives there too).
- Run the bash script, not the `.ps1` wrapper: `cmd /c '"C:\Program Files\Git\bin\bash.exe" -l <script> > <log> 2>&1'`
  via a small runner that sets PATH and `cd`s into the worktree. Observed: 23 checks, 8 passed, 0 failed,
  15 skipped, exit 0; SkillSpector scanned 1 skill, 0 issues.
- Run the gates before committing. To scan an already committed skill, `git reset --soft origin/main` in a
  throwaway worktree (changes become staged), or set `SECURITY_NEW_SKILL_BASE=origin/main` for
  `check-new-skill-security.sh`, which honours it.
- Without `SNYK_TOKEN`, `check-new-skill-security.sh` printed "SNYK_TOKEN is not set; skipping Snyk Agent
  Scan" and still exited 0.
- Follow-up, not done: teach `has_changed_skill_files` to honour `SECURITY_NEW_SKILL_BASE`.

# Why
The gate scripts skip any WindowsApps candidate by design, so a shim that `exec`s the real executable from a
non-WindowsApps path satisfies the check without editing it. `pip --user` writes scripts to the Store
package's own folder, which was not on PATH. The `.ps1` wrapper under PowerShell 5.1 turned native stderr
into an error record and ended the run early. The changed-skill scans look only at uncommitted state, so
timing matters. Untested: PowerShell 7, a non-Store Python install, and other machines.
