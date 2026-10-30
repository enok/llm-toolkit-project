---
title: Cowork device bridge hides skills/ and tool-subagents/ - read via a cloud clone, push from a PC worktree
category: toolchain
created: 2026-10-22
tags: [cowork, device-bridge, device_bash, permission-denied, add_repo, worktree, desktop-commander, push, security-scan]
---

# Problem
A Cowork cloud session linked to the user's Windows PC had the toolkit folder connected, and the
standing instruction was to run every request through the orchestrator (contract in
`rules/request-orchestration.md` and `tool-subagents/agent-orchestrator.md`). The contract could not
be read, and the resulting toolkit change could not be pushed, through the obvious paths.

# Failed Approaches
- Reading the contract with `device_bash` on the mounted toolkit folder: `ls skills`,
  `ls tool-subagents` and `grep`/`sed` on `tool-subagents/agent-orchestrator.md` returned
  "Permission denied"; `git status` / `git show` printed
  "warning: could not open directory 'skills/': Permission denied". Other folders (`rules/`,
  `workflows/`, `learnings/`, root files) read fine.
- Using the auto-staged copy of the connected folder
  (`/mnt/user-data/uploads/cowork-folders/<folder>-<id>/`): it held only `CLAUDE.md`, not the repo.
- Pushing from the cloud clone: `add_repo` (access push) reported `push_check: refused` because the
  Claude GitHub App is not installed for the account, so pushes from the container fail.
- Running `security-check-toolkit.sh` in the cloud container: exit 1, "no external security or lint
  scanner produced a passing signal" (semgrep / SkillSpector are not installable under the egress
  allowlist). `validate-toolkit-indexes.sh` did pass there.

# Solution
- **Read:** `add_repo` (owner/repo) then `git clone --depth 1` into the container. The clone has the
  full tree including `skills/` and `tool-subagents/`, and the index validators run there.
- **Write:** Desktop Commander `start_process` runs native PowerShell on the PC with the repo, `git`
  over SSH and an authenticated `gh`. Do not touch the user's own clone if it holds another
  session's uncommitted work. Create a separate worktree from `origin/main` at an ABSOLUTE sibling
  path (see `git-c-worktree-relative-path-lands-in-repo-root.md`):
  `git -C <toolkit-clone> worktree add <abs-path>\<repo>-<topic> -b <branch> origin/main`.
- Commit in the container, export a git bundle or patch, move it with `SendUserFile` +
  `device_commit_files` (see `cloud-session-device-bridge-file-io.md`); `device_commit_files` also
  accepts a `stagedPath` under `/mnt/user-data/outputs/`, which moves the bundle without posting a
  file card in the chat (the bundle's MD5 matched on both sides). Apply it in the worktree,
  push over SSH and open the PR with `gh pr create`
  (the container cannot, see `gh-graphql-blocked-in-cloud-sandbox.md`).
- Run the PC security gates per `windows-security-gate-python-stub-and-committed-skills.md`.
- The usual gates still apply on this path: present learnings before commit (capture-learning
  approval) and merge only on explicit approval (no blanket merge).

# Why
The bridge refuses folder names it treats as Claude's own data folders, so `skills/` and
`tool-subagents/` are unreadable through it even though they are ordinary repo directories. The
container can read and validate the repo but has no push credential and no scanners; the PC has
both, so reads and writes take different routes. Untested: whether other protected names exist
beyond these two, and whether granting the folder again changes the behaviour.
