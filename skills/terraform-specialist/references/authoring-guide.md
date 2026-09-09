---
title: Terraform authoring guide - create, structure, document, test
tags: [terraform, opentofu, modules, authoring, terraform-docs, testing, terratest, contract-tests]
---

# Terraform Authoring Guide: Create, Structure, Document, Test

Use this reference when WRITING Terraform (new modules, roots, docs, or
tests), as opposed to reviewing it - the review rules live in
`validation-checklist.md`. Sources: HashiCorp module-development docs and
style guide, terraform-docs.io, AWS Prescriptive Guidance, Google Cloud
Terraform best practices, Gruntwork Terratest. For deeper framework detail
(native test syntax, Terratest patterns, CI templates) see
`skills/terraform/references/testing-frameworks.md` and
`skills/terraform/references/ci-cd-workflows.md`.

## Create

- Scaffold order for a new module: `LICENSE` -> `README.md` ->
  `variables.tf` -> `main.tf` -> `outputs.tf`; add `versions.tf` for the
  `terraform`/`required_providers` block. The root module is the only
  required element - the standard filenames are recommended even if empty.
- Every variable and output declares `type` and `description` (one or two
  sentences); descriptions are the source documentation tooling consumes.
- No provider or backend blocks inside shared modules - providers are
  inherited from (and configured only in) root modules.
- Don't wrap a single resource in a module: if the module can't be named
  differently from the resource type inside it, it isn't a new abstraction.
  Group logical relationships that enable a capability (network foundation,
  data tier, security controls).
- Composition over embedding: keep the module tree flat (one level of child
  modules); use dependency inversion - pass dependencies in as variables
  (VPC/subnet IDs) instead of detect-or-create logic inside the module; let
  the caller decide create-vs-lookup via data sources.
- Every resource in a reusable module gets at least one output referencing
  it, so consumers inherit correct dependency ordering.
- Workflow while authoring: `terraform get`/`init` -> `fmt` -> `validate` ->
  plan/apply from the owning root.

## Structure

- Root-module layout: `main.tf`, `variables.tf` (alphabetical), `outputs.tf`
  (alphabetical), `providers.tf`, `versions.tf`, `locals.tf`, `data.tf` (only
  if data sources are numerous), `backend.tf`, `terraform.tfvars`, and
  per-env values under `envs/<env>/terraform.tfvars`.
- Reusable-module repos add `examples/` and optionally `modules/` for nested
  submodules. A nested module with a README is externally usable; without
  one it's internal. Call nested modules by relative path
  (`./modules/name`) so they travel as one package. Nesting: one, at most
  two, levels - modules build on modules, not tunnel through them.
- Multi-env pattern: `modules/<service>/` holds the reusable service config;
  `environments/{dev,qa,prod}/` each hold a small root (`backend.tf` +
  `main.tf`) pinned to the default workspace. Keep a root under ~100
  resources, ideally a few dozen.
- Keep resources in `main.tf` until a logical group exceeds ~150 lines, then
  split into a purpose-named file (`iam.tf`). Support directories:
  `scripts/` (called by Terraform), `helpers/` (not called by Terraform),
  `files/` (static `file()` content), `templates/` (`.tftpl` for
  `templatefile()`).
- Naming: underscores in all Terraform identifiers (labels, variables,
  locals); hyphens are fine only in cloud-side `name` arguments. Singleton
  resources are `main` or `this`; singular names; never repeat the resource
  type in the label. Positive boolean names (`enable_x`); units in numeric
  names (`ram_size_gb`, binary prefixes for storage).
- Parameterize only what genuinely varies per instance/environment; repeated
  literals that don't vary belong in `locals`. Adding a defaulted variable
  is backward-compatible; removing one is not.
- Block layout: `count`/`for_each` first (blank line after), then arguments,
  then nested blocks, then `lifecycle`, then `depends_on`. Variable blocks:
  `type` -> `description` -> `default` -> `sensitive` -> `validation`.
- Registry-ready repos: name `terraform-<provider>-<name>`, SemVer `vX.Y.Z`
  tags, module code at repo root - follow it even before publishing.

## Document

- README.md required on the root module and every externally-facing nested
  module: purpose, usage snippet, `examples/` reference, optional diagram.
  Module root holds only `.tf` files + repo metadata; deeper docs go in
  `docs/`.
- Generate the Requirements/Providers/Inputs/Outputs tables with
  terraform-docs instead of hand-writing them:
  `terraform-docs markdown table . --output-file README.md --output-mode inject`
  between `<!-- BEGIN_TF_DOCS -->` / `<!-- END_TF_DOCS -->` markers; wire the
  terraform-docs CI action so tables can't drift from `variables.tf`.
- `examples/` is living documentation and the proof the module works: each
  example has its own README and is exercised in CI. Example `module` blocks
  reference the module by external source address (registry/VCS ref), never
  a relative path - relative-path examples silently break when copied into
  consumer repos.
- Version modules with SemVer tags (registries ignore non-version tags);
  consumers pin `~>` major constraints. Keep a CHANGELOG and a
  CODEOWNERS/OWNERS record of module ownership.

## Test

Testing pyramid, bottom to top:

1. Static: `terraform fmt` + `terraform validate` + tflint + checkov, all in
   pre-commit hooks so violations never reach CI.
2. Unit: `terraform test` (>= 1.6) with `command = plan` run blocks and
   mocked providers (>= 1.7) in `tests/*.tftest.hcl` - `mock_provider` with
   `mock_resource` defaults, or targeted `override_resource`/`override_data`/
   `override_module` stubs; `test { parallel = true }` when runs are
   independent.
3. Integration: `terraform test` with `command = apply` (auto-destroys at
   file end) against disposable accounts; Terratest (Go) when apply-mode
   assertions aren't expressive enough - `terraform.InitAndApply` +
   live-resource checks (HTTP/SDK/SSH) with `defer terraform.Destroy`
   immediately after apply.
4. Contract tests on module interfaces - pick the mechanism by what is being
   asserted:
   - caller-supplied input shape/format -> `variable { validation {} }`
     (runs before plan, blocking);
   - assumption about an upstream resource/data source before building on
     it -> `lifecycle { precondition {} }` (plan-time, blocking);
   - guarantee the resource itself must uphold once it exists, protecting
     future refactors -> `lifecycle { postcondition {} }` (post-apply/read,
     blocking);
   - ongoing whole-system health that must not fail the run ->
     `check {}` block with scoped data source (non-blocking, monitoring
     style).
   Use `expect_failures = [var.x]` in `.tftest.hcl` to positively assert
   that bad input is rejected by a validation block.
5. Post-apply smoke: `check` blocks against live endpoints for what HCL can
   express; external probes (requests, datastore queries, metric/log
   evidence, rendered dashboards, alarm cycles) for the rest - reported per
   the specialist's post-apply test report contract (scenario matrix,
   resource links, verbatim requests).
