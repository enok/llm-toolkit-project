---
name: multi-language-study-repo
description: Use when the user wants a public GitHub repo per study topic (for example one repo per design pattern) that explains the topic, draws generic and example diagrams, implements one shared example identically in several languages with CI, and is owner-only write with a PR-only protected main; or asks to add, check, or fix such a repo.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Multi-Language Study Repo

Build one public repository per study topic. Each repo teaches the topic
(explanation, diagrams), shows one small example implemented identically in
several languages, proves it with CI, and accepts changes from the owner only,
through pull requests only.

## When to use

- One repo per `<topic>`, for example one repo per design pattern: the repo is
  `<owner>/<repo>` with `<repo>` = `<prefix>-<topic>` (example only:
  `design-pattern-<pattern>`; for a design pattern, `<pattern>` is the
  `<topic>`).
- The same example must exist in 3+ languages and stay consistent across them.
- The repo is public, but only `<owner>` can change it, and `main` is
  protected.
- Not for: a single-language sample, a private repo, a monorepo of many
  topics, or publishing the article/post (that is the next stage, see Related).

## Inputs to confirm first

`<owner>`, the `<prefix>` of `<repo>` (`<prefix>-<topic>`), `<topic>`,
languages and versions (default Java 25, Python 3.12+, JavaScript on Node 24,
TypeScript 7; check the current releases), whether an architecture view
applies, license holder name for `LICENSE`, and how the user names work items
(ticket ID, see step 7). Explain the topic in your own words; never paste book
passages.

## Content checklist (one repo)

| # | Item | Lives in |
| --- | --- | --- |
| 1 | Explanation of the pattern | `docs/01-pattern-explanation.md` |
| 2 | Generic diagram of the pattern | `docs/02-generic-diagram.md` + `docs/diagrams/*.mmd` + PNG |
| 3 | Example application of the pattern | `docs/03-application-example.md` |
| 4 | Diagram specific to the example | `docs/04-example-diagram.md` + `docs/diagrams/` |
| 5-8 | Code in every language, component by component | `docs/05-code-by-component.md` (generated) + one folder per language |
| 9 | Architecture-level application, with diagrams (only if applicable; otherwise one line in the README saying why not) | `docs/09-architecture-perspective.md` |
| 10 | Best video per language, curated and verified (`youtube-video-curation`) | `docs/10-videos.md` |

Also: `README.md` (index, run commands, links), `LICENSE`,
`.github/workflows/ci.yml`, `.github/CODEOWNERS`.

## Procedure

1. **Spec first.** Write the shared example spec (`EXAMPLE-SPEC.md`) and its
   golden table before any code
   ([golden-table-spec.md](references/golden-table-spec.md)). Recompute the
   golden values independently; a wrong value would propagate to every
   language.
2. **Repo + protection.** Create the public repo with a seed commit, set
   squash-only and delete-branch-on-merge, apply branch protection WITHOUT
   required checks, so all content arrives by PR
   ([repo-layout-and-protection.md](references/repo-layout-and-protection.md)).
3. **Per-language lanes in parallel.** One lane per language, each writing only
   its own folder to the spec: code, tests that assert every golden row and the
   exact demo text, README with run commands
   ([toolchain-notes.md](references/toolchain-notes.md)). Design files so each
   pattern component maps to whole files.
4. **Docs and diagrams lanes in parallel.** Docs 01-04, 09, 10. Diagrams follow
   `skills/diagram-authoring/SKILL.md` and
   `skills/diagram-authoring/references/publication-diagram-style.md`: `.mmd` source committed, PNG
   rendered in ONE environment, pilots shown to the user before restyling all,
   visual QA by a validator that did not produce them
   (`skills/image-quality-inspection/SKILL.md`). Videos via
   `skills/youtube-video-curation/SKILL.md` from the user's machine.
5. **Root merge (single writer).** Assemble lane outputs into one tree, write
   `components.json`, generate `docs/05-code-by-component.md`
   ([code-by-component.md](references/code-by-component.md)), run both script
   checks below. Keep generated artifacts the lanes cannot produce (for
   example `package-lock.json`) across re-merges.
6. **CI.** One job per language plus `docs`; job names are fixed and never
   matrix-expanded. Run the definitive builds on the user's machine or in CI,
   not only in a sandbox.
7. **Open the PR** as a draft from a ticket-named branch (`<TICKET-ID>-initial-content`;
   no ticket: see the branch rule in the layout reference); wait for the first
   CI run. Follow `rules/git-conventions.md`.
8. **Required checks after the first green run.** Read the real check-run
   names, re-apply protection with those names as required contexts.
9. **Merge** with squash, delete the branch, confirm CI on `main` is green, and
   verify protection by API read-back (never with a real push to `main`). Merge
   only after the user names that specific PR and its base in the current
   session; otherwise state the PR number and base and ask
   (`rules/git-conventions.md`).

Then hand the finished repo to the publication stage.

## Scripts

Python 3.9+, stdlib only. Exit 0 ok, 1 check failed, 2 usage or I/O error
(invalid config, missing source file). Run from the skill folder, or copy both
into the repo (for example `.github/scripts/`) for CI. Commands say `python`;
use `python3` where `python` is missing or not Python 3. On Windows keep
`python` (`python3` is often a Microsoft Store stub).

```bash
python scripts/check_docs.py --root <repo> [--diagrams docs/diagrams] [--docs docs README.md]
python scripts/gen_code_by_component.py --config components.json --root <repo> [--out docs/05-code-by-component.md] [--check]
```

`check_docs.py` exits 1 when:

- a `*.mmd` in `--diagrams` is not byte-identical (LF line endings, one trailing
  newline ignored) to a ```` ```mermaid ```` block in some Markdown file under
  `--docs` (files or folders);
- a fenced block directly preceded by `<!-- source: <path> -->` (the marker is on
  the line directly above the fence) differs from that file, or the file is
  missing or outside the repo; a marker not followed by a fence is reported too;
- a relative link target does not exist, escapes the repo root, or exists only
  with different letter case. Checked forms: inline links and images,
  reference definitions (`[id]: path`), and single-line `src=` /
  `href=` attributes of HTML tags such as `<img>` and `<a>`. Links inside code
  and `#anchor` parts are not checked.

`gen_code_by_component.py` renders the component-first page from a JSON config
(`title`, `intro`, `languages` `[{key,label,fence,dir}]`, `components`
`[{title, role, files: {<lang key>: [paths relative to that language dir]}}]`).
`--check` exits 1 when the file on disk differs from what would be generated.
A language with no files for a component is skipped for that component, so
list every language yourself. `scripts/components.example.json` is a generic
config to copy.

## Hard rules

- Spec and golden table before code; every language asserts all golden rows.
- Docs never hand-type code: the code-by-component page is generated and
  guarded; code shown elsewhere (articles, posts) must be byte-identical to
  the repo files (hash-check it).
- Protection is applied before content. Never push to `main`, never use
  force-push or admin bypass. `enforce_admins` binds the owner too.
- Required checks are added only after they have run once; names never
  change. Sequential versions inside one job, no matrix.
- Say where each build ran (sandbox, user machine, CI). Never report green
  from a partial sandbox run; sandboxes often block package registries.
- Creating the repo, changing protection and merging are external writes: do
  them for the owner the user named, and only as the user asked. Merge only
  after the user names that specific PR and base in the current session
  (`rules/git-conventions.md`). Publishing the article or posts has its own
  approval gates (Related).
- Public repo hygiene: no tokens, local absolute paths or verify logs in
  committed files.

## References

| File | Covers |
| --- | --- |
| [repo-layout-and-protection.md](references/repo-layout-and-protection.md) | Layout, repo settings, protection JSON, CI template, owner-only write, merge flow, PowerShell notes |
| [golden-table-spec.md](references/golden-table-spec.md) | Shared example spec: integer money, golden table, exact demo text, naming map |
| [code-by-component.md](references/code-by-component.md) | Component-first page, GitHub `<details>` and Medium formats, config schema |
| [toolchain-notes.md](references/toolchain-notes.md) | Java 25, Python 3.12+, Node 24, TypeScript 7, sandbox limits, user-local installs |

## Related

- `workflows/study-repo-to-publication.md` - next stage: article, README links,
  LinkedIn, all links bidirectional, with approval gates.
- `skills/youtube-video-curation/SKILL.md`, `skills/diagram-authoring/SKILL.md`,
  `skills/image-quality-inspection/SKILL.md`, `skills/medium-publishing/SKILL.md`,
  `skills/linkedin-publishing/SKILL.md`, `skills/ci-watcher/SKILL.md`.
