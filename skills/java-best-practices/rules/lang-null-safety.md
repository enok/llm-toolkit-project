---
title: Null Safety with Optional
impact: MEDIUM
impactDescription: Prevents NullPointerException at compile time
tags: java, null-safety, optional, requireNonNull
---

## Null Safety with Optional

Use `Optional` for return types that may be absent. Use `Objects.requireNonNull` for required parameters.

**Incorrect (null returns, no validation):**

```java
public User findById(String id) {
    return userMap.get(id);  // returns null silently
}
```

**Correct (explicit absence, fail-fast validation):**

```java
public Optional<User> findById(String id) {
    return Optional.ofNullable(userMap.get(id));
}

public void process(Order order) {
    Objects.requireNonNull(order, "order must not be null");
}
```

- Never return `null` from public methods — use `Optional`, empty collections, or throw.
- Use `Optional.map()` / `Optional.flatMap()` for chained access instead of nested null checks.
- Never use `Optional` as a method parameter or field — only as a return type.
