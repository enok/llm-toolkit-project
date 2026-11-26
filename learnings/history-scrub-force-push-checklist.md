---
title: Scrubbing terms from git history and force-pushing - checklist
category: security
created: 2026-11-26
tags: [git, filter-repo, force-push, history-rewrite, tags, mirror-scan, backup]
---

# Problem
Terms that should never have been public (names, identifiers) had to be removed from the whole
history of a shared repository, not just from the latest commit. A partial scrub leaves the
terms reachable through old tags, stale remote branches, or a local ref that is pushed later.

# Failed Approaches
- Editing files in a new commit: the old commits still contain the terms.
- Rewriting history but leaving tags: the tags keep pointing at the old commits.
- Pushing from a clone that still holds refs of the old history: this re-publishes the very
  commits that were scrubbed.

# Solution
1. Back up first (a mirror clone or bundle kept outside the repository and never pushed).
2. Run `git filter-repo` with the replacement or path rules for the terms.
3. Re-point tags to the rewritten commits (or recreate them).
4. Delete stale remote branches that still contain the old history.
5. Force-push the rewritten refs deliberately, after the owner approves
   (`rules/external-write-authorization.md`).
6. Scan a fresh mirror clone for the terms: the expected count is 0 hits across all refs.
7. Never push local refs of the old history; remove them from clones that will push.
8. Tell collaborators to re-clone, because their copies still hold the old commits.

Additions from later runs:
- Acceptance is a fresh mirror scan of blobs, paths, commit messages and tags with 0 hits.
- Another session's branch is rebased onto the rewritten history, never pushed from old refs; list
  the old local refs and mark them do-not-push (a temporary pre-push guard hook is optional).
- Keep the term list out of tracked files ("the list the owner gave"); a deny-list file stays
  untracked. When the owner adds items mid-run, extend that file and re-run the validators.
- Remove stale tool-directory copies or links of deleted skills.
- Strip a UTF-8 BOM that breaks a validator, in a separate commit.
- A pre-existing CI error found on the way is reported, not fixed in the scrub.
- Before flipping a repository public: audit all refs and personal emails, fix the git identity,
  audit in a clean clone, and answer "is it public?" with the verified visibility.
- Never copy the scrub scripts: they carry deny-list patterns. Related:
  `generalize-private-repo-into-public-toolkit-checklist.md`.

# Why
Git objects are reachable from any ref, so every branch, tag and stale clone is a path back to
the old content. The mirror scan is the check that proves the scrub, not the absence of the
terms in the working tree. A host may keep unreachable objects or pull-request refs for a
while; ask the host to purge them if that matters.
