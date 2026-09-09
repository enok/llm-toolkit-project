---
name: external-skill-intake
description: Safely evaluate, download, adapt, and index skills or workflow patterns from public LLM-tool repositories such as Claude, Codex, Cursor, Windsurf, MCP, or agent frameworks. Use before importing any external skill, prompt, agent, or rule; covers license review, Trust Hub URL checks, SkillSpector and prompt-injection scans, and generic adaptation.
license: MIT
metadata:
  author: dev-tools
  version: "1.1.0"
---

# External Skill Intake

## Use when

- Importing or adapting skills, workflows, prompts, agents, MCP guidance, integration guidance, or rules from public LLM-tool repositories.
- Comparing provider-specific skill formats and converting them into this toolkit's generic format.
- Reviewing downloaded skill content before it can affect this repository.

## Security gate before import

Before downloading or copying content into the repository:

1. Verify source repository, author, license, and intended use.
2. Read the candidate content before execution; do not run downloaded scripts during evaluation.
3. For a marketplace or install URL, check it with Gen Agent Trust Hub before import:
   - `GEN_AGENT_TRUST_HUB_SKILL_URLS="<skill-url>" scripts/check-new-skill-security.sh`
   - Proceed only when the returned severity is `SAFE`; otherwise reject or sandbox for manual analysis.
4. Check for secrets, credential handling, unsafe shell commands, network exfiltration, dependency installs, and destructive filesystem operations.
5. Prefer small reviewed excerpts or generic patterns over vendoring large opaque directories.
6. If the import adds or modifies `skills/<name>/SKILL.md`, run SkillSpector before accepting the local skill:
   - Bash: `scripts/validate-skills-with-skillspector.sh` (PowerShell: `scripts/validate-skills-with-skillspector.ps1`); both wrap `scripts/validate-skills-with-skillspector.py`, which scans every `skills/*` directory and fails on `HIGH`/`CRITICAL` findings.
   - Record reviewed false positives in `scripts/skillspector-allowlist.json` with a reason; never widen `SKILLSPECTOR_FAIL_SEVERITIES` to make a scan pass.
   - Keep the default static scan unless the user explicitly configures LLM-backed scanner credentials (`--with-llm`).
7. Run the skill gate with `SNYK_TOKEN` configured when Snyk Agent Scan prerequisites are available:
   - Bash: `if ./scripts/check-new-skill-security.sh --has-work; then ./scripts/check-new-skill-security.sh; fi`
   - PowerShell: `bash scripts/check-new-skill-security.sh --has-work`; if `$LASTEXITCODE -eq 0`, run `bash scripts/check-new-skill-security.sh`.
8. If a script is required, stage it as text first and run `scripts/security-check-toolkit.sh` (PowerShell: `scripts/security-check-toolkit.ps1`) before executing it.
9. Use scanner CLIs or HTTP APIs only for this gate; do not install or run scanner MCP servers.
10. Confirm `scripts/scan-llm-surface-security.py` passes for any imported or adapted LLM-loaded surface; prompt-injection or malicious-instruction findings block import until rewritten or justified.

## Adaptation rules

- Convert provider-specific details into generic skills, workflows, references, or examples.
- Adapt imported scripts and executable examples so the primary run path works on Windows, Linux, and macOS, or document why an artifact is intentionally OS-specific.
- Keep tool-specific directories as thin compatibility layers.
- Remove project names, branch names, ticket IDs, internal hostnames, and one-off paths.
- Link imported knowledge to related rules/workflows/skills instead of duplicating guidance.
- Preserve attribution or license notes when required.

## Skill quality checklist

When adapting a skill pattern, keep the always-loaded `SKILL.md` lean and verify:

- The `description` states both what the skill does and when to use it.
- Large examples, scripts, assets, and long references live behind explicit links so they are loaded only when needed.
- Paths are relative to the skill or repository, not absolute workstation paths.
- Dependencies, network calls, credential handling, and OS-specific requirements are explicit.
- Trigger examples and non-trigger examples are clear enough to avoid over-broad activation.

## Known intake sources

Use these sources as discovery inputs, not as trusted install targets:

| Source | Use for | Intake note |
| --- | --- | --- |
| `https://github.com/anthropics/skills` | Reference `SKILL.md` structure, progressive disclosure patterns, and official skill examples | Check per-skill licenses before copying content. |
| `https://github.com/VoltAgent/awesome-agent-skills` | Broad cross-agent discovery across official and community skills | Treat as curated, not audited; verify each upstream source. |
| `https://github.com/travisvn/awesome-claude-skills` | Claude-focused skill and resource discovery | Treat listed skills as executable code until reviewed. |
| `references/agent-evolution-sources.md` | Agent evaluation, orchestration, trace, and self-improvement pattern sources | Use as a discovery shortlist; do not vendor code or trust star counts without review. |

When a listed repository points to another upstream skill, review the upstream repository and license directly before importing or adapting content.

## Rejected sources

Evaluated and rejected; do not re-import without the listed re-evaluation condition being met. Record each rejection as a `learnings/` entry (category `security`) so the reasoning survives.

| Source | Decision (date) | Why | Re-evaluate when |
| --- | --- | --- | --- |
| `https://github.com/browser-use/browser-harness` | Rejected (2026-08-21) | Requires CDP remote debugging on the user's real logged-in browser; built-in session-cookie sync to a third-party cloud via a pipe-to-shell binary install; bot-detection-evasion guidance; opt-out telemetry; over-broad "always use for any web interaction" trigger; self-modifying executable helper file; Trust Hub cannot return `SAFE`. Cover screenshot/evidence needs with API-native renders (for example `aws cloudwatch get-metric-widget-image`) or the agent environment's permission-gated browser surface instead. | An isolated-profile-only mode exists with no real-profile CDP requirement, no cookie cloud sync, and telemetry off by default. |

## Completion checklist

- [ ] Candidate source and license reviewed.
- [ ] Gen Agent Trust Hub checked for external/marketplace skill URLs, or URL scan marked not applicable.
- [ ] Security risks reviewed before download or execution.
- [ ] New or modified local skill files scanned by SkillSpector through `scripts/validate-skills-with-skillspector.sh` (PowerShell: `scripts/validate-skills-with-skillspector.ps1`).
- [ ] New or modified local skill files scanned by Snyk Agent Scan through `scripts/check-new-skill-security.sh` when scanner prerequisites are available.
- [ ] Prompt-injection and malicious-instruction scan passed through `scripts/security-check-toolkit.sh` and `scripts/scan-llm-surface-security.py`.
- [ ] Imported content adapted to generic toolkit format.
- [ ] Any imported executable path is cross-platform or has documented OS-specific limits.
- [ ] Related knowledge linked and indexed in `AGENTS.md`, `README.md`, `INTENTS.md`, or `workflows/README.md` as applicable.
- [ ] `scripts/validate-toolkit-indexes.sh` passed (PowerShell: `scripts/validate-toolkit-indexes.ps1`).
- [ ] `scripts/security-check-toolkit.sh` passed (PowerShell: `scripts/security-check-toolkit.ps1`) or findings were fixed.

## Related

- `workflows/self-improvement.md`
- `workflows/toolkit-maintenance.md`
- `skills/llm-context-engineering/SKILL.md`
- `skills/security/SKILL.md`
- `rules/security-check-required.md`
