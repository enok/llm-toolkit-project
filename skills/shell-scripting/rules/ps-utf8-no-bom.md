---
title: Write Tool-Consumed Files as BOM-less UTF-8
impact: HIGH
impactDescription: Prevents strict parsers (aws CLI file://, JSON loaders) from rejecting files that look valid in editors
tags: powershell, bom, utf8, encoding, aws-cli, json
---

## Write Tool-Consumed Files as BOM-less UTF-8

In Windows PowerShell 5.1, both `Set-Content -Encoding UTF8` and `Out-File -Encoding utf8` emit a UTF-8 BOM (`EF BB BF`). Strict consumers such as the AWS CLI's `file://` JSON loader do not strip it and fail with parse errors (for example exit code 252, "Invalid JSON") even though the content looks valid in every editor — and `ConvertFrom-Json` parses it fine because PowerShell tolerates the BOM, so the usual validation checks pass.

**Incorrect (BOM breaks the downstream consumer):**

```powershell
$payload | Set-Content -Encoding UTF8 batch.json
aws s3api delete-objects --delete file://batch.json   # "Error parsing parameter '--delete': Invalid JSON"
```

**Correct (explicit BOM-less encoder):**

```powershell
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($outputFile, $payload, $utf8NoBom)
```

- Verify by dumping the first bytes: the file must start at `7B` (`{`), not `EF BB BF`.
- `WriteAllText` requires an absolute path — it resolves relative paths against the process working directory, not PowerShell's `$PWD`.
- PowerShell 7's `utf8` encoding is BOM-less by default; use the explicit encoder anyway when the script must run on both 5.1 and 7.
