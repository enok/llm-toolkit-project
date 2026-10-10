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
- [`linkedin-composer-file-inputs-belong-to-messaging-overlay.md`](./linkedin-composer-file-inputs-belong-to-messaging-overlay.md) — `input[id^="attachment-input"]` on LinkedIn belongs to the messaging overlay; forwarding a file there attaches it to a chat draft, so scope queries to the "Create post" dialog (`linkedin`, `composer`, `messaging-overlay`, `file-input`, `hazard`).

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

### Publishing / Browser Automation

- [`medium-paste-splits-code-blocks-at-blank-lines.md`](./medium-paste-splits-code-blocks-at-blank-lines.md) — A blank line inside a pasted `<pre>` splits one file into several Medium code boxes; put a single space on blank lines before pasting (`medium`, `code-blocks`, `blank-lines`, `paste`, `html`).
- [`medium-topic-autocomplete-swaps-typed-topic.md`](./medium-topic-autocomplete-swaps-typed-topic.md) — Medium topic input adds the first suggestion on Enter and a mouse click closed the dropdown without adding; dispatch a DOM click on the exact suggestion and verify the chip (`medium`, `publish-dialog`, `topics`, `autocomplete`, `dom-click`).
- [`linkedin-cannot-attach-media-after-publishing.md`](./linkedin-cannot-attach-media-after-publishing.md) — LinkedIn cannot add media to a published post; attach the image before Post. If it already went out, post again with the image and point the old post to it with a "More..." line; delete the old post only if asked (`linkedin`, `media`, `publishing`, `repost`, `more-pointer`, `back-links`).
- [`browser-extension-file-upload-requires-session-staged-path.md`](./browser-extension-file-upload-requires-session-staged-path.md) — The browser file-upload tool accepted only the session-staged uploads path, not container output or Windows paths (`browser-automation`, `file-upload`, `session-staging`, `drag-and-drop`, `datatransfer`).
- [`linkedin-image-change-needs-new-post-with-more-pointer.md`](./linkedin-image-change-needs-new-post-with-more-pointer.md) — LinkedIn's editor changes a published post's text and alt text only; for a new image publish a new post, edit a "More... <url>" line into the old post, repoint links, delete only if asked (`linkedin`, `edit-post`, `image-change`, `more-pointer`, `back-links`).
- [`medium-editor-code-block-hash-needs-pre-content-innertext.md`](./medium-editor-code-block-hash-needs-pre-content-innertext.md) — Hash Medium editor code blocks from `pre .pre--content` innerText (nbsp to space, trim, single-space lines to empty), not `pre.innerText`, and compare 12-hex SHA-256 prefixes with the source (`medium`, `code-blocks`, `sha256`, `verification`, `innertext`).
- [`medium-published-story-link-edit-via-toolbar-link-button.md`](./medium-published-story-link-edit-via-toolbar-link-button.md) — To change one link in a published Medium story select the text, click the toolbar link button twice (remove, then "Paste or type a link"), press Enter and read the anchor back (`medium`, `edit-published-story`, `link`, `toolbar`).
- [`auto-mode-classifier-denies-final-publish-click.md`](./auto-mode-classifier-denies-final-publish-click.md) — The browser tool's auto-mode classifier denied the final "Save and publish" click after content approval; an explicit go that names the click let it through (`auto-mode`, `permission-classifier`, `publish-click`, `medium`).
- [`medium-change-topics-popover-enter-adds-first-suggestion.md`](./medium-change-topics-popover-enter-adds-first-suggestion.md) — In a published story's Change topics popover neither mouse nor DOM clicks add a suggestion; type until the exact topic is first, press Enter, read the chips back; normalise curly quotes and no-break spaces before comparing editor text (`medium`, `topics`, `change-topics`, `typeahead`, `normalisation`).
- [`posts-need-aida-structure-and-role-positioning.md`](./posts-need-aida-structure-and-role-positioning.md) — Study articles and posts follow Attention, Interest, Desire, Action (hook inside the "see more" cut, problem, value and results, one next step) and titles lead with the highest-level concept the body supports; show the stage map with the `NOT POSTED` draft (`linkedin`, `medium`, `aida`, `narrative-structure`, `title`, `positioning`, `engagement`).

### Diagrams

- [`github-mermaid-custom-font-clips-labels.md`](./github-mermaid-custom-font-clips-labels.md) — GitHub's Mermaid viewer clips label ends when the init asks for a font viewers lack; commit Arial sources and swap fonts only at PNG render time (`mermaid`, `github`, `diagram`, `font-family`, `rendering`).
- [`mermaid-classdiagram-styling-needs-style-statements.md`](./mermaid-classdiagram-styling-needs-style-statements.md) — In mermaid-cli 11 classDiagram, `cssClass`/`:::` did not colour boxes; use one `style` line per class and put annotations on their own line (`mermaid`, `class-diagram`, `styling`, `style-statement`, `annotations`).
- [`mermaid-subgraph-direction-ignored-with-external-links.md`](./mermaid-subgraph-direction-ignored-with-external-links.md) — A Mermaid subgraph `direction` is ignored when its nodes link outside it, collapsing layouts into strips (`mermaid`, `flowchart`, `subgraph`, `direction`, `layout`).

### Build / CI

- [`cloud-sandbox-egress-blocks-registries-verify-on-user-machine.md`](./cloud-sandbox-egress-blocks-registries-verify-on-user-machine.md) — Cloud sandbox egress blocked npm, Maven Central and GitHub; run definitive builds on the user's machine with user-local toolchains (`sandbox`, `egress`, `registries`, `http-403`, `verification`).
- [`typescript-7-needs-explicit-node-types-and-quoted-test-globs.md`](./typescript-7-needs-explicit-node-types-and-quoted-test-globs.md) — TypeScript 7 no longer auto-includes `@types`; add `@types/node` + `"types": ["node"]`, avoid removed options, and quote the `node --test` glob (`typescript`, `nodejs`, `tsconfig`, `node-test`, `glob`).
- [`branch-protection-required-checks-need-stable-job-names.md`](./branch-protection-required-checks-need-stable-job-names.md) — Add required status checks after the first CI run and use job names that never change (no matrix-expanded names) (`github`, `branch-protection`, `ci`, `status-checks`, `job-names`).
- [`required-checks-must-follow-removed-ci-jobs.md`](./required-checks-must-follow-removed-ci-jobs.md) — Drop a removed CI job from the branch-protection required checks before merging the PR that deletes it, or the PR waits forever for a check that never reports (`github`, `branch-protection`, `ci`, `required-checks`, `language-set`).
- [`gh-api-array-fields-for-required-checks.md`](./gh-api-array-fields-for-required-checks.md) — `gh api -f contexts[]` did not update required status checks; send a JSON body with `--input` to the PATCH `required_status_checks` endpoint (`github`, `gh-cli`, `branch-protection`, `required-status-checks`, `input`).
- [`ci-run-hung-force-cancel.md`](./ci-run-hung-force-cancel.md) — A CI job that hangs with no output needs a force-cancel through the Actions API, then a rerun (`github-actions`, `ci`, `hung-job`, `force-cancel`, `rerun`).
- [`quality-gate-blocks-unclassified-suffixes.md`](./quality-gate-blocks-unclassified-suffixes.md) — The changed-code quality gate blocks file types it cannot classify (`.html`, `.mmd`, `.gitattributes`); store fixtures as `.txt` with a `{{SPACE}}` marker for significant whitespace (`quality-gate`, `ci`, `fixtures`, `suffix`, `unrecognized-file-type`).
- [`gh-graphql-blocked-in-cloud-sandbox.md`](./gh-graphql-blocked-in-cloud-sandbox.md) — `gh pr create` fails in the cloud container (GraphQL blocked, repository not attached); run `gh` for PR work on the user's machine (`gh-cli`, `graphql`, `cloud-sandbox`, `pull-request`).

### Git / Windows / Shell

- [`git-bash-path-conversion-breaks-aws-cli-args.md`](./git-bash-path-conversion-breaks-aws-cli-args.md) — Git Bash's MSYS layer rewrites slash-prefixed arguments like CloudWatch log group names into Windows paths; set `MSYS_NO_PATHCONV=1` (`git-bash`, `msys`, `windows`, `aws-cli`, `path-conversion`).
- [`git-c-worktree-relative-path-lands-in-repo-root.md`](./git-c-worktree-relative-path-lands-in-repo-root.md) — `git -C <repo> worktree add <relative-path>` resolves the relative path against the repo, not your shell's cwd; always pass an absolute path (`git`, `worktree`, `relative-path`, `scratchpad`).
- [`lagging-branch-checkout-looks-like-broken-clone.md`](./lagging-branch-checkout-looks-like-broken-clone.md) — A checkout of a lagging branch can show sparse or empty directories that look like missing content; compare `git rev-list --count` against a reference branch before assuming corruption (`git`, `branch`, `checkout`, `stale-tree`, `verification`).
- [`powershell-remove-item-recurse-deletes-junction-targets.md`](./powershell-remove-item-recurse-deletes-junction-targets.md) — PowerShell 5.1's `Remove-Item -Recurse -Force` on an NTFS junction deletes the target directory's contents, not just the link; check for reparse points first (`powershell`, `junction`, `symlink`, `remove-item`, `data-loss`).
- [`stale-local-clone-false-negative-search.md`](./stale-local-clone-false-negative-search.md) — A zero-match grep in a stale local clone looks identical to "code was removed"; fetch and compare `git rev-list --count`, then search the remote ref directly with `git grep <ref>` (`git`, `grep`, `stale-clone`, `cross-repo`, `false-negative`).
- [`windows-readonly-dir-blocks-git-checkout.md`](./windows-readonly-dir-blocks-git-checkout.md) — "Permission denied" on Windows `git checkout` is usually the ReadOnly directory attribute, not symlinks; clear it recursively and mark link surfaces skip-worktree (`windows`, `git`, `checkout`, `readonly`, `permission-denied`).
- [`powershell-set-clipboard-ashtml-mangles-non-ascii.md`](./powershell-set-clipboard-ashtml-mangles-non-ascii.md) — Windows PowerShell 5.1 `Set-Clipboard -AsHtml` mangles non-ASCII characters; entity-encode them before the clipboard write (`powershell`, `clipboard`, `html`, `non-ascii`, `encoding`).
- [`device-commit-to-existing-path-can-keep-stale-bytes.md`](./device-commit-to-existing-path-can-keep-stale-bytes.md) — A device commit to an existing path once kept the old bytes; write each version to a fresh filename and verify a marker on the machine (`device-bridge`, `file-transfer`, `stale-content`, `fresh-filename`, `verification`).
- [`powershell-gh-jq-quoting-breaks.md`](./powershell-gh-jq-quoting-breaks.md) — Windows PowerShell breaks `gh --jq` quoting ("accepts 1 arg(s), received 5"); pipe `gh api` output to `ConvertFrom-Json` instead (`powershell`, `github-cli`, `jq`, `quoting`, `windows`).
- [`powershell-redirect-writes-utf16.md`](./powershell-redirect-writes-utf16.md) — A Windows PowerShell 5.1 redirect wrote a script as UTF-16 and Python could not read it; redirect through `cmd /c` or use `Out-File` with an explicit encoding (`powershell`, `redirect`, `utf-16`, `encoding`, `out-file`).
- [`windows-text-stdout-crlf.md`](./windows-text-stdout-crlf.md) — Windows text-mode stdout writes CRLF, which broke subprocess output assertions; normalise newlines in the test helper before asserting (`windows`, `crlf`, `newline`, `subprocess`, `test-helpers`).
- [`device-bridge-transfer-reencodes-png-compare-decoded-pixels.md`](./device-bridge-transfer-reencodes-png-compare-decoded-pixels.md) — A device-bridge transfer can re-encode a PNG: byte hashes differ while pixels match, so compare decoded pixels (`device-bridge`, `png`, `re-encode`, `checksum`, `pixels`).
- [`synced-folder-fresh-file-staging-refused-as-hardlinked.md`](./synced-folder-fresh-file-staging-refused-as-hardlinked.md) — Staging a file just written into a cloud-synced folder can be refused as "hardlinked"; wait for the sync to settle and retry the same file, no extra copy (`device-bridge`, `staging`, `cloud-sync`, `hardlink`).

### Agent Behavior / Validation

- [`agent-self-reported-counts-are-not-evidence.md`](./agent-self-reported-counts-are-not-evidence.md) — LLM agents miscount pattern occurrences in large files; verify any count that gates a decision with a deterministic command (`rg`/`jq`), not a narrative summary (`llm`, `agent`, `verification`, `count`, `audit`).
- [`architecture-absence-may-be-a-deliberate-decision.md`](./architecture-absence-may-be-a-deliberate-decision.md) — An absent architecture element (e.g. no gateway in front of a function) may be a deliberate, undocumented decision, not a gap; check caller config and history before "filling" it (`architecture-decision`, `negative-decision`, `documentation`, `latency`).
- [`browser-harness-intake-rejected.md`](./browser-harness-intake-rejected.md) — A browser-automation skill that requires CDP access to the user's real logged-in browser is a structural security hazard; reject it and cover the use case with sanctioned, scriptable alternatives (`external-skill-intake`, `browser`, `cdp`, `security`, `rejection`).
- [`diagnose-live-vs-source-before-assuming-source-causes-symptom.md`](./diagnose-live-vs-source-before-assuming-source-causes-symptom.md) — When a live resource and its IaC source disagree, compare live-vs-source directly before assuming source caused the symptom; drift can mean live is right and source is stale (`terraform`, `drift`, `live`, `source`, `root-cause`).
- [`find-generator-not-just-instances.md`](./find-generator-not-just-instances.md) — A bad pattern repeated across many generated files means a shared generator is producing it; trace instances back to the template and fix both, or the pattern keeps recurring (`templates`, `generator`, `pattern`, `root-cause`, `regression`).
- [`hanging-validator-trains-agents-to-skip-validation.md`](./hanging-validator-trains-agents-to-skip-validation.md) — A hanging validator (command-line argument overflow) is worse than no validator: agents learn to skip it; fix the root cause (e.g. `xargs`) and prove it with a large synthetic input (`validation`, `hang`, `timeout`, `xargs`, `testing`).
- [`validators-must-scan-rendered-html-for-markdown-leftovers.md`](./validators-must-scan-rendered-html-for-markdown-leftovers.md) — Markdown left in converted HTML (e.g. `](http`) rendered as raw text on Medium; validators must scan the rendered HTML for leftovers (`validation`, `markdown`, `html`, `converter`, `medium`).

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
