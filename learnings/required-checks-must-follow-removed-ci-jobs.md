---
title: Required status checks must change in the same window that removes a CI job
category: deployment
created: 2026-10-07
tags: [github, branch-protection, ci, status-checks, required-checks, language-set, gh-cli]
---

# Problem

A study repo can shrink its language set later (for example four languages down to one).
The change deletes the language folders and their CI jobs, but branch protection on `main`
still lists those job names as required status checks. A required check whose job no longer
runs never reports, so the pull request that removes the job would wait on "Expected -
Waiting for status to be reported" and could not merge. The session notes record this as a
rule applied proactively, not as an incident that was recovered from.

# Failed Approaches

None recorded in the session notes; rule applied proactively.

# Solution

1. Plan the removal as one change set in one PR: delete the language folders, delete their
   jobs from the workflow, drop them from the code-by-component config and regenerate the
   page, update the README, the video list and the repo description.
2. BEFORE merging that PR, rewrite the required checks to the jobs that remain
   (`<language>` and `docs`). The `PUT` needs the whole protection file, so edit
   `protection.json` so `contexts` lists only the remaining jobs and apply it:

```powershell
(gh api repos/<owner>/<repo>/branches/main/protection/required_status_checks | ConvertFrom-Json).contexts
gh api -X PUT repos/<owner>/<repo>/branches/main/protection --input protection.json
```

3. Wait for the remaining checks, merge under the normal merge rule, read the protection
   back, and confirm CI on `main` is green.

Adding a language is the mirror image: its job runs once first, and only then does its name
become a required check.

Durable guidance: skills/multi-language-study-repo/SKILL.md (section "Reducing the language
set later") and skills/multi-language-study-repo/references/repo-layout-and-protection.md.

# Why

The recorded rule says what to do, not why. Inference, not observed in this session: GitHub
matches a required check by name against the check runs reported for the PR head, a deleted
job produces no check run, and with administrators enforced nobody can bypass the missing
check. Lowering the required list before the merge also costs nothing, because it only drops
checks for code that the same PR deletes. Related: `branch-protection-required-checks-need-stable-job-names.md`
covers the first half of the same interface (names must not change).
