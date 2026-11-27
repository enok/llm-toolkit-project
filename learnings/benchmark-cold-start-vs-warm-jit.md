---
title: Benchmark cold start for single-call code - warm JIT results can hide a 4x slowdown
category: testing
created: 2026-11-26
tags: [benchmark, jit, cold-start, javascript, python, percentiles, correction]
---

# Problem
Candidate JavaScript snippets for a judge that runs each solution once were compared with a
warmed-up benchmark loop. The warm numbers ranked a `for...of` loop level with an indexed
loop; measured cold, the `for...of` version was about four times slower.

# Failed Approaches
- Benchmarking after warm-up iterations: the JIT had optimised the loop, so the result
  described steady state that a single-call run never reaches.
- Reading p50/p95 percentiles of millisecond-resolution timers: at that resolution the
  percentiles are mostly timer noise.
- Quietly swapping in the corrected figures: the earlier claim stayed in circulation.

# Solution
- When the real workload is one call per process, measure a fresh process per run (cold
  start), repeat enough times to see the spread, and report the median and the range.
- Use timers with enough resolution for the work being measured; if the work takes a few
  milliseconds, batch it or use a high-resolution timer.
- State a correction explicitly ("earlier result was warm; cold start differs by about 4x") so
  readers can replace what they remembered.
- In Python, push work into builtins (slicing, bytes operations, `str` methods) instead of
  per-element loops; the same cold, single-call reasoning applies.

# Why
A JIT compiles hot code after many iterations; a one-shot run pays interpreter cost for the
whole call. A benchmark has to match how the code will actually be executed. The about 4x gap
is from one snippet pair on one engine and should be re-measured, not assumed.
