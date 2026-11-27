# Multi-Copy Stacks and Short-Path Copies

## Reconcile applied-but-uncommitted drift before committing

Context: a stack existed in several synchronized copies (an app-repo branch worktree, a canonical infra-repo branch, and a short-path working copy initialized against the real backend). `git status` showed modified files the current session never touched: a prior session had authored and applied a change (a variable validation guard) in the working copy and mirrored it to the branch worktree, but never committed it.

- Do not assume a clean prior state and run `git add -A`: it would smuggle unrelated changes into the fix's commit.
- Do not revert the unknown diff: if it is already applied live, reverting creates git-vs-live drift and a surprise diff on the next plan.
- Before committing: run `git status` / `git diff` and explain every changed file; run `diff -rq` (excluding `.terraform`, logs, plans) between the branch copy and the real-backend working copy to learn which side is ahead.
- Classify each unexpected diff. If it is already applied/live, commit it separately with an honest message stating it was previously uncommitted applied config; if it is stale, sync it from the ahead side rather than reverting.
- Only then commit the new fix, and re-verify all copies are byte-identical for the touched files (docs included) after pushing.
- Why: working copies that apply against real backends can legitimately run ahead of git history when a session ends after apply but before commit. Every copy is a potential source of truth for some file, so check the provenance of each diff and make one commit per intent.

## Deep Windows paths break `terraform init` of git-sourced modules

- Symptom: on Windows, `terraform init` in a root consuming git-sourced modules (`git@github.com:...//modules/<name>`) fails with git errors such as "$GIT_DIR too big" when the working directory is deeply nested; the same root initializes fine elsewhere.
- Cause: git-sourced modules clone into nested `.terraform/modules/` cache directories whose absolute path length compounds the deep repo path; git (msys) fails when the computed `.git` directory path exceeds its limits. The failure is deterministic: re-running init or clearing `.terraform` does not help, and fetching the module repo into the cache by hand is fragile and fights Terraform's cache layout. Shortening the prefix is the only reliable fix.
- Fix: copy the roots plus local modules to a short scratch path (for example `C:\Users\<u>\AppData\Local\Temp\tfv\`) and run `terraform init -backend=false` then `terraform validate` there for static checks.
- For state operations, keep one short-path copy initialized against the real backend and run plan/apply from it. Treat the short-path copy as disposable; the repo checkout stays the source of truth.
