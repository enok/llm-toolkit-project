---
title: Required status checks need job names that never change, so avoid matrix names
category: deployment
created: 2026-10-07
tags: [github, branch-protection, ci, status-checks, job-names, matrix, gh-cli]
---

# Problem

The rule applied when protecting `main`: add required status checks only AFTER the first
CI run, and only with job names that never change. Matrix-expanded names such as
`python (3.12)` do not qualify. This was a rule followed, not an incident recovered from.

# Failed Approaches

None recorded in the session notes; this was a rule applied from the start.

# Solution

1. Create the repo settings and an initial protection with no required checks (PR required
   with 0 approvals, `enforce_admins` true, no force-push, no deletion, conversation
   resolution). Squash-only merges and delete-branch-on-merge come from `gh repo edit`.
2. Give every CI job an explicit `name:` equal to its id. Do not use `strategy.matrix` for a
   required job; run several versions sequentially inside ONE job, named `python`
   (excerpt of `.github/workflows/ci.yml`):

```yaml
jobs:
  python:
    name: python
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: '3.12'
      - run: PYTHONPATH=src python -m unittest discover -s tests -t . -v
      - uses: actions/setup-python@v6
        with:
          python-version: '3.13'
      - run: PYTHONPATH=src python -m unittest discover -s tests -t . -v
```

3. After the first green PR run, read the real check names and apply the protection again
   with them as `required_status_checks.contexts`, sending the whole protection file.

```powershell
(gh api repos/<owner>/<repo>/commits/<head-sha>/check-runs | ConvertFrom-Json).check_runs.name
gh api -X PUT repos/<owner>/<repo>/branches/main/protection --input protection.json
```

Durable guidance: skills/multi-language-study-repo/references/repo-layout-and-protection.md

# Why

The recorded rule says what to do, not why. General guidance, not observed in this session:
GitHub matches a required check by its name, so a name that never reports, or that changes
when a matrix gains a version, leaves the pull request waiting on a check that never
arrives. Inference: hence the names are read back after the first run and kept fixed.
