---
title: Use MDC for Correlation IDs
impact: HIGH
impactDescription: Enables cross-service request tracing
tags: java, logging, mdc, correlation-id, observability
---

## Use MDC for Correlation IDs

Use MDC (Mapped Diagnostic Context) to automatically include correlation IDs in every log line.

**Incorrect (manually adding ID to every log call):**

```java
log.info("[requestId=" + rid + "] Processing order");
log.info("[requestId=" + rid + "] Order saved");
```

**Correct (MDC — automatic inclusion in every log line):**

```java
MDC.put("requestId", rid);
try {
    log.info("Processing order");  // requestId included automatically
    log.info("Order saved");
} finally {
    MDC.remove("requestId");
}
```

```xml
<PatternLayout pattern="%d [%X{requestId}] [%t] %-5p [%c] %m%n%xEx{200}"/>
```

- Set MDC at the request boundary (servlet filter, Lambda handler entry)
- Always clean up in `finally` — MDC is thread-local and leaks across pooled threads
- Use the correlation ID for cross-service tracing
