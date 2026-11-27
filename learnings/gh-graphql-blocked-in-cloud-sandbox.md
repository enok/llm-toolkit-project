---
title: gh pr create fails in the cloud sandbox (GraphQL blocked, repo not attached); run gh on the user's machine
category: environment
created: 2026-10-07
tags: [gh-cli, gh-pr-create, graphql, cloud-sandbox, egress, pull-request, user-machine]
---

# Solution
- In the container, try `gh pr create` at most once (no manual probe first); after it fails,
  make no more GraphQL-backed calls (`gh pr list`, `gh pr view`, `gh api graphql`).
- Go straight to REST: `gh api -X POST repos/<owner>/<repo>/pulls -f title=... -f head=... -f base=...`.

# Why
GraphQL is blocked from the container, so every repeat fails the same way.
