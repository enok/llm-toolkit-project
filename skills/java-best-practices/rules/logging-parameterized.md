---
title: Use SLF4J Parameterized Logging
impact: HIGH
impactDescription: Avoids unnecessary string construction when log level disabled
tags: java, logging, slf4j, performance
---

## Use SLF4J Parameterized Logging

Never use string concatenation in log statements — use `{}` placeholders for lazy evaluation.

**Incorrect (string concatenation — evaluated even if level disabled):**

```java
log.debug("Processing user: " + user.getId() + " with " + items.size() + " items");
```

**Correct (parameterized — lazy evaluation):**

```java
log.debug("Processing user: {} with {} items", user.getId(), items.size());
```

- Use appropriate levels: ERROR (action needed), WARNING (concerning), INFO (milestones), DEBUG (diagnostics).
- Log at function boundaries: entry (DEBUG), result (INFO/DEBUG), exceptions (ERROR/WARNING).
- Never log PII, credentials, or full request/response bodies in production.
- For startup beans or configuration loaders that establish critical runtime
  state, log the final sanitized or parsed value at `INFO` after successful
  construction. Prefer the value the application will use over raw config
  payloads, and keep equivalent logs for mock/test replacement paths.
