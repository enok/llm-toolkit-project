---
title: Single Responsibility Principle
impact: CRITICAL
impactDescription: Classes with multiple reasons to change are fragile and hard to test
tags: solid, srp, architecture, clean-code, separation-of-concerns
---

## Single Responsibility Principle

Each class/module/function does one thing well. If you can't describe its purpose in one sentence, split it.

**Incorrect (one class handles HTTP, validation, persistence, and email):**

```java
class OrderController {
    void createOrder(Request req) {
        Order order = parseJson(req.body());
        if (order.total() < 0) throw new Ex();
        db.save(order);
        emailService.send(order.customer(), "...");
    }
}
```

**Correct (each class has one reason to change):**

```java
class OrderController {
    void createOrder(Request req) {
        Order order = orderParser.parse(req);
        orderService.place(order);
    }
}

class OrderService {
    void place(Order order) {
        orderValidator.validate(order);
        orderRepository.save(order);
        notificationService.orderPlaced(order);
    }
}
```

- Controller: HTTP concern only
- Service: business orchestration only
- Repository: persistence only
- Notification: delivery only
