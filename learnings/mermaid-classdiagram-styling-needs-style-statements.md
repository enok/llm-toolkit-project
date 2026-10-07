---
title: Mermaid classDiagram boxes need one style line per class, and annotations need their own line
category: toolchain
created: 2026-10-07
tags: [mermaid, class-diagram, styling, style-statement, annotations, mermaid-cli, diagrams]
---

# Problem

With mermaid-cli 11, class-diagram boxes stayed uncoloured when styled through
`cssClass` or through separate `class X:::role` lines. Separately, a `<<interface>>`
annotation written on a member line rendered as `<>`.

# Failed Approaches

- `cssClass` statements: the boxes were not coloured.
- Separate `class X:::role` lines: the boxes were not coloured.
- `<<interface>>` placed on a member line: it rendered as `<>`.

# Solution

Colour each class with its own `style ClassName fill:...,stroke:...` line, and put the
annotation on its own line inside the class body. This renders correctly (checked in the
authoring sandbox with a mermaid-cli 11 render):

```text
classDiagram
    direction TB
    class Context {
        -strategy Strategy
        +run() Result
    }
    class Strategy {
        <<interface>>
        +execute(input) Result
    }
    Context o-- Strategy : has-a
    style Context fill:#B8E2B4,stroke:#2F6B35,stroke-width:2.5px
    style Strategy fill:#FDDCB5,stroke:#B35C0F,stroke-width:2.5px
```

Add a one-line colour key under each class diagram in the surrounding Markdown (for
example "green = context, light orange = abstraction"), since colour carries the roles.
The role palette and the rest of the style rules live in the diagram style reference.

Durable guidance: skills/diagram-authoring/references/publication-diagram-style.md

# Why

The session observed these behaviours on mermaid-cli 11: `cssClass` and separate
`class X:::role` lines did not colour class boxes, a `style` line per class did, and the
annotation placement changed the output. It did not establish why the first two are
ignored, and it did not compare other mermaid-cli versions. General guidance, not
observed in this session: re-render one class diagram after any mermaid-cli upgrade
before restyling a whole set, because the behaviour was seen on one major version.
