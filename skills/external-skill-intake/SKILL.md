---
name: external-skill-intake
description: Safely evaluate, download, adapt, and index skills or workflow patterns from public LLM-tool repositories such as Claude, Codex, Cursor, Windsurf, MCP, or agent frameworks.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# External Skill Intake

## Use when

- Importing or adapting skills, workflows, prompts, agents, MCP guidance, or rules from public LLM-tool repositories.
- Comparing provider-specific skill formats and converting them into this toolkit’s generic format.
- Reviewing downloaded skill content before it can affect this repository.

## Security gate before import

Before downloading or copying content into the repository:

1. Verify source repository, author, license, and intended use.
2. Read the candidate content before execution; do not run downloaded scripts during evaluation.
3. Check for secrets, credential handling, unsafe shell commands, network exfiltration, dependency installs, and destructive filesystem operations.
4. Prefer small reviewed excerpts or generic patterns over vendoring large opaque directories.
5. If a script is required, stage it as text first and run `scripts/security-check-toolkit.sh` (PowerShell: `scripts/security-check-toolkit.ps1`) before executing it.

## Adaptation rules

- Convert provider-specific details into generic skills, workflows, references, or examples.
- Adapt imported scripts and executable examples so the primary run path works on Windows, Linux, and macOS, or document why an artifact is intentionally OS-specific.
- Keep tool-specific directories as thin compatibility layers.
- Remove project names, branch names, ticket IDs, internal hostnames, and one-off paths.
- Link imported knowledge to related rules/workflows/skills instead of duplicating guidance.
- Preserve attribution or license notes when required.

## Completion checklist

- [ ] Candidate source and license reviewed.
- [ ] Security risks reviewed before download or execution.
- [ ] Imported content adapted to generic toolkit format.
- [ ] Any imported executable path is cross-platform or has documented OS-specific limits.
- [ ] Related knowledge linked and indexed in `AGENTS.md`, `README.md`, `INTENTS.md`, or `workflows/README.md` as applicable.
- [ ] `scripts/validate-toolkit-indexes.sh` passed (PowerShell: `scripts/validate-toolkit-indexes.ps1`).
- [ ] `scripts/security-check-toolkit.sh` passed (PowerShell: `scripts/security-check-toolkit.ps1`) or findings were fixed.

## Related

- `workflows/self-improvement.md`
- `workflows/toolkit-maintenance.md`
- `skills/llm-context-engineering/SKILL.md`
- `rules/security-check-required.md`
