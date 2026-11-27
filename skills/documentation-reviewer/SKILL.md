---
name: documentation-reviewer
description: Read-only documentation reviewer specialist for docs, runbooks, diagrams, generated LLM and tool-config surfaces, PR bodies, release notes, and human-facing documentation drafts, including an evidence-status audit (Tested, Implemented, Written, Decision, Gap) for docs about code that was never executed. Use whenever documentation was created or changed by an agent, chat, automation, script, or human and must be validated for source-grounded accuracy, audience fit, claim drift, and artifact quality before completion, or when a document claims that something "works" without test evidence.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.1.0"
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

## Evidence-status check

Use this when the documentation describes code, images, infrastructure or cloud
steps that were never built or run (offline sandbox, planned work, generated
drafts). A reader treats "works" as a promise, so every claim carries exactly
one status:

| Status | Meaning |
|---|---|
| Tested | A test or run was executed and its result is cited |
| Implemented | Code exists, no test evidence |
| Written | Described in text only, nothing implemented |
| Decision | A choice made, with its reason |
| Gap | Known missing or unverified |

Never upgrade Written or Gap to "works". Then audit with an independent pass
that did not write the document: first check each claim against the code, then
check the test evidence behind every Tested row. In one run 88 Tested rows were
checked, 68 were confirmed and 20 re-marked, and 13 wrong or loose claims were
corrected, so the second pass is not optional. Numbers quoted in public text
come from the documents that carry their caveat (sandbox only, not the target
runtime, shared CPU), never from a summary that dropped it. Related lesson:
[planned-or-asked-status-written-as-done-reread-source](../../learnings/planned-or-asked-status-written-as-done-reread-source.md).

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
