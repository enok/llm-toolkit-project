---
title: Mining a private work repo into the public toolkit - generalize, deny-list, scan
category: security
created: 2026-11-26
tags: [generalize, private-repo, deny-list, identifier-scan, public-toolkit, sanitization, intake]
---

# Problem
The owner asked to take all useful knowledge from a private work-tooling repository into the generic
toolkit without copying company or project names.

# Failed Approaches
- Copying files and renaming afterwards: the names remain in history.
- Keeping the deny-list inside the repository: the list itself leaks the terms.

# Solution
- Copy only generic patterns, agents and skills.
- Replace company module inventories with a generic stack inventory pattern.
- Generalize product-specific skills (performance testing, cross-environment data copy).
- Keep the deny-list in an untracked file.
- Scan identifiers (zero hits) before pushing.
- Install the tools the source uses only if the owner asked.
- Do not name the source repository.
- Related: `history-scrub-force-push-checklist.md`, `skills/external-skill-intake/SKILL.md`.

# Why
Sanitising at copy time is cheaper and safer than scrubbing history later.
