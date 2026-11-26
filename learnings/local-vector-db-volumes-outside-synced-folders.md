---
title: Keep local vector-DB container volumes outside cloud-synced folders
category: environment
created: 2026-11-26
tags: [docker, volumes, vector-db, knowledge-base, cloud-sync, compose-down, refresh-window]
---

# Problem
A project's local knowledge base ran as a vector database in a container. Its data volume sat
inside a folder that a cloud drive was syncing, and a cleanup command wiped more volumes than
intended.

# Failed Approaches
- Bind-mounting the database files under a synced folder: the sync client locks or rewrites
  files while the database writes them, which risks corruption and conflict copies.
- `docker compose down -v` to "reset" one service: `-v` removes every named volume of the
  stack, including cache volumes that took a long time to build.

# Solution
- Keep the volume data in a plain local folder (or a named Docker volume) outside every
  cloud-synced folder; sync only exports or backups.
- Before `down -v`, list the volumes (`docker volume ls`) and remove only the one you mean;
  use plain `down` otherwise.
- Schedule refresh and re-ingest windows so ingestion does not overlap with queries or backups.
- In a project that has a knowledge-base vector DB, query it to enrich answers and add new
  files and decisions as those instructions describe. See `skills/knowledge-base` for the
  conventions.

# Why
Sync clients and databases both assume they own the files, and `-v` is scoped to the whole
compose project, not to one service. Untested: bind mounts on a drive that syncs in
"online-only" mode.
