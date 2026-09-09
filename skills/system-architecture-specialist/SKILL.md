---
name: system-architecture-specialist
description: Read-only system architecture specialist for source-grounded application architecture, service boundaries, data flows, integrations, APIs/events, databases, operational qualities, LLM architecture, migrations, diagrams, docs, and architecture-related human reply drafts. Use whenever architecture correctness, maintainability, scalability, resilience, security, operability, rollout, or cross-service impact is in scope, or when the user asks for an architecture review, service-boundary check, data-flow review, or migration plan.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.0.0"
---

# System Architecture Specialist

Use this skill to route architecture review, discovery, or design validation
through the System Architecture Specialist. The specialist is read-only: it
grounds every claim in code, config, docs, tickets, logs, or metrics and returns
findings, tradeoffs, and handoffs; the root agent owns every change.

Trigger examples:

- "review the architecture of this change"
- "are these service boundaries right?"
- "trace the data flow from the API to the warehouse"
- "is this migration plan safe to roll out?"
- "which diagram do we need for this design?"

## Workflow

1. Load `workflows/system-architecture-specialist-validation.md`.
2. Invoke or follow `tool-subagents/system-architecture-specialist.md`.
3. Keep root-agent ownership for edits, docs, diagrams, validation, commits,
   pushes, and user-facing communication.
4. Compose with `skills/best-practices/SKILL.md`,
   `skills/llm-application-architecture/SKILL.md`,
   `workflows/project-discovery.md`, `workflows/document-creation.md`,
   `diagram-creation-specialist`, `confluence-documentation-specialist`,
   `documentation-reviewer`, `pr-validator`, and language/security/contract/log
   specialists only when their evidence lanes are relevant.
5. Keep product-specific architecture facts (service inventories, hostnames,
   account layouts) in the consumer repo's `docs/llm/`, not in this skill.
6. If the specialist misses a reusable pattern, run
   `workflows/system-architecture-specialist-evolution.md`.
