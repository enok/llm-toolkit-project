---
title: Source-backed modern Java guidance
tags: [java, spring, jdk, records, sealed-types, virtual-threads, maven]
---

# Source-backed modern Java guidance

Use this reference for runtime-aware Spring and modern-JDK decisions.

Primary sources:

- [Spring dependency injection](https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html)
- [Oracle Java secure coding guidelines](https://www.oracle.com/java/technologies/javase/seccodeguide.html)
- [Oracle JDK virtual threads](https://docs.oracle.com/en/java/javase/21/core/virtual-threads.html)

- Prefer constructor injection in Spring services unless preserving legacy
  behavior is the explicit task.
- Use records for simple immutable carriers only when the supported runtime and
  serialization framework are compatible.
- Use sealed types only for intentionally closed domains where exhaustive
  handling adds value.
- Treat virtual threads as a runtime choice, not a free performance switch.
  Check blocking dependencies, thread-local use, pools, timeouts, cancellation,
  and observability.
- For multi-JDK builds, prefer compiler `release` settings over unrelated
  `source` and `target` values.

Adapt external guidance to the destination framework, build tool, runtime, and
test style; do not import a language guide wholesale.
