---
name: python-best-practices
description: Python backend best practices for writing robust, testable, and maintainable code. This skill should be used when writing, reviewing, or refactoring Python code. Triggers on tasks involving Python modules, FastAPI/Flask services, Lambda handlers, concurrency, logging, error handling, or testing.
license: MIT
metadata:
  author: dev-tools
  version: "1.1.0"
---

# Python Best Practices

Comprehensive best practices guide for Python backend applications. Contains 30+ rules across 8 categories, prioritized by impact to guide code generation, review, and refactoring.

## When to Apply

Reference these guidelines when:
- Writing new Python modules, services, or handlers
- Implementing dependency injection or design patterns
- Writing concurrent or multi-threaded code
- Adding logging, error handling, or exception management
- Reviewing Python code for correctness and maintainability
- Writing or refactoring unit and integration tests
- Editing, validating, or operationalizing Python notebooks

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

- `di-constructor-injection` - Accept all dependencies as ABCs/Protocols via __init__
- `di-interface-isolation` - Define ABC or Protocol for every external dependency
- `di-config-wiring` - Let application entry point wire implementations
- `di-anti-patterns` - Never instantiate deps inside class, use module globals, or import concrete

### 2. Concurrency & Thread Safety (CRITICAL)

- `concurrency-gil-myth` - GIL does NOT eliminate race conditions on compound operations
- `concurrency-immutability` - Use frozen dataclasses and tuples as first defense
- `concurrency-read-modify-write` - Use threading.Lock for counter += 1 and similar
- `concurrency-shared-mutable` - Lock all access (reads AND writes) with same lock
- `concurrency-data-structures` - Use queue.Queue, threading.local(), Lock + dict
- `concurrency-lazy-init` - Double-checked locking with threading.Lock

### 3. Error Handling (HIGH)

- `error-specific-exceptions` - Catch the most specific exception type
- `error-context-managers` - Use `with` for all resources needing cleanup
- `error-chaining` - Always use `raise ... from e` to preserve cause

### 4. Logging (HIGH)

- `logging-parameterized` - Use %s/%d formatting, not f-strings, in logger calls
- `logging-exception-context` - Log with business context + exc_info=True
- `logging-correlation-ids` - Use logging.Filter for request ID propagation
- `logging-structured-json` - Use JSON formatter for production/cloud logs

### 5. Language Fundamentals (MEDIUM)

- `lang-type-hints` - Type hints on public function signatures
- `lang-string-handling` - f-strings for code, %s for logging
- `lang-collections` - Comprehensions, dict.get(), defaultdict
- `lang-method-design` - Small functions, single responsibility, guard clauses
- `lang-algorithmic` - Avoid O(n²) nested loops, use dict/set for lookup
- `lang-null-safety` - Defensive chaining, `is None`, early validation

### 6. Design Patterns (MEDIUM)

- `pattern-constants-module` - Centralize all magic values with Final
- `pattern-dataclasses` - Use @dataclass(frozen=True) for structured data

### 7. Testing (MEDIUM)

- `testing-pytest-structure` - Given/When/Then with named constants
- `testing-mock-interface` - Mock(spec=ABC) at the interface boundary

### 8. External Resources & Operations (LOW-MEDIUM)

- `resource-connection-pool` - SQLAlchemy pools, reuse boto3 clients
- `resource-http-sessions` - Reuse requests.Session with explicit timeouts
- `resource-caching` - TTLCache/lru_cache with maxsize and TTL
- `resource-dynamic-log-levels` - Env var or SSM parameter for runtime toggle
- `resource-notebook-execution-safety` - Execute notebooks to temp output during repair loops
- `resource-notebook-runtime-config` - Load environment-specific notebook values from env/config, not committed cells

## How to Use

- Use [references/source-backed-python-tooling.md](references/source-backed-python-tooling.md) for current tooling, async, typing, and notebook choices.
- [references/rules.md](references/rules.md) is a compact always-on summary of this baseline for consumer repos that want the whole thing in one short file.
- Read the standalone rule files below for detailed explanations and code examples. These are the only rule files that exist on disk — every other quick-reference slug is expanded in `AGENTS.md`:

```
rules/concurrency-gil-myth.md
rules/concurrency-immutability.md
rules/concurrency-shared-mutable.md
rules/di-constructor-injection.md
rules/di-interface-isolation.md
rules/error-specific-exceptions.md
rules/imports-remove-unused.md
rules/lang-algorithmic.md
rules/logging-exception-context.md
rules/logging-parameterized.md
rules/resource-notebook-execution-safety.md
rules/resource-notebook-runtime-config.md
rules/testing-mock-interface.md
```

Each rule file contains:
- Brief explanation of why it matters
- Incorrect code example with explanation
- Correct code example with explanation
- Additional context and key rules

## Related Skills

- **best-practices** — SOLID principles, architecture patterns, resilience (language-agnostic foundations that Python implements)
- **security** — Injection prevention, auth, secrets management (applies to all Python endpoints handling user data)
- **testing** — AC traceability, test pyramid, coverage checklist (universal testing discipline beyond Python-specific patterns)

## Full Compiled Document

For the complete guide with all rules expanded: `AGENTS.md`
