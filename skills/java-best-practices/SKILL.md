---
name: java-best-practices
description: Java backend best practices for writing robust, testable, and maintainable code. This skill should be used when writing, reviewing, or refactoring Java code. Triggers on tasks involving Java classes, Spring/Guice services, concurrency, logging, error handling, or testing.
license: MIT
metadata:
  author: dev-tools
  version: "1.1.0"
---

# Java Best Practices

Comprehensive best practices guide for Java backend applications. Contains 30+ rules across 8 categories, prioritized by impact to guide code generation, review, and refactoring.

## When to Apply

Reference these guidelines when:
- Writing new Java classes, services, or controllers
- Implementing dependency injection or design patterns
- Writing concurrent or multi-threaded code
- Adding logging, error handling, or exception management
- Reviewing Java code for correctness and maintainability
- Writing or refactoring unit and integration tests

## Rule Categories by Priority

| Priority | Category | Impact | Prefix |
|----------|----------|--------|--------|
| 1 | Dependency Injection | CRITICAL | `di-` |
| 2 | Concurrency & Thread Safety | CRITICAL | `concurrency-` |
| 3 | Error Handling | HIGH | `error-` |
| 4 | Logging | HIGH | `logging-` |
| 5 | Language Fundamentals | MEDIUM | `lang-` |
| 6 | Design Patterns | MEDIUM | `pattern-` |
| 7 | Testing | MEDIUM | `testing-` |
| 8 | External Resources & Operations | LOW-MEDIUM | `resource-` |

## Quick Reference

The slugs below are checklist IDs, not file paths: every slug's expanded guidance lives in this skill's compiled `AGENTS.md`, and only the rule files explicitly listed under "How to Use" exist as standalone `rules/` files.

### 1. Dependency Injection (CRITICAL)

- `di-constructor-injection` - Accept all dependencies as interfaces via constructor
- `di-interface-isolation` - Define interface for every external dependency
- `di-config-wiring` - Let configuration layer bind implementations
- `di-anti-patterns` - Never use field injection, concrete instantiation, or concrete types

### 2. Concurrency & Thread Safety (CRITICAL)

- `concurrency-immutability` - Make shared objects immutable as first defense
- `concurrency-read-modify-write` - Use AtomicInteger/AtomicReference for atomic ops
- `concurrency-shared-mutable` - Synchronize all access (reads AND writes) with private lock
- `concurrency-collections` - Use ConcurrentHashMap, AtomicReference, CopyOnWriteArrayList
- `concurrency-lazy-init` - Use holder pattern for thread-safe lazy initialization
- `concurrency-pitfalls` - Avoid synchronized(this), unsynchronized reads, publishing mutable refs

### 3. Error Handling (HIGH)

- `error-specific-exceptions` - Catch the most specific exception type
- `error-context` - Include business context (IDs, operation) in exception messages
- `error-chaining` - Always chain root cause with initCause() or constructor
- `error-custom-hierarchy` - Build project exception hierarchy from a common base

### 4. Logging (HIGH)

- `logging-parameterized` - Use SLF4J {} placeholders, never string concatenation
- `logging-exception-context` - Log with business context + root cause + full exception
- `logging-stack-depth` - Limit stack trace depth with %xEx{200}
- `logging-mdc` - Use MDC for correlation IDs across log lines
- `logging-slf4j-gotcha` - Throwable must be last arg in varargs form

### 5. Language Fundamentals (MEDIUM)

- `lang-immutability` - Prefer final fields, final classes, List.copyOf()
- `lang-null-safety` - Use Optional for return types, Objects.requireNonNull for params
- `lang-string-handling` - Avoid concatenation in loops, use StringBuilder or String.format
- `lang-collections` - Prefer Map.of/List.of, computeIfAbsent, unmodifiable views
- `lang-method-design` - Small methods, single responsibility, guard clauses
- `lang-algorithmic` - Avoid O(n²) nested loops, use Map/Set for lookup

### 6. Design Patterns (MEDIUM)

- `pattern-builder` - Use builder for objects with 4+ fields
- `pattern-strategy` - Use strategy map instead of growing switch/if chains

### 7. Testing (MEDIUM)

- `testing-unit-vs-integration` - Separate unit (mocked, fast) from integration (real, slow)
- `testing-mock-interface` - Mock at the interface boundary, not concrete implementations
- `testing-exception-verify` - Use assertThrows + message assertions

### 8. External Resources & Operations (LOW-MEDIUM)

- `resource-connection-pool` - Always use connection pools (HikariCP, SDK clients)
- `resource-http-timeouts` - Configure connect + read + idle timeouts
- `resource-caching` - Use Guava/Caffeine LoadingCache with TTL and max size
- `resource-metrics-registry-wiring` - Metrics wrappers must share the application registry and fail fast when wiring is missing
- `resource-log4j2-startup-log-level` - Feed early Log4j2 levels from validated JVM startup properties
- `resource-dynamic-log-levels` - Use Log4j2 monitorInterval for hot-reload
- `resource-java-release-cross-compile` - Use Maven compiler `release` when a newer JDK builds for an older runtime

## How to Use

Read the standalone rule files for detailed explanations and code examples. These are the only rule files that exist on disk — every other quick-reference slug is expanded in `AGENTS.md`:

Use [references/source-backed-modern-java.md](references/source-backed-modern-java.md)
for runtime-aware Spring and modern-JDK choices.

```
rules/concurrency-collections.md
rules/concurrency-immutability.md
rules/concurrency-read-modify-write.md
rules/concurrency-shared-mutable.md
rules/di-constructor-injection.md
rules/di-interface-isolation.md
rules/error-specific-exceptions.md
rules/lang-algorithmic.md
rules/lang-immutability.md
rules/lang-null-safety.md
rules/logging-exception-context.md
rules/logging-mdc.md
rules/logging-parameterized.md
rules/logging-slf4j-gotcha.md
rules/resource-java-release-cross-compile.md
rules/resource-log4j2-startup-log-level.md
rules/resource-metrics-registry-wiring.md
rules/testing-mock-interface.md
```

Each rule file contains:
- Brief explanation of why it matters
- Incorrect code example with explanation
- Correct code example with explanation
- Additional context and key rules

## Related Skills

- **best-practices** — SOLID principles, architecture patterns, resilience (language-agnostic foundations that Java implements)
- **security** — Injection prevention, auth, secrets management (applies to all Java endpoints handling user data)
- **testing** — AC traceability, test pyramid, coverage checklist (universal testing discipline beyond Java-specific patterns)

## Full Compiled Document

For the complete guide with all rules expanded: `AGENTS.md`
