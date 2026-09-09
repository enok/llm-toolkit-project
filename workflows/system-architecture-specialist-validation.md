---
description: Run the System Architecture Specialist for source-grounded application architecture, service boundaries, data flows, integrations, and operational-quality review
---

# System Architecture Specialist Validation

Use this workflow when application, service, platform, data-flow, integration,
LLM, migration, or operational architecture needs specialist review before
implementation, documentation, PR approval, or handoff.

## Phase 1 - Scope And Evidence

1. Establish repo, base/head, dirty-tree ownership, architecture boundary,
   affected services, constraints, and whether the ask is current-state,
   target-state, review, or migration planning.
2. Load only relevant context: `workflows/project-discovery.md`,
   `workflows/document-creation.md`, `skills/best-practices/SKILL.md`,
   `skills/llm-application-architecture/SKILL.md` for LLM systems, language
   skills, security/testing skills, ADRs, docs, diagrams, configs, tickets, PRs,
   logs, metrics, and the consumer repo's `docs/llm/` for project facts.
3. Identify whether code, contract, security, log, release, diagram, or docs
   specialists should handle a narrower evidence lane.

## Phase 2 - Specialist Pass

1. Invoke or follow `tool-subagents/system-architecture-specialist.md`.
2. Ask for current-state map, source-grounded findings, tradeoffs, claim drift,
   diagram/doc needs, validation gaps, and related-specialist handoffs.
3. Require concrete evidence for every architecture claim and avoid broad
   rewrites without a current-change risk.

## Phase 3 - Reduce And Act

1. Accept only evidence-backed, in-scope findings.
2. Apply the smallest safe architecture/code/doc change only when requested.
3. Hand accepted diagram work to `diagram-creation-specialist` and accepted doc
   or wiki work to `documentation-reviewer` or
   `confluence-documentation-specialist`.
4. Keep human-facing architecture replies draft-only until explicit approval
   (`rules/human-comment-reply-gate.md`).

## Phase 4 - Validate

Run the narrowest relevant checks:

- code/build/test/contract checks for changed implementation risk;
- docs/diagram/render checks for architecture artifacts;
- security/privacy checks for trust boundaries, secrets, auth, or PII;
- operational evidence checks for reliability, rollback, metrics, or logs.

## Phase 5 - Evolve

If the specialist misses recurring architecture risk, weak source grounding,
bad handoff, stale diagram/doc claim, or token-heavy context load, run
`workflows/system-architecture-specialist-evolution.md`.
