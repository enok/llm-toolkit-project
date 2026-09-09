---
description: Run a mandatory static-analysis gate against only code added or modified in the current Git change set
---

# Changed-code quality gate workflow

Use this workflow for every validation that includes created or updated source
code. It is not required for documentation-only or configuration-only changes.
`rules/changed-code-quality-gate-required.md` makes it mandatory before commit,
push, PR readiness, or completion.

## Steps

1. Confirm the repository root, the intended base/head, and whether the run is
   local, pull request, or push validation.
2. Select the base:
   - local uncommitted work: omit `--base`;
   - branch/pre-PR: pass the trusted target branch or an immutable base SHA;
   - CI PR: check out the real event head with full history, then pass the
     immutable base and head SHAs using `--event pull_request`;
   - CI push: pass the event `before` and `after` SHAs using `--event push`; for
     a new branch, pass the repository's trusted integration trunk explicitly
     (this toolkit uses `main`; other repositories should pass their own default
     branch).
3. Run the repository's copy of `scripts/changed_code_quality_gate.py` with the
   active platform's Python launcher. Use `--scope-only` only to inspect scope;
   it is not analyzer coverage.
4. Review the JSON result. Verify that every included path is added or modified
   code, that every failing finding overlaps an added or modified line, and that
   every exclusion has a valid reason.
   Confirm that candidate `.gitignore`/`.semgrepignore` files, inline
   suppression comments, minified formatting, and vendor/build path names did
   not reduce the scoped or analyzer-reported file set.
   The reference adapters support Java, Python, JavaScript, TypeScript
   (including common module extensions), Bash, and PowerShell. Java uses the
   trusted Semgrep policy; shell scripts additionally require their platform
   syntax parser and changed-line policy checks. Other recognized languages,
   unrecognized file types, oversized source, and source-like symlinks exit
   blocked until project-native results are normalized to the same scope.
5. Stop on exit 1-4. Do not convert unavailable, malformed, timed-out, broader
   unfiltered, or stale analyzer evidence into a pass.
6. Continue with unit, integration, build, dependency, documentation, and
   security validation. This gate replaces none of them.

## Reference commands

```bash
python scripts/changed_code_quality_gate.py --base origin/main
python scripts/changed_code_quality_gate.py --event pull_request --base "$BASE_SHA" --head "$HEAD_SHA"
```

```powershell
python scripts/changed_code_quality_gate.py --base origin/main
python scripts/changed_code_quality_gate.py --event pull_request --base $env:BASE_SHA --head $env:HEAD_SHA
```

Replace `origin/main` with the repository's default branch when it differs. Use
the platform's usable Python launcher (`python`, `python3`, or `py -3`).

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Passed, or no applicable changed code |
| 1 | Changed-code findings |
| 2 | Git scope or configuration error |
| 3 | Required analyzer or coverage unavailable |
| 4 | Analyzer execution or report failure |

Never put secrets on the command line. Scanner credentials are permitted only
for trusted CI events and must follow the target project's existing
secret-handling policy.

## Related

- `skills/changed-code-quality-gate/SKILL.md` for the contract and configuration.
- `skills/changed-code-quality-gate/references/analyzer-selection.md` for
  normalizing project-native Sonar or SpotBugs results back to this scope.
- `.github/workflows/changed-code-quality-gate.yml` for the CI wiring that runs
  the gate implementation, configuration, and rules from a protected revision.
