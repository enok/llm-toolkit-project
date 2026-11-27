---
name: token-efficiency
description: "Reduce LLM token consumption during agent work: command-output compaction proxies (RTK), gh --json and jq field selection, ripgrep output budgeting, ast-grep structural search, and repomix context packing. Use when sessions burn context on command output, large file dumps, API responses, or repo-wide searches, or when choosing safe token-saving tools."
license: MIT
metadata:
  author: dev-tools
  version: "1.1.0"
---

# Token Efficiency

Practical, security-reviewed techniques to cut token consumption without losing the evidence a task needs. Compact output is an optimization, never the only source of truth: when compaction omits required evidence, rerun the narrow raw command.

## Principles

1. **Select fields, don't dump payloads.** Ask APIs and CLIs for only the fields the task needs.
2. **Budget search output before running it.** Counts and file lists first; matching lines only for the narrowed set.
3. **Compact high-volume command output** through a reviewed proxy where one is approved.
4. **Isolate bulk reading in subagents.** A fan-out agent reads the 40 files and returns the conclusion; the parent keeps only the reduced result.
5. **Never trade evidence for tokens** on security, release, production, or byte-exact tasks — those stay raw (see `rules/command-safety.md`).

## Techniques

### RTK command-output compaction (reviewed deployments only)

Prefix high-output, non-interactive read/build/test commands with `rtk` (e.g. `rtk git status`, `rtk mvn test`). 60-90% output reduction with preserved exit codes.

- Follow `rules/command-safety.md` for the full constraint set: never route repository/history, remote-service, infrastructure, privilege, approval, release, or deployment mutations through RTK; keep byte-exact/security/production evidence raw; preserve and check exit status.
- Never run `rtk init`, `rtk trust`, `rtk telemetry enable`, `rtk llm-proxy`, `rtk claude`, `rtk pipeline add` or `rtk plugins`; no hooks, telemetry, tee, recall store or persistent tracking. Keep `RTK_DB_PATH=NUL` (the only effective tracking control; `[tracking] enabled = false` is not honoured), `RTK_TELEMETRY_DISABLED=1`, `RTK_TEE=0`, `RTK_RECALL=0`, `RTK_SUPPRESS_HOOK_WARNING=1`.
- Only the reviewed deployment (RTK 1.2.1 on Windows through winget, and the smoke-tested Homebrew build on macOS) is approved; a new version or platform needs its own review. Install, pin, config, smoke test, licence note (BUSL-1.1 engine in 1.x) and the `rtk mvn` caveat: `references/rtk-reviewed-deployment.md`.

### `gh --json` + `jq` field selection

API-shaped output is routinely 10-100x larger than the fields a task uses.

```bash
gh pr view 123 --json state,mergeable,statusCheckRollup
gh run list --limit 5 --json databaseId,status,conclusion,workflowName
aws cloudwatch describe-alarms --query 'MetricAlarms[].{name:AlarmName,state:StateValue}' --output json
jq '.items[] | {id, status}' response.json
```

- Ask for the 3-5 fields you need; add fields on a second pass only if the task demands them.
- `aws --query` (JMESPath) filters server-side output the same way.
- `jq empty FILE` parse-validates JSON; assert shape with `jq -e 'type == "object"'` — never `jq -e empty` (exit 4 on valid JSON).

### ripgrep output budgeting

- Files only: `rg -l PATTERN`; counts: `rg --count-matches PATTERN`; cap per file: `rg -m 3 PATTERN`.
- Narrow with `--type`/`-g` globs before running broad patterns.
- Two-pass discipline: run `-l`/`--count` first; fetch matching lines only for the shortlisted files.
- Exit code 1 means "no match", not failure — check it instead of re-running variants blindly.

### ast-grep structural search (search-only)

Structural queries return only AST-matching nodes, eliminating comment/string false positives that inflate text-grep output (~9x reduction measured on structural questions).

```bash
sg -p 'console.log($A)' --lang js
sg -p 'public $RET $NAME($$$ARGS) throws $EX' --lang java -l
```

- Use for structure-shaped questions (call sites of a signature, annotated methods, nested patterns); keep plain ripgrep for plain text.
- **Search-only under this toolkit's rules:** do not use `-r`/rewrite/codemod modes in agent lanes governed by read-only contracts.
- Install: `winget install ast-grep.ast-grep` / `npm i -g @ast-grep/cli` / `brew install ast-grep`.

### repomix context packing (local mode only)

When a task genuinely needs many files as context (cross-file refactor brief, external review handoff), pack once instead of pasting files repeatedly: `npx repomix@latest --include "src/auth/**" --compress`.

- `--compress` extracts signatures/structure (~70% reduction); per-file token counts let you budget before sending.
- **Local repos only.** Do not use remote-repo mode (network clone) or hosted variants; keep Secretlint enabled; treat packed output as potentially containing secrets until scanned.
- Prefer targeted reads or a subagent sweep first; packing an entire repo is rarely the cheapest option.

### Delegation as compression

- Fan out bulk reads/searches to subagents and require compact structured returns (see `rules/request-orchestration.md`); merged findings, not raw transcripts, reach the parent context.
- In quality loops (`workflows/task-quality-loop.md`), feed producers only the defect list on refinement — never the full validator transcript.
- The four-block return contract in `tool-subagents/agent-orchestrator.md` (outcome / evidence / blockers / decisions, capped at 40 lines or 400 words excluding fenced evidence) is the default reduction shape; send an over-cap return back for reduction rather than absorbing it.

## Tools evaluated and rejected (do not adopt without new review)

- `code2prompt`, `gitingest` CLI — redundant with repomix; gitingest's hosted URL variant exfiltrates repo identity/tokens.
- `RepoMapper`, `llm-context` — unvetted third-party code; would need `external-skill-intake` review first.
- `universal-ctags` — stale-index risk misleads evidence; marginal benefit over ripgrep for agents.
- **Context Mode** — rejected. Two permission-prompt problems: (1) its Codex plugin route and `setup --agents codex` switch off Codex's approval prompt for every tool, including arbitrary code execution, and run commands outside the Codex shell sandbox; (2) in Claude Code its subagent commands reach Bash as `node ... <base64>`, so allow/ask rules and the prompt cannot show the real command (a `Bash(node:*)` allow gives no prompt at all), and one "don't ask again" click on `ctx_execute` is a blanket allow for arbitrary code. It also stores every prompt and tool output in a local SQLite database.
- **Caveman** — the plugin, installer, CLI, proxy and hooks are rejected in the security review: the CLI sends usage telemetry by default. Its text-only skill passed that review but was not added: in the value check against the plain model, the plain model's answers were shorter and equally correct, so asking for brevity directly is enough.
- **Ponytail** — Claude Code plugin only, installed by the owner from a local clone checked out at the reviewed commit (`ebd8654`), never `marketplace add` of the upstream repo (it tracks the default branch). Ledger off, webhook URL and token empty, `PONYTAIL_MAP=0` on client repos. The scanner's three high findings (`hook-outside-root`, `hooks/claude-codex-hooks.json`) are judged false positives: each hook command is a `node -e "require(...)"` that normalises Windows backslashes and stays inside the plugin root. Re-review before moving the commit. <!-- gitleaks:allow -->
- **Headroom** — avoid: it puts a proxy in the model API path (sees all prompts, responses and credentials in transit) and sends a usage beacon by default.

## Related

- `rules/command-safety.md` — RTK constraint set and command-review discipline
- `references/rtk-reviewed-deployment.md` — the approved RTK install, settings and smoke test
- `learnings/external-tool-intake-verdicts-pin-and-opt-in.md` — the four intake verdicts and their conditions
- `rules/multi-agent-orchestration.md` — parallel fanout and reduction
- `skills/llm-context-engineering/SKILL.md` — keeping prompt surfaces lean
- `skills/model-selector/SKILL.md` — choosing the cheapest capable model per task
- `skills/external-skill-intake/SKILL.md` — reviewing an unvetted tool before adopting it
- `workflows/context-compaction.md` — turning a long session into a compact handoff
