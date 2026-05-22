---
title: Interface-Based Isolation for External Access
impact: CRITICAL
impactDescription: Decouples business logic from infrastructure
tags: java, dependency-injection, interfaces, repository, gateway, clean-architecture
---

## Interface-Based Isolation for External Access

Define an interface for every external dependency — database, HTTP client, message publisher, cache, file system.

**Incorrect (service depends on concrete implementation):**

```java
public class OrderService {
    private final DynamoDbOrderRepository repo;  // tied to DynamoDB
}
```

**Correct (interface + implementation + easy mocking):**

```java
// Interface — lives in service/domain layer
public interface OrderRepository {
    Optional<Order> findByUserId(String userId);
    void save(Order order);
}

// Implementation — lives in infrastructure layer
public class DynamoDbOrderRepository implements OrderRepository {
    private final DynamoDBMapper mapper;
    @Override
    public Optional<Order> findByUserId(String userId) {
        return Optional.ofNullable(mapper.load(Order.class, userId));
    }
}

// Test — trivial to mock
@Mock private OrderRepository orderRepository;
given(orderRepository.findByUserId("user-123")).willReturn(Optional.of(testOrder));
```

This is the Gateway / Repository / Adapter pattern from Clean Architecture.
