---
title: PowerShell 5.1 redirect wrote a file as UTF-16, so write tool-consumed files explicitly
category: environment
created: 2026-10-07
tags: [powershell, windows-powershell-5.1, redirect, utf-16, encoding, out-file, cmd, python]
---

# Problem

A script was written to disk through a Windows PowerShell 5.1 redirect, and Python then
could not read it: the file had been written as UTF-16. The session recorded this as a
low-severity tool-misuse mistake, found as a tool error.

# Failed Approaches

None recorded beyond the first attempt described in Problem: the redirect wrote the file,
the consumer failed on it, and the write was redone with an explicit mechanism.

# Solution

When a PowerShell 5.1 step writes a file that another tool will read, do not let the
redirect choose the encoding. Use one of the two fixes the session recorded:

- redirect through `cmd /c`, so the redirect is done by `cmd` and not by PowerShell; or
- write with `Out-File` and an explicit `-Encoding`.

Illustrative forms, with placeholders (not executed in the authoring session):

```powershell
cmd /c "<command> > <file>"
<command> | Out-File -Encoding <encoding> <file>
```

If the consumer also rejects a UTF-8 byte-order mark, `Out-File -Encoding utf8` is not
enough on 5.1; use the BOM-less writer in
`skills/shell-scripting/rules/ps-utf8-no-bom.md`.

Verify by reading the file back with the real consumer (here: Python), or by dumping its
first bytes, before relying on it.

# Why

The session recorded the symptom and the fix, not the mechanism. What the record supports:
the redirect produced a UTF-16 file under Windows PowerShell 5.1, and both fixes either
move the redirect out of PowerShell or state the encoding instead of inheriting one.
Inference, not observed in this session: the redirect operator applies PowerShell's own
default output encoding, which is why the consumer saw bytes it did not expect. Related:
`skills/shell-scripting/rules/ps-utf8-no-bom.md` covers the BOM side of the same
5.1 encoding behaviour.
