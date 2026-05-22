---
name: llm-application-architecture
description: "Design or evaluate LLM application architecture: RAG, knowledge-base retrieval, agent vs direct model calls, memory, tool use, gateways, evaluation sets, token/cost/latency, and rollout flags."
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# LLM Application Architecture

## Use when

- Comparing direct model calls, RAG, managed agents, custom agents, or agent runtimes.
- Designing memory for an agent or chat application.
- Adding tool use, gateway/identity, or MCP-style integrations.
- Evaluating retrieval quality, source diversity, token usage, latency, or cost.
- Planning rollout of a new LLM path behind flags.

## Architecture questions

1. **Task shape** — single-turn analysis, multi-turn chat, multi-step tool workflow, or report generation?
2. **Retrieval control** — does the app need deterministic category queries, deduplication, or source diversity guarantees?
3. **Memory scope** — session-only, long-term user preferences, semantic facts, or no memory?
4. **Tool orchestration** — should code decide tool calls, or should the model choose tools in a reasoning loop?
5. **Evidence and evaluation** — what golden set, side-by-side comparison, or contradiction check proves quality?
6. **Operational metrics** — token usage, latency, cost, failure rate, retrieval hit rate, and source count.
7. **Safety and privacy** — PII handling, tenant isolation, source redaction, data retention, and prompt injection boundaries.
8. **Rollout** — feature flag, tenant cohort, fallback path, rollback, and production validation plan.

## Decision guide

| Need | Typical fit |
| --- | --- |
| Deterministic report or summary with controlled retrieval | Direct retrieve + direct model call |
| Multi-turn chat with conversation state | Agent or chat framework with session management |
| Model chooses tools dynamically | Agent/tool orchestration runtime |
| Shared enterprise tools and identity | Gateway/MCP-style tool layer |
| Personalized responses across sessions | Explicit memory namespaces with retrieval-before-response and save-after-response |
| Quality-sensitive structured output | Golden set, schema checks, contradiction reconciliation, and source audits |

## Review checklist

- [ ] Source retrieval and deduplication strategy is explicit.
- [ ] Token, latency, and cost are measured from real responses where possible.
- [ ] Contradiction/reconciliation step exists when independent subtasks are merged.
- [ ] Memory is scoped per user/tenant and only stores appropriate facts.
- [ ] Tool access is least-privilege and auditable.
- [ ] New path has feature flag, fallback, rollout verification, and rollback.
- [ ] Generated outputs can be traced to source evidence.

## Related

- `skills/security-threat-model/SKILL.md`
- `skills/security/SKILL.md`
- `skills/testing/SKILL.md`
- `workflows/document-creation.md`
