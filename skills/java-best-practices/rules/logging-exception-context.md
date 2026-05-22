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
