---
title: Promise.all() for Independent Operations
impact: CRITICAL
impactDescription: 2-10× improvement by parallelizing independent I/O
tags: javascript, typescript, async, promise, parallelization
---

## Promise.all() for Independent Operations

When async operations have no interdependencies, execute them concurrently.

**Incorrect (sequential — 3 round trips):**

```typescript
const user = await fetchUser(id);
const orders = await fetchOrders(id);
const preferences = await fetchPreferences(id);
```

**Correct (parallel — 1 round trip):**

```typescript
const [user, orders, preferences] = await Promise.all([
  fetchUser(id),
  fetchOrders(id),
  fetchPreferences(id),
]);
```

**Correct (fault-tolerant — some may fail):**

```typescript
const results = await Promise.allSettled([
  fetchUser(id),
  fetchOrders(id),
  fetchPreferences(id),
]);
const succeeded = results.filter(r => r.status === "fulfilled").map(r => r.value);
```

- `Promise.all()` — fails fast on first rejection
- `Promise.allSettled()` — waits for all, reports each status
