---
title: Discriminated Unions and Type Narrowing
impact: CRITICAL
impactDescription: Compile-time exhaustiveness checking, eliminates runtime bugs
tags: typescript, type-safety, discriminated-unions, narrowing, exhaustive
---

## Discriminated Unions and Type Narrowing

Use discriminated unions with a literal `status` or `kind` field so TypeScript can narrow types in each branch.

**Incorrect (string status, no exhaustiveness):**

```typescript
interface ApiResponse {
  status: string;
  data?: unknown;
  error?: string;
}
```

**Correct (discriminated union with exhaustive matching):**

```typescript
type ApiResponse =
  | { status: "success"; data: OrderData }
  | { status: "error"; error: string; statusCode: number }
  | { status: "loading" };

function handleResponse(response: ApiResponse): string {
  switch (response.status) {
    case "success":
      return response.data.orderId;  // TS knows data exists
    case "error":
      throw new AppError(response.error, response.statusCode);
    case "loading":
      return "Loading...";
    default:
      const _exhaustive: never = response;  // compile error if case missed
      throw new Error(`Unhandled status: ${_exhaustive}`);
  }
}
```

The `never` check ensures a compile error if a new variant is added but not handled.
