---
trigger: always_on
description: Explicit deploy order, verification, and rollback planning for release work
---

# Release safety

Before proposing or executing a release:

1. Identify migrations, backwards-compatibility risks, and config or secrets changes.
2. Define the deploy order explicitly across repos and services.
3. Define verification **before** rollout begins.
4. Define rollback **before** production action begins.
5. If multiple repos or environments are involved, treat this as **release coordination**, not a single-repo change.
6. If retiring an environment, sweep every durable reference before pushing:
   config trees, deployment hooks, runbooks, operational docs, generated PR
   rows, and environment tables. Validate with exact-name searches plus tracked
   file checks for the removed environment path; the search should return only
   intentionally retained historical notes.
7. Before changing an IaC-owned remote configuration object, capture an
   immutable or version-pinned preimage with its object identity, version,
   metadata, size, ETag when available, and SHA-256. Re-read the stored backup
   through the authoritative API and verify those values before mutation.
8. Change canonical IaC only through the authorized pipeline and environment
   route. Keep direct cloud/API access read-only for rollout validation unless
   a separately approved ownership procedure explicitly authorizes the write;
   administrator access is not a substitute for the owning pipeline.

## Completion evidence

Source, CI, deployed infrastructure, and documentation are asynchronous state
machines: success in one layer proves nothing about another, and an older green
build can race a newer branch commit. Never report a release or ticket as 100%
complete from a single layer's signal.

- Keep a completion ledger with separate evidence per layer: implementation and
  tests, ticket-branch push, the target branch's exact remote SHA, the CI/deploy
  build number **and its checkout SHA**, deployment gates passed, a live
  read-back of the deployed resource or behavior, and documentation
  publication/read-back when docs are in scope.
- A branch push is not a deployment; a green build only counts when its checkout
  SHA equals the intended remote SHA; IaC or dashboard source is not proof of
  live behavior; a draft is not published documentation.
- If any applicable ledger row lacks evidence, name it as pending instead of
  reporting completion.

## Rollback execution

An explicitly authorized rollback is an incident-timeboxed action: skip
planning, documentation, and backups not required to make the specific mutation
safe, and record optional follow-ups only after mitigation is underway.

- A build's source revision is fixed at checkout — an in-flight build of the
  pre-rollback SHA can never deploy the rollback. Compare the in-flight build's
  checkout SHA with the authorized rollback SHA first; if they differ and the
  user directed the rollback, abort the stale build immediately rather than
  watching it.
- Confirm the rollback commit is the exact remote head of the target branch,
  trigger a fresh pipeline, resolve the queue item to a build number, and verify
  that build's checkout SHA before approving any gate.
- Run independent read-only checks in parallel, but preserve the dependency
  chain: target SHA before trigger, build number and SHA before gate approval,
  successful deployment before the final live read-back.
