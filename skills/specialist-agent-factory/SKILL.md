---
name: specialist-agent-factory
description: Create or update reusable specialist agents with canonical tool-subagent prompts, validation/evolution workflows, skill entrypoints, routing, client overlays, provider sync, and validation checklists. Use when adding a new specialist agent to the toolkit or bringing an incomplete one up to repository standards.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Specialist Agent Factory

Use this skill when creating or evolving a reusable specialist agent in this
toolkit.

## Factory Command

Scaffold a specialist:

```bash
node scripts/create-specialist-agent.js <agent-name> --domain "<domain>" --description "<short trigger description>"
```

Preview only:

```bash
node scripts/create-specialist-agent.js <agent-name> --domain "<domain>" --dry-run
```

Validate a specialist:

```bash
node scripts/validate-specialist-agent.js <agent-name>
```

## Required Assets

Every specialist should have:

- canonical prompt: `tool-subagents/<agent-name>.md`
- provider metadata: `tool-subagents/<agent-name>.toml` (body identical to the `.md` body)
- validation workflow: `workflows/<agent-name>-validation.md`
- evolution workflow: `workflows/<agent-name>-evolution.md`
- skill entrypoint: `skills/<agent-name>/SKILL.md`
- routing in `INTENTS.md`
- index entries in `AGENTS.md`, `README.md`, `skills/README.md`, and
  `workflows/README.md`
- provider overlays refreshed by `npm run tool-configs:sync` and
  `npm run subagents:apply -- <provider> .`

## Design Rules

- Keep the subagent prompt single-purpose and provider-neutral.
- State read/write authority explicitly. Prefer read-only specialists unless
  the user specifically needs a worker.
- Define inputs, procedure, and output contract so root agents can reduce the
  result quickly.
- Include a related-specialist handoff section so the specialist can recommend
  companion agents through the root agent without taking over their scopes.
- Add a validation workflow for normal use and an evolution workflow for misses,
  noisy findings, and token-efficiency improvements.
- Include a `Learning/token efficiency` output section that points to the
  specialist's evolution workflow and `workflows/specialist-agent-evolution.md`.
- Keep human-facing reply behavior aligned with
  `rules/human-comment-reply-gate.md`, and any external write aligned with
  `rules/external-write-authorization.md`.
- Keep commands cross-platform per `rules/cross-platform-scripts.md`; where a
  gate has no portable form, give both the Bash and the PowerShell shape.
- Run `documentation-reviewer` on new or changed specialist prompts, workflows,
  skills, indexes, and generated client surfaces before final reporting.

## Validation Checklist

Run:

```bash
node --check scripts/create-specialist-agent.js
node --check scripts/validate-specialist-agent.js
node scripts/validate-specialist-agent.js <agent-name>
npm run skills:index:check
npm run rules:redirects:check
npm run workflows:size:check
npm run subagents:check
npm run llm-content:security-check
```

Then the toolkit-wide index and security gates:

```bash
./scripts/validate-toolkit-indexes.sh
./scripts/security-check-toolkit.sh
```

On Windows PowerShell use `./scripts/validate-toolkit-indexes.ps1` and
`./scripts/security-check-toolkit.ps1`.

Before commit and push, also run the repo's full validation path.

## Related

- `workflows/specialist-agent-factory.md` — the end-to-end creation procedure
- `workflows/specialist-agent-evolution.md` — improving an existing specialist
- `skills/agent-orchestrator/SKILL.md` — how specialists get routed and dispatched
- `skills/model-selector/SKILL.md` — choosing the tier a specialist runs at
