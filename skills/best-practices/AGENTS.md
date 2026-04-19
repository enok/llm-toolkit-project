# Software Engineering & Architecture Best Practices

Universal principles that apply to every project regardless of tech stack. These supplement language-specific skills with higher-level guidance on design, architecture, resilience, and code quality.

## SOLID Principles

### Single Responsibility Principle (SRP)

Each class/module/function does one thing well. If you can't describe its purpose in one sentence, split it.

```java
// WRONG — one class handles HTTP parsing, validation, persistence, and email
class OrderController {
    void createOrder(Request req) {
        Order order = parseJson(req.body());        // HTTP concern
        if (order.total() < 0) throw new Ex();      // validation concern
        db.save(order);                              // persistence concern
        emailService.send(order.customer(), "...");  // notification concern
    }
}

// CORRECT — each class has one reason to change
class OrderController {
    void createOrder(Request req) {
        Order order = orderParser.parse(req);
        orderService.place(order);   // delegates to service layer
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

### Open/Closed Principle (OCP)

Open for extension, closed for modification. Prefer adding new classes/strategies over modifying existing switch/if chains.

```python
# WRONG — adding a new discount type requires modifying this function
def calculate_discount(order, discount_type):
    if discount_type == "percentage":
        return order.total * 0.1
    elif discount_type == "fixed":
        return 10.0
    elif discount_type == "bogo":   # every new type modifies this function
        return order.total * 0.5

# CORRECT — new discount types are new classes, existing code unchanged
class DiscountStrategy(Protocol):
    def calculate(self, order: Order) -> Decimal: ...

class PercentageDiscount:
    def __init__(self, rate: Decimal): self.rate = rate
    def calculate(self, order: Order) -> Decimal:
        return order.total * self.rate

class FixedDiscount:
    def __init__(self, amount: Decimal): self.amount = amount
    def calculate(self, order: Order) -> Decimal:
        return self.amount

# Adding BuyOneGetOne just means creating a new class — no changes to existing code
```

### Liskov Substitution Principle (LSP)

Subtypes must be substitutable for their base types without breaking behavior.

```typescript
// WRONG — Square overrides setWidth/setHeight in a way that breaks Rectangle's contract
class Rectangle {
    setWidth(w: number) { this.width = w; }
    setHeight(h: number) { this.height = h; }
    area(): number { return this.width * this.height; }
}
class Square extends Rectangle {
    setWidth(w: number) { this.width = w; this.height = w; }  // violates LSP
    setHeight(h: number) { this.width = h; this.height = h; }
}
// Code expecting Rectangle behavior breaks when given a Square

// CORRECT — model as separate types or use a common Shape interface
interface Shape {
    area(): number;
}
class Rectangle implements Shape { /* width × height */ }
class Square implements Shape { /* side × side */ }
```

### Interface Segregation Principle (ISP)

Many small, focused interfaces over one large one. Clients shouldn't depend on methods they don't use.

```java
// WRONG — one fat interface forces all implementations to handle everything
interface Repository {
    void save(Entity e);
    Entity findById(String id);
    List<Entity> findAll();
    void delete(String id);
    void bulkInsert(List<Entity> entities);
    Report generateReport();       // not every repo needs reporting
    void archive(String id);       // not every repo supports archiving
}

// CORRECT — split by client need
interface ReadRepository {
    Entity findById(String id);
    List<Entity> findAll();
}
interface WriteRepository {
    void save(Entity e);
    void delete(String id);
}
interface BulkRepository {
    void bulkInsert(List<Entity> entities);
}
// Implementations compose only what they need
```

### Dependency Inversion Principle (DIP)

High-level modules should not depend on low-level modules. Both should depend on abstractions.

```python
# WRONG — service depends on concrete implementation
from app.infra.postgres_repo import PostgresOrderRepository

class OrderService:
    def __init__(self):
        self.repo = PostgresOrderRepository()  # tightly coupled to Postgres

# CORRECT — service depends on abstraction
class OrderRepository(Protocol):
    def save(self, order: Order) -> None: ...
    def find_by_id(self, order_id: str) -> Order | None: ...

class OrderService:
    def __init__(self, repo: OrderRepository):  # accepts any implementation
        self.repo = repo
```

## Clean Code

### Naming Reveals Intent

```typescript
// WRONG — cryptic abbreviations
const d = calcDiff(a, b);
function proc(lst: any[]) { ... }
const tmp = users.filter(u => u.a > 5);

// CORRECT — names describe what and why
const priceDifference = calculatePriceDifference(originalPrice, discountedPrice);
function filterActiveUsers(users: User[]): User[] { ... }
const highValueCustomers = users.filter(user => user.orderCount > 5);
```

- No abbreviations unless universally understood (`id`, `url`, `http`).
- Boolean names read as questions: `isActive`, `hasPermission`, `canEdit`.
- Functions named as verbs: `calculateTotal`, `sendNotification`, `validateOrder`.

### Small Functions — One Level of Abstraction

```python
# WRONG — mixing levels of abstraction
def process_order(order):
    # validation (low level)
    if not order.items:
        raise ValueError("Empty order")
    if order.total < 0:
        raise ValueError("Negative total")
    # persistence (different level)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO orders ...", order.to_dict())
    conn.commit()
    # notification (yet another level)
    smtp = smtplib.SMTP("mail.example.com")
    smtp.send_message(build_email(order))

# CORRECT — each function at one level of abstraction
def process_order(order: Order) -> None:
    validate_order(order)
    save_order(order)
    notify_customer(order)
```

### No Magic Numbers or Strings

```java
// WRONG — what does 3 mean? What does "PENDING" mean?
if (retryCount > 3) { ... }
if (order.getStatus().equals("PENDING")) { ... }
Thread.sleep(5000);

// CORRECT — named constants explain intent
private static final int MAX_RETRY_ATTEMPTS = 3;
private static final Duration RETRY_DELAY = Duration.ofSeconds(5);

if (retryCount > MAX_RETRY_ATTEMPTS) { ... }
if (order.getStatus() == OrderStatus.PENDING) { ... }
Thread.sleep(RETRY_DELAY.toMillis());
```

### Early Returns — Guard Clauses

```typescript
// WRONG — deeply nested
function processOrder(order: Order | null): Result {
  if (order) {
    if (order.items.length > 0) {
      if (order.status === "pending") {
        return doProcess(order);
      }
    }
  }
  return { error: "Invalid order" };
}

// CORRECT — guard clauses, flat structure
function processOrder(order: Order | null): Result {
  if (!order) return { error: "Order is null" };
  if (order.items.length === 0) return { error: "No items" };
  if (order.status !== "pending") return { error: "Not pending" };
  return doProcess(order);
}
```

### DRY — Rule of Three

- Don't abstract on the first or second occurrence — wait for three.
- Wrong abstraction is worse than duplication.
- When you do abstract, extract to a well-named function with clear inputs/outputs.

## Error Handling & Defensive Programming

### Fail Fast — Validate at Boundaries

```java
// WRONG — bad data propagates deep, fails cryptically later
public OrderResult process(OrderRequest request) {
    // no validation — null pointer somewhere 5 layers deep
    return orderPipeline.execute(request);
}

// CORRECT — validate at the entry point, fail with clear message
public OrderResult process(OrderRequest request) {
    Objects.requireNonNull(request, "OrderRequest must not be null");
    if (request.getItems().isEmpty()) {
        throw new ValidationException("Order must have at least one item");
    }
    if (request.getCustomerId() == null) {
        throw new ValidationException("Customer ID is required");
    }
    return orderPipeline.execute(request);
}
```

### Specific Exceptions — Never Catch-All

```python
# WRONG — catches everything, hides bugs
try:
    result = process_order(order)
except Exception:
    return {"error": "Something went wrong"}  # TypeError? NameError? Hidden.

# CORRECT — catch specific, handle appropriately
try:
    result = process_order(order)
except ValidationError as e:
    return {"error": str(e)}, 400
except OrderNotFoundError as e:
    return {"error": str(e)}, 404
except ExternalServiceError as e:
    logger.error("External service failed", exc_info=True, extra={"order_id": order.id})
    return {"error": "Service temporarily unavailable"}, 503
```

### No Swallowed Exceptions

```java
// WRONG — exception silently swallowed
try {
    orderRepository.save(order);
} catch (Exception e) {
    // empty catch — data loss with no indication
}

// WRONG — logged but not handled
try {
    orderRepository.save(order);
} catch (Exception e) {
    log.error("Save failed", e);
    // continues as if save succeeded — data inconsistency
}

// CORRECT — log with context AND handle
try {
    orderRepository.save(order);
} catch (DataAccessException e) {
    log.error("Failed to save order: orderId={}", order.getId(), e);
    throw new OrderPersistenceException("Could not save order", e);
}
```

### Input Validation at System Boundaries

- **API endpoints**: Validate request body, path params, query params before processing.
- **Event handlers**: Validate message payload schema before acting on it.
- **File imports**: Validate format, encoding, and field types before processing rows.
- **Null safety**: Check for null/None/undefined before use. Prefer Optional/Maybe types.

### Prefer Immutability

- Mutable shared state is the #1 source of concurrency bugs.
- Use `final`/`const`/`readonly`/`frozen` by default.
- When mutation is needed, make it explicit and contained.

## Architecture & Separation of Concerns

### Layered Architecture

```
Controller/Handler → Service/Business Logic → Repository/Data Access
```

| Layer | Responsibility | Must NOT contain |
|-------|---------------|-----------------|
| **Controller** | Parse input, validate shape, delegate, format response | Business logic, SQL, external service calls |
| **Service** | Business rules, orchestration, transaction boundaries | HTTP concerns, SQL construction |
| **Repository** | Data access, query construction, caching | Business rules, HTTP handling |

- **Never skip layers**: Controller → Repository directly bypasses business logic.
- **Thin controllers**: Parse and delegate. No logic beyond input extraction.
- **Service layer owns the rules**: All business logic lives here.

### API Design

- **Idempotency**: GET, PUT, DELETE are idempotent. POST creates new resources.
- **Consistent error responses**: Standard format across all endpoints: `{code, message, details}`.
- **Versioning**: Plan for evolution. Breaking changes require version bumps or feature flags.
- **Input validation**: Validate at the boundary. Return 400 for bad input, not 500.

### Data Design

- **Single source of truth**: Every piece of data has exactly one authoritative owner.
- **Schema evolution**: Adding fields is safe; renaming/removing is breaking. Plan for forward/backward compatibility.
- **TTL/retention**: Data should have an expiration strategy. Don't store indefinitely without reason.

### Coupling & Cohesion

- **Low coupling**: Services/modules independently deployable and testable. Changes don't cascade.
- **High cohesion**: Related functionality lives together. If two things always change together, they belong together.
- **Contract-first**: Define interfaces/schemas before implementation.
- **Event-driven**: For cross-service communication, prefer events over synchronous calls where possible.

## Resilience & Operational Patterns

### Timeouts on Every External Call

```typescript
// WRONG — no timeout, hangs indefinitely if service is down
const response = await fetch("https://api.payment.com/charge", {
  method: "POST",
  body: JSON.stringify(charge),
});

// CORRECT — timeout prevents resource exhaustion
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 5000);
try {
  const response = await fetch("https://api.payment.com/charge", {
    method: "POST",
    body: JSON.stringify(charge),
    signal: controller.signal,
  });
} finally {
  clearTimeout(timeoutId);
}
```

### Retry with Exponential Backoff

```python
import time, random

def retry_with_backoff(fn, max_attempts=3, base_delay=1.0):
    for attempt in range(max_attempts):
        try:
            return fn()
        except TransientError:
            if attempt == max_attempts - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)  # jitter
            time.sleep(delay)
```

- Cap max retries (3-5 is typical).
- Add jitter to prevent thundering herd.
- Only retry transient failures — never retry validation errors or auth failures.

### Circuit Breaker

For frequently-failing dependencies, stop calling and fail fast:

| State | Behavior |
|-------|----------|
| **Closed** | Normal operation, requests pass through |
| **Open** | After N failures, reject immediately for a cool-down period |
| **Half-Open** | After cool-down, allow one probe request to test recovery |

### Observability

- **Structured logging**: JSON or structured fields. Include correlation IDs.
- **Correlation IDs**: Propagate request/trace ID across all services.
- **Metrics**: Track latency, error rates, throughput at every service boundary.
- **Alerting**: Alert on symptoms (error rate, latency), not causes. Avoid alert fatigue.

### Graceful Degradation

If a non-critical dependency fails, serve a degraded response rather than failing entirely:

```java
public ProductPage getProductPage(String productId) {
    Product product = productService.getById(productId);  // critical — fail if missing
    List<Review> reviews;
    try {
        reviews = reviewService.getForProduct(productId);  // non-critical
    } catch (ServiceUnavailableException e) {
        log.warn("Review service unavailable, serving without reviews");
        reviews = List.of();  // degrade gracefully
    }
    return new ProductPage(product, reviews);
}
```

## Anti-Patterns to Avoid

| Anti-Pattern | Symptom | Fix |
|-------------|---------|-----|
| **God class** | One class doing everything, 1000+ lines | Split by single responsibility |
| **Premature optimization** | Complex caching before measuring | Profile first, optimize bottlenecks |
| **Premature abstraction** | Abstract factory for 1 implementation | Wait for 3+ concrete cases |
| **Distributed monolith** | Microservices sharing DB or needing sync deploy | Consolidate or truly decouple |
| **Stringly typed** | Raw strings where enums/types would prevent errors | Use enums, typed IDs, value objects |
| **Feature envy** | Method uses more data from another class than its own | Move method to where the data lives |
| **Shotgun surgery** | One change requires edits in many places | Consolidate scattered logic |
| **Primitive obsession** | Using raw strings/ints for domain concepts (money, email) | Introduce value objects |
| **Anemic domain model** | Entity classes with only getters/setters, all logic elsewhere | Move behavior into the entity |

## Related Skills

This skill provides **language-agnostic foundations**. Pair it with language-specific implementations:

- **java-best-practices** — Java implementation of SOLID, DI (Spring/Guice), concurrency (java.util.concurrent), error handling
- **python-best-practices** — Python implementation of SOLID, DI (Protocol/ABC), concurrency (threading/asyncio), error handling
- **js-ts-best-practices** — TypeScript/JavaScript implementation of DI, async patterns, type safety, error handling
- **nodejs** — Node.js runtime patterns for resilience (timeouts, graceful shutdown, streams, circuit breaker)
- **security** — Security-specific defensive rules (injection, auth, secrets) that complement the defensive programming section above
- **testing** — Testing discipline (AC traceability, test pyramid) that validates architecture and code quality
