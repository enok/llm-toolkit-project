---
title: Flipping a legacy service's shared config needs IAM on the new target first
category: deployment
created: 2026-08-19
tags: [lambda, sqs, iam, parallel-stack, migration, cutover, environment-variables]
---

# Problem

During a parallel-stack migration (an old service still serving live
traffic; a new, differently-named stack running beside it), the plan
called for both to run the same code and the same shared config (an
environment-variable set) until callers cut over. That would flip the old
service's queue-URL variable to the new queue - which its old execution
role has no send permission on. Applying the config flip alone would have
made every live request silently fail its downstream write, since the
send was fire-and-forget.

# Failed Approaches

- Updating code and config first, treating IAM as a follow-up: the failure
  mode is silent (a logged error, no user-facing failure), so live traffic
  would have dropped records until someone noticed an error-rate metric.
- Granting the permission by hand outside of infrastructure as code:
  leaves no record of the temporary grant and nothing to clean up at
  cutover.

# Solution

Order matters: (1) infrastructure as code first - a temporary, clearly
labeled resource that looks up the old role and attaches the new stack's
access policy to it, with a header comment marking it TEMPORARY and a
tracked follow-up to delete it at cutover. Plan, confirm exactly one add,
apply, and re-plan to a clean no-op. (2) Only then deploy the new code
package to the old service and verify the deployed version matches (for
example, compare a content hash). (3) Only then flip the shared config.
(4) Verify live: send a real request and check for the expected success
log line plus zero new error events.

# Why

Config, code, and IAM change through different mechanisms and different
APIs, but the running service consumes them as one unit at request time.
Permissions must land before the config that exercises them; a
clearly-tombstoned, temporary grant keeps the coupling visible and
reversible in one revert-and-apply at cutover.
