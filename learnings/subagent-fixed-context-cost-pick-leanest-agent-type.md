---
title: A subagent's fixed context cost depends on its agent type, so pick the leanest one
category: toolchain
created: 2026-11-26
tags: [subagent, tokens, context, agent-type, tool-surface, orchestration, delegation-cost]
---

# Problem

A helper that does no work at all still costs tokens at start, because every tool schema and skill
listing it loads is paid before the first instruction runs. Measured once with an idle helper: about
78k tokens with a full tool surface, about 66k with a search-only one, and about 14k with a six-tool one.
On small tasks the tool and skill lists, not the work, dominate the cost.

# Failed Approaches

- Defaulting every dispatch to the general-purpose agent type: each small task pays the full fixed cost.
- Trimming only the prompt: the brief was short, but the fixed cost sat in the tool surface.
- Choosing a cheaper model alone: it lowers the per-token price but not the fixed token count.

# Solution

When dispatching a task, pick the agent type with the smallest tool surface that can do it, then the
cheapest model the tier allows. Keep the brief to the goal, exact input paths or IDs, boundaries, the
write location and the return contract. Where the platform lists agent types, compare their tool
counts before the first dispatch; if a narrow type brings its own role prompt that could bias the
result (for example a comparison run), use a lean general type instead. Re-measure on a new platform
or version with one no-op dispatch, since the numbers change.

# Why

Fixed context is paid once per lane. A wave of ten small tasks on a full tool surface spends several
hundred thousand tokens before any work happens, while the same wave on a narrow type spends a fraction.
Choosing the executor is therefore a cost decision as large as the model tier.
