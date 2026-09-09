---
title: Performance result analysis
tags: [jmeter, performance, analysis, baseline-comparison, tracing]
---

# Performance Result Analysis

Use this reference to turn a summarized `.jtl` (see
`scripts/summarize_jmeter_jtl.py`) into a pass/fail call, a baseline
comparison, and a report. Get real thresholds and the baseline run from the
project's documented plan or `docs/llm/` when they exist; the numbers below
are illustrative starting points, not a standard.

## Pass/Fail Thresholds

Gate on percentiles and rates, not on the average. A stable mean with a
growing p99 is a regression the average will never show.

| Signal | Illustrative default | Notes |
| --- | --- | --- |
| p50 latency | within the documented SLO, or the noise band around baseline | typical-request feel |
| p90 latency | within SLO | first percentile where queueing shows up |
| p95 latency | within SLO | the usual gate for "is this endpoint healthy" |
| p99 latency | within SLO, tracked even if not gated | tail; see minimum sample size below before trusting it |
| Error rate | < 1% for a smoke probe, < 0.1% for a load gate | split 4xx (client/test issue) from 5xx (service issue) |
| Throughput achieved | >= target throughput | a run that never reached target has not validated that scenario, regardless of how good the latency looks |

A run only passes when every gated signal passes. Record every threshold
source (SLO doc, ticket, prior baseline) in the report; an undocumented
threshold is an opinion, not a gate.

## Baseline Comparison Arithmetic

State the comparison direction and the formula before any table, so a reader
never has to guess which side is the baseline.

- `ratio = candidate / baseline`
- `percent_change = (candidate - baseline) / baseline * 100`
- For latency and error rate (lower is better): `percent_slower = (ratio - 1) * 100`, `percent_faster = (1 - ratio) * 100`
- For throughput and success rate (higher is better): `percent_change` as above, read directly (positive = better)

Use wording such as `candidate vs baseline` and name the actual build,
branch, or commit on each side.

### Noise Band

Run-to-run variance is normal; do not call every wiggle a regression.

- Before trusting a delta, establish the noise band by running the same
  plan, profile, and environment twice with no real change and measuring the
  spread. Absent that, `+/-10%` on latency percentiles and `+/-1` percentage
  point on error rate are reasonable illustrative starting bands to
  calibrate from.
- A delta inside the noise band is **stable**, not improved or regressed,
  even if it is not exactly zero.
- Widen the band for smaller sample sizes and tighter percentiles (p99 is
  noisier than p50 at the same sample count).

### Minimum Sample Size

A percentile is only as meaningful as the samples behind it.

| Percentile | Rough minimum samples (per label) |
| --- | --- |
| p50 | tens |
| p90 / p95 | a few hundred |
| p99 | at least ~1,000 |
| p99.9 | at least ~10,000 |

Below the minimum, report the percentile as indicative only, or report max
and a note instead of treating it as a stable tail figure. A `p99` computed
from 40 samples is really just "close to max."

## Improved / Regressed / Stable Decision Rule

Apply in order; stop at the first rule that matches.

1. **Inconclusive** if: sample size is below the minimum for the percentile
   being judged, target throughput was not reached, the load generator or
   client was saturated (see below), observability had a gap during the
   window, or another run overlapped without being separated out.
2. **Regressed** if: any hard pass/fail threshold is breached (error rate
   over limit, a gated percentile over SLO, throughput under target), or a
   gated latency/error signal moved worse than the noise band.
3. **Improved** if: no threshold is breached, and at least one gated signal
   moved better than the noise band with none moving worse than it.
4. **Stable** otherwise: every gated signal sits inside its noise band and
   every threshold passes.

End the report with one aggregate sentence using one of these four words,
then list the supporting metrics underneath it. Do not average an
improvement in one endpoint against a regression in another into a false
"stable" — report per-label results and let the aggregate sentence describe
the overall shape (for example "stable overall, one endpoint regressed").

## Multi-Hop And Asynchronous Trace Reconstruction

Use this when the question depends on a chain of hops (a synchronous
request that triggers async work: a queue, a downstream service, a delayed
callback), not just the first response time JMeter measures directly.

### Inject A Trace Token Per Request

1. Generate an identifier per request or iteration: `${__UUID()}` in the
   plan, or a JSR223 PreProcessor, assigned to a JMeter variable (for
   example `trace_id`). If the target stack already speaks W3C Trace
   Context / OpenTelemetry, propagate its `traceparent` the same way instead
   of inventing a bespoke header.
2. Propagate it downstream as a request header (`X-Trace-Id: ${trace_id}`,
   or `traceparent` for W3C-style propagation) or a body/query field the
   entry service is expected to log and forward to whatever it calls next.
   A token that stops at hop one only proves hop one; ask the service owner
   to confirm forwarding before relying on hop two evidence.
3. Record it client-side: run JMeter with `sample_variables` set to your
   variable name (for example `--property sample_variables=trace_id`, which
   `run_jmeter.py` passes through as `-J`), so every JTL row carries the
   token as an extra CSV column, joinable one-to-one with server-side log
   lines carrying the same value.

### Evidence And Timing Rules

- Capture the full set of trace tokens for the run (or a stratified sample
  when volume is high), then query every hop's logs for exactly that token
  set within the run's bounded time window. Validate log access, index or
  log-group names, and retention before the run, not after.
- Treat the entry service's synchronous response as the front-door latency,
  not the full chain's latency. For asynchronous completion, wait for the
  async work to drain, then measure end-to-end completion at the *last* hop
  for the same token.
- Prefer hop-local duration fields and propagated source timestamps over
  raw cross-service log ordering; clock drift between hosts makes raw
  timestamp subtraction unreliable across services.
- Use queue, topic, or message IDs to split publish latency, delivery
  delay, consumer processing time, and downstream call latency into
  separate numbers instead of one opaque "async lag."
- Keep p50/p95/p99 and a few outlier examples per hop; a healthy front door
  with a slow last hop is a real regression the front-door number alone
  will hide.
- When the bottleneck appears to be upstream of where your trace token
  evidence starts, do not infer the cause from timestamps alone; request
  explicit propagation or use existing message IDs and service-local
  durations before naming a cause.

## Saturation Signals

Before crediting or blaming the service under test, rule out the load
generator and confirm the target's own capacity was not the limiter for
reasons unrelated to the change being tested (see
`references/metrics-checklist.md` for the full signal list). Saturation
turns a comparison inconclusive rather than regressed when it caps *both*
runs equally, and turns it into a real finding when it appears only on one
side.

- Throughput plateaus or drops while offered load (threads) keeps
  increasing: the classic knee of the curve.
- Thread pool, connection pool, or queue depth pinned at its ceiling.
- Error responses that mean "I'm full," not "you're wrong": `503`,
  connection refused or reset, timeouts, throttling responses.
- GC pause frequency or duration climbing across the run; heap sawtoothing
  without recovering.
- Load-generator CPU, memory, file descriptors, or ephemeral ports pinned;
  a saturated generator reports its own queueing as service latency.
- A capacity ceiling that caps the result regardless of the change under
  test: desired/max instance counts, concurrency limits, rate limits.

## Report Template

```markdown
## Performance Result: <scenario name>

**Profile / environment:** <profile> against <environment>, <base URL>
**Window:** <start> to <end> (UTC), build/commit <candidate>
**Baseline:** <baseline build/commit or prior run>, <when it ran>

### Traffic
- Threads / ramp-up / duration: <n> / <n>s / <n>s
- Throughput achieved vs target: <n>/min vs <n>/min

### Latency And Success (by label)

| Label | Count | Success % | p50 | p90 | p95 | p99 | Threshold |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| <label> | <n> | <n>% | <n>ms | <n>ms | <n>ms | <n>ms | pass/fail |

### Baseline Comparison
Direction: candidate vs baseline. `ratio = candidate / baseline`,
`percent_slower = (ratio - 1) * 100`.

| Label | Baseline p95 | Candidate p95 | Percent change | Inside noise band? |
| --- | ---: | ---: | ---: | --- |
| <label> | <n>ms | <n>ms | <n>% | yes/no |

### Trace Reconstruction (if applicable)
<front-door latency vs full-chain latency, per-hop breakdown, sample size>

### Saturation And Infrastructure Findings
<generator health, service pools/queues, capacity ceilings, GC>

### Decision
**<Improved | Regressed | Stable | Inconclusive>** - <one sentence>, then
the supporting metrics.

### Residual Risks / Follow-Ups
<observability gaps, expired session, overlapping load, only if necessary>
```
