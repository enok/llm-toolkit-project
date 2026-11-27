---
title: Windows security gates - Store Python alias is skipped, pip --user tools are off PATH, and committed skills are not scanned
category: toolchain
created: 2026-10-30
tags: [windows, python, windowsapps, git-bash, security-check, skillspector, semgrep, powershell, shim]
---

# Solution
Run the bash gate script through Git Bash, not the `.ps1` wrapper under Windows PowerShell 5.1:

```powershell
cmd /c '"C:\Program Files\Git\bin\bash.exe" -l scripts/security-check-toolkit.sh > <log> 2>&1'
```

# Why
Under PowerShell 5.1 the wrapper turns native stderr into an error record: it aborted at
"Semgrep auto scan" with an empty `bash.exe :` NativeCommandError, exit 1, log truncated.
