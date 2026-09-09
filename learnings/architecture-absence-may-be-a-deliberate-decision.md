---
title: An absent architecture element may be a deliberate decision, not a gap
category: architecture
created: 2026-08-19
tags: [api-gateway, lambda, latency, architecture-decision, negative-decision, documentation]
---

# Problem

A sweep found no API Gateway in front of a Lambda function that external
applications call. The absence was read as a gap: a gateway was built, applied
in stage, validated, then mandated as "the only sanctioned entry point", with
IAM caller policies and documentation across several wiki pages. The owner then
reversed everything — the gateway had been removed from that architecture long
ago **for performance reasons**: the primary caller invokes with a 250 ms client
timeout, and the extra hop does not fit that budget. A full day of build plus
documentation was torn down (ten Terraform destroys, one module retired, four
pages rewritten).

# Failed Approaches

- Treating "nothing points at this function" (an API sweep with zero
  integrations) as evidence that a gateway was *missing* rather than *removed*.
- Generalizing from the standard best practice ("never expose a bare function to
  external callers") without checking the caller's latency budget: direct SDK
  invoke was chosen precisely because p99 must fit inside 250 ms.

# Solution

Before adding an architectural element that "should" exist, actively look for
evidence that its absence is deliberate:

- caller configuration (timeout budgets, hard-coded function or queue names);
- git history of both the caller repo and the infrastructure repo;
- the owning team or service owner, asked directly.

When the element is then added or removed, record the **negative decision** in
the docs — a short "No API Gateway (deliberate: removed for the caller's latency
budget)" section stating the reason and the condition that would justify
revisiting it — so the next reader or agent can tell a decision from an omission.

# Why

Documentation and infrastructure record what exists, never what was
intentionally removed. An undocumented negative decision looks identical to a
gap, and best-practice priors push hard toward "filling" it. Only an explicit
tombstone ("none, deliberate, because X") breaks that loop.
