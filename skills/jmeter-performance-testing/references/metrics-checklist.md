---
title: Performance run metrics checklist
tags: [jmeter, performance, observability, metrics, monitoring]
---

# Performance Run Metrics Checklist

Use this checklist while observing and reporting a load run. Resolve the actual
metric names, namespaces, dashboards, and log locations from the consumer repo's
`docs/llm/` or from the service owner — never guess them, and validate that each
one is populated *before* the run rather than discovering a blind spot after.

## Before The Run

- Confirm the target environment, base URL, and build/commit under test.
- Confirm access to every observability surface you intend to cite, and that any
  session or credential will outlive the run. An expired session makes a healthy
  system look unmonitored.
- Record the start time in UTC and local time, and note anything else happening
  in the window: deployments, batch jobs, dependency scans, other load runs.
- Capture a short pre-run idle sample so the baseline is not the busy period.

## Client-Side (JMeter) Signals

The load generator's own view, from the `.jtl`:

- Sample count, throughput achieved vs. throughput targeted.
- Latency: avg, p50, p95, p99, max — overall and per label.
- Success rate, error count, and response-code distribution.
- Assertion failures separated from transport failures: a `200` that fails a
  content assertion is a different defect from a connection reset.
- Connect time vs. latency vs. elapsed, to separate network/TLS setup from
  server work.
- Load-generator health: CPU, memory, open file descriptors, ephemeral ports. A
  saturated generator reports its own queueing as service latency.

## Service-Level Signals

For each service in the request path:

- Request count and rate per endpoint.
- Latency percentiles per endpoint (p50, p95, p99, max), not averages alone.
- Error rate split by 4xx and 5xx, plus exception/stack-trace counts in logs.
- Timeouts, retries, and circuit-breaker trips.
- Thread pool, connection pool, and queue depth utilization.
- Cache hit/miss/load-failure counters, and cold-start or warmup counters.
- Runtime health: GC pause time and frequency, heap usage, restarts.

## Dependency And Downstream Signals

- Database: latency, connection pool saturation, lock waits, slow queries,
  throttling or write errors.
- Queues, topics, and streams: publish failures, consumer lag, delivery delay,
  dead-letter volume.
- Serverless functions: invocations, errors, throttles, duration p95/p99,
  concurrency limits.
- Third-party or internal APIs: latency, error rate, rate-limit responses.
- For asynchronous work triggered by the test, the completion latency measured
  at the *end* of the chain, not just the synchronous response time.

## Infrastructure Signals

- Load balancer: request count, target response time, 4xx/5xx at the balancer
  vs. at the target, rejected/surged connections.
- Instances or containers: CPU, memory, network, disk I/O, restarts, unhealthy
  target count, autoscaling events during the window.
- Any capacity ceiling that could cap the result: desired/max instance counts,
  concurrency limits, connection or rate limits.

## After The Run

- Record the end time, then let asynchronous work drain before reading the final
  numbers.
- Re-check error logs for the full window, including the ramp-up you excluded
  from percentiles.
- Note every gap: metrics that were unavailable, dashboards that lagged,
  sampling that hid the tail, sessions that expired mid-run.
- Confirm the environment is back to its pre-test state.

## Known Pitfalls

- Cross-service timestamps drift. Correlate with a request/trace ID and a
  bounded window rather than raw log ordering.
- Averages hide tails. A stable mean with a growing p99 is a regression.
- Cloud dashboards aggregate at coarse periods; a one-minute spike can vanish at
  five-minute granularity.
- Overlapping deployments, scans, or background load distort results — report
  them instead of averaging them away.
- A test that never reached its target throughput has not validated that
  throughput, regardless of how good the latency looks.
