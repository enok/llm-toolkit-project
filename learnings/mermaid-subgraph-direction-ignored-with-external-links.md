---
title: Mermaid subgraph direction is ignored when its nodes link outside the subgraph
category: toolchain
created: 2026-10-07
tags: [mermaid, flowchart, subgraph, direction, layout, aspect-ratio, diagrams]
---

# Problem

In a flowchart with an outer left-to-right direction and an inner `direction TB`
subgraph, the inner direction was ignored because the subgraph's nodes linked to nodes
outside it. The whole diagram collapsed into a 5.6:1 strip, which is illegible once it is
scaled into an article column (aim for an aspect ratio between 2:1 and 1:1.6).

# Failed Approaches

- Setting `direction TB` inside the subgraph of an LR flowchart: ignored whenever the
  subgraph's nodes had links to the outside.

# Solution

Do not rely on a subgraph `direction`. Decide the shape with the outer direction and the
structure: fan out, fold the chain into ranks, or split into two diagrams, then check the
rendered aspect ratio. A top-to-bottom fan-out renders like this (checked in the
authoring sandbox with mermaid-cli 11):

```text
flowchart TB
    Client(["Client"]) --> UC["Use case"]
    UC --> P1{{"Port: Repository"}}
    UC --> P2{{"Port: Notifier"}}
    P1 -.-> A1["DB adapter"]
    P2 -.-> A2["Mail adapter"]
```

A subgraph is still fine as a visual grouping; just do not expect its `direction` to
apply when its nodes link outside it. Two syntax traps seen in the same session: a node
id of `default` or `DEFAULT` collides with a Mermaid keyword (use an id such as
`DefaultCase`), and any label that contains `:`, `(`, `)`, `/`, `,`, `'` or `?` must be
quoted, as in `P1{{"Port: Repository"}}` above.

Durable guidance: skills/diagram-authoring/references/publication-diagram-style.md

# Why

The session observed the condition (a subgraph whose nodes link outside) and the outcome
(a 5.6:1 strip), and the visual check by a separate validator caught strips like it. General
guidance, not observed in this session: Mermaid's documentation says a subgraph with links
to the outside inherits the parent's direction, which would explain an LR parent flattening
an inner TB chain. Because the layout can change between renderer versions (a sandbox 11.16
and a machine 11.17 laid the same file out differently), judge the PNG that is actually
committed.
