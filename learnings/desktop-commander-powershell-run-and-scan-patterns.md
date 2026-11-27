---
title: Desktop Commander on Windows - PowerShell run mode, split destructive calls, scan per folder, hand off elevation
category: toolchain
created: 2026-11-26
tags: [desktop-commander, powershell, start_process, remove-item, long-scan, read_process_output, elevation, classifier, windows]
---

# Problem
Cleaning and inspecting a Windows PC through Desktop Commander `start_process` hit several
recurring failures: wrapped PowerShell commands behaved unreliably, a command that mixed
`Remove-Item` with diagnostics was blocked, whole-drive recursive scans timed out, and an
elevated command was refused.

# Failed Approaches
- Wrapping the script as `powershell -NoProfile -Command "..."` inside the command string:
  quoting and `$` handling were less reliable than passing the script directly.
- One command that deleted files and also printed diagnostics: the delete verb made the whole
  call blocked, including the harmless part.
- One recursive scan over a whole drive: it timed out before returning.
- `Start-Process -Verb RunAs` to get elevation: denied by the auto-mode safety classifier;
  retrying the same call does not change the verdict.
- Variables written as `$name` in a command that crossed the device bridge: the `$` text was
  stripped before PowerShell saw it.

# Solution
- Set the shell to `powershell.exe` and send the raw multi-line script. Put anything with `$`
  variables or nested quotes in a script file and run the file; see
  `skills/shell-scripting/rules/ps-file-vs-command-args.md`.
- Keep destructive verbs (`Remove-Item` and similar) in their own call, after the read-only
  diagnostics have run and the user has approved the list.
- Split long scans: one process per top-level folder, narrowed to subtrees where possible.
  Poll each with `read_process_output` by pid and a timeout of about 170-175 seconds, and
  write results to a file so a timeout loses nothing.
- When elevation is needed, stop and hand off to the user with the options (run the
  elevated step themselves, change the setting in the UI, or accept a smaller non-elevated
  scope) instead of retrying.
- `docker compose down -v` also removes named volumes, including cache volumes; check which
  volumes exist before using `-v`.
- The chat app cannot create local OS scheduled tasks: put the registration script in the
  prompt for the user to run, and say so. It also cannot reach the toolkit repo: apply the
  request-orchestration contract from memory and say that this was done.
- General file movement and large scans through the bridge:
  `learnings/cloud-session-device-bridge-file-io.md`.

# Why
The classifier judges the whole command, so one destructive verb taints everything in the same
call. Scans through a bridge have a per-call time limit, so the work has to be chunked and
polled. Elevation is a decision for the person at the keyboard. Untested: whether the same
splits are needed on PowerShell 7.
