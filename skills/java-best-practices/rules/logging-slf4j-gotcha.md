---
title: Prefer Explicit Throwable Logging Over Varargs Guessing
impact: HIGH
impactDescription: Preserves stack traces across SLF4J, Log4j-backed adapters, and Commons Logging
tags: java, logging, slf4j, log4j, exceptions, throwable
---

## Prefer Explicit Throwable Logging Over Varargs Guessing

When logging an exception, prefer the explicit `(String, Throwable)` overload
after building the message string. Do not rely on every project logging stack
to interpret `String + placeholders + values + Throwable` the same way.

**Risky (depends on varargs throwable handling):**

```java
log.error("Failed for model {}", model, e);
```

**Safer (explicit throwable overload):**

```java
log.error(String.format("Failed for model %s", model), e);
```

This is especially important in projects that bridge SLF4J, Log4j, and Commons
Logging, or where tests and runtime use different logger adapters.

If you add source-level regression guards for this, verify the guard is
discovered by the repository's normal build lifecycle. A directly invoked test
is not enough proof if Surefire or Failsafe naming patterns would skip it during
the default validation command.
