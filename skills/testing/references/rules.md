---
trigger: always_on
description: Testing discipline — coverage, AC traceability, test patterns
---

# Testing Rules

Testing discipline that applies to any project and tech stack.

## Non-Negotiable Requirements

- **Never commit code without ALL related tests passing at 100%.**
- **You are responsible for running and verifying tests** — never ask the user to test on your behalf.
- **Every new or modified method requires test coverage** — happy path + edge cases + exceptions.
- **Always create tests for edge cases** — null/empty inputs, boundary values (zero, negative, max), single-element and large collections, off-by-one, concurrent access, and unexpected types. Edge case tests catch the bugs that happy-path tests miss.
- **Create test file if none exists** — mirror the source path under the test directory.
- **Keep tests DRY** — use named constants, shared builders, reusable fixtures.

## AC-to-Test Traceability

For every ticket, map each acceptance criterion (AC) to its test(s) before writing code. This prevents untested ACs — one of the main drivers of endless review cycles.

**Template** (add as a comment at the top of the primary test file for the ticket):

```
// AC Coverage for <TICKET>:
// AC-1: "<AC text>" → testMethod_or_testName()
// AC-2: "<AC text>" → testMethod_1(), testEdgeCase_2()
// AC-3: "<AC text>" → [MISSING — add before merge]
```

**Rules:**
- Each AC maps to one or more test names.
- If an AC has no test yet, mark it `[MISSING]` — this is a blocker.
- If an AC is untestable as written, flag it to the ticket author before starting implementation.
- E2E tests count as AC coverage for user-facing, integration-level ACs.

## Test Patterns

### Unit Tests
- Use the project's standard test runner (JUnit, Jest, pytest, etc.).
- Named constants over magic literals — define once per test file, reference everywhere.
- Structure: given/when/then or arrange/act/assert.
- Cover: happy path, null/empty inputs, boundary conditions, exception paths, collection edge cases.

### Integration / E2E Tests
- For API, cross-service, or database changes — ensure integration tests exist.
- For user-facing UI changes — add or update E2E tests.

## Test Coverage Checklist

- [ ] Happy path (valid input, expected output)
- [ ] Null/empty inputs (guard clauses tested)
- [ ] Collection edge cases (empty list, single element, large list)
- [ ] Exception paths (verify exception type and message)
- [ ] Boundary conditions (zero, negative, max values)

## Test Discipline Summary

1. **Read source before writing tests** — verify method signatures, return types.
2. **Test file mirrors source path** — create it if it doesn't exist.
3. **Named constants over magic literals** — define once, reference everywhere.
4. **DRY fixtures** — builder methods or shared test data, no copy-paste.
5. **Verify results yourself** — run every test after every code change.
