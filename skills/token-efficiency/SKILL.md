---
name: token-efficiency
description: "Reduce LLM token consumption during agent work: command-output compaction proxies (RTK), gh --json and jq field selection, ripgrep output budgeting, ast-grep structural search, and repomix context packing. Use when sessions burn context on command output, large file dumps, API responses, or repo-wide searches, or when choosing safe token-saving tools."
license: MIT
metadata:
  author: dev-tools
  version: "1.1.0"
---

# Token Efficiency

The owner-approved token-saving tools and their limits. Compact output never
replaces required evidence: security, release, production and byte-exact work
stays raw (`rules/command-safety.md`).

## Approved tools

- **RTK** (`rtk <cmd>` on high-output, non-interactive read/build/test commands): reviewed deployment only (RTK 1.2.1 via winget on Windows, the smoke-tested Homebrew build on macOS; a new version or platform needs its own review). Never route mutations of repos, remotes, infrastructure, privileges, approvals, releases or deployments through it. Never run `rtk init`, `trust`, `telemetry enable`, `llm-proxy`, `claude`, `pipeline add` or `plugins`. Keep `RTK_DB_PATH` on a null target (the only effective tracking control; `[tracking] enabled = false` is not honoured), `RTK_TELEMETRY_DISABLED=1`, `RTK_TEE=0`, `RTK_RECALL=0`, `RTK_SUPPRESS_HOOK_WARNING=1`. Install, pin, smoke test, licence and the `rtk mvn` caveat: `references/rtk-reviewed-deployment.md`.
- **ast-grep** (`sg`): search only in agent lanes; no rewrite or codemod modes under read-only contracts.
- **repomix**: local repos only (`npx repomix@latest --include "<glob>" --compress`); no remote-repo or hosted mode; keep Secretlint on and treat packed output as possibly holding secrets.
- `jq -e empty` exits 4 on valid JSON: validate with `jq empty FILE` and assert shape with `jq -e 'type == "object"'`.

## Rejected (do not adopt without a new review)

- `code2prompt`, `gitingest` (its hosted variant leaks repo identity and tokens), `RepoMapper`, `llm-context`, `universal-ctags`.
- **Context Mode**: its Codex route disables approval prompts and runs outside the shell sandbox; in Claude Code its commands reach Bash base64-encoded, so permission rules cannot see them; it stores every prompt and output locally.
- **Caveman**: plugin, installer, CLI, proxy and hooks rejected (default usage telemetry); the text-only skill added nothing over asking for brevity.
- **Ponytail**: Claude Code plugin only, installed by the owner from a local clone at reviewed commit `ebd8654`, never `marketplace add`; ledger off, webhook URL and token empty, `PONYTAIL_MAP=0` on client repos; its three `hook-outside-root` scanner findings are judged false positives. Re-review before moving the commit. <!-- gitleaks:allow -->
- **Headroom**: proxies the model API path (sees prompts, responses, credentials) and sends a usage beacon by default.

Verdict conditions: `learnings/external-tool-intake-verdicts-pin-and-opt-in.md`.
