---
trigger: always_on
description: Write trial-and-error wins into the skill, rule or workflow that owns them; a learning file is only a short-lived intake, migrated and deleted
---

# Error-Driven Learning

- Before a non-trivial task, read `learnings/INDEX.md` (pending intake items only, normally none) and the owning assets' `## Known pitfalls`, and follow their solution.
- After trial-and-error, write the lesson into the asset that owns it: a skill `## Known pitfalls` bullet or reference, one workflow bullet, or one rule line (`workflows/capture-learning.md`). No ticket IDs, customer names, hostnames or credentials.
- Only when the owner is unclear, capture `learnings/<kebab-topic>.md` (frontmatter `title`, `category`, `created`, `tags`) plus its line in `learnings/INDEX.md`. Migrate it into its owner and delete the file and its INDEX line in that change, at the latest in the next toolkit maintenance pass; a migrated learning never keeps its file.
- Never reference `learnings/<slug>.md` for a file that does not exist. `tests/test_learning_promotion_coverage.py` fails on a dangling reference or a missing INDEX line.
