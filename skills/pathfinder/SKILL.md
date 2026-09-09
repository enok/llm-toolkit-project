---
name: pathfinder
description: "Use when you have a design doc or implementation plan and need to decompose it into deliverable vertical slices before execution. Triggers include 'slice this plan', 'break this into phases', 'what should we build first', 'pathfinder', 'find the path', 'how should I sequence this', 'de-risk this', 'cost of late discovery', concerns about discovering problems too late, wanting to prove risky integrations work early, restructuring plans to retire risk faster, or any multi-layer feature (schema + services + API + UI) that spans multiple PRs and needs sequencing."
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Pathfinder

Find the optimal deployment path through a feature plan by minimizing **CoLD** — the **C**ost **o**f **L**ate **D**iscovery — the compounding waste that occurs when a wrong assumption is discovered only after layers of infrastructure have been built on top of it.

## The Problem Pathfinder Solves

Engineers naturally decompose work by technical layer: first the database tables, then the entities, then the repositories, then the services, then the API, then the frontend. Each PR feels productive in isolation. But this horizontal sequencing hides a trap: **the riskiest assumptions aren't tested until the very end.**

The result: you ship 6 PRs that each pass CI, then discover during integration (or worse, during QA) that the pub/sub channel doesn't support cross-agency delivery, or the external API returns data in a shape your model can't handle, or the query patterns your UI needs aren't supported by your schema. Now you're refactoring across every layer you already built.

**CoLD** (Cost of Late Discovery) = (probability an assumption is wrong) × (amount of work built on top of that assumption)

Pathfinder inverts the sequence. Instead of building bottom-up by layer, you identify which assumptions carry the highest Cost of Late Discovery and prove them first with the thinnest possible end-to-end slice. Everything else follows with confidence.

## Overview

Pathfinder takes a design doc or PRD and produces:

1. A **Cost of Late Discovery assessment** ranking assumptions by how expensive they'd be to discover wrong after the fact
2. Slicing strategy options (risk-first, standard vertical, hybrid)
3. An ordered **slice manifest** where each slice cuts through all necessary layers and retires a specific assumption
4. **Re-plan checkpoints** between slices that incorporate learnings before committing to the next slice

## When to Use

- Feature spans multiple layers (schema, service, API, pub/sub, UI)
- Multiple PRs to deliver
- Integration unknowns or untested assumptions in the plan
- You want to prove the riskiest parts work before building infrastructure on top of them
- You've been burned before by late-stage integration surprises

## When NOT to Use

- Single-layer changes (just a migration, just a UI component)
- Feature is small enough for one PR
- Design doc doesn't exist yet (use brainstorming first)

## Process

```
Read design doc
    ↓
Explore codebase for integration points
    ↓
Cost of Late Discovery assessment
    ↓
Present slicing strategies
    ↓
User picks strategy
    ↓
Generate slice manifest with parallelization map
    ↓
Generate slice 1 full plan
    ↓
Execute slice 1
    ↓
Re-plan checkpoint → What changed? What did we learn?
    ↓
Generate next slice plan (adjusted for reality)
    ↓
Execute next slice → Re-plan checkpoint → ...
```

## Phase 1: Cost of Late Discovery Assessment

Before slicing anything, identify what would be most expensive to discover is wrong after infrastructure is built on top of it. Read the design doc and the codebase, then systematically check:

### Integration Risk Checklist

Run through these common sources of high CoLD. Not every project has all of these, but check each one:

| Risk Category | What to look for | Why it's expensive late |
| --- | --- | --- |
| **New external service integration** | System talks to something it never has before — a cloud storage provider, a third-party API, a new WebSocket data source, an external protocol system. Check whether your DI framework already has a binding module for it or if you need to wire one from scratch. | Every layer assumes the integration works; if the external service behaves differently than expected, everything unravels |
| **Cross-tenant / cross-boundary data flow** | Data needs to cross isolation boundaries (tenant, agency, department, org) that the existing pub/sub or messaging infrastructure wasn't designed for. Most real-time systems scope messages to a single tenant — cross-tenant delivery often requires a completely different routing pattern. | If you assume the standard messaging path supports cross-boundary delivery and it doesn't, you discover this after building every layer on top of that assumption |
| **New real-time message type (pub/sub end-to-end)** | A new message requires coordinated changes across 4 independently-built pieces: topic/channel definition, backend publisher, backend subscriber/router, and frontend listener. These are typically built by different engineers in different PRs. | Producer-consumer mismatches (wrong payload shape, missing routing fields, incorrect filtering) only surface when all four pieces are integrated — which happens last |
| **Data model ↔ query pattern mismatch** | Schema designed around write patterns (one entity per table, normalized) but the frontend needs read patterns the model doesn't efficiently support (filtered lists, joins across entities, sorted/paginated views). Check whether your indexes support the actual query patterns the UI will drive. | Requires schema redesign which cascades through entity, repo, service, API, and frontend layers |
| **Cross-window / cross-process state sync** | New state that must stay consistent across multiple windows, tabs, or processes (desktop apps, multi-monitor setups, Electron + web). Each platform may handle message routing, acknowledgment, and cleanup differently. Memory leaks from uncleaned subscriptions compound over long-running sessions. | Cross-window bugs only surface in multi-window testing environments, which are typically exercised last |
| **Feature flag / configuration default changes** | New configuration with a default value. If the default changes later, every tenant/department without an explicit override silently gets new behavior. The safe pattern: NULL defaults in storage, explicit fallbacks in code — so you can distinguish "wants the default" from "has an override." | Default behavior changes break existing workflows silently and are extremely hard to diagnose in production |
| **Environment-specific configuration** | Credentials, bucket names, IAM roles, endpoint URLs, or connection strings that differ across environments (dev, QA, staging, production, region-specific deployments). External services that have separate sandbox vs production endpoints. | Works in dev, fails in staging or production — discovered during deploy, not during development |
| **Behavioral edge cases at system boundaries** | Concurrent access, race conditions, permission interactions, state machine transitions that span multiple services. The happy path works when systems are tested in isolation; edge cases only appear when they interact under realistic conditions. | These bugs are invisible in unit tests and single-service integration tests; they surface during QA, load testing, or production — maximum CoLD |

### Scoring Each Risk

For each risk you identify, assess:

- **Probability it's wrong:** How confident are you that this will work as assumed? (Low/Medium/High)
- **Layers built on top:** How many layers of code will be built assuming this works? Count them.
- **Cost of Late Discovery:** Probability × Layers built on top. This is what determines sequencing priority.

Present the top 3 risks, ranked by Cost of Late Discovery. For each, state specifically:

- What the assumption is
- What happens if it's wrong
- How many layers of work would need to be revisited

**CRITICAL: Risks are retired by working code, not by design documents.** The instinct to "write a behavioral contract first" or "add a spec document" does not retire risk — it moves it to a different document. A risk is retired when you have running code that proves the assumption holds.

## Phase 2: Slicing Strategies

Present three options:

### Option A: Risk-First

Start with the scariest integration. Build the thinnest possible end-to-end path that proves it works — even if that means hardcoding things, skipping management infrastructure, or using a fixed dataset. Then build the real infrastructure with confidence.

**When to pick:** The core integration is genuinely uncertain. You're not sure the thing will work at all. Cost of Late Discovery for the top risk is HIGH.

### Option B: Standard Vertical

Take the plan's features and reorder them into thin end-to-end slices. Each slice delivers a narrow but complete path through all necessary layers. No slice is purely one layer.

**When to pick:** The integrations are well-understood. The risk is more about scope and sequencing than technical uncertainty. Cost of Late Discovery is LOW across the board.

### Option C: Hybrid

One risk-first tracer round to prove the scariest assumption, then switch to standard vertical slices for the rest.

**When to pick:** There's one or two big unknowns but the rest is well-charted territory. Most common choice.

For each option, state: what you learn first, what you defer, and the review/blast radius trade-off.

## Phase 3: Slice Manifest

After the user picks a strategy, generate the manifest. For each slice:

| Field | What it contains |
| --- | --- |
| **Name** | Short label (e.g., "Cross-agency pub/sub tracer round") |
| **Proves** | The specific assumption this retires — framed as a question that gets answered |
| **CoLD** | What would go wrong if this assumption failed after later slices were built |
| **Layers** | Which layers are touched (schema, entity, repo, service, endpoint, pub/sub, UI, test) |
| **Scope per layer** | What's included — ONLY what's needed to make this slice's proof work |
| **Depends on** | Which prior slices must be complete |
| **Parallel with** | Which other slices can run concurrently (important for team coordination) |
| **Verification** | How you DEMONSTRATE it works — not "tests pass" but "I can do X and see Y" |
| **Deferred** | What the full design calls for but this slice intentionally skips |
| **PR scope** | What a reviewer should focus on (do NOT include time/day estimates — they're unreliable and irrelevant) |

**Slice 1:** Full implementation plan, ready to execute.
**Slices 2+:** Summary only. Full plan generated at the re-plan checkpoint.

### Parallelization Map

After generating all slices, explicitly state which slices can run concurrently:

```
Slice 0 (tracer)
   |
   +---> Slice 1 (can start after Slice 0)
   |
   +---> Slice 2 (can start after Slice 0, parallel with Slice 1)
   |
   +---> Slice 3 (can start after Slice 0, parallel with Slices 1-2)
   |        |
   |        +---> Slice 4 (depends on Slice 3)
```

This matters because teams often have multiple engineers who can work in parallel once the tracer proves the integration.

### Thickness Check for the First Slice

After drafting the first slice, ask: "Can this proof be made thinner?" Specifically:

- Can you hardcode something instead of building the full infrastructure?
- Can you use a fixed dataset instead of building the upload/creation flow?
- Can you test the integration with an in-memory stub instead of the full repository layer?

If yes, split: make the thinner proof Slice 0, and the infrastructure that replaces the hardcoding becomes Slice 1. If the proof genuinely requires the infrastructure (e.g., you need to prove the DB-to-engine wiring specifically), the thickness is justified — note why.

## Phase 4: Re-Plan Checkpoint

Between slices:

1. Ask what changed or was learned during the previous slice
2. Read the current codebase state (what was actually built)
3. Compare against the next slice's summary
4. **Re-assess Cost of Late Discovery** — did the previous slice change the risk landscape?
5. Generate the full implementation plan for the next slice, adjusted for reality
6. Update the deferred list

## Slicing Rules

These rules prevent the most common failure modes:

### Rule 1: Every slice must cross at least two layers

A slice that is entirely migration + entity + repo is NOT a vertical slice — it's a horizontal layer. If your slice doesn't touch at least one consumer of the data (service, endpoint, test that exercises real behavior, integration proof), it's not vertical.

**STOP: Check yourself.** If every slice in your manifest has the same layers (all "migration, entity, repo, test"), you've produced a horizontal decomposition with vertical labels. Start over.

### Rule 2: Verification must demonstrate behavior, not just persistence

"Migration runs and tests pass" is necessary but proves nothing about whether the system works. Good verification: "Agency B's browser session displays a real-time notification when Agency A creates a request." Bad verification: "The request table has rows in it."

### Rule 3: Risk is retired by running code, not documents

When you identify a risk, the response is "build the thinnest slice that proves it" — not "write a design doc that specifies the contract." Documents describe intent. Code proves reality.

### Rule 4: Later slices are drafts, not commitments

Only the next slice gets a full implementation plan. Later slices are summaries that WILL change based on what you learn. Don't over-invest in planning slices you haven't started yet.

### Rule 5: Deferred items must be tracked

Every item in the original design must appear in exactly one slice or in the deferred list. Nothing gets silently dropped.

### Rule 6: Each slice should map to a reviewable PR

A slice should be small enough that a single engineer can implement it and another can review it without heroics. If a slice feels too large, split it. Never include time or day estimates in slice descriptions — they're unreliable and distract from what matters: what can you **see or do** at the end of the slice that you couldn't before?

## Common Mistakes

| Mistake | CoLD impact | What to do instead |
| --- | --- | --- |
| Every slice is "table + entity + repo + test" | Maximum — integration never tested until the end | At least one slice must prove an integration end-to-end |
| All slices defined upfront as a static plan | You commit to a path before learning from early slices | Only plan the next slice in detail; later slices are summaries |
| Risk assessment recommends "write more design docs" | Documents don't retire risk; they defer it | Convert the doc into a proof slice with running code |
| Slices are too thick (entire features) | Multiple assumptions bundled; if one fails, unclear which | Ask: "what's the ONE thing this slice proves?" If "and," split it |
| Verification is always "tests pass" | Tests can pass while the system is broken end-to-end | Add behavioral verification: "I can do X and see Y" |
| No parallelization map | Team blocked on serial execution | Explicitly state which slices can run concurrently after the tracer |

## Output Location

Write the slice manifest to the same directory as the design doc, named `SLICES.md`. Example: if the design is at `docs/plans/admin-implementation/MANIFEST.md`, write to `docs/plans/admin-implementation/SLICES.md`.

## Related Skills

- **task-starter** — turns a ticket into a scoped plan; Pathfinder sequences it
- **design-driven-dev** — investigation-first design; Pathfinder decomposes the result
- **project-discovery** — understand the codebase before slicing
- **ticket-review** (or **review**) — review each slice's PR
