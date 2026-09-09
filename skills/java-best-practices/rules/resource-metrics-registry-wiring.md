---
title: Fail Closed on Metrics Registry Wiring
impact: HIGH
impactDescription: Private fallback registries hide operational signals from reporters and dashboards
tags: java, metrics, observability, spring, dropwizard, wiring
---

## Fail closed on metrics registry wiring

Production monitoring wrappers must use the shared application metrics registry.
Do not create a fresh local registry when dependency injection fails.

**Incorrect (silent private registry):**

```java
public MonitoredClient(Client delegate, MetricRegistry registry) {
    this.delegate = delegate;
    this.registry = registry != null ? registry : new MetricRegistry();
}
```

That keeps the application running but records cache hits, misses, latency, and
failure meters in a registry that CloudWatch, Prometheus, or other reporters do
not export.

**Correct (required shared registry):**

```java
@Bean
public MonitoredClient monitoredClient(MetricRegistry metricRegistry) {
    return new MonitoredClient(delegate(), metricRegistry, cacheSize, ttl);
}

public MonitoredClient(Client delegate, MetricRegistry metricRegistry) {
    this.delegate = Objects.requireNonNull(delegate, "delegate");
    this.metricRegistry = Objects.requireNonNull(metricRegistry, "metricRegistry");
}
```

Configuration tests should assert that the monitored wrapper receives the exact
same registry instance as the application reporter. Metrics are an operational
contract; broken wiring should fail startup or tests instead of silently
discarding signals.
