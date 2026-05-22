---
title: Avoid O(n²) — Use Map/Set for Lookup
impact: MEDIUM
impactDescription: O(n²) to O(n) for collection matching
tags: java, performance, algorithmic-complexity, collections
---

## Avoid O(n²) — Use Map/Set for Lookup

Never nest loops over collections. Build a lookup Map or Set first.

**Incorrect (O(n²) — scans activeUsers for every order):**

```java
for (Order order : orders) {
    for (User user : activeUsers) {
        if (user.getId().equals(order.getUserId())) { /* match */ }
    }
}
```

**Correct (O(n) — build lookup map first):**

```java
Map<String, User> userById = activeUsers.stream()
    .collect(Collectors.toMap(User::getId, Function.identity()));
for (Order order : orders) {
    User user = userById.get(order.getUserId());
    if (user != null) { /* match */ }
}
```

- Three levels of nesting is a red flag — extract inner loops into named methods
- Use `Set` for membership checks — `O(1)` vs `List.contains()` at `O(n)`
- Batch external calls — never call a database or HTTP API inside a loop
