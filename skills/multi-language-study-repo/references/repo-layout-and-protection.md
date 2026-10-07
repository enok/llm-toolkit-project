---
title: Repo layout, protection and CI for a multi-language study repo
tags: [github, branch-protection, ci, layout, codeowners, gh-cli, powershell]
---

# Repo layout, protection and CI

Placeholders: `<owner>` (GitHub user or org), `<repo>` = `<prefix>-<topic>`
(example only: `design-pattern-<pattern>` when the topic is a design pattern),
`<topic>`, `<package>` (Java package), `<python_package>`.

## 1. Layout

```text
<repo>/
├── README.md                    # index: what it is, run commands, links to docs and videos
├── LICENSE                      # MIT, "Copyright (c) <year> <license holder>"
├── .gitattributes               # * text=auto eol=lf   (stable byte comparisons on Windows)
├── .gitignore                   # target/ __pycache__/ node_modules/ dist/   (NOT package-lock.json)
├── .github/
│   ├── CODEOWNERS               # * @<owner>
│   ├── workflows/ci.yml         # jobs: java, python, javascript, typescript, docs
│   └── scripts/                 # check_docs.py, gen_code_by_component.py, components.json
├── docs/
│   ├── 01-pattern-explanation.md
│   ├── 02-generic-diagram.md
│   ├── 03-application-example.md
│   ├── 04-example-diagram.md
│   ├── 05-code-by-component.md  # GENERATED (see code-by-component.md)
│   ├── 09-architecture-perspective.md   # only if applicable
│   ├── 10-videos.md
│   └── diagrams/                # *.mmd sources + rendered *.png (+ *.svg for hand-authored views)
├── java/        # pom.xml, src/main/java/<package path>/**, src/test/java/**, README.md
├── python/      # pyproject.toml, src/<python_package>/**, tests/**, README.md
├── javascript/  # package.json ("type": "module"), src/**, test/**, README.md
└── typescript/  # package.json, package-lock.json, tsconfig.json, src/**, test/**, README.md
```

Numbering `NN` follows the content checklist; items 5 to 8 (code per
language) are one component-first page, `05`. Skip `09` when no architecture
view applies and say so in the README. Each language README holds install,
test and demo commands. `CODEOWNERS` documents ownership and requests reviews;
it does not gate merges (`require_code_owner_reviews` stays false).

## 2. Create the repo and its settings

Seed `main` with an initial commit first. Branch protection requires PRs, so
nothing else may be pushed to `main` afterwards.

```bash
gh repo create <owner>/<repo> --public --description "<topic> in Java, Python, JavaScript and TypeScript" --license mit --add-readme
gh repo edit <owner>/<repo> --enable-squash-merge --enable-merge-commit=false --enable-rebase-merge=false --delete-branch-on-merge --enable-wiki=false --enable-projects=false
```

Squash-only keeps `main` linear and one commit per PR. If the installed `gh`
lacks `--add-readme`, create the repo empty and push one initial commit.
Optional hardening in the web UI: Settings, Actions, General, require approval
for workflows from fork PRs (the CI template already uses read-only
`permissions`).

## 3. Branch protection (PR-only main, owner bound too)

Two files, applied in two phases. `PUT` needs all four top-level keys
(`required_status_checks`, `enforce_admins`, `required_pull_request_reviews`,
`restrictions`), each nullable.

`protection.initial.json` (phase 1, before any CI exists):

```json
{
  "required_status_checks": null,
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 0
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
```

`protection.json` (phase 2, after the first green CI run; replace the
contexts with the exact job names read back, see section 4):

```json
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["java", "python", "javascript", "typescript", "docs"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 0
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
```

```bash
gh api -X PUT repos/<owner>/<repo>/branches/main/protection --input protection.initial.json
```

| Field | Why |
| --- | --- |
| `required_pull_request_reviews` present | A PR is required; direct pushes are rejected |
| `required_approving_review_count: 0` | A sole owner cannot approve their own PR; 1 would deadlock |
| `enforce_admins: true` | The owner is bound too; `gh pr merge --admin` cannot bypass |
| `strict: true` | Head must be up to date with `main`; after merging one PR run `gh pr update-branch <n>` on the others |
| `allow_force_pushes` / `allow_deletions: false` | `main` history is permanent |
| `required_conversation_resolution: true` | Review threads must be resolved before merge |
| `restrictions: null` | No push allow-list; PR-only is enforced by the review rule |

## 4. Required checks only after the first CI run, with stable names

A required context that has never reported, or whose name changed, blocks the
PR forever with "Expected - Waiting for status to be reported". So:

1. Apply `protection.initial.json` (no required checks).
2. Open the first PR with `ci.yml`; wait for a green run.
3. Read the real names, then apply `protection.json` with exactly those:

```bash
gh api repos/<owner>/<repo>/commits/<head-sha>/check-runs --jq '.check_runs[].name'
gh api -X PUT repos/<owner>/<repo>/branches/main/protection --input protection.json
```

```powershell
(gh api repos/<owner>/<repo>/commits/<head-sha>/check-runs | ConvertFrom-Json).check_runs.name
gh api -X PUT repos/<owner>/<repo>/branches/main/protection --input protection.json
```

Stable-name rules (learning `branch-protection-required-checks-need-stable-job-names`):

- Give every job an explicit `name:` equal to its id (`java`, `python`, ...).
- Never use `strategy.matrix` for a required job: the check becomes
  `python (3.12)`, and adding or dropping a version renames the required check.
  Run several versions sequentially inside ONE job, as in the template.
- Renaming a job later means: change the workflow, wait for one run, update
  the contexts in the same PR window. Treat names as an interface.

## 5. Owner-only write on a public repo

- No collaborators and no teams (check below).
- `main` protected as in section 3: PR required, 0 approvals, admins enforced.
- The owner opens their own PRs and, once required checks are green, merges
  them under the merge rule in section 7.
- Everyone else can read, clone and fork; they cannot push or merge.

```bash
gh api repos/<owner>/<repo>/collaborators --jq '.[].login'
gh api repos/<owner>/<repo>/branches/main --jq .protected     # true
gh api repos/<owner>/<repo>/branches/main/protection --jq '{admins: .enforce_admins.enabled, checks: .required_status_checks.contexts, approvals: .required_pull_request_reviews.required_approving_review_count}'
```

```powershell
gh api repos/<owner>/<repo>/collaborators | ConvertFrom-Json | ForEach-Object login
(gh api repos/<owner>/<repo>/branches/main | ConvertFrom-Json).protected
$p = gh api repos/<owner>/<repo>/branches/main/protection | ConvertFrom-Json
$p.enforce_admins.enabled; $p.required_status_checks.contexts; $p.required_pull_request_reviews.required_approving_review_count
```

Verify protection by API read-back only. Do not test it with a real push to
`main`: if protection were missing, the test commit would land on `main`
permanently. A behavioral test belongs in a scratch repo with the same JSON.

PowerShell rule (learning `powershell-gh-jq-quoting-breaks`): never rely on
`gh --jq '...'` with nested quotes (it failed with "accepts 1 arg(s), received
5"); pipe to `ConvertFrom-Json` and select with PowerShell. Pass JSON bodies
with `--input <file>`, not inline strings.

## 6. CI template (`.github/workflows/ci.yml`)

Refresh the action major versions and toolchain versions to current releases.
Each language job runs tests and the demo; `docs` runs the two scripts.

```yaml
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

jobs:
  java:
    name: java
    runs-on: ubuntu-latest
    timeout-minutes: 10
    defaults: { run: { working-directory: java } }
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-java@v5
        with: { distribution: temurin, java-version: '25', cache: maven, cache-dependency-path: java/pom.xml }
      - run: mvn -B -ntp verify
      - run: java -cp target/classes <package>.Demo

  python:
    # Stable required-check name: two versions run sequentially in this one job.
    name: python
    runs-on: ubuntu-latest
    timeout-minutes: 10
    defaults: { run: { working-directory: python } }
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with: { python-version: '3.12' }
      - run: PYTHONPATH=src python -m unittest discover -s tests -t . -v
      - run: PYTHONPATH=src python -m <python_package>
      - uses: actions/setup-python@v6
        with: { python-version: '3.13' }
      - run: PYTHONPATH=src python -m unittest discover -s tests -t . -v
      - run: PYTHONPATH=src python -m <python_package>

  javascript:
    name: javascript
    runs-on: ubuntu-latest
    timeout-minutes: 10
    defaults: { run: { working-directory: javascript } }
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v5
        with: { node-version: '24' }
      - run: node --test
      - run: node src/demo.js

  typescript:
    name: typescript
    runs-on: ubuntu-latest
    timeout-minutes: 10
    defaults: { run: { working-directory: typescript } }
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v5
        with: { node-version: '24', cache: npm, cache-dependency-path: typescript/package-lock.json }
      - run: npm ci
      - run: npm test
      - run: npm run demo

  docs:
    name: docs
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with: { python-version: '3.13' }
      - name: Code-by-component page is up to date
        run: python .github/scripts/gen_code_by_component.py --config .github/scripts/components.json --root . --check
      - name: Links, diagram drift and code drift
        run: python .github/scripts/check_docs.py --root .
```

Run the scripts from the repo root with `--root .`, so a cwd-relative
`--config` path is unambiguous. `python` is right on the runner; locally use
`python3` where `python` is missing or not Python 3 (on Windows keep `python`,
since `python3` is often a Microsoft Store stub).

## 7. Merge flow

Branch, commit and PR conventions come from `rules/git-conventions.md`:

- **Branch name = ticket ID**: `<TICKET-ID>-initial-content`, using the ID the
  user gives. With no ticket, do not invent a generic name such as
  `feat/<topic>-initial`: ask whether to use a GitHub issue as the work item
  (create it first so the ID is real, then name the branch
  `GH-<n>-initial-content`) or a name the user picks.
- Commit subjects and the PR title carry the same ID (`GH-<n>: Add <topic>
  content`); the PR body has the file-changes table the rule requires.
- Open the PR as a draft; CI runs on drafts. Mark it ready once checks are
  green.
- **Merge only after the user names that specific PR and its base (`main`)
  in the current session.** Otherwise state the PR number and base and ask.
  An agent never self-merges on its own judgment; a general "finish the work"
  does not name a PR.

```bash
git switch -c <TICKET-ID>-initial-content
git push -u origin <TICKET-ID>-initial-content
gh pr create --draft --base main --title "<TICKET-ID>: Add <topic> content" --body-file pr-body.md
gh pr checks <pr> --watch                 # wait for the first green run, then apply protection.json (section 4)
gh pr ready <pr>
gh pr merge <pr> --squash --delete-branch # only under the merge rule above; repo setting also deletes the remote branch
gh run list --repo <owner>/<repo> --branch main --limit 1   # CI on main after the merge
```

Later changes (README links after publication, fixes) repeat the same flow
as new PRs with their own ticket-named branch; never push to `main`.

## 8. Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| PR stuck on "Expected - Waiting for status to be reported" | Required context name does not match a job `name:` or never ran; read names from `check-runs`, fix `protection.json` |
| `GH006: protected branch update failed` on push | Correct behavior; use a branch and a PR |
| Cannot merge own PR | A required approval count above 0; keep it 0 for a sole owner |
| "Branch is out of date" | `strict: true`; run `gh pr update-branch <n>` and wait for CI again |
| `--admin` merge refused | `enforce_admins: true` by design; fix the failing check instead |
| `gh api ... --jq` fails in PowerShell | Use `| ConvertFrom-Json` |
| PUT returns 422 | A required top-level key is missing; use the JSON above verbatim |
