---
trigger: always_on
description: Capture trial-and-error wins as indexed learnings, consult learnings/ before starting a task, and migrate reusable lessons into durable toolkit assets
---

# Error-Driven Learning

- Before a non-trivial task, read `learnings/INDEX.md` and the files that match the task, and follow their solution.
- A learning is one file `learnings/<kebab-topic>.md` (frontmatter `title`, `category`, `created`, `tags`), captured through `workflows/capture-learning.md`, with no ticket IDs, customer names, hostnames or credentials.
- Every learning has a one-line entry under its category in `learnings/INDEX.md`, committed with the file and with its link from the owning skill, rule, workflow or agent (a `## Known pitfalls` bullet, or the path in text that already states the lesson). `tests/test_learning_promotion_coverage.py` fails on an unlinked learning or a missing INDEX line.
- Migrate learnings into durable assets at most 5 files per batch. A migrated learning keeps its file and INDEX line (owners and run records link it; `scripts/validate-toolkit-indexes.sh` fails on a missing target). Strike an INDEX line through only when the learning is superseded, naming the replacement, and link both from the owner. A learning that cannot be migrated safely stays, with the blocker reported.
