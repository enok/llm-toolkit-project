---
title: Confluence MCP getConfluencePage exposes no numeric version for backups
category: api
created: 2026-08-19
tags: [confluence, mcp, version, backup, rollback, updateConfluencePage]
---

# Problem

Pre-mutation backups of Confluence pages must record the page version for the
rollback manifest, but the Atlassian MCP `getConfluencePage` result carries only
a human-relative `lastModified` ("6 minutes ago") — there is no numeric version
field. Backup agents could not record the pre-edit version directly.

# Failed Approaches

- Looking for a version field anywhere in the `getConfluencePage` response, in
  either markdown or html content format: only `lastModified` exists.
- Assuming the version seen at creation time is still current: one target page
  had been modified minutes before the run, so cached or assumed versions are
  unsafe.

# Solution

- Record `lastModified` in the backup `meta.json`, plus an explicit note that
  the numeric version was unavailable at fetch time.
- After the write, take the authoritative number from the
  `updateConfluencePage` response — it returns the NEW version — and infer
  pre-edit = new - 1.
- Confirm the increment is exactly 1. A jump greater than 1 means someone else
  wrote between your fetch and your update, so the backup no longer matches the
  state you overwrote and the rollback artifact must be re-taken.

# Why

The MCP tool surface is a simplified projection of the Confluence REST API;
`version.number` is mapped into write responses but not into the read tool.
Rollback safety therefore has to be established retroactively via the
single-increment check rather than up front.
