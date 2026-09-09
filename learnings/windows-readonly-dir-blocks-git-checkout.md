---
title: Permission denied on Windows git checkout is usually the ReadOnly directory attribute, not symlinks
category: environment
created: 2026-08-26
tags: [windows, git, checkout, readonly, attribute, permission-denied, file-system]
---

# Problem

On Windows, `git checkout` fails with "cannot rmdir '.cursor/rules':
Permission denied" (and similar for 80+ directories), leaving ~93 phantom
deletions that must be recovered with `git restore .`. Checkout by branch
name also fails outright when the branch is already checked out in a
linked worktree.

# Failed Approaches

- Blaming symlinks: `core.symlinks` was already false and the scripts
  were already junction-first (`mklink /J`), so neither symlink mode nor
  junction creation logic was the cause.
- Suspecting process handles: no indexer or file explorer held locks on
  the affected directories (verified with `handle.exe`).
- Trying different checkout methods: both `git checkout <branch>` and
  `git worktree add` failed identically.

# Solution

Remove junctions as links only (no `/s` flag), clear the ReadOnly
attribute recursively, then mark link surfaces as skip-worktree:

```powershell
# Remove junctions without touching targets
cmd /c "rmdir `.cursor\rules`"

# Clear ReadOnly attribute recursively on all directories
Get-ChildItem -Recurse -Force -Directory |
  Where-Object { $_.Attributes -band [IO.FileAttributes]::ReadOnly } |
  ForEach-Object { $_.Attributes = $_.Attributes -band (-bnot [IO.FileAttributes]::ReadOnly) }

# Mark link surfaces as skip-worktree (durable)
git update-index --skip-worktree .cursor/rules .cursor/workflows .agents/skills
```

Verified non-destructive: `.agents/skills` held 90 files before and after.
For the branch-already-checked-out error, use worktree-relative paths or
detach the worktree first.

# Why

`RemoveDirectory()` returns `ERROR_ACCESS_DENIED(5)` on any directory
carrying `FILE_ATTRIBUTE_READONLY`, regardless of whether it contains
files. Git's MinGW layer maps this to EACCES "Permission denied".
Controlled test: `rmdir` on a normal empty dir exits 0, on a ReadOnly
empty dir exits 5. The ReadOnly attribute was present on 84 directories
in the affected tree.
