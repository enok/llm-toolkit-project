# Python Best Practices

Language-specific best practices for Python projects. These apply to any Python codebase regardless of framework.

## Language Fundamentals

### Code Style (PEP 8)
- **4 spaces** for indentation (never tabs, unless matching an existing project that uses tabs).
- **snake_case** for functions, methods, variables. **PascalCase** for classes. **UPPER_SNAKE_CASE** for constants.
- **Line length**: 88–120 chars (match project's formatter — Black uses 88, most projects use 120).
- **Imports**: stdlib → third-party → local, separated by blank lines. One import per line. No wildcard imports (`from x import *`) except in `__init__.py` re-exports.

### Type Hints
```python
# GOOD — clear contracts
def calculate_score(threshold: float, values: list[float]) -> float:
    return sum(v for v in values if v > threshold)

# Constants with Final
from typing import Final
MAX_RETRIES: Final = 3
TABLE_NAME: Final = "orders"
```
- Use type hints on public function signatures — they serve as documentation and enable static analysis.
- Match existing project style — if the codebase doesn't use type hints on functions, don't add them selectively.
- Use `Final` for constants that should never be reassigned.

### String Handling
```python
# WRONG — concatenation
msg = "Processing " + str(count) + " items for " + user_id

# CORRECT — f-strings (Python 3.6+) for general code
msg = f"Processing {count} items for {user_id}"

# CORRECT — % formatting for logging (lazy evaluation)
logger.info("Processing %d items for %s", count, user_id)
```
- Use f-strings for general string building (readable, fast).
- Use `%s`/`%d` formatting for `logger` calls — avoids string construction when log level is disabled.
- Match whatever pattern the existing codebase uses.

### Collections
```python
# Prefer comprehensions over map/filter for readability
squares = [x**2 for x in numbers if x > 0]
lookup = {item.id: item for item in items}

# Use dict.get() with defaults instead of KeyError handling
value = config.get("key", "default")

# Use collections for specialized needs
from collections import defaultdict, Counter, OrderedDict
```
- Prefer `dict.get(key, default)` over `if key in dict: dict[key]`.
- Use `defaultdict` when building grouped/accumulated results.
- Never modify a dict/list while iterating — build a new one or collect keys to delete.

### Method Design

- **Keep functions small** — a function should do one thing. If you need a comment to explain a block of code inside a function, extract it into a named helper.
- **Target 10–20 lines per function.** Functions over 30 lines are a strong signal to refactor.
- **One level of abstraction per function** — don't mix high-level orchestration with low-level details.

```python
# WRONG — does too many things, hard to test individual parts
def process_order(order):
    if not order.items:
        raise ValidationException("No items")
    if order.total <= 0:
        raise ValidationException("Invalid total")
    discount = sum(item.discount for item in order.items if item.is_on_sale)
    order.discount = discount
    order_repository.save(order)
    email_service.send_confirmation(order)

# CORRECT — each function does one thing, independently testable
def process_order(order):
    validate_order(order)
    order.discount = calculate_discount(order.items)
    order_repository.save(order)
    email_service.send_confirmation(order)
```

- **Extract early returns** for validation (guard clauses) — reduces nesting.
- **Boolean parameters are a code smell** — prefer two clearly named functions or an enum.

### Algorithmic Complexity

- **Avoid nested loops over collections** — `O(n²)` or worse. Use a `dict` or `set` for lookup instead.

```python
# WRONG — O(n²), scans active_users for every order
for order in orders:
    for user in active_users:
        if user.id == order.user_id:
            # match
            pass

# CORRECT — O(n), build lookup dict first
user_by_id = {user.id: user for user in active_users}
for order in orders:
    user = user_by_id.get(order.user_id)
    if user:
        # match
        pass
```

- **Three levels of nesting is a red flag** — extract inner loops into named functions.
- **Use `set` for membership checks** — `O(1)` vs `list` at `O(n)`.
- **Batch external calls** — never call a database or HTTP API inside a loop. Collect IDs, batch-fetch, then process.

### Null Safety
```python
# WRONG — AttributeError on None
result = response.get("data").get("items")

# CORRECT — defensive chaining
data = response.get("data") or {}
items = data.get("items", [])

# CORRECT — early validation
if not request_payload:
    raise ValidationException(ERROR_CODE, "Missing payload")
```
- Check for `None`, empty strings, and empty collections explicitly.
- Use `or` for default values: `value = x or "default"` (but beware of falsy values like `0` or `False`).
- Use `is None` / `is not None` for explicit None checks — never `== None`.

## Error Handling

### Exception Patterns
```python
# WRONG — bare except
try:
    process(data)
except:
    pass

# WRONG — catching too broadly
try:
    process(data)
except Exception as e:
    logger.error("Failed: %s", e)

# CORRECT — specific, contextual, preserves cause
try:
    value = int(raw_value)
except ValueError as e:
    raise ValidationException(
        ERROR_CODE, f"Invalid numeric value: {raw_value}"
    ) from e
```
- Catch the most specific exception type.
- Use `raise ... from e` to preserve the cause chain.
- Never use bare `except:` — at minimum use `except Exception:`.
- Never swallow exceptions silently. Log or re-raise with context.
- Custom exceptions should inherit from a project-specific base (e.g., `ApplicationException`), not bare `Exception`.

### Context Managers
```python
# CORRECT — automatic cleanup
with open("file.txt") as f:
    data = f.read()

# For custom resources
from contextlib import contextmanager

@contextmanager
def managed_connection(url):
    conn = create_connection(url)
    try:
        yield conn
    finally:
        conn.close()
```
- Use `with` statements for all resources that need cleanup (files, connections, locks).
- Create custom context managers for project-specific resource management.

## Logging

### Parameterized Logging
```python
# WRONG — string constructed even if level is disabled
logger.debug(f"Processing user: {user_id} with {len(items)} items")

# CORRECT — lazy evaluation (string only constructed if DEBUG is enabled)
logger.debug("Processing user: %s with %d items", user_id, len(items))
```
- Use `%s`/`%d` formatting for `logger` calls — avoids string construction when log level is disabled.
- Use f-strings only when you're certain the log line will be emitted (e.g., inside an `if logger.isEnabledFor()` block), or in non-logging code.
- Use appropriate levels: ERROR (action needed), WARNING (concerning), INFO (milestones), DEBUG (diagnostics).
- Log at function boundaries: entry (DEBUG), result (INFO/DEBUG), exceptions (ERROR/WARNING).
- Never log PII, credentials, or full request/response bodies in production.

### Logging Exceptions with Context

When logging an exception, include enough context to diagnose the issue **without** reading the full stack trace:

```python
# WRONG — no business context
logger.error("Operation failed", exc_info=True)

# CORRECT — business context + root cause + full traceback
logger.error(
    "DynamoDB retrieval failed for requestId=%s [root cause: %s]",
    request_id, str(e),
    exc_info=True
)
```

**Pattern**: `logger.error("What failed for key=%s [root cause: %s]", key, str(e), exc_info=True)`

- **`exc_info=True`** — tells the logging framework to append the full traceback. Without it, only the message is logged.
- Include business context (IDs, operation name) in the message for quick log scanning.
- Never include PII in exception messages. Pseudonymous IDs (`requestId`, `orderId`, `userId`) are OK.

### Correlation IDs

Use a correlation ID to trace requests across log lines and services:

```python
import logging

# Add correlation ID to log records via a filter
class CorrelationFilter(logging.Filter):
    def __init__(self):
        super().__init__()
        self.request_id = ""

    def filter(self, record):
        record.request_id = self.request_id
        return True

# Configure log format to include correlation ID
formatter = logging.Formatter(
    "%(asctime)s [%(request_id)s] %(levelname)s %(name)s %(message)s"
)
```

- Set the correlation ID at the request entry point (Lambda handler, Flask/FastAPI middleware).
- Pass the same ID to downstream service calls for cross-service tracing.

### Structured Logging (JSON)

For production services (especially Lambda/cloud), use JSON-formatted logs for easy parsing:

```python
import json
import logging

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "requestId": getattr(record, "request_id", ""),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)
```

- JSON logs are easier to query in CloudWatch, Datadog, Splunk, etc.
- Libraries like `python-json-logger` or `structlog` simplify this.
- Always include a correlation/request ID in structured logs.

## Design Patterns

### Dependency Injection (DI) — The Core Principle

**Every class receives its external collaborators as abstract types (ABCs or Protocols) through the constructor.** The application entry point (main, Lambda handler bootstrap, FastAPI/Flask factory) is the only place that knows which concrete implementation to wire. This is the single most important pattern for testability, loose coupling, and maintainability.

#### The Rule

1. **Define an interface** for every external dependency (database, HTTP client, message publisher, cache, file system, third-party SDK) — use `abc.ABC` or `typing.Protocol`.
2. **Accept the interface in `__init__`** — never instantiate collaborators inside a class.
3. **Let the application entry point wire** the concrete implementation.
4. **In tests, pass a mock** — no framework magic needed.

#### Full Example

```python
from abc import ABC, abstractmethod
from typing import Optional

# 1. INTERFACE — defines the contract. Lives in the service/domain layer.
class OrderRepository(ABC):
    @abstractmethod
    def find_by_user_id(self, user_id: str) -> Optional[dict]:
        ...

    @abstractmethod
    def save(self, order: dict) -> None:
        ...

class NotificationClient(ABC):
    @abstractmethod
    def send_order_confirmation(self, order: dict) -> None:
        ...

# 2. IMPLEMENTATION — lives in the infrastructure layer. Knows about DynamoDB.
class DynamoDbOrderRepository(OrderRepository):
    def __init__(self, table):
        self._table = table

    def find_by_user_id(self, user_id: str) -> Optional[dict]:
        response = self._table.get_item(Key={"userId": user_id})
        return response.get("Item")

    def save(self, order: dict) -> None:
        self._table.put_item(Item=order)

# 3. SERVICE — depends ONLY on interfaces. Knows nothing about DynamoDB, HTTP, etc.
class OrderService:
    def __init__(self, order_repo: OrderRepository, notification_client: NotificationClient):
        self._order_repo = order_repo
        self._notification_client = notification_client

    def place_order(self, order: dict) -> None:
        self._validate(order)
        self._order_repo.save(order)
        self._notification_client.send_order_confirmation(order)

# 4. CONFIGURATION — the ONLY place that knows which implementation to use.
# Application entry point (e.g., main.py, app factory, Lambda bootstrap):
def create_order_service() -> OrderService:
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("orders")
    repo = DynamoDbOrderRepository(table)
    notifier = HttpNotificationClient(base_url=os.environ["NOTIFICATION_URL"])
    return OrderService(repo, notifier)

# FastAPI example:
def get_order_service() -> OrderService:
    return create_order_service()

@router.post("/orders")
async def create_order(order: OrderRequest, service: OrderService = Depends(get_order_service)):
    service.place_order(order.dict())

# Lambda example:
_order_service = None  # cached across warm starts

def initialize():
    global _order_service
    if _order_service is None:
        _order_service = create_order_service()

def lambda_handler(event, context):
    initialize()
    _order_service.place_order(parse_event(event))

# 5. TEST — trivial to mock, no framework needed.
from unittest.mock import Mock

class TestOrderService:
    def setup_method(self):
        self.mock_repo = Mock(spec=OrderRepository)
        self.mock_notifier = Mock(spec=NotificationClient)
        self.service = OrderService(self.mock_repo, self.mock_notifier)

    def test_place_order_saves_and_notifies(self):
        order = {"userId": "user-123", "total": 99.99}
        self.service.place_order(order)
        self.mock_repo.save.assert_called_once_with(order)
        self.mock_notifier.send_order_confirmation.assert_called_once_with(order)
```

#### Alternative: `typing.Protocol` (Structural / Duck-Typing DI)

```python
from typing import Protocol, Optional

# Protocol — no need to inherit. Any class with matching methods satisfies it.
class OrderRepository(Protocol):
    def find_by_user_id(self, user_id: str) -> Optional[dict]: ...
    def save(self, order: dict) -> None: ...
```
- Use `Protocol` when you want duck-typing compatibility (any class with the right methods works).
- Use `ABC` when you want explicit inheritance and enforcement.

#### Anti-Patterns (Never Do This)

```python
# WRONG — instantiating a concrete dependency inside the class. Untestable, tightly coupled.
class OrderService:
    def __init__(self):
        self.db = boto3.resource("dynamodb")  # coupled to AWS

# WRONG — importing and using a concrete class directly.
from myapp.infra.dynamo_repo import DynamoDbOrderRepository
class OrderService:
    def __init__(self):
        self.repo = DynamoDbOrderRepository()  # tied to DynamoDB

# WRONG — using module-level globals as hidden dependencies.
_repo = DynamoDbOrderRepository()  # hidden, untestable
class OrderService:
    def process(self, order):
        _repo.save(order)
```

#### Why This Matters

- **Testability** — swap real implementations for mocks in one line.
- **Loose coupling** — service logic never changes when you switch databases, HTTP clients, or message brokers.
- **Explicit dependencies** — the `__init__` signature is the dependency manifest. No hidden surprises.
- This is the **Gateway** / **Repository** / **Adapter** pattern from Clean Architecture.

### Constants Module
```python
# Constants.py — all magic values in one place
from typing import Final

TABLE_NAME: Final = "orders"
MAX_RETRIES: Final = 3
ERROR_MISSING_ID: Final = "4001"
ERROR_MISSING_ID_DESC: Final = "Missing required order ID"
```
- Centralize all constants — JSON keys, error codes, table names, env var names.
- Never hardcode strings or numbers inline. If a value appears more than once, it's a constant.

### Data Classes (Python 3.7+)
```python
from dataclasses import dataclass

@dataclass(frozen=True)  # frozen = immutable
class AppConfig:
    config_id: str
    endpoint: str
    threshold: float
```
- Use `@dataclass` for structured data — cleaner than plain dicts.
- Use `frozen=True` for immutable value objects.

## Performance

### Avoid Common Pitfalls
```python
# WRONG — mutable default argument (shared across calls!)
def process(items=[]):
    items.append("new")
    return items

# CORRECT
def process(items=None):
    items = items or []
    items.append("new")
    return items
```
- Never use mutable default arguments (`[]`, `{}`, `set()`).
- Use generators for large datasets — don't load everything into memory.
- Use `set` for membership testing (`O(1)`) instead of `list` (`O(n)`).
- Profile before optimizing — use `cProfile`, `line_profiler`, or `py-spy`.

### AWS/Lambda Specific
- **Cache boto3 clients** at module level (survive warm starts). Create in `initialize()`, not per-invocation.
- **Minimize cold start**: Keep imports lean. Avoid importing unused libraries.
- **Connection reuse**: boto3 handles HTTP connection pooling internally — don't recreate clients.
- **Payload size**: Lambda has a 6MB sync / 256KB async payload limit. Validate input size early.

## Testing

### Test Structure
```python
import pytest
from unittest.mock import Mock, patch, MagicMock

class TestOrderService:
    # Named constants — no magic values
    ORDER_ID = "ORD-12345"
    CUSTOMER_ID = "CUST-001"

    def setup_method(self):
        self.mock_db = Mock()
        self.service = OrderService(self.mock_db)

    def test_should_return_order_when_exists(self):
        # Given
        self.mock_db.get_item.return_value = {"id": self.ORDER_ID}
        # When
        result = self.service.get_order(self.ORDER_ID)
        # Then
        assert result["id"] == self.ORDER_ID
        self.mock_db.get_item.assert_called_once_with(self.ORDER_ID)

    def test_should_raise_when_order_not_found(self):
        self.mock_db.get_item.return_value = None
        with pytest.raises(NotFoundException):
            self.service.get_order(self.ORDER_ID)
```
- Use `pytest` over `unittest` (unless matching existing project style).
- Use `unittest.mock.Mock` / `MagicMock` for mocking. Use `moto` for AWS service mocking.
- Name tests: `test_should_[expected]_when_[condition]`.
- Given/When/Then structure. Named constants for all test data.

### What to Test
- Happy path, edge cases (None, empty, boundary values), error paths.
- For Lambda: all validation error codes, external service error handling (DynamoDB, S3, etc.), cold start + warm start behavior.
- Mock external services — never call real AWS services in unit tests.

## External Resource Access

### Database Connections

- **Always use a connection pool** — `sqlalchemy` with connection pooling, or reuse boto3 clients (thread-safe singletons).
- **Configure timeouts** — connection timeout, read timeout, and idle timeout to prevent connection leaks.
- **Use context managers** for connections — `with engine.connect() as conn:`.
- **Use parameterized queries** — never concatenate user input into SQL or DynamoDB expressions.

```python
# WRONG — SQL injection risk, no pool
import sqlite3
conn = sqlite3.connect("db.sqlite")
cursor = conn.execute(f"SELECT * FROM users WHERE id = '{user_id}'")

# CORRECT — parameterized, pooled (SQLAlchemy)
from sqlalchemy import create_engine, text
engine = create_engine("postgresql://...", pool_size=10, pool_timeout=30)
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id})
```

- **DynamoDB / NoSQL** — reuse boto3 `resource` / `client` as module-level singletons (thread-safe).
- **Batch operations** — use `batch_get_item` / `batch_write_item` instead of single-item calls in a loop.
- **Limit result sets** — always use `Limit` on queries. Never scan an entire table.

### HTTP Connections

- **Reuse HTTP sessions** — create one `requests.Session()` or `httpx.Client()` and share it. Never create per-request.
- **Configure timeouts** — always set both connect and read timeouts.

```python
import requests

# WRONG — no timeout, no session reuse
response = requests.get(f"https://api.example.com/data/{item_id}")

# CORRECT — session reuse, explicit timeouts
session = requests.Session()
session.timeout = (3, 10)  # (connect_timeout, read_timeout)
response = session.get(f"https://api.example.com/data/{item_id}")
response.raise_for_status()
```

- **Retry with exponential backoff** — use `urllib3.util.Retry` or `tenacity` for transient failures.
- **Never trust external input** — validate response status, content type, and body before processing.

### Caching

Use caching to avoid redundant calls to external resources:

```python
from functools import lru_cache
from cachetools import TTLCache

# Simple in-memory cache with TTL
config_cache = TTLCache(maxsize=100, ttl=600)  # 10 min TTL

def get_config(config_id: str) -> dict:
    if config_id not in config_cache:
        config_cache[config_id] = config_service.fetch_from_remote(config_id)
    return config_cache[config_id]

# For pure functions with hashable args — stdlib lru_cache
@lru_cache(maxsize=128)
def compute_expensive_result(key: str) -> str:
    return expensive_computation(key)
```

- **Always set a TTL** — stale data is usually acceptable for a few minutes. Never cache forever.
- **Bound the cache size** — use `maxsize` to prevent unbounded memory growth.
- **`functools.lru_cache`** — great for pure functions, but has no TTL. Use `cachetools.TTLCache` when TTL is needed.
- **Cache at the right layer** — cache in the service/helper layer, not in the handler or data access layer.

## Concurrency

### GIL: What It Does and Doesn't Protect

Python's Global Interpreter Lock (GIL) prevents two threads from executing Python bytecode simultaneously. This means:
- **Single bytecode operations** (e.g., reading/writing a single reference) are atomic.
- **Compound operations are NOT atomic** — read-modify-write (`counter += 1`), check-then-act (`if k not in d: d[k] = v`), and iterating + modifying a collection are all race conditions even with the GIL.
- The GIL does **not** eliminate race conditions. It only prevents memory corruption at the C level.

### First Defense: Immutability

The simplest way to prevent race conditions is to **make objects immutable** — if state can't change, it can't be corrupted.

```python
from dataclasses import dataclass

# THREAD-SAFE — frozen dataclass. No synchronization needed. Can be freely shared.
@dataclass(frozen=True)
class OrderSnapshot:
    order_id: str
    total: float
    item_ids: tuple[str, ...]  # tuple, not list — immutable

# Creating a new snapshot instead of mutating
def update_total(snapshot: OrderSnapshot, new_total: float) -> OrderSnapshot:
    return OrderSnapshot(
        order_id=snapshot.order_id,
        total=new_total,
        item_ids=snapshot.item_ids,
    )
```

- **`frozen=True`** — prevents attribute assignment after creation. `snapshot.total = 99` raises `FrozenInstanceError`.
- **Use `tuple` instead of `list`** for collection fields — tuples are immutable.
- **Create new objects** instead of mutating existing ones — return a new `OrderSnapshot` with the updated value.
- **`NamedTuple`** is also immutable by default: `class OrderSnapshot(NamedTuple): ...`

**Rule of thumb**: If an object is shared across threads, make it immutable. If it can't be immutable, protect it with a lock.

### Race Conditions: Read-Modify-Write

The most common race condition is **read-modify-write** — two threads read the same value, both modify it, and one write overwrites the other.

```python
import threading

# WRONG — race condition. Two threads can read count=5, both write 6. One increment lost.
# `+=` is NOT atomic: read count → add 1 → write count (3 bytecode ops).
counter = 0
def increment():
    global counter
    counter += 1  # RACE CONDITION

# CORRECT — use a Lock to make the operation atomic.
counter = 0
counter_lock = threading.Lock()
def increment():
    global counter
    with counter_lock:
        counter += 1  # only one thread at a time

# CORRECT — for simple counters, use a thread-safe wrapper.
import itertools
counter = itertools.count()  # thread-safe, but only increments by 1
```

### Race Conditions: Check-Then-Act

```python
# WRONG — another thread can insert between the `in` check and the assignment.
if key not in shared_dict:
    shared_dict[key] = compute_value()  # two threads can both enter here

# CORRECT — use a lock around the compound operation.
with dict_lock:
    if key not in shared_dict:
        shared_dict[key] = compute_value()

# CORRECT — for simple cases, use dict.setdefault() (atomic for CPython due to GIL,
# but NOT guaranteed by the language spec — use a lock for safety in production).
shared_dict.setdefault(key, compute_value())  # note: compute_value() always runs
```

### Race Conditions: Shared Mutable Objects

When an object's attributes are modified by multiple threads, **every access** (read and write) must be protected by the same lock.

```python
import threading
from copy import deepcopy

# WRONG — unsynchronized mutable state. Thread A calls set_status() while
# Thread B calls get_errors(). Thread B may see inconsistent state.
class OrderProcessor:
    def __init__(self):
        self.status = "NEW"
        self.errors = []  # list is not thread-safe for compound ops

    def set_status(self, s): self.status = s
    def get_status(self): return self.status
    def add_error(self, e): self.errors.append(e)
    def get_errors(self): return self.errors  # caller can mutate the list

# CORRECT — lock protects all access, defensive copies on reads.
class OrderProcessor:
    def __init__(self):
        self._lock = threading.Lock()
        self._status = "NEW"
        self._errors = []

    def set_status(self, s):
        with self._lock:
            self._status = s

    def get_status(self) -> str:
        with self._lock:
            return self._status

    def add_error(self, e):
        with self._lock:
            self._errors.append(e)

    def get_errors(self) -> tuple:
        with self._lock:
            return tuple(self._errors)  # defensive copy — caller can't mutate
```

**Key rules:**
- **Lock both reads and writes** — locking only writes is a bug. Without a locked read, the reading thread may see a partially updated or stale value.
- **Return defensive copies** from locked getters — returning a mutable `list` reference lets callers modify the object outside the lock.
- **Use `with lock:`** (context manager) — never use `lock.acquire()` / `lock.release()` manually (exception-unsafe).
- **One lock per shared resource** — don't use a single global lock for unrelated data (contention). Don't use multiple locks for the same data (deadlocks).

### Thread-Safe Data Structures

| Need | Use | Not |
|------|-----|-----|
| Thread-safe FIFO queue | `queue.Queue` | `list` + lock |
| Thread-safe dict operations | `threading.Lock` + `dict` | bare `dict` with compound ops |
| Thread-safe counter | `threading.Lock` + `int` | bare `int` with `+=` |
| Share data between processes | `multiprocessing.Queue` / `Manager` | shared `list` or `dict` |
| Thread-local storage | `threading.local()` | global variables |

```python
import queue
import threading

# queue.Queue — thread-safe producer/consumer pattern.
work_queue = queue.Queue(maxsize=100)

def producer():
    work_queue.put(item)  # blocks if full

def consumer():
    item = work_queue.get()  # blocks if empty
    try:
        process(item)
    finally:
        work_queue.task_done()

# threading.local() — each thread gets its own copy. No locking needed.
thread_data = threading.local()
thread_data.request_id = "abc-123"  # only visible to this thread
```

### Thread-Safe Lazy Initialization

```python
# WRONG — race condition. Two threads may both see _instance is None and create two instances.
_instance = None
def get_instance():
    global _instance
    if _instance is None:
        _instance = ExpensiveResource()  # two threads can enter here
    return _instance

# CORRECT — lock around initialization.
_instance = None
_init_lock = threading.Lock()
def get_instance():
    global _instance
    if _instance is None:  # fast path — no lock if already initialized
        with _init_lock:
            if _instance is None:  # double-check inside lock
                _instance = ExpensiveResource()
    return _instance
```

### Async Work

- **Use `concurrent.futures`** for parallel I/O — `ThreadPoolExecutor` for I/O-bound, `ProcessPoolExecutor` for CPU-bound.
- **Prefer `asyncio`** for high-concurrency I/O (web servers, many HTTP calls) — but only if the project already uses async.
- **Handle exceptions** in futures — unhandled exceptions are silently swallowed unless you call `.result()`.

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_all(ids: list[str]) -> list[dict]:
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_one, id_): id_ for id_ in ids}
        results = []
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                logger.error("Fetch failed for %s: %s", futures[future], e)
        return results
```

### Common Concurrency Pitfalls

| Pitfall | Example | Fix |
|---------|---------|-----|
| **Non-atomic `+=`** | `counter += 1` on a shared `int` | `with lock: counter += 1` |
| **Check-then-act** | `if k not in d: d[k] = v` | `with lock:` around both lines |
| **Publishing mutable object** | Returning an internal `list` | Return `tuple(list)` copy |
| **Locking writes but not reads** | Only `set` uses the lock | Lock both `get` and `set` |
| **Double-check without lock** | `if x is None: x = create()` | Double-check with `threading.Lock` |
| **Modifying collection while iterating** | `for item in lst: lst.remove(item)` | Build new list or collect indices |
| **GIL = thread-safe (myth)** | Assuming `dict[k] = v` is safe in compound ops | Always lock compound operations |

## Operational Best Practices

### Dynamic Log Levels for Production Troubleshooting

When troubleshooting in production, temporarily change log levels to get more diagnostic detail:

```python
import logging

# Change at runtime (e.g., triggered by an environment variable or config reload)
logging.getLogger("myapp.service").setLevel(logging.DEBUG)

# For Lambda: check an env var or SSM parameter at handler entry
import os
if os.environ.get("DEBUG_LOGGING") == "true":
    logging.getLogger().setLevel(logging.DEBUG)
```

- **Always revert** after troubleshooting — leaving DEBUG on in production causes log flooding and increased costs.
- **Prefer narrow scope** — change the level for a specific module, not the root logger.
- **For Lambda**: use an environment variable or SSM parameter to toggle debug logging without redeployment.

## Security

- **Never log** secrets, tokens, PII, or full request payloads in production.
- **json.loads() / json.dumps()** — never build JSON by string concatenation.
- **Validate inputs** before use — especially values used in S3 keys, DynamoDB queries, or log messages.
- **Pin dependencies** in `requirements.txt` — `boto3==1.34.0` not `boto3`.
- **Audit dependencies** for CVEs before adding (`pip-audit`, `safety`).

## Related Skills

- **best-practices** — SOLID principles, layered architecture, resilience patterns (language-agnostic foundations that Python implements)
- **security** — Injection prevention (parameterized queries), auth, secrets management, PII — applies to all Python endpoints handling user data
- **testing** — AC-to-test traceability, test pyramid, coverage checklist — universal testing discipline beyond Python-specific pytest patterns
