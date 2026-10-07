---
title: gh pr create fails in the cloud sandbox (GraphQL blocked, repo not attached); run gh on the user's machine
category: environment
created: 2026-10-07
tags: [gh-cli, gh-pr-create, graphql, cloud-sandbox, egress, pull-request, user-machine]
---

# Problem

`gh pr create` run in the cloud container failed. The session recorded two causes in the
same failure: the GitHub GraphQL API was blocked from the container, and the repository
was not attached to it. The session classed this as a low-severity env-constraint mistake,
found as a tool error.

# Failed Approaches

None recorded beyond the first attempt described in Problem: `gh pr create` failed in the
container, and the recorded fix is to move the PR work to the user's machine.

# Solution

Do pull-request work with `gh` on the user's machine, not in the cloud container. Route it
the same way the definitive builds are routed in
`learnings/cloud-sandbox-egress-blocks-registries-verify-on-user-machine.md` (through the
root session's device bridge; lanes cannot reach it), and report the container-side
attempt as blocked instead of retrying it.

# Why

The record names two causes: GraphQL was blocked from the container and the repository was
not attached. Inference, not observed in this session: the same sandbox network policy that
returned HTTP 403 for package registries and GitHub web in the related learning also blocks
the GraphQL endpoint, and `gh pr create` relies on that API, which is why the command fails
there even when other GitHub calls might work.
