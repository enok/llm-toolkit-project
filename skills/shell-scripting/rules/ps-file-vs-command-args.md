---
title: Use -Command for Array Parameters — -File Binds Literal Strings
impact: MEDIUM
impactDescription: Prevents [string[]] parameters from silently receiving one comma-joined literal string
tags: powershell, parameters, string-array, cli, bash, quoting
---

## Use -Command for Array Parameters — -File Binds Literal Strings

`powershell -File` performs no expression parsing on script arguments — every token is bound as a literal string (by design, so arbitrary arguments cannot execute code). Array literals, `@()`, and comma constructors are language syntax and only take effect when PowerShell itself parses the command line, i.e. under `-Command`.

**Incorrect (a `[string[]]` parameter receives one element `"a.png,b.svg"`):**

```bash
powershell -File script.ps1 -Only a.png,b.svg
powershell -File script.ps1 -Only "a.png","b.svg"   # bash strips quotes; same result
```

**Correct (invoke through `-Command` so a real PowerShell parser builds the array):**

```bash
powershell -NoProfile -Command "& 'script.ps1' -Only @('a.png','b.svg')"
```

- Alternatively, keep `-File` invocation but accept a single delimited string and split inside the script: `$Only -split ','`.
- Symptom to watch for: validation rejecting a comma-joined value as one unknown name.
