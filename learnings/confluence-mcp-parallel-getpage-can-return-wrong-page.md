---
title: Parallel Confluence MCP getConfluencePage calls can return the wrong page
category: api
created: 2026-08-19
tags: [confluence, mcp, atlassian, parallel-tool-calls, getConfluencePage]
---

# Problem

Two `getConfluencePage` calls for different page IDs (`<page-id-A>` and
`<page-id-B>`) were issued in the same parallel tool block. Both results came
back with the body of the FIRST page — the second result claimed to answer the
second call but contained page A's content, `id` field included.

# Failed Approaches

- Batching independent `getConfluencePage` calls in one parallel block for
  speed: the second result silently duplicated the first. Nothing errored, so
  without checking the `id` inside the payload, the wrong content would have
  been used as the "backup" and the edit source for the other page.

# Solution

- Issue Confluence MCP page fetches sequentially. If you do batch them, verify
  that the `id` inside each result matches the `pageId` you requested before
  using the body for anything.
- Re-fetch any mismatched page in its own call — the sequential retry returned
  the correct body immediately.

# Why

The remote MCP server appears to mis-route or cache-collide responses when
identical tools run concurrently within one request. The tool-result envelope
gives no error, so the only defense is payload-level verification
(`content.nodes[0].id == requested pageId`). This matters most before
mutations: a backup taken from a mis-routed fetch makes the rollback artifact
worthless.
