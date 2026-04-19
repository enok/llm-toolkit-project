---
title: Timeouts on Every External Call
impact: MEDIUM
impactDescription: Missing timeouts cause resource exhaustion and cascading failures
tags: resilience, timeouts, external-calls, fault-tolerance
---

## Timeouts on Every External Call

Every HTTP call, database query, or external service interaction must have a timeout. No unbounded waits.

**Incorrect (no timeout — hangs indefinitely if service is down):**

```typescript
const response = await fetch("https://api.payment.com/charge", {
  method: "POST",
  body: JSON.stringify(charge),
});
```

**Correct (timeout prevents resource exhaustion):**

```typescript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 5000);
try {
  const response = await fetch("https://api.payment.com/charge", {
    method: "POST",
    body: JSON.stringify(charge),
    signal: controller.signal,
  });
} finally {
  clearTimeout(timeoutId);
}
```

- Set timeouts on HTTP clients, DB connections, message consumers
- Choose timeout values based on SLAs (e.g., P99 latency × 2)
- Combine with retry + circuit breaker for full resilience
