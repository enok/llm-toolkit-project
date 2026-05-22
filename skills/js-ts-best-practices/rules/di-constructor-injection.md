---
title: Constructor Injection with Interfaces
impact: HIGH
impactDescription: Testability, loose coupling, explicit dependencies
tags: javascript, typescript, dependency-injection, interfaces, clean-architecture
---

## Constructor Injection with Interfaces

Every class receives its external collaborators as interfaces through the constructor. The composition root is the only place that knows which concrete implementation to bind.

**Incorrect (importing concrete implementation — tightly coupled):**

```typescript
import { DynamoDbOrderRepository } from "../infra/dynamo-repo";
class OrderService {
  private repo = new DynamoDbOrderRepository();  // untestable without DynamoDB
}
```

**Correct (constructor injection with interface):**

```typescript
interface OrderRepository {
  findByUserId(userId: string): Promise<Order | null>;
  save(order: Order): Promise<void>;
}

class OrderService {
  constructor(
    private readonly orderRepo: OrderRepository,
    private readonly notificationClient: NotificationClient,
  ) {}
}

// Test — trivial to mock
const mockRepo: OrderRepository = {
  findByUserId: vi.fn().mockResolvedValue(testOrder),
  save: vi.fn().mockResolvedValue(undefined),
};
const service = new OrderService(mockRepo, mockNotifier);
```

- Accept interfaces, never concrete classes
- Constructor signature = dependency manifest
- Composition root / DI container wires implementations
