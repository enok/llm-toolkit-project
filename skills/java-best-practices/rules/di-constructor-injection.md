---
title: Constructor Injection with Interfaces
impact: CRITICAL
impactDescription: Testability, loose coupling, explicit dependencies
tags: java, dependency-injection, constructor, interfaces, clean-architecture
---

## Constructor Injection with Interfaces

Every class receives its external collaborators as interfaces through the constructor. The configuration layer is the only place that knows which concrete implementation to bind.

**Incorrect (field injection — hidden, mutable, untestable without framework):**

```java
@Service
public class OrderService {
    @Autowired private OrderRepository orderRepository;
}
```

**Incorrect (concrete instantiation — tightly coupled, untestable):**

```java
public class OrderService {
    private final OrderRepository repo = new DynamoDbOrderRepository();
}
```

**Correct (constructor injection with interfaces):**

```java
public class OrderService {
    private final OrderRepository orderRepository;
    private final NotificationClient notificationClient;

    public OrderService(OrderRepository orderRepository, NotificationClient notificationClient) {
        this.orderRepository = Objects.requireNonNull(orderRepository);
        this.notificationClient = Objects.requireNonNull(notificationClient);
    }
}
```

Key rules:
- Accept interfaces, never concrete classes
- Use `Objects.requireNonNull()` for fail-fast validation
- `final` fields for immutability and thread safety
- Constructor signature = dependency manifest
