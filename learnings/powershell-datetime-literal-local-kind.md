---
title: A PowerShell [datetime] cast of a Z timestamp is Local kind and skews UTC comparisons
category: toolchain
created: 2026-10-22
tags: [powershell, datetime, utc, timezone, LastWriteTimeUtc, DateTimeOffset, Get-CimInstance, commandline]
---

# Problem
A file filter used `[datetime]'2026-10-15T16:38:00Z'` as the cutoff and compared it with
`LastWriteTimeUtc`. On a UTC-3 machine the filter returned files written at 14:58Z, which is
before the cutoff.

# Failed Approaches
- `$cutoff = [datetime]'2026-10-15T16:38:00Z'` then `$_.LastWriteTimeUtc -gt $cutoff`: the cast
  turned the Z string into a Local-kind value (13:38 on this machine), and the comparison used the
  raw values with no kind conversion, so 14:58Z passed a 13:38 cutoff.

# Solution
Convert the cutoff to UTC before comparing, and compare UTC to UTC:

```powershell
$cutoff = [datetime]::Parse('2026-10-15T16:38:00Z').ToUniversalTime()
# or: $cutoff = ([DateTimeOffset]'2026-10-15T16:38:00Z').UtcDateTime
Get-ChildItem $dir | Where-Object { $_.LastWriteTimeUtc -gt $cutoff }
```

Print `$cutoff.Kind` and `$cutoff.ToString('o')` once to confirm it reads `Utc` and the expected time.

Related lookup used in the same session: to find a process by its command line (for example
the one holding a file open), `Get-Process` is not enough; use

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select-Object ProcessId,CommandLine
```

# Why
The `[datetime]` cast parses the string with the local culture and converts a `Z` (UTC) value to
local time. `LastWriteTimeUtc` is UTC kind, so the two values were on different clocks.
