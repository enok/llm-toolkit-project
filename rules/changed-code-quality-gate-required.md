---
trigger: always_on
description: Require a static-analysis quality gate scoped to added or modified code during code validation
---

# Changed-code quality gate required

Whenever source code is created or updated, code validation must include the
`changed-code-quality-gate` skill and `workflows/changed-code-quality-gate.md`.
The gate is blocking before commit, push, PR readiness, or completion.

- Derive scope from Git. Include added, modified, renamed destinations, and
  untracked code, including Git-ignored source; exclude only deletions and
  files with a NUL byte in the bounded content probe.
- For branch or PR validation, supply the trusted base so committed branch
  changes are not omitted. A local worktree-only run is insufficient proof.
- Count only findings mapped to changed files and added/modified line ranges.
  A broader project scan may provide context but must not be described as a
  changed-code result unless its findings are filtered to that scope.
- Candidate ignore files, inline analyzer suppression comments, minified
  formatting, and vendor/build-style path names must not remove changed source
  from analysis. Require analyzer coverage metadata for every scoped file.
- Validation is blocked by a configured mandatory analyzer that is missing,
  unusable, times out, emits malformed output or analysis errors, or cannot
  cover applicable code. Optional unavailable analyzers are `SKIP`/`WARN`,
  never `PASS`.
- The reference adapters cover Java, Python, JavaScript, TypeScript, Bash, and
  PowerShell. Java is analyzed by the same trusted Semgrep invocation and
  changed-line mapping as the other Semgrep languages. Bash and PowerShell use
  trusted syntax parsers plus changed-line policy checks. Changed code in
  another recognized language, an unrecognized file type, an oversized
  source file, or a source-like symlink blocks until a project-native analyzer
  (for example Sonar or SpotBugs) produces findings normalized to the same
  changed files and lines.
- Keep full test, build, dependency, and `security-check-toolkit` gates
  independent. Changed-code analysis supplements them; it replaces none.

The portable reference command is:

```text
python scripts/changed_code_quality_gate.py --base <trusted-base>
```

Use the active platform's usable Python launcher. Do not install analyzers,
pass credentials, or enable scanner MCP servers implicitly.
