---
title: Catch Specific Exceptions with Context
impact: HIGH
impactDescription: Enables targeted recovery and clear diagnostics
tags: java, error-handling, exceptions, catch
---

## Catch Specific Exceptions with Context

Catch the most specific exception type. Include business context and preserve the cause chain.

**Incorrect (catching too broadly, no context):**

```java
try {
    process(data);
} catch (Exception e) {
    log.error("Failed", e);
}
```

**Correct (specific, contextual, preserves cause):**

```java
try {
    int value = Integer.parseInt(rawValue);
} catch (NumberFormatException e) {
    throw new ValidationException(
        String.format("Invalid numeric value: %s", rawValue), e);
}
```

- Never catch `Exception` or `Throwable` unless at the top-level handler
- Use `raise ... from e` / constructor chaining to preserve root cause
- Custom exceptions should inherit from a project-specific base
- Never swallow exceptions silently (`catch (Exception e) { }`)
