---
title: Log Exceptions with Business Context
impact: HIGH
impactDescription: Enables diagnosis without reading full stack traces
tags: java, logging, exceptions, context, slf4j
---

## Log Exceptions with Business Context

Include enough context to diagnose the issue without reading the full stack trace.

**Incorrect (no business context, useless in CloudWatch):**

```java
log.error("Operation failed", e);
```

**Correct (business context + root cause + full exception):**

```java
log.error(
    String.format("DynamoDB retrieval failed for requestId %s [root cause: %s]",
        requestId, ExceptionUtils.getRootCauseMessage(e)),
    e);
```

Pattern: `log.error(String.format("What failed for key=%s [root cause: %s]", key, ExceptionUtils.getRootCauseMessage(e)), e)`

- First arg (String): human-readable message with business context and root cause
- Second arg (Throwable): full exception for stack trace
- Never include PII in exception messages. Pseudonymous IDs (requestId, orderId) are OK.
- For exception logs, prefer the explicit `(String, Throwable)` overload after
  preformatting the message; avoid mixed placeholder varargs when the project
  logging stack might treat the throwable as a normal formatting argument.
- At external-client or request-boundary failure points, include sanitized
  request identifiers, routing keys, model/config identifiers, and downstream
  dependency names. Wrap unexpected dependency parsing/runtime failures in a
  project exception that preserves the original cause.
