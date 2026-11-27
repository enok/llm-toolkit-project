# Device bridge, cloud sandbox and Windows tool pitfalls

Detail for the Known pitfalls in `SKILL.md`. Covers a cloud session working with a user's PC through a device bridge (`device_bash`, Desktop Commander), the sandbox's limits, and diagnosing an unreachable site.

## Moving and refreshing files through the bridge mount

- Refreshing files that already exist on the mount with `tar -xzf pkg.tgz -C existing_dir` or `cp new old` fails with `Cannot open: File exists`: the mount refuses unlink by default, so replace-by-recreate fails. Never unlink/recreate existing names there (no `tar -x`, `cp`, `mv` over them).
- Extract or copy to a NEW folder on the mount, then overwrite each existing file in place: `cat new/file > old/file` (truncate + write, no delete permission needed). Verify with `md5sum`.
- A command run through the bridge can hit its per-call timeout while the process keeps running: redirect output to a log file and poll the log.
- Keep transfer folders outside `.git`; writes into `.git` are refused, so use a folder that is not excluded.

## Zero-context patch from sandbox to device worktree

Every byte passes through the model; less text means fewer errors, and the checksum catches the rest. Send a zero-context patch, not whole files, and never base64 or whole-file pastes as the transport.

```bash
git diff --cached -U0 > <patch-file>             # sandbox
git apply --unidiff-zero --check <patch-file>    # device worktree; --unidiff-zero is required for -U0
git apply --unidiff-zero --index <patch-file>
```

Compare per-file SHA-256 with the sandbox values. On any mismatch do not commit; inspect or re-send that file only.

## Cowork bridge hides `skills/` and `tool-subagents/`

Symptom: with the toolkit folder connected through a Cowork bridge to a Windows PC, `ls skills`, `ls tool-subagents` and `grep`/`sed` on `tool-subagents/agent-orchestrator.md` return "Permission denied"; `git status` / `git show` print "warning: could not open directory 'skills/': Permission denied". Other folders (`rules/`, `workflows/`, `learnings/`, root files) read fine. The bridge refuses folder names it treats as Claude's own data folders, so these are unreadable even though they are ordinary repo directories. Untested: whether other protected names exist beyond these two, and whether granting the folder again changes the behaviour.

Routes that do not work: the auto-staged copy of the connected folder (`/mnt/user-data/uploads/cowork-folders/<folder>-<id>/`) held only `CLAUDE.md`, not the repo. Pushing from the cloud clone: `add_repo` (access push) reported `push_check: refused` because the Claude GitHub App is not installed for the account. `security-check-toolkit.sh` in the container exits 1 with "no external security or lint scanner produced a passing signal" (semgrep / SkillSpector are not installable under the egress allowlist); `validate-toolkit-indexes.sh` did pass there.

- **Read:** `add_repo` (owner/repo) then `git clone --depth 1` into the container. The clone has the full tree including `skills/` and `tool-subagents/`, and the index validators run there.
- **Write:** Desktop Commander `start_process` runs native PowerShell on the PC with the repo, `git` over SSH and an authenticated `gh`. Do not touch the user's own clone if it holds another session's uncommitted work. Create a separate worktree from `origin/main` at an ABSOLUTE path in a folder the owner named or approved for the task: `git -C <toolkit-clone> worktree add <abs-path>\<repo>-<topic> -b <branch> origin/main`.
- Commit in the container, export a git bundle or patch, move it with `SendUserFile` + `device_commit_files`; `device_commit_files` also accepts a `stagedPath` under `/mnt/user-data/outputs/`, which moves the bundle without posting a file card in the chat (the bundle's MD5 matched on both sides). Apply it in the worktree, push over SSH and open the PR with `gh pr create` on the PC (the container cannot, see "gh in the cloud sandbox" below).
- Run the PC security gates per "Windows security gate" below.
- The usual gates still apply: present learnings before commit (capture-learning approval) and merge only on explicit approval (no blanket merge).
- **Junction or symlinked folders** give the same `d?????????` / "Permission denied" symptom in the bridge's Linux shell. Read from a read-only clone of the public repo; reading or writing the folder itself through the native shell needs it to be an allowed folder or the owner's approval.
- **Git noise and residue:** `git status` through the bridge floods with warnings for the unreadable folders; filter with `git status -- . ':!skills' ':!tool-subagents'`. Device-side `git commit` via the bridge leaves `.lock` files that cannot be deleted, so run git natively on the PC.
- **Bundle clone pitfall:** a clone from `git bundle --all` maps `refs/heads`, so `origin/main` may be missing or stale and a branch cut from it silently uses an old base. Fetch an explicit mapping (`git fetch <bundle> refs/remotes/origin/main:refs/heads/upstream-main`) and verify the base SHA before branching.
- **Folders granted mid-session** may never mount in the sandbox: check with `ls` of the mount root, fall back to the device bridge or Desktop Commander for those paths and say so; do not loop on re-requesting.
- **Allowed folders only (owner decision, 2026-11-27):** work only in the folders the owner connected or named for the task. A refusal on a protected folder is a boundary, not an obstacle: do not copy a script or file out of it to run or edit it elsewhere, and do not reach it through another shell, plugin or path unless the owner approved that folder. When the task needs a folder that is not allowed, stop, say which folder and why, and ask the owner for approval (a folder-access request, or the owner runs that step). Reading the public repository through a cloud clone stays allowed: it never touches the protected folder.

## gh in the cloud sandbox

GraphQL is blocked from the container (and the repository is not attached), so every repeat fails the same way. Try `gh pr create` at most once (no manual probe first); after it fails, make no more GraphQL-backed calls (`gh pr list`, `gh pr view`, `gh api graphql`). Go straight to REST: `gh api -X POST repos/<owner>/<repo>/pulls -f title=... -f head=... -f base=...`, or run `gh` on the user's machine.

## Desktop Commander on Windows: long scans

- Never scan a whole drive in one recursive process: bridge calls have a per-call time limit and a whole-drive scan (over a million files) times out before returning. Start one `start_process` per top-level folder of each drive (and per suspect folder), narrowed to subtrees where possible.
- Poll each with `read_process_output` by pid with a timeout of at most about 170-175 seconds, writing results to a file so a timeout loses nothing.

## A site will not open for the user

Vantage points: cloud sandbox, the user's PC through the device bridge, and a browser tool. Their first answers can disagree (one tool refused to navigate at all while the site was merely slow). Work from the outside in and stop at the layer that fails:
1. Sandbox first (is the site up at all?). Testing only from the sandbox proves the site is up from there, not from the user's network.
2. The user's PC: DNS, hosts file, TCP connect, proxy and VPN settings, system clock, TLS.
3. A clean browser profile (no extensions, no sync).

- Compare `curl` with a browser user agent against plain `curl` timing. A multi-second gap on HTTPS usually means security software is scanning the connection. Inference from one case: the gap is a hint, not proof; confirm by repeating with the security software's HTTPS scanning disabled when the user agrees. Phone-hotspot IP ranges and outdated browsers also trigger anti-bot challenges.
- `claude-in-chrome` `navigate` can apply a built-in URL category filter. Do not conclude "the site is blocked" from its refusal: report it as a tool-level block and do not switch to another browser tool to open it. A reachability probe with `curl.exe` on the PC (no sign-in, no form data) is allowed for diagnosis only, with the user's consent.
- Before any `computer_*` screenshot or click action, call `computer_request_access` naming the exact app. UI panels animate in: take a fresh screenshot before clicking an element found in an earlier one.
- A vendor driver app can override an OS setting (for example a peripheral's scroll or button behaviour): check both the OS settings and the vendor's own app.
- A security filter can also cause local-file "Access denied".

## Windows security gate

Run the bash gate script through Git Bash, not the `.ps1` wrapper under Windows PowerShell 5.1:

```powershell
cmd /c '"C:\Program Files\Git\bin\bash.exe" -l scripts/security-check-toolkit.sh > <log> 2>&1'
```

Under PowerShell 5.1 the wrapper turns native stderr into an error record: it aborted at "Semgrep auto scan" with an empty `bash.exe :` NativeCommandError, exit 1, log truncated.

## A command that reads standard input swallows the rest of a piped script

Problem: a multi-step shell script sent to a shell through a here-document is the shell's own standard input. A command in it that also reads standard input consumes the remaining script lines. The shell then reaches end of input, every later step (state checks, verification, closing timestamp) is skipped, no error is printed, and the exit status is 0. The gap shows only because expected output sections are missing.

Observed once, with a remote-shell client run in connection-test mode that inherited the shell's standard input. Other standard-input readers (interactive container commands, media converters, read loops) are expected to behave the same way: untested.

Happy path:

```bash
ssh -o BatchMode=yes <host> true </dev/null   # give every possible stdin reader an empty input
echo SCRIPT-COMPLETE                            # sentinel as the last line
```

- Inside a script that arrives on standard input, redirect every command that may read it from the null device (`</dev/null`), or use the client's own no-input flag; or write the script to a file and run the file.
- End the script with a sentinel line and treat a missing sentinel as a failed run, because the exit status does not show the loss.

## Git over SSH from an automation-started process on macOS

Observed once: git over SSH run from a process started by a desktop automation tool failed with "Permission denied (publickey)" because the process had no SSH agent socket. On macOS, exporting the socket before the git command made fetch and push work:

```bash
export SSH_AUTH_SOCK=$(launchctl getenv SSH_AUTH_SOCK)
```
