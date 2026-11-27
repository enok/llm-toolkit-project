---
title: A local repo can be reachable from chat through a desktop file plugin even with no folder attached
category: environment
created: 2026-10-22
tags: [desktop-commander, local-files, chat, tooling, connected-folders, discovery]
---

# Problem

In several chat sessions the answer to "process this with the toolkit repo on my
drive" was "the chat cannot reach that machine; run it in a coding CLI". In a later
session the same repo was fully readable and writable. The difference was not the
chat app: the session exposed a desktop file-and-terminal plugin, and its tools
were deferred (not loaded) until searched for.

# Failed Approaches

- Concluding "unreachable" from the absence of an attached folder.
- Concluding "unreachable" without checking which local plugins the session had.

# Solution

- Before declaring a local path unreachable, call the device-info tool and read
  both `connectedFolders` and `localMcpServers`; load any file, terminal or git
  plugin tools through the tool-search mechanism.
- Use absolute Windows paths. Listing, reading, searching and PowerShell all work
  through the plugin even when `connectedFolders` is empty.
- Overwriting an existing file requires an explicit rewrite mode (the plugin
  rejects ambiguous writes); that guard also protects other sessions' files.
- Say exactly what was tried and which route worked, so the owner's picture of
  what the chat can reach stays accurate.

# Related

- `learnings/cloud-session-device-bridge-file-io.md`: moving files between a cloud
  session and the computer once the route is known.

# Why

Capabilities are per session and deferred by default; absence of one route says
nothing about the others.
