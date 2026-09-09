---
title: Scope ErrorActionPreference Per Native Call and Decide by Exit Code
impact: HIGH
impactDescription: Prevents PowerShell 5.1 from killing successful native commands on their first stderr line
tags: powershell, windows-powershell-5.1, stderr, erroractionpreference, native-commands, exit-codes
---

## Scope ErrorActionPreference Per Native Call and Decide by Exit Code

Under Windows PowerShell 5.1, `$ErrorActionPreference = "Stop"` (correct for script safety) plus `2>&1` on a native command wraps the first stderr line in an `ErrorRecord` and promotes it to a terminating `NativeCommandError` — the script dies even when the command exits 0 (many CLIs write progress/warnings to stderr) and `$LASTEXITCODE` is never inspected.

**Incorrect (global Stop + stderr capture kills the script):**

```powershell
$ErrorActionPreference = "Stop"
$output = & aws @AwsArguments 2>&1   # first stderr line throws NativeCommandError
```

Removing `2>&1` leaks stderr and loses diagnostics; setting `Continue` globally loses fail-fast; `try/catch` loses the remaining output and breaks exit-code flow control.

**Correct (scope EAP to the invocation, restore in `finally`, return the exit code):**

```powershell
function Invoke-NativeCommand {
    param([Parameter(Mandatory)][string[]]$CommandArguments)
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & aws @CommandArguments 2>&1
        return [pscustomobject]@{ Output = $output; ExitCode = $LASTEXITCODE }
    } finally {
        $ErrorActionPreference = $previousPreference
    }
}
```

- Callers decide success from `ExitCode`, not exceptions.
- When parsing JSON from `Output`, filter stderr records first — they arrive as `ErrorRecord` objects interleaved with strings:

```powershell
$json = ($result.Output | Where-Object { $_ -isnot [System.Management.Automation.ErrorRecord] }) -join "`n"
```

- PowerShell 7 changed this behavior, so scripts that must run on 5.1 (default on Windows Server and enterprise desktops) need the wrapper even if they appear fine in pwsh.
