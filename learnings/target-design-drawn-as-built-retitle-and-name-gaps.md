---
title: Diagrams labelled as built showed controls the sources say are missing; retitle, name the gaps, re-validate
category: architecture
created: 2026-11-24
tags: [diagrams, as-built, target-design, validation-gap, gaps, documentation]
---

# Problem
Diagrams labelled as built showed controls that the sources say are missing. A target design was
drawn as if it existed. The session classed this as a medium-severity validation gap.

# Failed Approaches
- Labelling the diagrams as built without checking each drawn control against the sources.

# Solution
Retitle the diagram so it does not claim to be as built, name the gaps in the text and in the
diagram, and validate it again against the sources.

# Why
A diagram that mixes target and current state reads as a statement of fact about what exists.
Inference, not observed: checking each drawn element against the sources, not only the label, is
what separates a built control from a planned one.
