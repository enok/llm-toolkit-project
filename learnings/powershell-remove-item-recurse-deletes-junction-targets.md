---
title: Remove-Item -Recurse -Force on a junction deletes the target's contents
category: environment
created: 2026-08-26
tags: [powershell, junction, symlink, remove-item, data-loss, windows]
---

# Problem

On PowerShell 5.1, `Remove-Item -Recurse -Force` on an NTFS junction
deletes the target directory's contents, not just the junction link. This
sat in a link-repair helper script that is called on paths that are
routinely junctions pointing at canonical content trees.

# Failed Approaches

- Trusting PowerShell's documentation: the docs warn about symlinks but not
  junctions. Junctions are a separate reparse point type with different
  behavior.
- Using `-Force`: the flag bypasses prompts but doesn't change the
  recursive-into-target behavior.
- Testing on directories with junctions to empty targets: the bug only
  manifests when the target has content, so superficial testing missed it.

# Solution

Check for reparse points before removal and delete links non-recursively:

```powershell
function Remove-PathSafely {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }
    $item = Get-Item -Force -LiteralPath $Path
    if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
        # Delete the link only (no recursion, preserves target)
        [System.IO.Directory]::Delete($Path, $false)
    } else {
        Remove-Item -Recurse -Force -LiteralPath $Path
    }
}
```

Test the fix with a junction to a directory containing files:

```powershell
New-Item -ItemType Directory -Path C:\test\target
"content" | Out-File C:\test\target\file.txt
cmd /c "mklink /J C:\test\link C:\test\target"
Remove-PathSafely "C:\test\link"
Test-Path C:\test\target\file.txt  # Should be True
```

# Why

PowerShell 5.1's `Remove-Item -Recurse` follows junctions and deletes their
target contents. This is a known issue (fixed in PowerShell 7+) but remains
a hazard on Windows systems using the built-in 5.1. NTFS junctions
(`mklink /J`) are reparse points, not true symbolic links; checking the
`ReparsePoint` attribute distinguishes them from regular directories. The
low-level `System.IO.Directory.Delete($path, $false)` removes only the link.
