---
title: terraform init of git-sourced modules fails on deep Windows paths - validate from a short-path copy
category: environment
created: 2026-08-19
tags: [terraform, windows, git, init, modules, path-length, workaround]
---

# Problem

On Windows, `terraform init` in a root consuming git-sourced modules
(`git@github.com:...//modules/<name>`) failed with git errors like
"$GIT_DIR too big" when the working directory was deeply nested (long
repo paths under `C:\Users\<user>\code\...`). The same root initialized
fine elsewhere.

# Failed Approaches

- Re-running init / clearing `.terraform`: the failure is deterministic -
  the module cache path under `.terraform/modules/` plus git's temp dirs
  exceed what git's msys layer tolerates.
- Fetching the module repo manually into the cache: fragile and fights
  Terraform's cache layout.

# Solution

Copy the roots plus local modules to a short scratch path (e.g.
`C:\Users\<u>\AppData\Local\Temp\tfv\`) and run
`terraform init -backend=false` + `terraform validate` there for static
checks. For state operations, keep one short-path copy initialized
against the real backend and run plan/apply from it. Treat the short-path
copy as disposable - the repo checkout stays the source of truth.

# Why

Git-sourced Terraform modules clone into nested cache directories whose
absolute path length compounds the already-deep repo path; git (msys)
fails when the computed `.git` directory path exceeds its limits.
Shortening the prefix is the only reliable fix on Windows.
