# Learnings Index

Fast-scan index of every committed learning. **Read this at session start** (per `skills/error-driven-learning/SKILL.md`) to skip directly to the happy path on previously-solved problems.

**Format:** one line per learning — link, one-sentence summary, and tags for keyword matching.

**Update rule:** whenever `learnings/<new>.md` is added, append a line here in the same commit. When a learning is superseded, mark the old line with `~~strikethrough~~` and note the replacement.

---

## Index

### Architecture

- [`llm-toolkit-junction-architecture.md`](./llm-toolkit-junction-architecture.md) — Multi-repo LLM tooling via Windows junctions: zero duplication, zero git traces (`llm-toolkit`, `junctions`, `gitignore`, `multi-repo`, `windows`).
- [`llm-adaptive-skill-loading.md`](./llm-adaptive-skill-loading.md) — Progressive/two-tier skill loading keeps session context under 1 KB (`skills`, `context-optimization`, `progressive-disclosure`).
- [`gold-schema-drift-breaks-notebooks.md`](./gold-schema-drift-breaks-notebooks.md) — Gold schema changes break notebooks with hardcoded column names; check dynamic column generation and pt-BR translation maps (`notebook`, `gold`, `schema`, `column-names`, `data-pipeline`, `drift`).

### Security

- [`notebook-hardcoded-aws-credentials.md`](./notebook-hardcoded-aws-credentials.md) — Notebook hardcoded AWS credentials must use `runtime_config.json`; never print secrets in notebook outputs (`notebook`, `aws`, `credentials`, `security`, `runtime-config`, `s3`).

### API

- [`transparency-portal-api.md`](./transparency-portal-api.md) — Portal da Transparência API auth, endpoint catalog, and pagination (`transparency-portal`, `api`, `brazil`, `cgu`, `sanctions`, `ceis`, `cnep`, `cepim`).

### Notebooks / Toolchain

- [`notebook-embedded-plotly-output-size.md`](./notebook-embedded-plotly-output-size.md) — Plotly choropleth outputs embedded in notebooks inflate files to 100MB+, blocking `git push`; run `clear_notebook_outputs.py` before every commit (`notebook`, `plotly`, `outputs`, `file-size`, `git`, `push`, `ipynb`, `clear-outputs`).
- [`notebook-patch-anchor-mismatch-ptbr.md`](./notebook-patch-anchor-mismatch-ptbr.md) — pt-BR notebook patch anchors silently miss when `except`/`print` strings were never translated; verify exact cell content before writing anchors (`notebook`, `patch`, `anchor`, `ptbr`, `translation`, `scripted-edit`, `silent-failure`).
- [`notebook-timestamp-noise-in-diff.md`](./notebook-timestamp-noise-in-diff.md) — `ExecuteTime` metadata creates large git diffs with zero source change; detect with source-only comparison and revert before committing (`notebook`, `metadata`, `ExecuteTime`, `git`, `diff`, `noise`, `revert`).
- [`powerpoint-template-visual-qa.md`](./powerpoint-template-visual-qa.md) — Official-template PPTX decks are not done until PowerPoint/PDF renders are visually inspected for logo fidelity, text overflow, and placeholder drift (`powerpoint`, `pptx`, `template`, `visual-qa`, `pdf-export`).

### Data Pipeline

- [`geojson-property-language-drift.md`](./geojson-property-language-drift.md) — GeoJSON property names drift to whichever notebook language ran last; pick one canonical language and generate from a dedicated script, not a notebook side effect (`geojson`, `qgis`, `ptbr`, `english`, `assets`, `schema`, `drift`, `presentation-assets`).

### AWS / CloudWatch / Monitoring

- [`alarm-e2e-must-validate-the-notification-path.md`](./alarm-e2e-must-validate-the-notification-path.md) — CloudWatch alarms can show valid state transitions while every notification action is empty, so E2E tests must check delivery, not just alarm history (`cloudwatch`, `alarms`, `sns`, `e2e-testing`, `notification`, `silent-failure`).
- [`apigw-trigger-tab-cannot-represent-alias-scoped-permissions.md`](./apigw-trigger-tab-cannot-represent-alias-scoped-permissions.md) — The Lambda console Triggers tab reads only the unqualified function policy, so an alias-scoped API Gateway integration never shows there even when it works (`lambda`, `api-gateway`, `alias`, `console`, `permission`).
- [`aws-lambda-timeouts-metric-does-not-exist.md`](./aws-lambda-timeouts-metric-does-not-exist.md) — `AWS/Lambda` publishes no `Timeouts` metric, so alarms and widgets built on it apply and read back clean while staying permanently silent; back timeouts with a log metric filter instead (`cloudwatch`, `lambda`, `timeouts`, `phantom-metric`, `metric-filter`).
- [`aws-sso-device-login-cannot-run-unattended.md`](./aws-sso-device-login-cannot-run-unattended.md) — AWS SSO device-code login is an interactive OAuth grant an agent must hand to the user immediately rather than try to complete itself (`aws`, `sso`, `oidc`, `device-authorization`, `credentials`).
- [`cloudwatch-console-deep-links-in-wiki-tables.md`](./cloudwatch-console-deep-links-in-wiki-tables.md) — CloudWatch console URLs use `~`-based fragment encoding that breaks Markdown links; author deep-link tables in HTML and document the per-account sign-in caveat (`cloudwatch`, `console-url`, `deep-link`, `dashboards`, `alarms`).
- [`json-validity-does-not-prove-metric-math-validity.md`](./json-validity-does-not-prove-metric-math-validity.md) — A valid-JSON CloudWatch dashboard can still contain invalid metric math (bad `IF()` arity, dangling operators) that silently renders no data; validate arity and balance, not just JSON syntax (`cloudwatch`, `json`, `metric-math`, `validation`, `arity`).
- [`no-data-and-zero-are-different-in-monitoring.md`](./no-data-and-zero-are-different-in-monitoring.md) — Conflating "no datapoint" with "zero" breaks dashboards and alarms; zero-fill counts/rates but leave latencies unfilled, and use `treat_missing_data = breaching` for silence-detection alarms (`cloudwatch`, `metrics`, `zero`, `no-data`, `treat-missing-data`).
- [`putmetricalarm-putdashboard-silently-overwrite-same-name.md`](./putmetricalarm-putdashboard-silently-overwrite-same-name.md) — CloudWatch alarms and dashboards are upserts keyed by name, so a Terraform "1 to add" plan can silently overwrite a live same-name resource with no warning (`cloudwatch`, `alarm`, `dashboard`, `terraform`, `upsert`).
- [`verify-metric-dimensions-from-source-before-reconciling.md`](./verify-metric-dimensions-from-source-before-reconciling.md) — An empty `get-metric-data` result looks identical to "no traffic yet"; always confirm dimension names against the emitting source or a proven alarm/dashboard before trusting the result (`cloudwatch`, `get-metric-data`, `dimensions`, `validation`).

### Terraform / IaC

- [`hcl-variable-descriptions-interpolate-dollar-brace.md`](./hcl-variable-descriptions-interpolate-dollar-brace.md) — Terraform variable `description` strings are ordinary HCL and interpolate `${...}`; use angle-bracket placeholders like `<org>` in docs instead (`terraform`, `hcl`, `variables`, `description`, `interpolation`).
- [`lambda-permission-alias-belongs-in-qualifier.md`](./lambda-permission-alias-belongs-in-qualifier.md) — Putting `name:alias` in `aws_lambda_permission`'s `function_name` causes a perpetual replacement diff; the alias belongs in the dedicated `qualifier` argument (`terraform`, `lambda`, `permission`, `alias`, `qualifier`).
- [`narrow-gitignore-patterns-miss-state-files.md`](./narrow-gitignore-patterns-miss-state-files.md) — Narrow `.gitignore` patterns like `**/terraform.tfstate` miss real backup/recovery state file names; use broad `*.tfstate*` wildcards plus a pre-commit guard (`gitignore`, `terraform`, `state`, `secrets`, `patterns`).
- [`parallel-stack-parity-env-flip-needs-iam-first.md`](./parallel-stack-parity-env-flip-needs-iam-first.md) — Flipping a legacy service's shared config to point at a new target fails silently if the old execution role lacks IAM on the new target; grant access before flipping config (`lambda`, `sqs`, `iam`, `parallel-stack`, `cutover`).
- [`reconcile-applied-drift-before-committing-in-multi-copy-stacks.md`](./reconcile-applied-drift-before-committing-in-multi-copy-stacks.md) — In multi-copy Terraform layouts, `git status` can show applied-but-uncommitted drift from a prior session; classify and commit it separately before committing a new fix (`terraform`, `git`, `worktree`, `drift`, `commit-hygiene`).
- [`terraform-allowed-account-ids-invalid-in-backend-block.md`](./terraform-allowed-account-ids-invalid-in-backend-block.md) — `allowed_account_ids` is a provider argument, not a backend argument; placing it in the S3 backend block fails `terraform init` (`terraform`, `backend`, `s3`, `provider`, `init`).
- [`terraform-init-git-modules-fail-on-deep-windows-paths.md`](./terraform-init-git-modules-fail-on-deep-windows-paths.md) — `terraform init` on git-sourced modules fails on deep Windows paths ("$GIT_DIR too big"); validate from a short scratch-path copy (`terraform`, `windows`, `git`, `init`, `path-length`).
- [`terraform-sso-token-refresh-fails-when-cli-works.md`](./terraform-sso-token-refresh-fails-when-cli-works.md) — Terraform's Go SDK can fail AWS SSO token refresh (`InvalidGrantException`) even when the AWS CLI works; export the CLI's credentials into env vars instead (`terraform`, `aws-sso`, `credentials`, `s3-backend`).
- [`terraform-state-migration-must-verify-target-key-unused.md`](./terraform-state-migration-must-verify-target-key-unused.md) — Before migrating Terraform state, verify the target bucket+key isn't claimed by another root's state, pending migration, or open PR (`terraform`, `state`, `migration`, `s3`, `collision`).
- [`terraform-targeted-apply-root-needs-warning.md`](./terraform-targeted-apply-root-needs-warning.md) — A Terraform root whose untargeted plan would create resources another root owns must be marked targeted-apply-only with a written README warning (`terraform`, `targeted-apply`, `resource-ownership`, `plan`).

### Confluence / Wiki

- [`confluence-mcp-does-not-expose-page-version-number.md`](./confluence-mcp-does-not-expose-page-version-number.md) — The Confluence MCP `getConfluencePage` result has no numeric version field for rollback manifests; derive it from the write response instead (`confluence`, `mcp`, `version`, `backup`, `rollback`).
- [`confluence-mcp-parallel-getpage-can-return-wrong-page.md`](./confluence-mcp-parallel-getpage-can-return-wrong-page.md) — Parallel Confluence MCP `getConfluencePage` calls in one tool block can both return the first page's body; fetch sequentially or verify the `id` in each result (`confluence`, `mcp`, `parallel-tool-calls`).
- [`confluence-page-archive-is-ui-only-verify-via-status.md`](./confluence-page-archive-is-ui-only-verify-via-status.md) — Confluence page archive has no API/MCP surface; hand the user the click path and verify completion via an API readback of `status` (`confluence`, `archive`, `mcp`, `ui-only`, `verification`).
- [`confluence-storage-normalization-and-link-rewriting-on-save.md`](./confluence-storage-normalization-and-link-rewriting-on-save.md) — Confluence rewrites entities and same-site links on save, so readbacks never byte-match; validate semantically (heading counts, fragment presence) instead (`confluence`, `storage-format`, `entity-encoding`, `readback-validation`).

### Git / Windows / Shell

- [`git-bash-path-conversion-breaks-aws-cli-args.md`](./git-bash-path-conversion-breaks-aws-cli-args.md) — Git Bash's MSYS layer rewrites slash-prefixed arguments like CloudWatch log group names into Windows paths; set `MSYS_NO_PATHCONV=1` (`git-bash`, `msys`, `windows`, `aws-cli`, `path-conversion`).
- [`git-c-worktree-relative-path-lands-in-repo-root.md`](./git-c-worktree-relative-path-lands-in-repo-root.md) — `git -C <repo> worktree add <relative-path>` resolves the relative path against the repo, not your shell's cwd; always pass an absolute path (`git`, `worktree`, `relative-path`, `scratchpad`).
- [`lagging-branch-checkout-looks-like-broken-clone.md`](./lagging-branch-checkout-looks-like-broken-clone.md) — A checkout of a lagging branch can show sparse or empty directories that look like missing content; compare `git rev-list --count` against a reference branch before assuming corruption (`git`, `branch`, `checkout`, `stale-tree`, `verification`).
- [`powershell-remove-item-recurse-deletes-junction-targets.md`](./powershell-remove-item-recurse-deletes-junction-targets.md) — PowerShell 5.1's `Remove-Item -Recurse -Force` on an NTFS junction deletes the target directory's contents, not just the link; check for reparse points first (`powershell`, `junction`, `symlink`, `remove-item`, `data-loss`).
- [`stale-local-clone-false-negative-search.md`](./stale-local-clone-false-negative-search.md) — A zero-match grep in a stale local clone looks identical to "code was removed"; fetch and compare `git rev-list --count`, then search the remote ref directly with `git grep <ref>` (`git`, `grep`, `stale-clone`, `cross-repo`, `false-negative`).
- [`windows-readonly-dir-blocks-git-checkout.md`](./windows-readonly-dir-blocks-git-checkout.md) — "Permission denied" on Windows `git checkout` is usually the ReadOnly directory attribute, not symlinks; clear it recursively and mark link surfaces skip-worktree (`windows`, `git`, `checkout`, `readonly`, `permission-denied`).

### Agent Behavior / Validation

- [`agent-self-reported-counts-are-not-evidence.md`](./agent-self-reported-counts-are-not-evidence.md) — LLM agents miscount pattern occurrences in large files; verify any count that gates a decision with a deterministic command (`rg`/`jq`), not a narrative summary (`llm`, `agent`, `verification`, `count`, `audit`).
- [`architecture-absence-may-be-a-deliberate-decision.md`](./architecture-absence-may-be-a-deliberate-decision.md) — An absent architecture element (e.g. no gateway in front of a function) may be a deliberate, undocumented decision, not a gap; check caller config and history before "filling" it (`architecture-decision`, `negative-decision`, `documentation`, `latency`).
- [`browser-harness-intake-rejected.md`](./browser-harness-intake-rejected.md) — A browser-automation skill that requires CDP access to the user's real logged-in browser is a structural security hazard; reject it and cover the use case with sanctioned, scriptable alternatives (`external-skill-intake`, `browser`, `cdp`, `security`, `rejection`).
- [`diagnose-live-vs-source-before-assuming-source-causes-symptom.md`](./diagnose-live-vs-source-before-assuming-source-causes-symptom.md) — When a live resource and its IaC source disagree, compare live-vs-source directly before assuming source caused the symptom; drift can mean live is right and source is stale (`terraform`, `drift`, `live`, `source`, `root-cause`).
- [`find-generator-not-just-instances.md`](./find-generator-not-just-instances.md) — A bad pattern repeated across many generated files means a shared generator is producing it; trace instances back to the template and fix both, or the pattern keeps recurring (`templates`, `generator`, `pattern`, `root-cause`, `regression`).
- [`hanging-validator-trains-agents-to-skip-validation.md`](./hanging-validator-trains-agents-to-skip-validation.md) — A hanging validator (command-line argument overflow) is worse than no validator: agents learn to skip it; fix the root cause (e.g. `xargs`) and prove it with a large synthetic input (`validation`, `hang`, `timeout`, `xargs`, `testing`).

---

## Scanning Tips

- Match by **tags** first (grep the tags line) — fastest filter.
- Match by **title** second.
- If multiple learnings match, read the newest (`created:` date) first.
- If nothing matches, proceed normally and watch for capture triggers (see `skills/error-driven-learning/SKILL.md` § Phase 2).

## Hygiene Checklist When Adding A Learning

- [ ] File created under `learnings/<kebab-case>.md` following the template in `learnings/README.md`.
- [ ] Frontmatter has `title`, `category`, `created`, `tags`.
- [ ] Body has `# Problem`, `# Failed Approaches`, `# Solution`, `# Why` sections.
- [ ] Line appended to the appropriate category above in this INDEX.
- [ ] User approval gate passed (per `workflows/capture-learning.md` §6).
- [ ] Committed with a descriptive message.
