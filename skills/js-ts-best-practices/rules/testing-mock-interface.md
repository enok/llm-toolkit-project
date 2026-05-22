---
title: Mock at the Interface Boundary
impact: MEDIUM
impactDescription: Clean tests that survive implementation changes
tags: javascript, typescript, testing, vitest, jest, mocking
---

## Mock at the Interface Boundary

Mock the interface, not the module internals. This is why DI matters — testability.

**Incorrect (mocking module internals — fragile):**

```typescript
vi.mock("@aws-sdk/client-dynamodb", () => ({
  DynamoDBClient: vi.fn().mockImplementation(() => ({
    send: vi.fn().mockResolvedValue({ Item: testOrder }),
  })),
}));
```

**Correct (mock the interface — clean, survives impl changes):**

```typescript
const mockRepo: OrderRepository = {
  findByUserId: vi.fn().mockResolvedValue(testOrder),
  save: vi.fn().mockResolvedValue(undefined),
};
const service = new OrderService(mockRepo, mockNotifier);

await service.placeOrder(order);
expect(mockRepo.save).toHaveBeenCalledWith(order);
```

- Interface mocks are plain objects satisfying the type — no framework magic
- Tests survive when you swap DynamoDB for PostgreSQL (only infra layer changes)
