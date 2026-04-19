---
trigger: always_on
description: SOLID, clean code, architecture, resilience, and anti-patterns
---

# Software Engineering & Architecture Best Practices

Universal principles that apply to every project regardless of tech stack. These supplement `code-rules.md` with higher-level guidance.

## Software Engineering Principles

### SOLID
- **Single Responsibility**: Each class/module/function does one thing well. If you can't describe its purpose in one sentence, split it.
- **Open/Closed**: Open for extension, closed for modification. Prefer adding new classes/strategies over modifying existing switch/if chains.
- **Liskov Substitution**: Subtypes must be substitutable for their base types without breaking behavior.
- **Interface Segregation**: Many small, focused interfaces over one large one. Clients shouldn't depend on methods they don't use.
- **Dependency Inversion**: Depend on abstractions, not concretions. High-level modules should not depend on low-level modules.

### Clean Code
- **Naming**: Names reveal intent. `calculateMonthlyRevenue()` not `calc()`. No abbreviations unless universally understood (`id`, `url`, `http`).
- **Functions**: Small (ideally < 20 lines), do one thing, one level of abstraction per function. If a function needs a comment to explain what it does, rename it.
- **No magic numbers/strings**: Extract to named constants. `MAX_RETRY_ATTEMPTS = 3` not bare `3`.
- **Early returns**: Reduce nesting. Validate and fail early instead of deep if/else chains.
- **DRY**: Don't Repeat Yourself — but don't over-abstract either. Duplication is better than the wrong abstraction (Rule of Three: abstract on the third occurrence).
- **Boy Scout Rule**: Leave code cleaner than you found it — but only within the scope of your task.

### Error Handling
- **Fail fast**: Validate inputs at the boundary. Don't let bad data propagate deep into the system.
- **Specific exceptions**: Catch the narrowest exception type possible. Never catch `Exception`/`Throwable` unless re-throwing.
- **No swallowed exceptions**: Every catch block must log, re-throw, or handle meaningfully.
- **Error messages**: Include context (what failed, what was expected, what was received). Never expose internal details to clients.

### Defensive Programming
- **Validate all inputs** at system boundaries (API endpoints, event handlers, message consumers).
- **Null safety**: Check for null/None/undefined before use. Prefer Optional/Maybe types where available.
- **Immutability**: Prefer immutable data structures. Mutable shared state is the #1 source of concurrency bugs.
- **Boundary conditions**: Test zero, one, many, negative, max-value, empty string, empty collection.

## Architecture Best Practices

### Separation of Concerns
- **Layered architecture**: Controller/Handler → Service/Business Logic → Repository/Data Access. Never skip layers.
- **Thin controllers**: Controllers parse input and delegate. No business logic in controllers.
- **Service layer**: All business logic lives here. Services are the only layer that knows the business rules.
- **Data access layer**: Isolate all database/external service calls. Services never build queries directly.

### API Design
- **Idempotency**: GET, PUT, DELETE should be idempotent. POST creates new resources.
- **Consistent error responses**: Standard error format across all endpoints (`{code, message, details}`).
- **Versioning**: Plan for API evolution. Breaking changes require version bumps or feature flags.
- **Input validation**: Validate at the API boundary. Return 400 for bad input, not 500.

### Data Design
- **Single source of truth**: Every piece of data has exactly one authoritative owner.
- **Schema evolution**: Design for forward/backward compatibility. Adding fields is safe; renaming/removing is breaking.
- **TTL/retention**: Data should have an expiration strategy. Don't store data indefinitely without a reason.
- **Composite keys**: Prefer natural composite keys over auto-increment when the combination is naturally unique.

### Resilience
- **Timeouts**: Every external call must have a timeout. No unbounded waits.
- **Retries with backoff**: Retry transient failures with exponential backoff + jitter. Cap max retries.
- **Circuit breakers**: For frequently-failing dependencies, stop calling and fail fast.
- **Dead letter queues**: For async processing, route failed messages to DLQ for later investigation.
- **Graceful degradation**: If a non-critical dependency fails, serve a degraded response rather than failing entirely.

### Observability
- **Structured logging**: Log in a parseable format (JSON or structured fields). Include correlation IDs.
- **Correlation IDs**: Propagate a request/trace ID across all services for cross-service debugging.
- **Metrics**: Track latency, error rates, throughput at every service boundary.
- **Alerting**: Alert on symptoms (error rate, latency), not causes. Avoid alert fatigue.

### Coupling & Cohesion
- **Low coupling**: Services/modules should be independently deployable and testable. Changes in one should not cascade.
- **High cohesion**: Related functionality lives together. If two things always change together, they belong together.
- **Contract-first**: Define interfaces/schemas before implementation. Changes to contracts require coordination.
- **Event-driven**: For cross-service communication, prefer events/messages over synchronous calls where possible.

## Anti-Patterns to Avoid

- **God class/function**: One class doing everything. Split by responsibility.
- **Premature optimization**: Measure first. Optimize only proven bottlenecks.
- **Premature abstraction**: Don't abstract until you have 3+ concrete cases. Wrong abstractions are worse than duplication.
- **Distributed monolith**: Microservices that must be deployed together. If services share a database or require synchronized deploys, they're a monolith.
- **Stringly typed**: Using raw strings where enums, constants, or typed objects would prevent errors.
- **Feature envy**: A method that uses more data from another class than its own. Move the method to where the data lives.
- **Shotgun surgery**: One change requires edits in many unrelated places. Consolidate the scattered logic.
