---
title: Adaptive/progressive skill loading — lightweight context by default
category: architecture
created: 2026-04-19
tags: [llm-toolkit, skills, context-optimization, progressive-disclosure, adaptive-loading]
---

# Problem

Loading all LLM skill content upfront bloats context, burns tokens, and slows sessions — even when most skills are irrelevant to the current task. A project with 30+ skills would inject hundreds of kilobytes into every session.

# Failed Approaches

1. **Embedding full skill content in rules files** — every session pays full token cost regardless of task.
2. **One giant AGENTS.md with all skills inlined** — unmanageable, stale, and slow.

# Solution

Two-tier loading pattern:

1. **Always loaded (lightweight):** Skill name + one-line description only — enough for the model to decide whether to invoke it.
2. **On demand (full content):** Full `SKILL.md` loaded only when the skill is explicitly invoked via `skill(SkillName)`.

### Directory layout
```
skills/
  research-thesis-support/SKILL.md
  thesis-bibliography/SKILL.md
  document-conversion/SKILL.md
  abnt-formatting/SKILL.md
  transparency-portal/SKILL.md
  ...
```

### Per-project filtering via `docs/llm/toolkit-selection.txt`
Each consuming project lists only the skills it needs. Skills not listed are never surfaced to the model — not even their names. Adding new skills to the toolkit has zero cost for projects that don't select them.

### Result
- Session starts with <1 KB of skill metadata instead of 100 KB+ of full content.
- Full skill text is only paid for when actually needed.
- Skills are versioned in one place; all consumers get updates automatically via the junction.

# Why

Progressive disclosure is a standard UX pattern applied to LLM context management. The model only needs enough information to recognize relevance; full implementation detail is deferred until invocation.
