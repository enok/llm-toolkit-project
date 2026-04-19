---
name: testing
description: Universal testing discipline and best practices for any project regardless of tech stack. This skill should be used when writing, reviewing, or planning tests. Triggers on tasks involving test coverage, AC traceability, unit/integration/E2E tests, mocking strategies, test structure, or test-driven development.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Testing Best Practices

Universal testing discipline that applies to any project and tech stack. Contains 20+ rules across 5 categories, prioritized by impact to guide test authoring, review, and coverage planning.

## When to Apply

Reference these guidelines when:
- Writing new tests for features or bug fixes
- Planning test coverage for a ticket or story
- Reviewing tests for completeness and quality
- Mapping acceptance criteria to test cases
- Choosing between unit, integration, and E2E tests
- Designing mocks, fixtures, and test data

## Rule Categories by Priority

| Priority | Category | Impact | Prefix |
|----------|----------|--------|--------|
| 1 | Test Discipline & Non-Negotiables | CRITICAL | `discipline-` |
| 2 | AC-to-Test Traceability | HIGH | `ac-` |
| 3 | Test Structure & Patterns | HIGH | `pattern-` |
| 4 | Mocking & Test Isolation | MEDIUM | `mock-` |
| 5 | Coverage & Test Pyramid | MEDIUM | `coverage-` |

## Quick Reference

### 1. Test Discipline (CRITICAL)

- `discipline-never-skip` - Never commit without ALL related tests passing at 100%
- `discipline-every-method` - Every new/modified method requires test coverage
- `discipline-verify-yourself` - Run and verify tests yourself — never ask user to test
- `discipline-read-source-first` - Read source before writing tests — verify signatures, types

### 2. AC-to-Test Traceability (HIGH)

- `ac-mapping` - Map every acceptance criterion to test(s) before writing code
- `ac-missing-blocker` - Unmapped ACs are merge blockers
- `ac-untestable` - Flag untestable ACs to ticket author before starting

### 3. Test Structure & Patterns (HIGH)

- `pattern-arrange-act-assert` - Structure: given/when/then or arrange/act/assert
- `pattern-named-constants` - Named constants over magic literals in tests
- `pattern-one-assertion-focus` - Each test verifies one behavior
- `pattern-dry-fixtures` - Shared builders/factories — no copy-paste test data

### 4. Mocking & Test Isolation (MEDIUM)

- `mock-at-boundary` - Mock external dependencies at the interface boundary
- `mock-no-internals` - Never mock private methods or internal implementation
- `mock-verify-interactions` - Verify mock was called with expected arguments

### 5. Coverage & Test Pyramid (MEDIUM)

- `coverage-happy-path` - Always test the happy path first
- `coverage-edge-cases` - Null, empty, boundary, negative, max-value
- `coverage-exception-paths` - Verify exception type and message
- `coverage-pyramid` - Many unit tests, fewer integration, fewest E2E

## How to Use

Read individual rule files for detailed explanations and code examples:

```
rules/ac-mapping.md
rules/pattern-arrange-act-assert.md
```

Each rule file contains:
- Brief explanation of why it matters
- Incorrect code example with explanation
- Correct code example with explanation
- Additional context and key rules

## Related Skills

This skill provides **universal testing discipline**. Pair it with language-specific testing patterns:

- **java-best-practices** — JUnit 5, Mockito, `assertThrows`, mock-at-interface patterns for Java
- **python-best-practices** — pytest, `Mock(spec=ABC)`, fixtures, given/when/then patterns for Python
- **js-ts-best-practices** — Vitest/Jest, `vi.fn()`, async test patterns, mock-at-interface for TypeScript
- **best-practices** — Architecture patterns (layered, SOLID) that make code testable in the first place
- **security** — Security-specific test cases: injection attempts, auth bypass, PII exposure

## Full Compiled Document

For the complete guide with all rules expanded: `AGENTS.md`
