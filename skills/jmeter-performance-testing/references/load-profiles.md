---
title: JMeter load profile design
tags: [jmeter, performance, load-testing, thread-group, throughput]
---

# JMeter Load Profile Design

A load profile is four numbers plus a target rate: threads, ramp-up, duration,
and throughput. Get them from the project's documented performance plan when one
exists; otherwise derive them from production traffic and the question being
asked. Record the source of every number in the run report — an undocumented
profile makes two runs incomparable.

## Thread Group And CTT Pattern

- Use one Thread Group per scenario or endpoint group you want to size and
  report independently.
- Thread Group fields: **threads** (concurrent virtual users), **ramp-up
  seconds** (time to start all threads), **duration seconds** (steady-state
  length, with the scheduler enabled).
- Add a **Constant Throughput Timer (CTT)** when you are targeting a request
  *rate* rather than a concurrency level:
  - Throughput is expressed in **samples per minute**, not per second.
  - Choose the target scope deliberately. "All active threads (shared)" spreads
    one plan-wide rate across every running thread; "this thread only" multiplies
    the rate by the thread count.
  - Apply the timer independently to each Thread Group that needs its own rate.
- The CTT can only *slow* threads down. If the requested rate is not reached,
  the bottleneck is thread count, the client, or the service — not the timer.
  Always report achieved throughput next to target throughput.

## Sizing The Numbers

1. **Start from the business rate.** Convert the target to requests per minute:
   `requests_per_minute = (flows_per_hour * requests_per_flow) / 60`.
   State `requests_per_flow` explicitly; a flow that calls two endpoints doubles
   the endpoint rate for the same business volume.
2. **Derive the thread floor.** With Little's Law,
   `threads >= (target_requests_per_second) * (expected_response_seconds)`.
   Add headroom (roughly 2x) so a latency regression does not silently cap
   throughput and mask itself.
3. **Ramp up over at least 30-60 seconds**, and longer for large thread counts,
   so connection pools, JIT warmup, autoscaling, and caches are not measured as
   steady state. Discard the ramp-up window from steady-state percentiles.
4. **Run long enough to see steady state.** Anything under a few minutes mostly
   measures warmup. Long soak runs surface leaks, pool exhaustion, and cache
   eviction that a short run cannot.
5. **Check the client.** A load generator that saturates its own CPU, file
   descriptors, ephemeral ports, or network reports client latency as service
   latency. Watch generator resources and distribute the run if needed.

## Profile Shapes

| Profile | Purpose | Typical shape |
| --- | --- | --- |
| Smoke | Prove the plan, URL, auth, and assertions work | A few threads, seconds of ramp-up, ~1 minute |
| Baseline | Reproducible reference for comparisons | Steady expected production rate, moderate ramp-up, 10-30 minutes |
| Load | Busy-day simulation, the usual pass/fail gate | Peak expected rate, 5-10 minute ramp-up, 30 minutes |
| Stress | Find the knee: where latency or errors break | Step above peak until failure, then stop |
| Soak | Leaks, pool exhaustion, cache/GC drift | Baseline rate, hours |
| Spike | Recovery from an abrupt surge | Short ramp-up to a multiple of peak, then return |

These are illustrative starting points, not a standard. Resolve the real
threads/ramp-up/duration/throughput numbers for the scenario you are running
— from the project's documented plan when one exists, otherwise derived as
above — and pass them explicitly to `scripts/run_jmeter.py` with
`--threads`, `--ramp-up`, and `--duration` (see
`references/jmeter-execution.md`).

## Recording A Project Profile

Keep project profiles in the consumer repo (for example
`docs/llm/performance-profiles.json`) so runs are reproducible and
reviewable, then pass the numbers for the profile you are running explicitly
on the command line:

```json
{
  "peak-day": {
    "threads": 30,
    "ramp_up_seconds": 600,
    "duration_seconds": 1800,
    "throughput_per_minute": 750
  }
}
```

```bash
python3 skills/jmeter-performance-testing/scripts/run_jmeter.py \
  --jmx /path/to/test.jmx --base-url https://api.example.com \
  --threads 30 --ramp-up 600 --duration 1800 \
  --property throughput_per_minute=750
```

For each documented profile, record: the source (which plan, which revision,
which date), the business target it models, the requests-per-flow assumption,
and the environment it was sized for. Re-derive rather than reuse when the
service's endpoint mix changes.

## Concurrent Runs

When two profiles run at once against the same target, report three numbers:
each profile's own volume, and the combined threads and requests per minute. A
report that shows only the per-profile figures understates the load the service
actually absorbed, and makes the latency look inexplicably bad.
