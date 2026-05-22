---
title: Custom Error Classes with Typed Properties
impact: HIGH
impactDescription: Structured error handling with context for diagnostics
tags: javascript, typescript, error-handling, custom-errors
---

## Custom Error Classes with Typed Properties

Extend Error with structured metadata (statusCode, context) for consistent error handling.

**Incorrect (plain Error, no structured metadata):**

```typescript
throw new Error("Order not found");
```

**Correct (custom error hierarchy with context):**

```typescript
class AppError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
    public readonly context?: Record<string, unknown>,
    public readonly isOperational = true,
  ) {
    super(message);
    this.name = this.constructor.name;
    Error.captureStackTrace?.(this, this.constructor);
  }
}

class NotFoundError extends AppError {
  constructor(resource: string, id: string) {
    super(`${resource} not found: ${id}`, 404, { resource, id });
  }
}

throw new NotFoundError("Order", orderId);
```

- `isOperational` distinguishes expected errors (404, validation) from bugs (TypeError)
- `context` provides structured metadata for logging/diagnostics
