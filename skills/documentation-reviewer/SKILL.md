---
name: documentation-reviewer
description: Read-only documentation reviewer specialist for docs, runbooks, diagrams, generated LLM and tool-config surfaces, PR bodies, release notes, and human-facing documentation drafts. Use whenever documentation was created or changed by an agent, chat, automation, script, or human and must be validated for source-grounded accuracy, audience fit, claim drift, and artifact quality before completion.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.0.0"
---

# Documentation Reviewer

Route documentation created or changed by any agent, chat, automation, script,
or human through the read-only Documentation Reviewer specialist before the
work is treated as complete. `rules/documentation-review-required.md` makes
this mandatory for README files, runbooks, architecture docs, generated LLM or
tool-config surfaces, PR bodies, release notes, wiki content, API docs,
diagrams, screenshots, PDFs, and human-facing documentation replies.

## When to Use

- "review these docs", "validate the generated documentation", "check the PR
  description", "is this runbook accurate"
- A task produced or changed documentation and is about to be declared done
- A documentation reply to a reviewer or stakeholder must be drafted

## Workflow

1. Load `workflows/documentation-reviewer-validation.md`.
2. Invoke or follow `tool-subagents/documentation-reviewer.md`.
3. Keep root-agent ownership for edits, validation, commits, pushes, and
   user-facing communication.
4. Require artifact QA (`image-quality-inspection`) for generated diagrams,
   screenshots, PDFs, rendered docs, or slide/document exports.
5. Keep human-facing documentation replies draft-only until explicit user
   approval (`rules/human-comment-reply-gate.md`).
6. Compose with `confluence-documentation-specialist`,
   `diagram-creation-specialist`, `system-architecture-specialist`,
   `pr-validator`, and domain specialists only when their evidence lanes are
   relevant.
7. If the specialist misses a reusable pattern, run
   `workflows/documentation-reviewer-evolution.md`.

## Required Context

- The changed docs, their destination, and their intended audience.
- The source evidence each doc claims to summarize: code diffs, tests, build
  logs, API specs, diagrams, tickets, PR bodies, comments, and wiki pages.
- Required gates: artifact QA, human reply approval, security checks, workflow
  size limits, and tool-config sync status.

## Expected Output

Evidence-backed findings separated into blockers and optional polish, claim
drift, artifact QA status, draft-only human-facing replies, the validation that
proves the doc is now accurate, related-specialist handoffs, and a
learning/token-efficiency note.
