---
title: gh --jq filters break under Windows PowerShell, so pipe to ConvertFrom-Json
category: environment
created: 2026-10-07
tags: [powershell, github-cli, jq, quoting, windows, convertfrom-json, shell]
---

# Problem

Under Windows PowerShell, a `gh api <endpoint> --jq '<filter>'` call failed with
"accepts 1 arg(s), received 5". The session recorded it as a quoting failure.

# Failed Approaches

None recorded in the session notes; the `--jq '<filter>'` call failed as described above
and was replaced instead of repaired.

# Solution

In PowerShell, do not pass a `--jq` filter. Pipe the JSON to `ConvertFrom-Json` and select
the fields with PowerShell:

```powershell
$p = gh api repos/<owner>/<repo>/branches/main/protection | ConvertFrom-Json
$p.required_status_checks.contexts
$p.enforce_admins.enabled
```

General guidance, not observed in this session: send request bodies with `--input <file>`
instead of inline JSON strings:

```powershell
gh api -X PUT repos/<owner>/<repo>/branches/main/protection --input protection.json
```

The failure was recorded under Windows PowerShell only; the session says nothing about
other shells.

Durable guidance: skills/multi-language-study-repo/references/repo-layout-and-protection.md

# Why

The session recorded the symptom and the replacement, not the cause, and it names Windows
PowerShell without a version. Inference from the message only: `gh` expects one positional
argument and saw five, which suggests the quoted filter was split into several arguments
before it reached `gh`. That is unverified. Moving the filtering into PowerShell removes
the quoted filter from the command line, which is why the `ConvertFrom-Json` form works
regardless of the cause.
