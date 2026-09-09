---
title: A hanging validator trains agents to skip validation
category: testing
created: 2026-08-26
tags: [validation, hang, timeout, command-line-limit, xargs, testing]
---

# Problem

`validate-toolkit-indexes.sh` hung for five-plus minutes because it expanded 337
markdown paths into a single `awk`/`grep` argument list, overflowing the
command-line limit. Several sessions hit it, two dismissed it as
"environmental", and a full day of toolkit work went unvalidated until it was
fixed with `xargs`.

# Failed Approaches

- Assuming an environmental issue: "it works on the CI server" or "works in a
  different shell" sidesteps the real problem. The hang was reproducible and
  deterministic.
- Increasing timeouts: a longer wait does not fix a hang, it only delays the
  failure.
- Running a subset manually: partial validation gives false confidence, and the
  full run is what gates the commit.

# Solution

Fix the validator so it handles large input sets:

```bash
# Before — hangs on large file lists
FILES=$(find . -name "*.md")
awk '/pattern/ { print FILENAME }' $FILES

# After — works at any size
find . -name "*.md" -print0 |
  xargs -0 awk '/pattern/ { print FILENAME }'
```

Then prove the fix with a large synthetic input:

```bash
mkdir -p /tmp/validator-test
for i in $(seq 1 500); do touch "/tmp/validator-test/file$i.md"; done
./scripts/validate-toolkit-indexes.sh /tmp/validator-test   # should finish in seconds
```

Never accept "environmental" for a reproducible hang. Investigate, fix, and
validate the fix before moving on.

# Why

Shells and the kernel limit total command-line length. When a script expands a
glob or a variable into individual arguments, a large list exceeds that limit
and the command either hangs or fails with "Argument list too long". `xargs`
reads from stdin and batches arguments safely. A hanging validator is worse than
no validator: agents hit it, conclude validation is broken, and skip it — so
fixing it immediately is what keeps it a trusted gate.
