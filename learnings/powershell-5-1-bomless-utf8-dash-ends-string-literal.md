---
title: A BOM-less UTF-8 PowerShell script with an em dash in a string does not parse on Windows PowerShell 5.1
category: environment
created: 2026-11-26
tags: [powershell, windows-powershell-5.1, encoding, utf-8, bom, em-dash, parse-error, ascii, bootstrap]
---

# Problem

A `.ps1` file saved as UTF-8 without a BOM ran on PowerShell 7 and in CI, but failed on stock
Windows PowerShell 5.1 with `Missing ')' in method call` at a line that looked correct. The line
held an em dash inside a double-quoted string. PowerShell 5.1 reads a BOM-less file in the ANSI
code page, where the three UTF-8 bytes of an em dash decode to three characters, the last one a
right typographic quote. PowerShell accepts typographic quotes as quote characters, so the string
ended there and the rest of the line was parsed as code. En dashes, box-drawing lines and arrows
decode to a typographic quote the same way.

# Failed Approaches

- Trusting CI: the Linux runner uses PowerShell 7, which reads UTF-8, so the check stayed green.
- Trusting a run that went through a temporary copy: a copy written with a BOM parses, so the
  defect in the tracked file stayed hidden.
- Linting only: the analyzer reported a missing BOM as a warning among many others.

# Solution

Keep PowerShell sources ASCII-only: use `-`, `->` and `...` in strings and comments. Where
non-ASCII text is required, save the file as UTF-8 with a BOM. Enforce it with a unit test that
fails on any tracked `.ps1`, `.psm1` or `.psd1` that has a non-ASCII byte and no BOM
(`tests/test_powershell_scripts_ascii.py`). To confirm a script on the lowest supported shell,
parse it there without running it:
`[System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$null, [ref]$errors)`.

# Why

The defect only shows on the shell most Windows users have by default, and only when the tracked
file itself is executed. A byte-level test catches it on every platform, before anyone runs it.
