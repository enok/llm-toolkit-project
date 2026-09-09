---
title: Agent self-reported counts are not evidence
category: toolchain
created: 2026-08-26
tags: [llm, agent, verification, count, audit, independent-check]
---

# Problem

Two parallel agent lanes misreported their own `FILL(` counts across a set of
dashboard JSON files (61 when the real number was 123; 49 when it was 57/58),
creating confusion about which dashboards were already converted. An
independent audit command settled it and exposed the discrepancy.

# Failed Approaches

- Trusting an agent's summary count: agents miscount, especially when the
  pattern also appears in expressions, comments, and nested structures.
- Asking the same agent to recount: the logic error that produced the miscount
  simply repeats.
- Manual visual inspection: in large JSON files with nested expressions, humans
  miss instances too.

# Solution

Verify any count that gates a decision with your own deterministic command:

```bash
# Total matches
rg "FILL\(" --type json | wc -l

# Per-file breakdown, for an audit trail
rg "FILL\(" --type json --count-matches

# Nested or multi-line values: extract strings first, then count
jq -r '.. | select(type == "string" and contains("FILL(")) | .' *.json | wc -l
```

Record the verification command and its output in the work log. Run the
independent check before accepting any count that gates marking work complete,
closing a ticket, or approving a PR.

# Why

LLM agents miscount for several reasons: tokenization artifacts, context
truncation on large inputs, pattern ambiguity (a match inside a comment versus
inside an expression), or plain hallucination. A count is a measurement, and
measurements that gate irreversible actions need a deterministic tool rather
than a narrative summary. An audit command is cheap insurance against a
misreported "done".
