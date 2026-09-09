# Architecture Rubric

Evaluate architecture and layering quality. Use this rubric when reviewing code that introduces or modifies structural components - layers, boundaries, services, repositories, or inter-module dependencies. For the full review checklist (including correctness, security, performance), see `rubrics/code-review-checklist.md`.

---

## Layering & Boundaries

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Business logic in controller/handler | Yes | |
| Database query built in service layer | Yes | |
| Repository method containing business rules | Yes | |
| Cross-layer import skipping a layer | Yes | |
| Shared mutable state across layers | Yes | |
| Thin controllers delegating to services | | Yes - verify present |
| Service layer unaware of HTTP/transport details | | Yes - verify present |

## Separation of Concerns

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Single class/module with unrelated responsibilities | | Yes |
| Hard-coded infrastructure details (DB URL, bucket name) in domain code | Yes | |
| Configuration read inside domain logic instead of injected | | Yes |
| More than one public responsibility per module | | Yes - split |
| Abstraction/interface with a single implementation and no anticipated variation | | Yes - simplify |

## Dependency Injection

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Collaborators instantiated inside a class (`new X()` in constructor body) | Yes | |
| Service depends on a concrete implementation, not an interface | | Yes |
| Test doubles impossible without framework magic | Yes | |
| Application wiring (concrete bindings) leaks into domain classes | Yes | |

## Transaction Safety

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Multiple writes without transactional boundary | Yes | |
| Partial failure leaves data in inconsistent state | Yes | |
| Transaction spanning external HTTP or queue call | Yes | |
| Retry logic inside a transaction | | Yes - review |
| Concurrent access to shared state without a synchronization/locking strategy | Yes | |
| Event ordering or cache-invalidation assumption undocumented or inconsistent with the intended model | | Yes - document |

## Coupling & Cohesion

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Services that must deploy together share database or in-process state | Yes | |
| Change in one module requires cascade edits in many unrelated places | | Yes - consolidate |
| Duplicated business logic across services/modules (rule of three violated) | | Yes |
| Event or message schema changed without consumer impact assessment | Yes | |

## API & Contract Design

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Breaking change to a public API without version bump or feature flag | Yes | |
| Renaming/removing a schema field consumed by downstream without migration | Yes | |
| Adding required fields to an existing schema | Yes | |
| Non-idempotent GET or DELETE | | Yes |
| Missing input validation at API boundary | Yes | |
| Error response format inconsistent with existing endpoints | | Yes |

## Data Design

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Multiple owners for the same data (no single source of truth) | Yes | |
| Auto-increment PK where natural composite key would be more correct | | Yes |
| Schema change without forward/backward compatibility consideration | Yes | |
| Data stored indefinitely without retention or TTL strategy | | Yes |

## Resilience

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| External call without timeout | Yes | |
| Retry without backoff (tight loop) | Yes | |
| Failed async message discarded silently (no DLQ) | Yes | |
| Hard dependency on a non-critical service with no fallback | | Yes |

---

## Scoring Guide

Apply severity using the `rubrics/code-review-checklist.md` severity levels:
- **Blocker** (Red): must be fixed before merge.
- **Suggestion** (Yellow/Green): should be addressed; can be deferred with explicit justification.
