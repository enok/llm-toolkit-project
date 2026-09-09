---
description: Create a reusable specialist agent with prompt, workflows, skill entrypoint, routing, client overlays, and validation gates
---

# Specialist Agent Factory

Use this workflow to create a new reusable specialist agent or bring an
incomplete specialist up to repository standards.

## Phase 1 - Define Contract

1. Name the specialist in kebab-case.
2. Define the specialist's domain, read/write authority, trigger phrases,
   required inputs, procedure, and output contract.
3. Decide whether it is read-only, a worker, or a coordinator. Prefer read-only
   for validators and reviewers.
4. Identify companion rules, skills, workflows, validation gates, and related
   specialists the new agent should recommend through the root agent.
5. Include a `Learning/token efficiency` output section that points to the
   specialist's evolution workflow and `workflows/specialist-agent-evolution.md`.

## Phase 2 - Scaffold

Run:

```bash
node scripts/create-specialist-agent.js <agent-name> --domain "<domain>" --description "<trigger description>"
```

The factory creates or updates the standard asset set:

- `tool-subagents/<agent-name>.md`
- `tool-subagents/<agent-name>.toml` (body identical to the `.md` body)
- `workflows/<agent-name>-validation.md`
- `workflows/<agent-name>-evolution.md`
- `skills/<agent-name>/SKILL.md`

## Phase 3 - Index And Route

Update:

- `INTENTS.md`
- `AGENTS.md`
- `README.md`
- `skills/README.md`
- `workflows/README.md`
- `clients/README.md` if client overlay behavior changes

Keep indexes short. Put detailed operating instructions in the prompt, workflow,
or skill body rather than root guidance.

## Phase 4 - Documentation Review

Run `documentation-reviewer` against the new or updated prompt, workflow, skill,
indexes, and generated-surface changes. Fix source-grounding, audience-fit,
claim-drift, artifact, or draft-reply issues before syncing and validating.

## Phase 5 - Sync Provider Surfaces

Run:

```bash
npm run tool-configs:sync
npm run subagents:apply -- <provider> .
```

Use the provider argument expected by the destination client. On Windows
PowerShell the same sync is available through `./scripts/sync-tool-configs.ps1`.

## Phase 6 - Validate

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
npm run validate
```

Then the toolkit-wide gates:

```bash
./scripts/validate-toolkit-indexes.sh
./scripts/security-check-toolkit.sh
```

## Phase 7 - Commit And Push

1. Preserve unrelated dirty files.
2. Stage only the specialist assets, indexes, scripts, and generated provider
   surfaces touched by this change.
3. Rebase on the branch base when safe.
4. Commit with the repository's commit conventions
   (`rules/git-conventions.md`).
5. Push the selected branch.

Report changed files, validations, skipped optional gates, commit SHA, pushed
branch, preserved unrelated files, and the factory invocation commands.
