---
title: Arrange-Act-Assert Test Structure
impact: HIGH
impactDescription: Clear test structure makes tests readable, maintainable, and debuggable
tags: testing, arrange-act-assert, given-when-then, structure, pattern
---

## Arrange-Act-Assert (Given-When-Then)

Every test has exactly three phases, clearly separated.

**Incorrect (mixed phases, unclear what's being tested):**

```typescript
it("order test", async () => {
  const order = buildOrder({ items: [{ sku: "A", qty: 2 }] });
  await service.placeOrder(order);
  expect(mockRepo.save).toHaveBeenCalled();
  const bad = buildOrder({ items: [] });
  await expect(service.placeOrder(bad)).rejects.toThrow();
});
```

**Correct (clear phases, one behavior per test):**

```typescript
it("saves order on valid placeOrder", async () => {
  // Arrange
  const order = buildOrder({ items: [{ sku: "A", qty: 2 }] });

  // Act
  await service.placeOrder(order);

  // Assert
  expect(mockRepo.save).toHaveBeenCalledWith(order);
});

it("rejects empty items", async () => {
  // Arrange
  const order = buildOrder({ items: [] });

  // Act & Assert
  await expect(service.placeOrder(order)).rejects.toThrow(ValidationError);
});
```

- One behavior per test — if a test name needs "and", split it
- Named constants over magic literals
- Test name reads as a specification: `methodName_condition_expectedBehavior`
