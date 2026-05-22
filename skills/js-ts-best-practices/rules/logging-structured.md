---
title: Structured JSON Logging with Correlation IDs
impact: MEDIUM
impactDescription: Enables filtering, alerting, and cross-service tracing
tags: javascript, typescript, logging, pino, structured, correlation-id
---

## Structured JSON Logging with Correlation IDs

Use a structured JSON logger (pino, winston) with automatic correlation ID propagation.

**Incorrect (console.log with string concatenation):**

```typescript
console.log("Processing order " + orderId + " for user " + userId);
```

**Correct (structured logger with context):**

```typescript
import pino from "pino";
const logger = pino({ level: process.env.LOG_LEVEL ?? "info" });

logger.info({ orderId, userId, itemCount: order.items.length }, "Processing order");
logger.error({ orderId, err }, "Order processing failed");
```

**Correct (automatic correlation IDs via AsyncLocalStorage):**

```typescript
import { AsyncLocalStorage } from "async_hooks";

const als = new AsyncLocalStorage<{ requestId: string }>();

app.use((req, res, next) => {
  const requestId = req.headers["x-request-id"] as string ?? crypto.randomUUID();
  als.run({ requestId }, () => next());
});

const logger = pino({
  mixin() {
    const store = als.getStore();
    return store ? { requestId: store.requestId } : {};
  },
});
```

- Never log tokens, PII, or full request/response bodies in production
