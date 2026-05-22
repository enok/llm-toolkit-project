---
title: Prefer Immutability
impact: MEDIUM
impactDescription: Prevents accidental mutation, simplifies reasoning
tags: java, immutability, final, defensive-copy
---

## Prefer Immutability

Use `final` fields wherever possible. Return unmodifiable collections from getters.

**Incorrect (mutable, error-prone):**

```java
public class User {
    public String name;
    public List<String> roles;
}
```

**Correct (immutable, safe):**

```java
public final class User {
    private final String name;
    private final List<String> roles;

    public User(String name, List<String> roles) {
        this.name = Objects.requireNonNull(name);
        this.roles = List.copyOf(roles);
    }

    public String getName() { return name; }
    public List<String> getRoles() { return roles; }
}
```

- Use `List.copyOf()` or `Collections.unmodifiableList()` for collection fields
- Use `@Value` (Lombok) or Java records for simple immutable data carriers
