---
title: README catalog counts drift from the files on disk - recompute them before quoting
category: architecture
created: 2026-10-31
tags: [documentation, counts, drift, readme, catalog, validation, public-claims, cv]
---

# Problem

A repository README stated how many skills, workflows and learnings it contained, and those
counts did not match the files on disk. In one check the README listed 94 workflows while 96
workflow files were on disk, and its skill and learning counts were also stale. A count
copied from the README into a public place (a CV line, a profile entry, a PR description)
inherits the drift.

# Failed Approaches

- Quoting the README count because it sits next to the catalog and looks authoritative.

# Solution

- Compute any count that leaves the repository (CV, profile, article, PR text) from disk at
  the time of writing, for example `ls workflows/*.md | grep -vc README` or
  `find skills -mindepth 2 -maxdepth 2 -name SKILL.md | wc -l`, and note the date.
- When a change adds or removes a catalog item, update the README count in the same change
  and recompute it from disk instead of adding one to the old number.
- For a public claim, prefer a rounded floor ("90+") over an exact count that can go stale,
  unless the exact figure is verified in the same session.
- A validator that reviews a CV or profile draft recomputes counts from the evidence
  repository and flags any mismatch with the README or with the draft.

Durable guidance: skills/llm-context-engineering/SKILL.md (Known pitfalls) and
tool-subagents/cv-truthfulness-reviewer.md

# Why

Observed: the README totals differed from the directory listings. Inference: counts in
prose are written once by hand and nothing fails when a file is added, so they only move
when someone remembers to edit them; the file listing is the source of truth. The same
reasoning applies to any derived number stored in text: regenerate it from the source it
summarises.
