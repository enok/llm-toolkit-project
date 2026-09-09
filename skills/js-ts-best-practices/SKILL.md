---
name: js-ts-best-practices
description: JavaScript and TypeScript backend best practices for writing robust, testable, and maintainable code. This skill should be used when writing, reviewing, or refactoring JS/TS code. Triggers on tasks involving Node.js services, Express/Fastify/NestJS, async patterns, TypeScript types, error handling, or testing. Pair with project-local frontend/React guidance when the destination repo provides it.
license: MIT
metadata:
  author: dev-tools
  version: "1.1.0"
---

# JavaScript / TypeScript Best Practices

Comprehensive best practices guide for JavaScript and TypeScript backend and full-stack applications. Contains 30+ rules across 8 categories, prioritized by impact to guide code generation, review, and refactoring.

## When to Apply

Reference these guidelines when:
- Writing new TypeScript/JavaScript modules, services, or handlers
- Implementing async operations or concurrent patterns
- Designing types, interfaces, and dependency injection
- Adding error handling, logging, or exception management
- Reviewing JS/TS code for correctness and maintainability
- Writing or refactoring unit and integration tests

## Rule Categories by Priority

| Priority | Category | Impact | Prefix |
|----------|----------|--------|--------|
| 1 | Type Safety | CRITICAL | `type-` |
| 2 | Async & Concurrency | CRITICAL | `async-` |
| 3 | Error Handling | HIGH | `error-` |
| 4 | Dependency Injection | HIGH | `di-` |
| 5 | Language Fundamentals | MEDIUM | `lang-` |
| 6 | Logging | MEDIUM | `logging-` |
| 7 | Testing | MEDIUM | `testing-` |
| 8 | External Resources & Operations | LOW-MEDIUM | `resource-` |

## Quick Reference

The slugs below are checklist IDs, not file paths: every slug's expanded guidance lives in this skill's compiled `AGENTS.md`, and only the rule files explicitly listed under "How to Use" exist as standalone `rules/` files.

### 1. Type Safety (CRITICAL)

- `type-strict-config` - Enable strict mode, noUncheckedIndexedAccess, exactOptionalPropertyTypes
- `type-narrowing` - Use discriminated unions and type guards over type assertions
- `type-no-any` - Never use `any` — use `unknown`, generics, or proper types
- `type-readonly` - Use Readonly<T>, ReadonlyArray<T>, as const for immutable data
- `type-branded` - Use branded types for domain IDs to prevent mixups

### 2. Async & Concurrency (CRITICAL)

- `async-promise-all` - Use Promise.all() for independent operations, Promise.allSettled() for fault-tolerant
- `async-error-handling` - Always catch or propagate — never fire-and-forget
- `async-race-conditions` - Shared mutable state across async boundaries is a race condition
- `async-abort-signals` - Use AbortController for cancellable operations and timeouts
- `async-event-loop` - Never block the event loop — offload CPU work to worker threads

### 3. Error Handling (HIGH)

- `error-custom-classes` - Extend Error with typed properties (statusCode, context)
- `error-exhaustive-catch` - Use discriminated unions, never catch-all silently
- `error-result-pattern` - Use Result<T, E> for expected failures instead of exceptions

### 4. Dependency Injection (HIGH)

- `di-constructor-injection` - Accept all dependencies as interfaces via constructor
- `di-interface-isolation` - Define interface for every external dependency
- `di-config-wiring` - Let composition root / DI container bind implementations
- `di-anti-patterns` - Never import concrete implementations in service code

### 5. Language Fundamentals (MEDIUM)

- `lang-immutability` - Prefer const, Object.freeze, spread over mutation
- `lang-nullish` - Use ?., ??, and strict null checks over manual checks
- `lang-destructuring` - Destructure for clarity, avoid deep nesting
- `lang-collections` - Use Map/Set for lookup, avoid O(n²) nested loops
- `lang-early-return` - Guard clauses over nested if/else

### 6. Logging (MEDIUM)

- `logging-structured` - Use structured JSON logging (pino, winston) with correlation IDs
- `logging-levels` - Appropriate levels: error (action needed), warn, info (milestones), debug
- `logging-no-secrets` - Never log tokens, PII, or full request/response bodies

### 7. Testing (MEDIUM)

- `testing-mock-interface` - Mock the interface, not the module internals
- `testing-async` - Always await async assertions, use fake timers for time-dependent code
- `testing-arrange-act-assert` - Structure tests with clear given/when/then sections

### 8. External Resources & Operations (LOW-MEDIUM)

- `resource-http-client` - Reuse HTTP clients, configure timeouts and retries
- `resource-connection-pool` - Use connection pools for databases
- `resource-env-validation` - Validate environment variables at startup, fail fast

## How to Use

Read the standalone rule files for detailed explanations and code examples. These are the only rule files that exist on disk — every other quick-reference slug is expanded in `AGENTS.md`:

Use [references/source-backed-node-typescript.md](references/source-backed-node-typescript.md)
for Node runtime and TypeScript-toolchain choices.

```
rules/async-promise-all.md
rules/async-race-conditions.md
rules/di-constructor-injection.md
rules/error-custom-classes.md
rules/logging-structured.md
rules/resource-env-validation.md
rules/testing-mock-interface.md
rules/type-narrowing.md
rules/type-no-any.md
```

Each rule file contains:
- Brief explanation of why it matters
- Incorrect code example with explanation
- Correct code example with explanation
- Additional context and key rules

## Related Skills

- Project-local frontend guidance — React/Next.js performance optimization when the destination repo provides it
- **best-practices** — SOLID principles, architecture patterns, resilience (language-agnostic foundations)
- **security** — Injection prevention, auth, secrets, XSS/CSRF (applies to all JS/TS endpoints)
- **testing** — AC traceability, test pyramid, coverage checklist (universal testing discipline)

## Full Compiled Document

For the complete guide with all rules expanded: `AGENTS.md`
