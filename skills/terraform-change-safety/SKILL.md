---
name: terraform-change-safety
description: "Terraform/OpenTofu change-safety patterns: terraform_data provisioner lifecycle and triggers_replace vs input, end-to-end module variable wiring to every root, plan/apply verification heuristics, first-datapoint planning for IaC-provisioned alarms, drift codification, import-block lifecycle, byte-identical multi-env roots, templated observability bodies, idle-period dashboard semantics, metadata hygiene, fail-closed backup-before-apply, caller-side naming overrides for shared modules, and alias-qualified Lambda permission wiring. Use when writing or reviewing provisioners, operator-set module variables, alarms on new metrics, imports, destroys, or multi-environment roots."
license: MIT
metadata:
  author: dev-tools
  version: "1.2.0"
---

# Terraform Change Safety

Change-safety patterns for Terraform and OpenTofu stacks where a plan that looks correct still ships a silent defect: provisioners that never re-run, module variables that documentation tells operators to set but no root forwards, and alarms that false-fire at first deploy.

## When to Apply

- Writing or reviewing `terraform_data` (or `null_resource`) resources with provisioners.
- Adding a module variable that documentation or a runbook instructs a human to set.
- Reviewing plans/applies for changes that must actually execute something, not just update state.
- Provisioning CloudWatch (or equivalent) alarms on brand-new sparse custom metrics through IaC.
- Importing live resources, handing state between backends, or planning any destroy.
- Maintaining multi-environment roots, file-loaded dashboard/alarm bodies, or resource metadata (tags, descriptions, comments).
- Preparing a risky apply that needs a verified rollback point.

## terraform_data: triggers_replace vs input

`input` changes update the resource **in place**, and provisioners only run on resource **creation** — so a value passed via `input` never re-runs a `local-exec` provisioner. The operator believes the script executed when it silently did not. `terraform apply -replace=...` works as a workaround but is easy to forget and hides the intent from the code.

```hcl
resource "terraform_data" "cleanup" {
  # triggers_replace (not input): any change forces replacement, which is the
  # only lifecycle event that re-runs the creation provisioner.
  triggers_replace = {
    dry_run    = var.dry_run
    script_sha = filesha256("${path.module}/cleanup.ps1")
  }

  provisioner "local-exec" { ... }
}
```

Rule of thumb: `input` is for passing data through to `output`; `triggers_replace` is for anything a provisioner depends on. Verified behavior: with `triggers_replace`, flipping a flag plans a replacement and re-runs the provisioner; with `input`, the same change plans an in-place update and the provisioner is skipped.

## Module Variables Must Be Wired to Every Root

A module variable that documentation tells an operator to set is a defect until **every root** that instantiates the module declares and forwards it. Both failure modes are bad, and one is silent:

- `terraform apply -var alert_email_addresses=...` fails loudly with "Value for undeclared variable" when the root does not declare it.
- A `.tfvars` entry for an undeclared variable is **silently ignored** — the module default (for example `[]`) applies, zero resources are created, and the operator believes the safety step is done. `terraform validate` passes; unused module defaults and undeclared-variable tfvars entries are not errors.

When a change adds a module variable that a human is instructed to set, wire it end to end in the same change:

1. Declare the variable in every root that instantiates the module (all environments, not just the one the doc mentions).
2. Forward it in each root's module block (`alert_email_addresses = var.alert_email_addresses`).
3. Have the doc name the root directory the command runs in, and verify the documented command is executable verbatim from that directory.

Review heuristic: for each operator instruction of the form "set X and apply", trace the instruction's exact command path from the root module the operator actually runs Terraform in — reviewing the module diff and the docs in isolation makes both look correct while the wiring gap stays invisible.

## Plan/Apply Verification Heuristics

- After an apply that is supposed to run something (provisioner, script, seed step), verify the effect happened — do not infer execution from a clean apply. An in-place update on a provisioner-bearing resource is a warning sign, not a success signal.
- Before approving a plan, check that every changed value that must trigger execution appears as a **replacement** (or explicit action), not an in-place update.
- For operator-facing variables, run the documented command mentally (or actually) from the named root: undeclared `-var` fails loudly; undeclared tfvars entries fail silently.
- Hash script content into `triggers_replace` (`filesha256`) so editing the script also re-runs it.

## First-Datapoint Planning for IaC-Provisioned Alarms

An alarm on a brand-new sparse custom metric (for example, a success metric emitted only by a once-daily job) with `treat_missing_data = "breaching"` will false-fire at first deploy: the metric has never been published, so the entire evaluation range is missing and the alarm transitions INSUFFICIENT_DATA -> ALARM before the emitter's first scheduled run, then recovers after the first real datapoint.

Do not fix this by weakening steady-state settings:

- `treat_missing_data = "notBreaching"` removes the deploy false alarm but defeats the alarm's purpose — a dead emitter produces missing data forever and never alerts.
- Widening evaluation periods only delays the false alarm; the pre-first-run range is still all-missing.

Keep `breaching` (correct steady state) and neutralize the one-time deploy artifact explicitly, choosing one of:

1. Trigger the emitting job once immediately after `apply` (for example, invoke the function/job with its normal operation payload) so the first datapoint exists before the alarm's first evaluation window closes.
2. Seed one synthetic success datapoint (`aws cloudwatch put-metric-data`) as a post-apply step.
3. At minimum, document in the stack README that exactly one false alarm + recovery pair is expected within the first day, so on-call does not chase it.

General lesson: `breaching` missing-data handling and "metric is new" are inherently in conflict for the first evaluation window — every alarm on a newly created sparse custom metric needs a deliberate first-datapoint plan in the same change, not just correct steady-state settings. Investigation-side triage of this pattern lives in `tool-subagents/aws-alarm-investigator.md`.

Alarm sensitivity choices (`treat_missing_data = "breaching"` on liveness metrics) must be justified with real traffic evidence documented in a comment above the resource — e.g. the metric's actual datapoint history over a representative window — plus a revisit condition. When a reviewer challenges the evidence, re-query it fresh; never cite the numbers from a prior review.

## Non-Destructive Plan Discipline

Iterate configuration and import blocks until the plan is minimal and expected: the enumerated imports plus intended changes, **0 to destroy** unless destruction is the explicit intent. Enumerate expected imports/changes/destroys before reading plan output, save the reviewed plan to a file, apply that exact artifact, and require the post-apply plan to report "No changes". Any surviving diff after apply is a wiring or drift defect, not noise.

Drift found during review is codified at its source and imported — never planned over. A plan that strips live configuration (encryption, lifecycle rules, alarms, IAM statements) is a defect in the code, not cleanup.

## Import-Block Lifecycle

`import` blocks whose targets are already in state fail every subsequent plan, so an imports file is a one-shot artifact, not permanent configuration. Any file of import blocks must ship with an explicit removal plan — tracked as a follow-up in business language — executed immediately after the first successful apply. State-ownership handoffs (a locally-applied stack handed to a pipeline-owned backend) must name which state owns the resources before and after.

Destruction is sequenced to avoid capability gaps: destroy a superseded notification topic only **after** the apply that re-points alarms to its replacement, or alerts silently vanish in the gap.

## Byte-Identical Multi-Environment Roots

Shared root `.tf` files are byte-identical across environments; every environment difference lives in per-env `.auto.tfvars`. Enforce equality and no-env-leak with contract tests so an edit to one root fails the suite until mirrored exactly. Gate not-yet-ready environments with empty-value counts (`count = var.secret_name != "" ? 1 : 0`) so every pipeline stays green until the prerequisite exists and enabling is a one-line tfvars change.

## Templated Observability Bodies

Dashboard or alarm bodies loaded from files must be `templatefile()` templates fed by module outputs — never hardcode ARNs, account IDs, or names of resources a module in the same root manages, or a module-side rename silently drifts the widgets. Tests that read the body as static JSON need a renderer against pinned per-env values that fails on unresolved `${...}` placeholders.

An offline renderer written for tests implements only the template subset the fragments actually use — typically `${...}` with dotted paths, `%{ for }`, `%{ if }`, `jsonencode()`, and whitespace strip markers — not full expression evaluation. Bracket indexing (`section.items[0].id`) is the common casualty: it renders under the real engine and fails the suite as an unresolved reference. Model any value a template needs as a named field on the object being iterated rather than reaching into a collection by position, and validate every new template feature through the offline suite before pushing. Real-engine acceptance is necessary, not sufficient.

## Idle Periods Are Gaps, Not Zeros

A dashboard metric that holds its last observed value through idle periods misreads as live traffic, but forcing it to zero is the worse fix: zero latency reads as "fast" rather than "no data". Gap-filling alone also fails outright when the window contains no datapoints at all — there is nothing to fill between, so the widget renders empty with no axis, which looks like a broken dashboard rather than an idle system.

Separate the two metric kinds:

- **Counts and rates** — fill missing with zero *and* add a synthetic zero series across the window (`TIME_SERIES(0)` in CloudWatch metric math). The synthetic series anchors the time axis so the widget always renders, even before the emitter's first datapoint.
- **Latencies and other gauges** — mask by traffic instead of filling: publish the value only where the corresponding count is above zero, so idle periods render as genuine gaps. This needs an explicit reference from the gauge to its governing count metric, carried as a named field in the widget inventory.

The pairing matters: the count's synthetic baseline guarantees an axis, and the mask keeps the gauge honest. Reach for it whenever a change asks for "no stale flat lines" — filling the gauge is the intuitive move and the wrong one.

## Metadata Hygiene

No ticket numbers in resource tags, descriptions, code comments, file paths, or strings — tickets close, live cloud metadata and comments go stale. Use business/component language (`order-sync-mismatch-detector`, `warehouse-airflow-platform`). Route notifications to shared team topics, never stack-created topics with personal-email subscribers, and verify subscriber lists live before claiming routing works. When one instance of a metadata smell is found, sweep the whole change set (added diff lines and new file paths) for the class, not just the flagged line.

## Backup-Before-Apply, Fail-Closed

Before a risky apply: timestamped state backup plus read-only cloud CLI snapshots committed with the change, and an immutable versioned artifact pinned by version-id + checksum. A dedicated verification root runs **before** the apply root (phase-ordering file) and errors if the snapshot disappears or mutates — the pipeline fails closed rather than applying without a rollback point.

## Post-Apply Visual Evidence Without a Browser

When a change needs "the widget shows the request arrived" evidence, do not
reach for browser automation. `aws cloudwatch get-metric-widget-image` renders
any widget's `MetricWidget` JSON to a deterministic PNG straight from the
metrics API — scriptable in pipelines and attachable to PRs, chat, or a wiki
page. Pair the image with the underlying `get-metric-data` or Logs Insights
query result; the numbers are the proof, the image is the presentation.
Reserve interactive browser screenshots (via the agent environment's
sanctioned, permission-gated browser tools) for console states that have no
API-rendered equivalent. Third-party harnesses that require enabling remote
debugging on a real browser are rejected for this use: they expose the
operator's authenticated sessions to any local process.

## Claims Are Draft Until Re-Queried

Every "resources created/changed" claim is DRAFT until re-queried live under the owning state after the apply actually runs. PR bodies fossilize superseded design decisions — diff body claims against the latest commit specifically before relying on them.

## Shared-Module Naming: Compose by Default, Override in the Caller

Shared modules compose canonical resource names internally (`coalesce(var.name, "<org>-<type>-<env>-<purpose>")`) and expose a full-name override that defaults to `null`. Team- or product-specific naming conventions (for example a team's `TEAM-<App>` dashboard names) belong in the **calling root** via that override — never in the module default. Baking one team's convention into a shared module forces it on every consumer and makes the module non-promotable; the override keeps the module team-neutral while the root owns the exception, with a comment stating whose convention it is.

The override is all-or-nothing by design: callers take the composed convention or supply the complete final name. Do not add prefix/suffix knobs — they multiply naming variants and defeat the convention.

Renaming via the override plans as **1 add + 1 destroy** (name is the resource identity), so treat a rename like any replacement: confirm the plan shape is exactly the expected pair, and for `Put*`-style APIs that overwrite silently (PutDashboard, PutMetricAlarm, PutRule), verify the target name is unused in **every** account the root will ever apply to before the first apply — an existing same-name resource is clobbered without warning, including in environments applied later.

## Alias-Qualified Lambda Permissions

`aws_lambda_permission` for an alias-fronted integration must use the **bare** `function_name` plus an explicit `qualifier`; baking `name:alias` into `function_name` plans as a perpetual replacement on every run.

The Lambda console's function-level **Triggers** tab reads only the *unqualified* function resource policy, so a correctly alias-scoped permission shows nothing there — the trigger is visible under **Aliases → \<alias\> → Configuration → Permissions**, and that is the correct place to verify it. Do **not** "fix" the empty Triggers tab by adding an unqualified twin permission: the row appears, but the console cross-checks it against the integration URI (which targets the alias) and permanently flags a resource/path mismatch warning on the trigger. The twin is an anti-pattern — revert it if found; document the alias-page verification path in the stack README instead.

## Related

- `skills/terraform-specialist/SKILL.md` — mandatory routing for all Terraform requests
- `skills/terraform-specialist/references/validation-checklist.md` — full detection-rule checklist (style, pinning, state safety, multi-env, secrets, testing)
- `skills/terraform-specialist/references/stack-inventory.md` — what to establish about a consumer's shared modules, environment roots, and backends before judging a change
- `skills/terraform/SKILL.md` — general Terraform/OpenTofu authoring, testing, and CI/CD guidance
- `tool-subagents/terraform-specialist.md` — the read-only specialist that enforces these patterns
- `rules/release-safety.md` — deploy order, verification, and rollback discipline
- `skills/shell-scripting/SKILL.md` — the scripts that provisioners and wrappers invoke
- `skills/dag-glue-specialist/references/validation-checklist.md` — IaC checks for data pipelines
- `tool-subagents/aws-alarm-investigator.md` — known false-positive alarm patterns
