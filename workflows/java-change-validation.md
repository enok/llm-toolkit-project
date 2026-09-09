---
description: Run a read-only Java specialist validation pass across Java diffs, tests, docs, build evidence, and reviewer reply drafts
---

# Java Change Validation

Use this workflow when Java changes need a specialist validation pass before
approval, merge, PR comment replies, or handoff to an implementer.

## Phase 1 - Establish Scope

1. Identify repo, base/head refs, branch, PR/ticket links, and dirty-tree state.
2. Preserve unrelated local changes. If ownership is unclear, keep validation
   read-only and do not stage unrelated files.
3. Gather project-local guidance: `AGENTS.md`, the repo's `docs/llm/`, build
   files, Java version/toolchain config, framework wiring, migration
   conventions, and relevant Java skills.
4. Capture exact validation evidence already available: local commands, CI jobs,
   test reports, PR body, docs, and reviewer reply drafts.

## Phase 2 - Invoke The Specialist

Use `tool-subagents/java-change-validator.md` as a read-only specialist. Provide:

- full diff or base/head refs;
- changed Java, test, docs, config, migration, and build files;
- relevant call paths and framework wiring to inspect;
- reviewer threads and reply drafts, when present;
- the required output contract from the specialist prompt.

The root agent remains responsible for user communication, edits, validation,
commits, pushes, and PR actions.

## Phase 3 - Reduce Findings

Accept only findings backed by code, tests, docs, build evidence, or full-thread
review. Reject generic Java advice that is not tied to the current diff.

Classify each finding:

| Severity | Meaning |
| --- | --- |
| Blocker | Correctness, compatibility, security, data, migration, or build risk that should stop merge/reply |
| Fix | Clear in-scope improvement needed before handoff |
| Evidence gap | Missing reliable command, CI report, test, or reviewer-thread context |
| Note | Non-blocking maintainability or follow-up guidance |

## Phase 4 - Implement Or Report

- If the user asked for fixes, make the smallest scoped code/docs/tests change,
  then rerun the narrowest meaningful Java validation.
- If the user asked only for validation, report findings and exact next checks.
- For reviewer replies, follow `rules/human-comment-reply-gate.md`: show exact
  draft text and target first; do not post, submit, resolve, delete, or send
  without explicit approval.

## Phase 5 - Closeout

Report:

- base/head SHA and files inspected;
- Java/framework guidance used;
- validation commands and CI/build evidence, including the changed-code quality
  gate (`workflows/changed-code-quality-gate.md`) when Java source changed;
- actionable findings or a clear "no findings";
- claim drift across code, docs, PR body, and reply drafts;
- human reply draft status;
- a learning/token-efficiency note for future toolkit improvement.

---

## Final Step - Evolution

If the validator missed a recurring Java issue, was too noisy, or required
excessive context, run `workflows/java-validator-evolution.md`.
