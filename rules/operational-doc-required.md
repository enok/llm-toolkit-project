---
trigger: always_on
description: Repeated operational work should become a runbook or runbook update
---

# Operational documentation

If a deploy, mitigation, rollback, or triage flow is non-trivial or recurring:

1. Check whether a runbook or ops doc already exists.
2. If it exists, update it with the new learning.
3. If it does not exist, create one before the knowledge disappears from working memory.

If a change adds, changes, or relies on operational metrics, document exact
metric catalog entries rather than only high-level categories. Include emitting
service, metric name, type, dimensions/tags, trigger, healthy signal,
troubleshooting use, and source evidence.

Before transferring or removing an observability collector, record the owner
of every affected signal, prove the target path is healthy, prove zero
duplicates remain on the retiring path, and preserve the exact reviewed inputs
and configuration that must not change. A successful canary for one signal
never authorizes removal of another signal's collector.

Before mutating an existing Confluence or wiki page or folder, a verified
rollback backup gate must pass. The gate is deployment-specific: configure it
from the template in `rules/examples/confluence-backup-gate.md` (approved
backup destination, fail-closed authorization, mutation-complete snapshot and
manifest, verified readback). Keep the concrete destination in the consuming
repo's own configuration (for example its `docs/llm/`); this shared rule stays
generic.
