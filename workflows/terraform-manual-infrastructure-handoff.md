---
description: Generate a source-grounded manual infrastructure handoff from Terraform when the target environment cannot be applied
---

# Terraform Manual Infrastructure Handoff

Use this workflow when Terraform defines the desired infrastructure but an authorized operator must create, update, rename, or remove resources manually.

## Safety boundary

1. Identify the target account, profile, region, environment, roots, backend, and write owner before running commands.
2. Treat production as read-only unless the user explicitly authorizes one concrete mutation. Never infer apply, import, state, endpoint-stimulation, or synthetic-data authority from a documentation request.
3. Use external tools through their CLI first. Refresh expired authentication and retry the original read-only command before reporting a connection blocker.
4. Do not initialize or plan against a production backend unless the user explicitly confirms that backend planning is safe. Never bypass a backend failure with a local state and present that result as the real stateful plan.
5. Use an isolated temporary copy with the backend removed for desired-resource expansion. Record that it is an empty-local-state plan and cannot prove update/delete actions.
6. Use `-refresh=false`, `-lock=false`, and `-input=false`. Never apply the generated plan.

## Evidence collection

1. Read repository instructions, root and module source, tfvars, lockfiles, tests, pipeline configuration, and operational documentation.
2. Read the destination wiki parent page and relevant sibling pages before drafting.
3. Run formatting, validation, and environment contract tests from the documented directories.
4. Capture two plan layers:
   - **Literal plan:** current feature gates and inputs. If backend access is prohibited, report it as unavailable rather than substituting local state.
   - **Expanded desired-resource plan:** isolated backend-free copy with approved feature gates enabled. Mark every prerequisite, data source, or unknown value that prevents a valid plan.
5. Query the target environment using read-only CLI calls for each planned resource class. Match by immutable identity and behavior, not name similarity alone. For alarms, compare metric namespace, metric names, dimensions, expressions, source service/function/topic, and operational purpose across the full relevant live inventory; do not rely on a short hand-maintained predecessor list.
6. Normalize provider/API representation differences before classification, including numeric strings versus numbers, omitted defaults versus explicit defaults, empty lists versus nulls, tag ordering, ARN formatting, and API-only computed fields. Representation-only differences are `Retain`, not `Update`.
7. Compare source, plan, live cloud evidence, and existing documentation. Treat conflicts as findings; do not silently choose one source.

## Classification

Classify each desired or retired resource:

- **Create:** desired identity is not found live.
- **Update:** the exact desired identity exists but properties differ.
- **Rename:** a verified live resource serves the same purpose under another name. Put its identity in `Previous name`; manual rename may require create, dependency cutover, verification, then delete.
- **Retain:** the exact desired identity and required properties already exist.
- **Delete:** a verified live resource is explicitly retired by source and operational evidence. Absence from an empty-state plan is not deletion evidence.
- **Blocked:** a prerequisite, authority, source conflict, or identity mapping is unresolved.

Never mark `Delete? = Yes` from name similarity, stale documentation, or because a resource is absent from desired configuration. Require explicit retirement evidence and dependency review.

## Required table

Use exactly these columns unless the user approves additions:

| # | Type | Previous name | Name | Description | Created | Updated | Deleted |
|---:|---|---|---|---|:---:|:---:|:---:|

Rules:

1. Include only resources that the reviewed Terraform execution will create, update, or delete. Exclude unchanged resources, disabled feature-gate inventories, blocked future resources, and speculative retirements.
2. Number rows from `1`, restarting only when the page has clearly separated project sections.
3. `Type` is a concise operator-facing category, such as `Alarm`, `Dashboard`, `Metric`, or `Log group`. Use `Alarm` for metric and composite alarms; use `Metric` for log metric filters and similar metric-producing resources. Put the precise cloud resource subtype in the detail section.
4. Leave `Previous name` blank only after verifying no predecessor is known. Use `Unknown - verification required` when evidence is incomplete.
5. `Name` is the exact post-execution resource identity, or the exact removed identity for a deletion row.
6. `Description` includes a concise purpose and action summary followed by a link to that row's unique detail anchor, for example `[Console creation details](#resource-12-metric-alarm-name)`. Every row must have a link. For every `Updated` row, put a concise `Before` and `After` summary in `Description`.
7. Put `X` in exactly one applicable change column. A replacement or rename normally requires separate created and deleted rows; do not mark a predecessor deleted unless the stateful reviewed plan explicitly removes it.
8. Do not include secrets, credentials, full state, sensitive plan values, customer data, or unnecessary account identifiers.
9. For every `Updated` row, include a field-level diff in its detail section. List only fields whose effective values change, separately identify verified unchanged safety-critical properties, and state whether the operation preserves identity and stored data.

## Per-resource details

After the table, add one uniquely anchored section for every row. A detail section must be sufficient for an authorized operator to create or safely process that resource in the cloud console without reverse-engineering Terraform. Include:

1. table row number, exact desired name, previous/live name, cloud service, resource type, target account/environment, and region;
2. direct console deep link when stable, plus the menu path from the service home as a fallback;
3. action classification: create, update, rename/cutover, retain/verify, delete, or blocked;
4. every non-sensitive console field required by the Terraform configuration, preserving exact case, units, dimensions, expressions, periods, thresholds, actions, tags, policies, retention, encryption, and lifecycle settings;
5. for `Updated`, separate `Before` and `After` blocks with only changed effective values, followed by a concise identity/data-preservation note only when needed for safe application;
6. dependencies and prerequisites with exact resource identities, creation order, and where operator-supplied secret values or ARNs must be selected without copying them into the document;
7. rename/cutover steps, including dependent alarms, dashboards, policies, subscriptions, and application references that must be repointed before predecessor deletion;
8. validation steps using both console inspection and narrow read-only CLI commands, including expected values or observable behavior;
9. rollback or recovery steps, and explicit stop conditions for missing permissions, prerequisites, uncertain identity, destructive diffs, or validation failures;
10. for `Deleted` rows, dependency-impact checks, backup/export requirements, disable-first guidance where supported, post-delete verification, and the exact evidence authorizing retirement;
11. source traceability: repository, exact commit SHA, Terraform root, module/resource address, module version, source file and line range, plan provenance, and live-evidence timestamp.

Use expandable sections or child detail pages when the destination supports them and the table would otherwise become unreadable. The row link must resolve to the exact section or child page after publication. Never use a generic shared link for multiple rows.

## Handoff metadata

Outside the required table, record:

- repository and exact commit SHA;
- Terraform root and module/version pins;
- target environment and region;
- literal and expanded plan summaries;
- whether state/backend was read;
- read-only cloud evidence timestamp;
- unresolved prerequisites and ownership decisions;
- explicit statement that the document does not authorize automated or manual mutation.

## Review and publication

1. Run the Terraform Specialist over source, plan provenance, live mappings, and every deletion claim.
2. Run the Documentation Reviewer and Confluence Documentation Specialist over the exact draft.
3. Show the user the exact page title, parent, and content before publication. Human-facing comments and replies use their separate approval gate (`rules/human-comment-reply-gate.md`).
4. Complete the configured wiki rollback-backup gate before any update, move, or destructive operation. For a new child page, verify parent identity, hierarchy, permissions, and create authority; preserve the draft locally until read-back succeeds.
5. Create or update through the CLI first, then re-read the page and verify title, parent, tables, row count, every row link, every detail target, and rendered content.
6. Keep toolkit indexes, the Terraform Specialist skill/agent, documentation, and generated tool surfaces synchronized. Show diffs before commit or push when requested.

## Completion report

Report separately:

- source and validation evidence;
- literal versus expanded plan results;
- live mappings and unresolved rows;
- page draft/publication/read-back state;
- toolkit and generated-surface synchronization state;
- every blocked external connection or skipped validator.
