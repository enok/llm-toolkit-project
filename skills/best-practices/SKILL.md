---
name: best-practices
description: Universal software engineering and architecture best practices that apply to every project regardless of tech stack. This skill should be used when writing, reviewing, or refactoring code in any language. Triggers on tasks involving SOLID principles, clean code, layered architecture, API design, resilience patterns, observability, error handling, or general code quality improvement.
license: MIT
metadata:
  author: dev-tools
  version: "1.1.0"
---

# Software Engineering & Architecture Best Practices

Universal principles that apply to every project regardless of tech stack. Contains 25+ rules across 6 categories, prioritized by impact to guide code generation, review, and refactoring.

## When to Apply

Reference these guidelines when:
- Writing new services, modules, or components in any language
- Reviewing code for architectural correctness
- Refactoring for maintainability or resilience
- Designing APIs, data models, or service boundaries
- Adding error handling, observability, or defensive patterns
- Identifying and eliminating anti-patterns

## Rule Categories by Priority

| Priority | Category | Impact | Prefix |
|----------|----------|--------|--------|
| 1 | SOLID Principles | CRITICAL | `solid-` |
| 2 | Clean Code | HIGH | `clean-` |
| 3 | Error Handling & Defensive Programming | HIGH | `error-` |
| 4 | Architecture & Separation of Concerns | HIGH | `arch-` |
| 5 | Resilience & Operational Patterns | MEDIUM | `resilience-` |
| 6 | Anti-Patterns | MEDIUM | `anti-` |

## Quick Reference

### 1. SOLID Principles (CRITICAL)

- `solid-single-responsibility` - Each class/module does one thing. If you can't describe it in one sentence, split it.
- `solid-open-closed` - Open for extension, closed for modification. Prefer strategies over switch/if chains.
- `solid-liskov-substitution` - Subtypes must be substitutable without breaking behavior.
- `solid-interface-segregation` - Many small interfaces over one large one.
- `solid-dependency-inversion` - Depend on abstractions, not concretions.

### 2. Clean Code (HIGH)

- `clean-naming` - Names reveal intent. calculateMonthlyRevenue() not calc().
- `clean-small-functions` - Under 20 lines, one level of abstraction, one purpose.
- `clean-no-magic` - Named constants. MAX_RETRY_ATTEMPTS = 3, not bare 3.
- `clean-early-return` - Guard clauses reduce nesting. Validate and fail early.
- `clean-dry-rule-of-three` - Abstract on the third occurrence. Wrong abstraction > duplication.

### 3. Error Handling & Defensive Programming (HIGH)

- `error-fail-fast` - Validate at boundaries. Don't let bad data propagate.
- `error-specific-exceptions` - Catch narrowest type. Never catch Exception/Throwable unless re-throwing.
- `error-no-swallowed` - Every catch must log, re-throw, or handle meaningfully.
- `error-input-validation` - Validate all inputs at system boundaries.
- `error-immutability` - Prefer immutable data. Mutable shared state = concurrency bugs.
- `error-classification-code` - Classify wrapped SDK errors by error code, not exception class name (see `rules/`).

### 4. Architecture & Separation of Concerns (HIGH)

- `arch-layered` - Controller → Service → Repository. Never skip layers.
- `arch-thin-controllers` - Controllers parse input and delegate. No business logic.
- `arch-api-design` - Idempotency, consistent errors, versioning, input validation.
- `arch-data-design` - Single source of truth, schema evolution, TTL.
- `arch-coupling-cohesion` - Low coupling, high cohesion, contract-first, event-driven.

### 5. Resilience & Operational Patterns (MEDIUM)

- `resilience-timeouts` - Every external call needs a timeout. No unbounded waits.
- `resilience-retry-backoff` - Exponential backoff + jitter. Cap max retries.
- `resilience-circuit-breaker` - Fail fast on frequently-failing dependencies.
- `resilience-observability` - Structured logging, correlation IDs, metrics, alerting.
- `resilience-graceful-degradation` - Optional dependency down: serve a reduced response, record it, never collapse.
- `handler-lifecycle-cleanup` - Wrap handlers (Lambda, jobs, consumers) in try/finally so context and connections are released (see `rules/`).

### 6. Anti-Patterns (MEDIUM)

- `anti-god-class` - Split by responsibility.
- `anti-premature-optimization` - Measure first, optimize proven bottlenecks.
- `anti-premature-abstraction` - Don't abstract until 3+ concrete cases.
- `anti-distributed-monolith` - If services share DB or need synchronized deploy, they're a monolith.
- Also watch for stringly-typed code, feature envy, shotgun surgery, primitive obsession, and anemic domain models (catalogue in `AGENTS.md`).

## How to Use

1. Use the quick reference above as the language-agnostic checklist during generation and review.
2. Pair it with the relevant language-specific best-practices skill and its local `rules/` files for implementation detail and stack idioms.
3. Load the compiled `AGENTS.md` when you need every rule expanded (with code examples) in one place.
4. Read the fine-grained rule files in `rules/` for the rules that need deeper treatment:

```text
rules/solid-single-responsibility.md
rules/arch-layered.md
rules/resilience-timeouts.md
rules/error-classification-code.md
rules/handler-lifecycle-cleanup.md
```

Each rule file contains a brief explanation of why it matters, an incorrect example, a correct example, and key rules.

`references/rules.md` is a compact always-on summary suitable for consumer repos that want the whole baseline in one short file. Toolkit-wide coding discipline, orchestration, and learning-capture constraints live in the canonical top-level rules (`rules/code-rules.md`, `rules/multi-agent-orchestration.md`, `rules/error-driven-learning.md`), not in this skill.

Use `references/source-review.md` when evaluating external material for inclusion in this generic skill.

## Related Skills

This skill provides **language-agnostic foundations**. Pair it with language-specific implementations:

- **java-best-practices** — Java implementation of SOLID, DI, concurrency, error handling
- **python-best-practices** — Python implementation of SOLID, DI, concurrency, error handling
- **js-ts-best-practices** — TypeScript/JavaScript implementation of DI, async patterns, error handling, and Node.js runtime resilience
- **security** — Security-specific rules (injection, auth, secrets) that complement the defensive programming section
- **testing** — Testing discipline (AC traceability, test pyramid) that validates architecture and code quality

## Full Compiled Document

For the complete guide with all rules expanded: `AGENTS.md`
