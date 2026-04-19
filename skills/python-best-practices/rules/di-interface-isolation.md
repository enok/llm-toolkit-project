---
title: Interface-Based Isolation with ABC/Protocol
impact: CRITICAL
impactDescription: Decouples business logic from infrastructure
tags: python, dependency-injection, abc, protocol, repository, clean-architecture
---

## Interface-Based Isolation with ABC/Protocol

Define an ABC or Protocol for every external dependency — database, HTTP client, message publisher, cache.

**Incorrect (service depends on concrete implementation):**

```python
from myapp.infra.dynamo_repo import DynamoDbOrderRepository
class OrderService:
    def __init__(self):
        self.repo = DynamoDbOrderRepository()  # tied to DynamoDB
```

**Correct (ABC interface + implementation + easy mocking):**

```python
from abc import ABC, abstractmethod

# Interface — lives in service/domain layer
class OrderRepository(ABC):
    @abstractmethod
    def find_by_user_id(self, user_id: str) -> Optional[dict]: ...
    @abstractmethod
    def save(self, order: dict) -> None: ...

# Implementation — lives in infrastructure layer
class DynamoDbOrderRepository(OrderRepository):
    def __init__(self, table):
        self._table = table
    def find_by_user_id(self, user_id: str) -> Optional[dict]:
        return self._table.get_item(Key={"userId": user_id}).get("Item")

# Test — trivial to mock
mock_repo = Mock(spec=OrderRepository)
mock_repo.find_by_user_id.return_value = {"userId": "user-123"}
```

Alternative: use `typing.Protocol` for duck-typing compatibility (no inheritance needed).
