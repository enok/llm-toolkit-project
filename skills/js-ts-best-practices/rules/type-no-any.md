---
title: Never Use `any` — Use `unknown`, Generics, or Proper Types
impact: CRITICAL
impactDescription: Defeats the entire type system
tags: typescript, type-safety, any, unknown, generics
---

## Never Use `any`

`any` disables type checking entirely. Use `unknown` + narrowing or generics instead.

**Incorrect (defeats the type system):**

```typescript
function process(data: any): any {
  return data.items.map((item: any) => item.name);
}
```

**Correct (unknown + narrowing):**

```typescript
function process(data: unknown): string[] {
  if (!isValidResponse(data)) {
    throw new ValidationError("Invalid response shape");
  }
  return data.items.map((item) => item.name);
}
```

**Correct (generics for parametric types):**

```typescript
function identity<T>(value: T): T {
  return value;
}
```

- Use `unknown` for values of uncertain type, then narrow with type guards
- Use `as` only when you've verified the type externally (e.g., after JSON schema validation)
