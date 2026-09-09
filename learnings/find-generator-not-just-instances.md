---
title: Find the generator, not just the instances
category: architecture
created: 2026-08-26
tags: [templates, generator, pattern, root-cause, contract-test, regression]
---

# Problem

A bad pattern (`FILL(m,0)+TIME_SERIES(0)`) appeared in five of six dashboard
bodies across two repositories. A contract guard was written to ban the pattern
in deployed dashboards, but the template that generated it kept producing new
instances. Fixing instances without fixing the source guarantees regression.

# Failed Approaches

- Fixing instances manually: the pattern reappeared in every new dashboard
  created from the same template.
- Writing a contract test on the output only: it caught deployed instances but
  could not stop the template from emitting the pattern again.
- Searching for literal matches only: the pattern was assembled from variables
  and loops in the template, so grepping for the exact string returned zero hits
  in the generator.

# Solution

Trace instances back to their generator and fix both sides:

```bash
# 1. Find all instances
rg "TIME_SERIES\(0\)" --type json

# 2. Trace to the source: which commit introduced it?
git log --follow --all -p -- path/to/instance.json | grep "TIME_SERIES"

# 3. Find the template or script that emits it (search by fragment, not literal)
rg "TIME_SERIES" -g '*.tftpl' -g '*.py' -g '*.sh' -g '*.j2'

# 4. Fix the generator first, then regenerate/fix all instances in one commit

# 5. Guard both sides:
#    - a contract test on deployed output (fails on bad instances)
#    - a lint/validation check on the template source (fails on a bad generator)
```

Record the template location in the fix commit message so future archaeologists
do not re-derive the same root cause.

# Why

Code generation, templating systems, and copy-paste from "a working example"
propagate patterns across a codebase. An instance-only fix treats the symptom
while the generator keeps producing new ones. A contract guard on output
provides detection but not prevention; only fixing the generator prevents
recurrence. When the same defect appears in several places with the same shape,
assume a shared generator exists and go find it.
