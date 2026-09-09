# Software Engineering & Architecture Best Practices

Universal, language-agnostic engineering principles. This is the compiled expansion of every rule slug in the `best-practices` skill quick reference. Examples use Java, Python, or TypeScript interchangeably — the principles apply to any stack.

## SOLID Principles

### `solid-single-responsibility` — One Reason to Change

Each class/module does one thing. If you can't describe it in one sentence without "and", split it.

```java
// WRONG — business rules + persistence + notification in one class
class OrderManager { placeOrder(); saveToDb(); sendEmail(); }

// CORRECT — one responsibility each, composed
class OrderService { placeOrder(); }      // business rules
class OrderRepository { save(); }         // persistence
class OrderNotifier { sendConfirmation(); } // notification
```

- Symptoms of violation: giant test files, unrelated imports, changes for unrelated reasons touching the same file.
- Applies at every level: functions, classes, modules, services.

### `solid-open-closed` — Extend, Don't Modify

New behavior should be added by adding code (new strategy, new handler), not by editing a growing conditional.

```typescript
// WRONG — every new type edits this switch
switch (type) { case "csv": ...; case "json": ...; /* grows forever */ }

// CORRECT — register a new exporter without touching existing ones
const exporters: Map<string, Exporter> = new Map([["csv", csvExporter], ["json", jsonExporter]]);
exporters.get(type)?.export(data);
```

- Prefer strategy maps, polymorphism, or plugin registration over switch/if chains keyed on a type field.
- Don't over-apply: wait for the second or third variant before introducing the extension point (see `anti-premature-abstraction`).

### `solid-liskov-substitution` — Subtypes Must Be Substitutable

Any code that works with the base type must keep working when handed a subtype — same contract, no surprises.

- A subtype must not strengthen preconditions ("this override also requires X"), weaken postconditions, or throw where the base promises success.
- Classic violation: `Square extends Rectangle` where `setWidth()` silently changes height.
- If an override is empty or throws `UnsupportedOperationException`, the hierarchy is wrong — use composition or a narrower interface instead.

### `solid-interface-segregation` — Many Small Interfaces

Clients should not be forced to depend on methods they don't use.

```python
# WRONG — one fat interface; readers must stub write methods in tests
class DataStore(ABC):
    def read(self): ...
    def write(self): ...
    def bulk_delete(self): ...

# CORRECT — segregated roles; depend only on what you need
class DataReader(ABC):
    def read(self): ...
class DataWriter(ABC):
    def write(self): ...
```

- Split by consumer need, not by implementation convenience. One implementation may satisfy several small interfaces.
- Smell: mocks that stub many irrelevant methods to test one behavior.

### `solid-dependency-inversion` — Depend on Abstractions

High-level business logic must not import low-level infrastructure. Both depend on interfaces; the composition root wires implementations.

```java
// WRONG — service constructs and depends on a concrete driver
class ReportService { private final S3Client s3 = new S3Client(); }

// CORRECT — service depends on an interface; wiring happens at the edge
class ReportService {
    private final ReportStore store; // interface
    ReportService(ReportStore store) { this.store = store; }
}
```

- Constructor injection of interfaces is the default mechanism (see the language skills' `di-*` rules for stack-specific patterns).
- Payoff: infrastructure swaps and unit tests never touch business logic.

## Clean Code

### `clean-naming` — Names Reveal Intent

A name should answer why it exists and what it does — without needing a comment.

- `calculateMonthlyRevenue()` not `calc()`. `isEligibleForDiscount` not `flag2`.
- Booleans read as predicates (`isExpired`, `hasAccess`). Functions are verbs; classes are nouns.
- No abbreviations that save three characters and cost every reader a lookup (`usrMgrSvc`).
- If naming a unit is hard, the unit probably does too much — fix the design, not the name.

### `clean-small-functions` — Under ~20 Lines, One Purpose

Functions do one thing, at one level of abstraction.

- Target 10–20 lines; over 30 is a strong refactor signal.
- If you need a comment to label a block inside a function, extract the block into a function named after the comment.
- Don't mix orchestration ("what happens") with details ("how it happens") in the same function.
- Boolean parameters are a smell — split into two named functions or use an enum.

### `clean-no-magic` — Named Constants Over Bare Literals

Every non-obvious literal gets a name explaining what it means and why that value.

```python
# WRONG — what is 3? what is 86400?
if attempts > 3: block(user, 86400)

# CORRECT
MAX_LOGIN_ATTEMPTS = 3
BLOCK_DURATION_SECONDS = 24 * 60 * 60
if attempts > MAX_LOGIN_ATTEMPTS: block(user, BLOCK_DURATION_SECONDS)
```

- Centralize shared constants in one module/class per domain — not duplicated per file.
- Applies to strings too: header names, queue names, status values.

### `clean-early-return` — Guard Clauses Reduce Nesting

Validate and fail at the top; keep the happy path flat.

```typescript
// WRONG — happy path buried three levels deep
function process(order?: Order) {
  if (order) { if (order.items.length > 0) { if (order.isPaid) { /* work */ } } }
}

// CORRECT — guards first, then flat logic
function process(order?: Order) {
  if (!order) throw new ValidationError("order required");
  if (order.items.length === 0) throw new ValidationError("no items");
  if (!order.isPaid) return;
  /* work */
}
```

- Three levels of nesting is a red flag — extract or invert conditions.

### `clean-dry-rule-of-three` — Abstract on the Third Occurrence

Duplication is cheaper than the wrong abstraction.

- First occurrence: write it. Second: copy it and note the similarity. Third: now extract the shared abstraction — you finally know what varies and what is fixed.
- Never merge two code paths just because they look similar today; merge them when they change for the same reason.
- Un-DRY when an abstraction accumulates flags/params to serve divergent callers — split it back apart.

## Error Handling & Defensive Programming

### `error-fail-fast` — Validate at Boundaries

Detect bad state as early as possible; don't let invalid data propagate to fail mysteriously three layers deeper.

- Validate constructor arguments and required config at startup, not on first use (`Objects.requireNonNull`, schema-validated env/config).
- A process that cannot start correctly should crash loudly at boot — not limp along half-configured.
- Reject invalid requests at the entry point with a clear message naming the offending field.

### `error-specific-exceptions` — Catch the Narrowest Type

Catch only what you can handle, as specifically as possible.

```java
// WRONG — swallows everything from NPEs to OOM signals
try { parse(input); } catch (Exception e) { return null; }

// CORRECT — specific, contextual, cause preserved
try { parse(input); }
catch (NumberFormatException e) {
    throw new ValidationException("Invalid numeric input: " + input, e);
}
```

- Never catch `Exception`/`Throwable`/bare `except:` unless re-throwing after cleanup or at a top-level boundary that logs and translates.
- Always preserve the cause chain when wrapping (`new X(msg, cause)`, `raise ... from e`, `{ cause }`).

### `error-no-swallowed` — Every Catch Acts

Every catch block must log with context, re-throw, or handle meaningfully. An empty catch hides bugs until production.

- "Handle" means the program continues correctly — e.g., fall back to a default and record that it did.
- Log once at the layer that handles the error; don't log-and-rethrow at every layer (duplicate noise).
- Async variants count: unhandled promise rejections, fire-and-forget tasks, and executor exceptions are swallowed errors too.

### `error-input-validation` — Validate All Inputs at System Boundaries

Anything crossing into the system — HTTP requests, queue messages, file contents, CLI args, third-party responses — is untrusted until validated.

- Validate shape, type, range, and size before use; reject with actionable errors.
- Prefer declarative validation at the edge (schema validators, framework binding) over ad-hoc checks scattered through business logic.
- Internal calls between your own modules don't need re-validation — validate once at the boundary, then trust typed data.
- Security-critical validation (injection, path traversal) is covered in depth by the **security** skill.

### `error-immutability` — Prefer Immutable Data

State that cannot change cannot be corrupted — by concurrency, by aliasing, or by distant code.

```python
# WRONG — shared mutable default, mutated by every caller
def add_item(item, items=[]): items.append(item); return items

# CORRECT — immutable input, new value out
def add_item(item: str, items: tuple[str, ...]) -> tuple[str, ...]:
    return (*items, item)
```

- Make fields final/readonly/frozen by default; reach for mutability only with a reason.
- Return defensive copies or unmodifiable views of internal collections.
- Mutable shared state is the root of most concurrency bugs — see the language skills' `concurrency-*` rules.

## Architecture & Separation of Concerns

### `arch-layered` — Controller → Service → Repository

Requests flow down through layers; no layer skips or reaches back up.

| Layer | Responsibility | Must NOT contain |
|-------|---------------|-----------------|
| **Controller/handler** | Parse input, validate shape, delegate, map result to response | Business logic, SQL, external service calls |
| **Service** | Business rules, orchestration, transaction boundaries | HTTP concerns, SQL construction |
| **Repository/gateway** | Data access, query construction, caching, external systems behind interfaces | Business rules, HTTP handling |

- Never let a controller query the database directly, or a repository make business decisions.
- Dependencies point one way (down); cycles between layers mean the boundaries are wrong.

### `arch-thin-controllers` — No Business Logic at the Edge

Controllers/handlers parse input and delegate. That's all.

```typescript
// WRONG — pricing rules inside the route handler
app.post("/orders", async (req, res) => {
  let total = 0;
  for (const i of req.body.items) total += i.qty * i.price * (i.sale ? 0.9 : 1);
  await db.insert("orders", { ...req.body, total });
});

// CORRECT — handler delegates; logic lives in the testable service
app.post("/orders", async (req, res) => {
  const order = await orderService.place(parseOrderRequest(req.body));
  res.status(201).json(toOrderResponse(order));
});
```

- Business logic in controllers cannot be reused (CLI, queue consumer, scheduled job) and can only be tested through HTTP.

### `arch-api-design` — Contracts That Age Well

Design APIs as long-lived contracts, not as views of today's implementation.

- **Idempotency**: retried mutations must not double-apply — use idempotency keys or natural idempotent semantics (PUT).
- **Consistent errors**: one machine-readable error shape (code, message, correlation id) across all endpoints; never leak stack traces.
- **Versioning**: additive changes only within a version; breaking changes require a new version and a deprecation path.
- **Validation**: reject unknown/invalid input explicitly at the edge.
- Model resources and behaviors from the consumer's viewpoint; don't expose internal table shapes as response bodies.

### `arch-data-design` — Own Your Data Shape

- **Single source of truth**: each fact has one authoritative owner; everything else is a cache or projection with defined freshness.
- **Schema evolution**: plan for change — additive columns/fields, backfill strategy, expand-migrate-contract for breaking changes.
- **TTL / retention**: data that expires (sessions, caches, events) gets an explicit TTL and cleanup path from day one — never "we'll prune it later".
- Choose keys and indexes from the read patterns, not from what's convenient to write.

### `arch-coupling-cohesion` — Low Coupling, High Cohesion

Things that change together live together; things that change independently stay independent.

- **Contract-first**: modules and services interact through explicit interfaces/schemas, never by reaching into each other's internals or databases.
- **Event-driven** decoupling where the producer shouldn't care who reacts — publish domain events instead of calling every interested party.
- Measure coupling by the blast radius of a change: if adding a field forces edits in five modules, cohesion is misplaced.
- Shared utility grab-bags (`common/utils`) breed hidden coupling — prefer purpose-named modules.

## Resilience & Operational Patterns

### `resilience-timeouts` — Every External Call Is Bounded

No network call — HTTP, database, queue, cache — may wait forever.

- Set explicit connect and read timeouts on every client; never rely on library defaults (often infinite).
- Size timeouts from the caller's budget: an endpoint with a 2s SLA cannot make a 30s downstream call.
- A hung dependency without timeouts exhausts your thread/connection pool and takes your service down with it.

### `resilience-retry-backoff` — Retry Transient Failures, With Discipline

```python
# Exponential backoff + jitter, capped attempts
delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY) * random.uniform(0.5, 1.5)
```

- Retry only transient failures (timeouts, 5xx, connection resets) — never 4xx client errors.
- Always exponential backoff **with jitter**; naive immediate retries synchronize clients into thundering herds.
- Cap max attempts (typically 3) and total elapsed time; retried operations must be idempotent.
- Prefer library/SDK built-in retry policies over hand-rolled loops.

### `resilience-circuit-breaker` — Fail Fast on Broken Dependencies

When a dependency fails repeatedly, stop calling it for a cooling-off period instead of stacking up doomed, slow requests.

- Closed (normal) → Open after a failure threshold (calls fail immediately) → Half-open probes let it recover.
- Pair every breaker with a defined fallback: cached data, default response, or an explicit degraded-mode error.
- Use an established implementation (resilience4j, opossum, pybreaker) rather than writing your own.
- Without a breaker, retries against a down dependency amplify the outage (retry storm).

### `resilience-observability` — If You Can't See It, You Can't Run It

- **Structured logging**: machine-parseable (JSON) with consistent fields; log events, not prose.
- **Correlation IDs**: generate at the entry point, propagate through every call and log line, so one request can be traced end to end.
- **Metrics**: rate, errors, duration (RED) for every endpoint and dependency; business counters for key flows.
- **Alerting**: alert on user-facing symptoms (error rate, latency) with actionable thresholds — not on every internal blip.
- Instrument when you build the feature, not after the first incident.

### `resilience-graceful-degradation` — Degrade, Don't Collapse

When a non-critical dependency fails, serve a reduced response instead of failing the whole request.

```java
public ProductPage getProductPage(String productId) {
    Product product = productService.getById(productId);  // critical — fail if missing
    List<Review> reviews;
    try {
        reviews = reviewService.getForProduct(productId);  // non-critical
    } catch (ServiceUnavailableException e) {
        log.warn("Review service unavailable, serving without reviews: productId={}", productId);
        reviews = List.of();  // degrade gracefully
    }
    return new ProductPage(product, reviews);
}
```

- Decide per dependency, up front, whether it is critical (fail) or optional (degrade); never guess at runtime.
- Record every degraded response (log or metric) so silent partial outages are visible.
- Pair with `resilience-circuit-breaker`: the fallback is what the breaker returns while open.

## Anti-Patterns

### `anti-god-class` — Split by Responsibility

A class that knows everything and coordinates everyone becomes the change bottleneck of the codebase.

- Warning signs: thousands of lines, dozens of dependencies in the constructor, names like `Manager`/`Processor`/`Util` covering unrelated verbs, every feature PR touching it.
- Fix by extracting cohesive responsibility clusters into their own classes (see `solid-single-responsibility`), then composing them.
- Don't "fix" it by inheritance — split, don't subclass.

### `anti-premature-optimization` — Measure First

- Write clear, correct code first; optimize only proven bottlenecks identified with a profiler or production metrics.
- Micro-optimizations that hurt readability (manual loop unrolling, caching everything, clever bit tricks) are almost never where the time goes.
- Exception: obvious algorithmic wins are not premature — avoiding O(n²) lookups or N+1 queries at design time is just competence.
- Keep a measured baseline so "it's faster now" is a fact, not a feeling.

### `anti-premature-abstraction` — Wait for Three Concrete Cases

Don't build the framework before the second user exists.

- Interfaces with one implementation "for flexibility", generic engines with a single mode, and config options nobody sets are speculative complexity.
- Follow the rule of three (`clean-dry-rule-of-three`): abstract when the third concrete case proves what actually varies.
- Exception: boundaries to external infrastructure (DB, HTTP, queues) deserve interfaces from day one — that's `solid-dependency-inversion`, not speculation.

### `anti-distributed-monolith` — Independent Services or One Service

If services share a database or must deploy in lockstep, they are one monolith paying network tax.

- Symptoms: cross-service joins, one schema migration coordinating three deploys, service A breaking when B releases, shared libraries carrying business logic between them.
- Each service owns its data store and exposes it only through its API/events; deployments are independently releasable and backward compatible.
- If two "services" always change together, merge them — an honest monolith beats a distributed one.

### Other code smells worth naming

| Anti-pattern | Symptom | Fix |
|-------------|---------|-----|
| **Stringly typed** | Raw strings where enums/types would prevent errors | Use enums, typed IDs, value objects |
| **Feature envy** | Method uses more data from another class than its own | Move the method to where the data lives |
| **Shotgun surgery** | One change requires edits in many places | Consolidate scattered logic (see `arch-coupling-cohesion`) |
| **Primitive obsession** | Raw strings/ints for domain concepts (money, email, IDs) | Introduce value objects |
| **Anemic domain model** | Entities with only getters/setters, all logic elsewhere | Move behavior into the entity |

## Related Skills

This document provides **language-agnostic foundations**. Pair it with:

- **java-best-practices** / **python-best-practices** / **js-ts-best-practices** — language-specific implementations of DI, error handling, concurrency, and testing patterns
- **security** — injection prevention, auth, secrets, PII (builds on the defensive programming rules here)
- **testing** — AC traceability, test pyramid, mocking discipline that validates these structures
