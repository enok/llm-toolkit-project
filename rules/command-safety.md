---
trigger: always_on
description: Review shell commands for destructive, exfiltration, or injection risk before execution
---

# Command safety

Before running a local command that has side effects, review it for safety first.

## Always review

- Commands with network access, downloads, or uploads
- Commands with pipes, shell substitution, or inline interpreter execution
- Commands whose literal search patterns or regexes contain shell-active characters such as backticks, `$()`, `;`, `&`, `|`, `<`, or `>`
- Installers and dependency-management commands
- Destructive file operations or Git history rewrites
- Commands touching secrets, auth files, or system-managed paths
- Privileged commands such as `sudo` or `su`

## Review flow

1. Split chained commands into independent segments.
2. If the repository provides a command-assessment script or policy, follow it.
3. Block critical-risk commands by default until the user explicitly reconfirms.
4. Ask for confirmation on high-risk commands and propose a safer alternative.
5. Quote literal patterns so the shell does not execute them. Prefer single-quoted literals for `rg`, `sed`, and similar; escape backticks or `$` when single quotes are not possible.
6. Keep the final command as narrow as possible.

## Windows command reliability

On Windows, command correctness includes the shell boundary.

- Prefer PowerShell-native commands for Windows filesystem and Git work unless a
  script specifically requires Git Bash.
- Keep Git Bash invocations narrow. Avoid broad pipelines that enumerate many
  Git metadata files or spawn a new shell per path when a scoped filesystem scan
  gives the same answer.
- Do not assume bare `bash` resolves to Git for Windows; it may invoke a WSL
  shim with different paths, repository state, credentials, and tools. Prefer
  the repository's PowerShell wrapper or resolve Git-for-Windows `bash.exe`
  explicitly. Before trusting a gate that reports no changed work, compare its
  discovery output with a host-side changed-file inventory and require every
  expected path.
- If a command times out, verify the resulting state before retrying or
  reporting failure. Some Git and filesystem commands finish after the tool
  timeout window.
- When passing PowerShell through Bash, quote or escape `$` so PowerShell
  variables such as `$_` are not expanded by Bash first.
- When passing paths to `cmd.exe` built-ins such as `mklink`, convert them to
  backslashed Windows form first (`cygpath -w` in Git Bash). `cmd.exe` parses
  forward-slash paths like `C:/Users/...` as switches and fails.
- Batch validation work into one script or one shell session when possible; many
  tiny cross-shell calls are slower and harder to reason about.

## Shell state does not reliably persist across tool calls

Exported environment variables can silently reset between separate command-execution tool calls, even when the working directory persists. Treating "the shell" as one continuous session across calls is the natural mental model but is wrong for at least some tool implementations. Export and consume a credential or dynamic value in the **same** call:

```bash
export API_TOKEN="..."
curl -u "user:${API_TOKEN}" "https://.../api/json"
```

Never split the export and the use across two separate tool invocations when the value matters (credentials, tokens, dynamic config). If a credential independently verified as correct still fails when used from inside a tool call, decode the literal bytes actually sent (e.g. `curl -v`, inspect the `Authorization` header) before assuming the credential itself is wrong — compare what was actually transmitted to what was intended.

## Credential handoff and discovery

When a task needs a credential the session does not already have:

- **Never enumerate, probe, or guess** at a credential's identity, username pairing, or shape — looping plausible usernames against one token, listing OS credential-manager entries, or printing even a masked prefix/length "to sanity check" are all in scope for this, not just literal secret reads. Ask the human for it directly instead.
- **Never delegate** a task to a sub-agent or tool whose prompt would need to embed literal credential commands or values; do that specific step inline in the current session instead.
- **Relay the credential through a scratch file**, not chat text: ask the human to write it to a temp file, read the file once, use the value immediately (same call, per the section above), then delete the temp file before doing anything else. This avoids a secret persisting in plaintext conversation history.
- Cross-check a handed-over credential's shape against the target system before spending time debugging apparent auth failures — different providers' tokens have recognizably different shapes, and being handed the wrong credential (pointed at the wrong system) is an easy-to-miss failure mode when multiple tokens are in flight.
- A safety classifier may block credential-adjacent actions beyond literal secret reads (env enumeration, username guessing, credential-store listing, credential-bearing delegation) while still allowing use of a credential once it is legitimately in hand. Treat a block here as a boundary to respect, not a puzzle to route around with a cleverer masked command.

## RTK command-output optimization

RTK (an open-source command-output compactor) may be used only where a
specific version and platform build has passed a privacy and provenance review
for your environment. On such a reviewed deployment, invoke the `rtk` binary
explicitly for high-output, non-interactive read/build/test commands whose
compact form preserves the evidence needed for the task. Good candidates
include Git status/log/diff, repository searches, dependency listings, and test
or lint runs. Other operating systems and RTK versions require their own
review before use.

- Do not route commands that mutate repository/history, remote services,
  infrastructure, privileges, approvals, or release/deployment state through
  RTK. Keep Git writes and history changes, Terraform/OpenTofu
  apply/destroy/import/state operations, cloud API mutations, and PR state
  changes on their raw command paths. Ordinary local compilation, tests, lint,
  and their disposable artifacts remain valid RTK candidates.
- Use the raw command when byte-exact output, full security evidence, complete
  Terraform plans, release evidence, or production diagnostics are required.
  Treat compact output as an optimization, not as the only source of truth.
- Preserve and check the wrapped command's exit status. If filtering fails or
  omits required evidence, rerun only the narrow command with RTK disabled.
- Never put secrets, tokens, credentials, or signed URLs in command arguments.
- Keep RTK telemetry, raw-output tee, hook audit, and persistent command-history
  storage disabled, and verify the effective environment plus the absence of
  any history database, tee directory, or audit log after a harmless smoke
  test. Some builds do not enforce `tracking.enabled = false` and let
  `RTK_DB_PATH` override the config file (observed on native Windows 0.44.x):
  there, set the user environment `RTK_DB_PATH=NUL` and
  `tracking.database_path = "NUL"` as well.
- Do not enable global automatic rewrite hooks (`rtk init`) without a separate
  security review. Prompt-level explicit use keeps command selection visible
  and makes state-changing exclusions enforceable.
- Report RTK reduction statistics only as approximate command-output savings;
  they are not exact tokenizer counts or total model/billing reductions.

## Link and generated-surface repair

Repair scripts that manage symlinks, junctions, or generated LLM surfaces must
preserve working links until a replacement is ready.

- Before a generator, mirror, sync, cleanup, or repair mutates a worktree,
  enumerate symlinks, junctions, and other reparse points in scope. Resolve
  each final target and prove it is contained by an explicitly approved
  writable root. A separate worktree is not an isolation boundary when a link
  resolves into another checkout; exclude unresolved or out-of-root targets
  and fail closed.
- Create the replacement link in a temporary path first, then verify target,
  type, and readability before replacing the existing link.
- Do not delete a healthy existing symlink or junction before the replacement
  has been verified.
- If an expected link path contains a regular file or directory, stop unless the
  user or script flag explicitly requested replacement.
- Treat optional compatibility links as warnings when canonical generated
  surfaces can still be refreshed safely.
- If Windows privileges, ACLs, or synced-folder behavior block link creation, report
  the exact path and command; do not leave the repo with a broken generated
  surface.
- If a command crossed a link boundary and mutated an external target, stop
  related writers before recovery. Inventory the affected paths, Git state,
  file modes, and link metadata; preserve the current affected bytes and dirty
  tracked state in a contained quarantine; and diff the proposed restore.
  Require explicit approval of the exact paths and trusted pre-incident ref
  before overwriting them, then compare restored bytes and link targets. Never
  use broad reset, recursive cleanup, or unvalidated archive extraction as
  recovery, and retain untracked evidence until review confirms the tracked
  surface is whole.

## Local artifact and preview boundaries

Generated artifact helpers still need explicit trust boundaries even when they
only run on a developer machine.

- For cleanup or overwrite paths, require a relative child path, resolve the
  parent and child to absolute paths, and verify the child is strictly under the
  expected parent before recursive delete, move, or overwrite operations.
- Do not trust string concatenation such as `Join-Path $outDir $userInput`
  without a resolved-path containment check.
- For temporary preview servers, bind explicitly to loopback, such as
  `127.0.0.1`, not only a loopback browser URL.
- Add focused validation for traversal inputs like `..` and for loopback-only
  listeners when a script starts a server.

This is guidance for the agent, not kernel-level enforcement.
