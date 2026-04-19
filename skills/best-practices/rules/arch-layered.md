---
title: Layered Architecture — Never Skip Layers
impact: HIGH
impactDescription: Bypassing layers couples presentation to data access and breaks testability
tags: architecture, layered, separation-of-concerns, controller, service, repository
---

## Layered Architecture — Never Skip Layers

Controller → Service → Repository. Each layer has clear responsibilities and must not be bypassed.

**Incorrect (controller calls repository directly — no business logic layer):**

```java
@RestController
class OrderController {
    @Autowired OrderRepository repo;

    @PostMapping("/orders")
    Order create(@RequestBody OrderRequest req) {
        Order order = new Order(req);
        return repo.save(order);  // no validation, no business rules
    }
}
```

**Correct (controller delegates to service, service owns the rules):**

```java
@RestController
class OrderController {
    private final OrderService orderService;

    @PostMapping("/orders")
    OrderResponse create(@RequestBody OrderRequest req) {
        return orderService.placeOrder(req);  // delegates
    }
}

class OrderService {
    private final OrderRepository repo;
    private final NotificationService notifier;

    OrderResponse placeOrder(OrderRequest req) {
        validate(req);
        Order order = repo.save(Order.from(req));
        notifier.orderPlaced(order);
        return OrderResponse.from(order);
    }
}
```

| Layer | Responsibility | Must NOT contain |
|-------|---------------|-----------------|
| Controller | Parse input, delegate, format response | Business logic, SQL |
| Service | Business rules, orchestration, transactions | HTTP concerns, query building |
| Repository | Data access, queries, caching | Business rules, HTTP handling |
