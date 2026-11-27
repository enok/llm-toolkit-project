---
title: A vector index kept in a file-sync folder was left at 0 bytes and crashed the database; keep the index in memory
category: toolchain
created: 2026-11-24
tags: [vector-database, file-sync, sqlite, segfault, index, rebuild, high-severity]
---

# Problem
A vector database kept its index files in a folder managed by a file-sync client. The sync client
left the index link file at 0 bytes, and the database process exited with a segfault status once
the index loaded. An index copied between machines arrived with zeroed vectors.

# Failed Approaches
None recorded beyond the failing setup described in Problem: the index files were kept inside the
synced folder and loaded from there.

# Solution
- Keep the index in memory by setting a very high sync threshold, and keep the vectors in the
  SQLite log. This avoided the crash in the recorded case.
- When an index was copied between machines and arrived with zeroed vectors, rebuild it from the
  stored texts instead of using the copy.
- This is already the default in the toolkit's knowledge-base design (the
  `LLM_KB_SYNC_SAFE_INDEX` setting).

# Why
The record shows the sync client left the link file at 0 bytes and that the process then crashed
when the index loaded. Inference, not observed: a file-sync client that rewrites or placeholders
index files conflicts with a database that expects them to stay intact on disk, so the index must
not live there.
