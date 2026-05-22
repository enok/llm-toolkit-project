# Python Backend Rules (Template)

> **This is a template.** Copy and fill in your project's Python backend conventions.

## Code Style

[Define your project's formatter, linting, and naming conventions.]

```python
# Example: Black formatter (88 char line length)
# Example: isort for import sorting
# Example: flake8 or ruff for linting

# Naming: snake_case for functions/variables, PascalCase for classes, UPPER_SNAKE_CASE for constants
```

**Imports:**
```python
# stdlib → third-party → local, separated by blank lines
import os
import json

import boto3
from fastapi import FastAPI

from myapp.services import OrderService
from myapp.models import Order
```

## Framework Pattern

[Show your project's standard framework pattern, e.g.:]

### FastAPI
```python
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/api/v1/entity", tags=["entity"])

@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: int,
    user: User = Depends(get_current_user),  # always add authorization
    service: EntityService = Depends(get_entity_service),
):
    entity = service.get_by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity
```

### Flask
```python
from flask import Blueprint, jsonify, request

bp = Blueprint("entity", __name__, url_prefix="/api/v1/entity")

@bp.route("/<int:entity_id>", methods=["GET"])
@login_required  # always add authorization
def get_entity(entity_id):
    entity = entity_service.get_by_id(entity_id)
    if not entity:
        return jsonify({"error": "Entity not found"}), 404
    return jsonify(entity.to_dict())
```

### Lambda Handler
```python
def lambda_handler(event, context):
    initialize()  # cached clients, warm start optimization
    try:
        payload = parse_and_validate(event)
        result = process(payload)
        return build_response(200, result)
    except ValidationException as e:
        logger.warning("Validation failed: %s", e)
        return build_response(400, {"error": str(e)})
    except Exception as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        return build_response(500, {"error": "Internal server error"})
```

## Service Layer Pattern

```python
class EntityService:
    def __init__(self, repository: EntityRepository, mapper: EntityMapper):
        self.repository = repository
        self.mapper = mapper

    def get_by_id(self, entity_id: int) -> EntityDto:
        entity = self.repository.find_by_id(entity_id)
        if not entity:
            raise NotFoundException(f"Entity not found: {entity_id}")
        return self.mapper.to_dto(entity)
```

## Multi-tenancy (if applicable)

[Describe how tenant isolation works in your project, e.g.:]

```python
# All queries must filter by tenant
tenant_id = get_current_tenant_id()
results = repository.find_by_tenant(tenant_id)
```

## Feature Flags (if applicable)

```python
if feature_flags.is_enabled("MY_FEATURE"):
    # new behavior
    pass
```

## Database Migrations

- **Tool:** [e.g., Alembic, Django migrations, raw SQL]
- **Location:** `[your migration directory]`
- **Naming:** `[your naming convention]`
- **Run:** `[your migration command, e.g., alembic upgrade head]`
- **Never modify existing migration files**

## Testing

```python
# [Show your project's test pattern]
import pytest
from unittest.mock import Mock

class TestEntityService:
    TEST_ID = 42

    def setup_method(self):
        self.mock_repository = Mock(spec=EntityRepository)
        self.mock_mapper = Mock(spec=EntityMapper)
        self.service = EntityService(self.mock_repository, self.mock_mapper)

    def test_get_by_id_returns_dto(self):
        self.mock_repository.find_by_id.return_value = mock_entity
        result = self.service.get_by_id(self.TEST_ID)
        assert result is not None
        self.mock_repository.find_by_id.assert_called_once_with(self.TEST_ID)

    def test_get_by_id_raises_when_not_found(self):
        self.mock_repository.find_by_id.return_value = None
        with pytest.raises(NotFoundException):
            self.service.get_by_id(self.TEST_ID)
```

## Running Tests

```bash
# [Your project's test commands]
# pytest:     pytest tests/test_module.py -v
# pytest specific: pytest tests/test_module.py::TestClass::test_method
# with coverage:   pytest --cov=myapp tests/
# Django:     python manage.py test app_name
```
