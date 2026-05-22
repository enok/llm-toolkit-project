# Cursor Layout

This directory is a thin compatibility surface for Cursor. Canonical shared content lives at the repository root:

| Canonical path | Cursor-facing path |
| --- | --- |
| `rules/` | `.cursor/rules` |
| `workflows/` | `.cursor/workflows` |
| `tool-subagents/` | `.cursor/agents` |
| `skills/` | `.agents/skills` |

Do not hand-edit linked folders under `.cursor/`. Edit `rules/`, `workflows/`, `tool-subagents/`, or `skills/` instead, then run:

```bash
./scripts/sync-tool-configs.sh . --skip-agents-md
```

PowerShell wrapper:

```powershell
.\scripts\sync-tool-configs.ps1 . -SkipAgentsMd
```

## Subagents

The canonical subagent definitions live in `tool-subagents/*.toml`:

| File | Role |
| --- | --- |
| `ci-triage.toml` | CI log triage and likely fix hints |
| `code-reviewer.toml` | Deep code review |
| `contract-analyzer.toml` | API/schema downstream impact |
| `cross-repo-analyst.toml` | Multi-repo read-only impact map |
| `documentation-sync.toml` | Documentation drift checks |
| `owasp-security-auditor.toml` | OWASP-focused audit lane |
| `parallel-explorer.toml` | Fast codebase exploration |
| `release-coordinator.toml` | Release ordering, verification, and rollback |
| `security-auditor.toml` | Security-focused review |
| `test-runner.toml` | Test selection and failure triage |
| `verifier.toml` | Skeptical completion check |
