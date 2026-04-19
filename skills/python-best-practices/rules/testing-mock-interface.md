---
title: Mock at the Interface Boundary
impact: MEDIUM
impactDescription: Clean tests that survive implementation changes
tags: python, testing, mock, unittest, pytest
---

## Mock at the Interface Boundary

Mock the ABC/Protocol, not the concrete implementation or low-level internals.

**Incorrect (mocking boto3 internals):**

```python
with patch("boto3.resource") as mock_resource:
    mock_table = mock_resource.return_value.Table.return_value
    mock_table.get_item.return_value = {...}  # fragile, tied to boto3 API
```

**Correct (mocking the interface):**

```python
from unittest.mock import Mock

mock_repo = Mock(spec=OrderRepository)
mock_repo.find_by_user_id.return_value = {"userId": "user-123"}

mock_notifier = Mock(spec=NotificationClient)

service = OrderService(mock_repo, mock_notifier)
service.place_order(order)

mock_repo.save.assert_called_once_with(order)
mock_notifier.send_order_confirmation.assert_called_once_with(order)
```

- Use `Mock(spec=ABC)` to enforce interface contract
- This is why Interface-Based Isolation matters — testability
- Use `moto` for AWS service mocking in integration tests
