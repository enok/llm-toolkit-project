---
title: Constructor Injection with ABCs/Protocols
impact: CRITICAL
impactDescription: Testability, loose coupling, explicit dependencies
tags: python, dependency-injection, abc, protocol, clean-architecture
---

## Constructor Injection with ABCs/Protocols

Every class receives its external collaborators as abstract types (ABCs or Protocols) through `__init__`. The application entry point is the only place that knows which concrete implementation to wire.

**Incorrect (concrete instantiation — tightly coupled, untestable):**

```python
class OrderService:
    def __init__(self):
        self.db = boto3.resource("dynamodb")  # coupled to AWS
```

**Incorrect (module-level globals as hidden dependencies):**

```python
_repo = DynamoDbOrderRepository()
class OrderService:
    def process(self, order):
        _repo.save(order)  # hidden, untestable
```

**Correct (constructor injection with abstract type):**

```python
class OrderService:
    def __init__(self, order_repo: OrderRepository, notification_client: NotificationClient):
        self._order_repo = order_repo
        self._notification_client = notification_client

    def place_order(self, order: dict) -> None:
        self._order_repo.save(order)
        self._notification_client.send_order_confirmation(order)
```

Key rules:
- Accept ABCs or Protocols, never concrete classes
- `__init__` signature = dependency manifest
- Application entry point wires implementations
- Tests pass `Mock(spec=OrderRepository)` — no framework needed
