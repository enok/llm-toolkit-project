# Architecture Rubric

Evaluate architecture and layering quality. Use this rubric when reviewing code that introduces or modifies structural components — layers, boundaries, services, repositories, or inter-module dependencies.

---

## Layering & Boundaries

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Business logic in controller/handler | ✅ | |
| Database query built in service layer | ✅ | |
| Repository method containing business rules | ✅ | |
| Cross-layer import skipping a layer | ✅ | |
| Shared mutable state across layers | ✅ | |
| Thin controllers delegating to services | | ✅ verify present |
| Service layer unaware of HTTP/transport details | | ✅ verify present |

## Separation of Concerns

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Single class/module with unrelated responsibilities | | ✅ |
| Hard-coded infrastructure details (DB URL, bucket name) in domain code | ✅ | |
| Configuration read inside domain logic instead of injected | | ✅ |
| More than one public responsibility per module | | ✅ split |

## Dependency Injection

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Collaborators instantiated inside a class (`new X()` in constructor body) | ✅ | |
| Service depends on a concrete implementation, not an interface | | ✅ |
| Test doubles impossible without framework magic | ✅ | |
| Application wiring (concrete bindings) leaks into domain classes | ✅ | |

## Transaction Safety

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Multiple writes without transactional boundary | ✅ | |
| Partial failure leaves data in inconsistent state | ✅ | |
| Transaction spanning external HTTP or queue call | ✅ | |
| Retry logic inside a transaction | | ✅ review |

## Coupling & Cohesion

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Services that must deploy together share database or in-process state | ✅ | |
| Change in one module requires cascade edits in many unrelated places | | ✅ consolidate |
| Duplicated business logic across services/modules (rule of three violated) | | ✅ |
| Event or message schema changed without consumer impact assessment | ✅ | |

## API & Contract Design

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Breaking change to a public API without version bump or feature flag | ✅ | |
| Renaming/removing a schema field consumed by downstream without migration | ✅ | |
| Adding required fields to an existing schema | ✅ | |
| Non-idempotent GET or DELETE | | ✅ |
| Missing input validation at API boundary | ✅ | |
| Error response format inconsistent with existing endpoints | | ✅ |

## Data Design

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Multiple owners for the same data (no single source of truth) | ✅ | |
| Auto-increment PK where natural composite key would be more correct | | ✅ |
| Schema change without forward/backward compatibility consideration | ✅ | |
| Data stored indefinitely without retention or TTL strategy | | ✅ |

## Resilience

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| External call without timeout | ✅ | |
| Retry without backoff (tight loop) | ✅ | |
| Failed async message discarded silently (no DLQ) | ✅ | |
| Hard dependency on a non-critical service with no fallback | | ✅ |

---

## Scoring Guide

Apply severity using the code-review-checklist rubric:
- **Blocker**: must be fixed before merge.
- **Suggestion**: should be addressed; can be deferred with explicit justification.
