# Learnings Index

Fast-scan index of every committed learning. **Read this at session start** (per `skills/error-driven-learning/SKILL.md`) to skip directly to the happy path on previously-solved problems.

**Format:** one line per learning — link, one-sentence summary, and tags for keyword matching.

**Update rule:** whenever `learnings/<new>.md` is added, append a line here in the same commit. When a learning is superseded, mark the old line with `~~strikethrough~~` and note the replacement.

---

## Index

### Architecture

- [`storyboard-to-video-pipeline-design-notes.md`](./storyboard-to-video-pipeline-design-notes.md) — Storyboard-to-video pipeline - design notes (implementation not in the toolkit). (`video`, `storyboard`, `tts`, `ffmpeg`, `srt`, `sapi`, `design-notes`, `fact-check`).
- [`tracker-sync-refuses-guessing.md`](./tracker-sync-refuses-guessing.md) — Tracker sync writes to a separate output path and refuses any output that already holds ticks unless an explicit carry-ticks option is given (`tracker`, `sync`, `progress`, `study-plan`, `design-rules`, `idempotency`, `unicode`, `spreadsheet`).

### Security

- [`notebook-hardcoded-aws-credentials.md`](./notebook-hardcoded-aws-credentials.md) — Notebook hardcoded AWS credentials must use `runtime_config.json`; never print secrets in notebook outputs (`notebook`, `aws`, `credentials`, `security`, `runtime-config`, `s3`).
- [`linkedin-composer-file-inputs-belong-to-messaging-overlay.md`](./linkedin-composer-file-inputs-belong-to-messaging-overlay.md) — Attach LinkedIn post images through your own temporary file input plus a drop/paste onto the Create post editor, remove it in `finally`, never touch messaging Send, and recover if it lands in a chat draft (`linkedin`, `composer`, `messaging-overlay`, `file-input`, `hazard`).
- [`av-false-positives-on-encoded-commands-and-scanner-fixtures.md`](./av-false-positives-on-encoded-commands-and-scanner-fixtures.md) — After an AV false positive: allowlist the folders actually in use but never `.ssh` or the tool's own config folder; restore quarantined fixtures from the tag after tag/`git fsck`/diff checks, AV left on (`antivirus`, `false-positive`, `base64`, `gzip`, `scanner-fixtures`, `allow-list`, `triage`, `git-fsck`).
- [`chained-email-ingest-and-workbook-update-tasks.md`](./chained-email-ingest-and-workbook-update-tasks.md) — Chained email-to-folder and workbook-update tasks - split ingest from update and harden both. (`scheduled-task`, `email`, `automation`, `workbook`, `formula-injection`, `allow-list`, `sha256`, `dry-run`, `additive`).
- [`external-tool-intake-verdicts-pin-and-opt-in.md`](./external-tool-intake-verdicts-pin-and-opt-in.md) — Four token-saving tools reviewed: adopt only a pinned, switched-off slice (RTK, Ponytail from a pinned clone); reject Caveman (plugin and CLI blocked; skill text not added after the value check) and Context Mode (`intake`, `rtk`, `caveman`, `ponytail`, `context-mode`, `telemetry`, `pinning`, `permission-prompt`).

### Notebooks / Toolchain

- [`site-unreachable-diagnosis-bridge-and-chrome-filter.md`](./site-unreachable-diagnosis-bridge-and-chrome-filter.md) — A site will not open for the user - diagnose in layers, and know the browser tool's URL filter. (`network`, `diagnosis`, `curl`, `dns`, `tls`, `vpn`, `claude-in-chrome`, `url-filter`, `computer-use`, `request_access`).

### AWS / CloudWatch / Monitoring

- [`no-data-and-zero-are-different-in-monitoring.md`](./no-data-and-zero-are-different-in-monitoring.md) — Latencies are not zero-filled: no `FILL(m1, 0)` on p99/percentile widgets, and latency alarms use `missing`/`ignore`/`breaching`, never `notBreaching` (`cloudwatch`, `metrics`, `zero`, `no-data`, `treat-missing-data`).

### Terraform / IaC

- [`parallel-stack-parity-env-flip-needs-iam-first.md`](./parallel-stack-parity-env-flip-needs-iam-first.md) — Grant the legacy role access to the new target only via Terraform (one add, clean re-plan), marked TEMPORARY with a tracked removal at cutover (`lambda`, `sqs`, `iam`, `parallel-stack`, `cutover`).
- [`reconcile-applied-drift-before-committing-in-multi-copy-stacks.md`](./reconcile-applied-drift-before-committing-in-multi-copy-stacks.md) — In multi-copy Terraform layouts, `git status` can show applied-but-uncommitted drift from a prior session; classify and commit it separately before committing a new fix (`terraform`, `git`, `worktree`, `drift`, `commit-hygiene`).
- [`terraform-init-git-modules-fail-on-deep-windows-paths.md`](./terraform-init-git-modules-fail-on-deep-windows-paths.md) — `terraform init` on git-sourced modules fails on deep Windows paths ("$GIT_DIR too big"); validate from a short scratch-path copy (`terraform`, `windows`, `git`, `init`, `path-length`).

### Confluence / Wiki

- [`confluence-mcp-does-not-expose-page-version-number.md`](./confluence-mcp-does-not-expose-page-version-number.md) — The Confluence MCP `getConfluencePage` result has no numeric version field for rollback manifests; derive it from the write response instead (`confluence`, `mcp`, `version`, `backup`, `rollback`).

### Publishing / Browser Automation

- [`medium-paste-splits-code-blocks-at-blank-lines.md`](./medium-paste-splits-code-blocks-at-blank-lines.md) — A blank line inside a pasted `<pre>` splits one file into several Medium code boxes; put a single space on blank lines before pasting (`medium`, `code-blocks`, `blank-lines`, `paste`, `html`).
- [`linkedin-cannot-attach-media-after-publishing.md`](./linkedin-cannot-attach-media-after-publishing.md) — LinkedIn cannot add media to a published post; attach the image before Post. If it already went out, post again with the image and point the old post to it with a "More..." line; delete the old post only if asked (`linkedin`, `media`, `publishing`, `repost`, `more-pointer`, `back-links`).
- [`linkedin-image-change-needs-new-post-with-more-pointer.md`](./linkedin-image-change-needs-new-post-with-more-pointer.md) — LinkedIn's editor changes a published post's text and alt text only; for a new image publish a new post, edit a "More... <url>" line into the old post, repoint links, delete only if asked (`linkedin`, `edit-post`, `image-change`, `more-pointer`, `back-links`).
- [`medium-change-topics-popover-enter-adds-first-suggestion.md`](./medium-change-topics-popover-enter-adds-first-suggestion.md) — In a published story's Change topics popover neither mouse nor DOM clicks add a suggestion; type until the exact topic is first, press Enter, read the chips back; normalise curly quotes and no-break spaces before comparing editor text (`medium`, `topics`, `change-topics`, `typeahead`, `normalisation`).
- [`study-posts-system-design-first-short-teaser.md`](./study-posts-system-design-first-short-teaser.md) — A complete, cited study publication still missed its purpose: write the target role, focus, and budgets in a consumer `PUBLICATION-PROFILE.md`; the article is a short system-design story with the study topic inside the body, the post a teaser with one article link and at most five hashtags; gate drafts with a shape check and a profile check, and replace a live miss with a new story plus pointers instead of retitling (`medium`, `linkedin`, `system-design`, `positioning-profile`, `teaser`, `hashtags`, `guard-script`, `drafts-only`).
- [`browser-portal-extraction-xhr-hook-and-react-widgets.md`](./browser-portal-extraction-xhr-hook-and-react-widgets.md) — Open custom React-style dropdowns with `pointerdown`, `mousedown`, `pointerup`, `mouseup`, `click` in order, not a lone click or a value assignment (`claude-in-chrome`, `javascript_tool`, `xhr`, `fetch-hook`, `react`, `get_page_text`, `localstorage`, `login`, `virtualized-list`).
- [`browser-tool-operational-limits.md`](./browser-tool-operational-limits.md) — Browser-extension tool limits that break long automation runs. (`browser`, `extension`, `limits`, `wait`, `page-text`, `file-upload`, `tab-group`, `javascript-tool`, `multi-browser`, `mid-publish`).
- [`dead-submit-button-analytics-only-request.md`](./dead-submit-button-analytics-only-request.md) — A Next button that only fires an analytics request is a page-side defect, not a user error. (`web-forms`, `debugging`, `network`, `analytics`, `instrumentation`, `submit`, `workaround`).
- [`linkedin-job-page-view-url-hangs-on-skeleton.md`](./linkedin-job-page-view-url-hangs-on-skeleton.md) — LinkedIn job pages opened by /jobs/view/<id> hang on skeletons; use the search layout with currentJobId. (`linkedin`, `jobs`, `browser`, `page-text`, `skeleton`, `webfetch`, `robots`).

### Build / CI

- [`quality-gate-blocks-unclassified-suffixes.md`](./quality-gate-blocks-unclassified-suffixes.md) — The changed-code quality gate blocks file types it cannot classify (`.html`, `.gitattributes`); classify diagram sources such as `.mmd` as non-code in `NON_CODE_SUFFIXES` (add the suffix with a test if missing); store HTML fixtures as `.txt` with a `{{SPACE}}` marker for significant whitespace (`quality-gate`, `ci`, `fixtures`, `suffix`, `unrecognized-file-type`).
- [`gh-graphql-blocked-in-cloud-sandbox.md`](./gh-graphql-blocked-in-cloud-sandbox.md) — In the cloud container, try `gh pr create` at most once, make no further GraphQL-backed calls, and open the PR via REST `gh api -X POST repos/<owner>/<repo>/pulls` (`gh-cli`, `graphql`, `cloud-sandbox`, `pull-request`).
- [`first-cloud-deploy-gotchas-and-demo-teardown.md`](./first-cloud-deploy-gotchas-and-demo-teardown.md) — First cloud deployment gotchas and planning the teardown of a demo. (`cloud-deploy`, `scale-to-zero`, `billing`, `permission-propagation`, `health-path`, `teardown`, `cost`, `demo`).

### Git / Windows / Shell

- [`powershell-5-1-bomless-utf8-dash-ends-string-literal.md`](./powershell-5-1-bomless-utf8-dash-ends-string-literal.md) — A BOM-less UTF-8 `.ps1` with an em dash in a string fails to parse on Windows PowerShell 5.1 (the dash decodes to a typographic quote); keep PowerShell sources ASCII-only or add a BOM, and test for it
- [`cloud-session-device-bridge-file-io.md`](./cloud-session-device-bridge-file-io.md) — Refresh existing files on the device-bridge mount without unlink: extract to a new folder, then `cat new > old` (no `tar -x`/`cp` over existing names) (`device-bridge`, `device_bash`, `desktop-commander`, `base64`, `mount`, `unlink`, `md5`).
- [`google-drive-desktop-folder-reorg.md`](./google-drive-desktop-folder-reorg.md) — Verify a Drive for desktop reorg per file (mapped path, same size) and treat Drive's own `desktop.ini` churn as noise, not a count mismatch (`google-drive`, `file-id`, `folder-id`, `rename`, `desktop.ini`, `reorg`).
- [`cowork-bridge-hides-skills-dirs-read-via-cloud-clone.md`](./cowork-bridge-hides-skills-dirs-read-via-cloud-clone.md) — In Cowork the device bridge returns "Permission denied" for `skills/` and `tool-subagents/`; read the toolkit through a shallow cloud clone and push from a fresh PC worktree via Desktop Commander, because the container cannot push or run the security scanners; to run a script from a protected folder, copy it to a non-protected folder first and park the copy for deletion (`cowork`, `device-bridge`, `permission-denied`, `worktree`, `desktop-commander`, `push`, `copy-out`).
- [`windows-security-gate-python-stub-and-committed-skills.md`](./windows-security-gate-python-stub-and-committed-skills.md) — Run the security gate bash script via Git Bash, not the `.ps1` wrapper under Windows PowerShell 5.1, which aborts on native stderr (`windows`, `python`, `windowsapps`, `git-bash`, `security-check`, `skillspector`).
- [`sandbox-to-device-zero-context-patch-with-checksums.md`](./sandbox-to-device-zero-context-patch-with-checksums.md) — Carry a sandbox change to a device worktree as a `-U0` patch applied with `--unidiff-zero`, never base64 or whole files; on a SHA-256 mismatch do not commit (`git-apply`, `patch`, `checksum`, `cloud-session`, `worktree`).
- [`consolidation-pr-is-the-harvest-base.md`](./consolidation-pr-is-the-harvest-base.md) — While consolidating, pause exactly the enabled repo-writing scheduled tasks, record them, and resume exactly those; never enable a disabled task (`consolidation`, `integration-pr`, `harvest`, `branch-hygiene`, `stacking`, `scheduled-writers`).
- [`desktop-commander-powershell-run-and-scan-patterns.md`](./desktop-commander-powershell-run-and-scan-patterns.md) — Split Desktop Commander drive scans into one process per top-level/suspect folder, each polled by pid with a timeout of at most about 170-175 s (`desktop-commander`, `powershell`, `start_process`, `remove-item`, `long-scan`, `read_process_output`, `elevation`, `classifier`, `windows`).
- [`relocate-repo-update-claude-config-paths.md`](./relocate-repo-update-claude-config-paths.md) — When relocating a repo, repoint every occurrence (`g`) in all config kinds and tell the user open sessions keep the old `CLAUDE.md` until restarted (`relocate`, `symlink`, `claude-config`, `claude-md`, `ln`, `readlink`, `sed`, `macos`, `launch-agents`).

### Scheduled Tasks / Automation

- [`scheduled-task-attached-folder-rename.md`](./scheduled-task-attached-folder-rename.md) — A computer-bound scheduled task's attached folder cannot be changed via the scheduling API: pause with a recovery record before a folder move, attach a stable parent folder, update prompts, and have the user switch the folder and re-enable; a catch-up `fire_trigger` can be refused once by the auto-mode classifier (`scheduled-task`, `trigger`, `attached-folder`, `pause`, `resume`, `cowork`).
- [`scheduled-run-resumes-after-usage-limit.md`](./scheduled-run-resumes-after-usage-limit.md) — A scheduled run that ends FAILED on a usage limit may resume later and overlap a hand-fired catch-up (overlap observed, cause inferred); fire at most once, add a single-run guard, use mtime-guarded writes, and audit shared files after a suspected overlap (`scheduled-task`, `fire_trigger`, `usage-limit`, `catch-up`, `overlapping-runs`, `mtime-guard`).
- [`deferred-follow-up-declared-impossible.md`](./deferred-follow-up-declared-impossible.md) — Before saying a deferred follow-up is impossible, state which tools/schedulers were checked; if none exists, report it as a finding with a concrete fallback (`scheduled-task`, `follow-up`, `reminder`, `deferred-tools`, `capability-check`, `limitation`, `chat`).
- [`many-daily-automations-exhaust-usage-limits.md`](./many-daily-automations-exhaust-usage-limits.md) — Move priority scheduled tasks well away from a digest burst (hours, not minutes); retries and small start-time nudges do not help under a shared usage limit (`scheduled-task`, `usage-limit`, `digest`, `consolidation`, `cost`, `scheduling`, `cowork`).
- [`parallel-save-requests-leave-orphan-worktrees.md`](./parallel-save-requests-leave-orphan-worktrees.md) — Move the main checkout back to the default branch after securing the feature branch's uncommitted and untracked work in a worktree or pushed branch (`worktree`, `unsaved-work`, `ledger`, `learnings`, `sweep`, `branch-hygiene`, `orphan`).

### Agent Behavior / Validation

- [`subagent-fixed-context-cost-pick-leanest-agent-type.md`](./subagent-fixed-context-cost-pick-leanest-agent-type.md) — A helper's fixed start cost depends on its agent type (idle: ~78k tokens full tool surface, ~66k search-only, ~14k six-tool); pick the smallest tool surface that can do the task, then the cheapest model (`subagent`, `tokens`, `context`, `agent-type`, `tool-surface`, `orchestration`).

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
