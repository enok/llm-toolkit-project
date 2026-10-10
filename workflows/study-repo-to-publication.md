---
description: End-to-end study topic to protected GitHub repo (one or more languages), Medium article, and LinkedIn post with bidirectional links and separate approval gates
---

# Study Repo To Publication

Turn one study topic (a design pattern, algorithm, protocol, framework feature) into three linked artifacts: a protected public repo with a worked example in one or more languages (identical across them), diagrams, docs, and curated videos; a Medium article built from the repo; and a LinkedIn post carrying a high-quality diagram. Every artifact links to the other two in both directions.

Route through `rules/request-orchestration.md`. The root agent owns all writes, external mutations, and user communication; lanes are bounded producers checked by read-only validators (`workflows/task-quality-loop.md`). Constraints: `rules/external-write-authorization.md`, `rules/human-comment-reply-gate.md`, `rules/git-conventions.md`.

## Environment Split

| Place | Does | Cannot |
| --- | --- | --- |
| Cloud sandbox (lanes) | Draft code, docs, diagram sources; best-effort checks with what is installed | Reach the user's machine or browser; often blocked from registries, GitHub web, video sites, Medium |
| User machine (root, device bridge) | Definitive builds and tests, user-local toolchain installs, publication renders, `git`/`gh` | Nothing relevant; source of truth for "it builds" |
| Browser (root, user's logged-in session) | Medium and LinkedIn editors, public-page verification | Solve bot checks or captchas: hand those to the user |

## Phase 0 - Intake

Ask only what is missing, in one batch:

1. Topic, source (book chapter, article), and example scope: one small realistic scenario, 3-6 components, deterministic output.
2. Repo `<owner>/<repo>` with `<repo>` = `<prefix>-<topic>` (`<prefix>`: the user's series prefix) and the **language set**: one or more languages with target versions, the user's per-project choice (one is fine; never assume all four; versions per `skills/multi-language-study-repo/references/toolchain-notes.md`). Required checks follow: one job per language plus `docs`.
3. **Content angle, target role, narrative.** Ask the author's target role: titles and hooks lead with the highest-level concept the body credibly supports for that role (an architecture style over a class-level pattern), never more than the body delivers. Article and post follow AIDA (Attention, Interest, Desire, Action; `skills/medium-publishing/references/aida-narrative.md`). For a widely covered topic they lead with non-obvious applications (architecture uses, where it hides in widely used frameworks), then principles, explanation, diagrams, code; each framework claim cites an official source checked on the day (`skills/medium-publishing/references/content-angle.md`).
4. Approval gates, each asked separately when reached, none implied by "do it all": repo creation plus protection; repo topics; every PR merge (Phase 6 rule); Medium draft creation; Medium publish; the Medium back-link edit; LinkedIn post; editing or deleting an earlier post. Phase 0 only confirms they will be asked.
5. Environment readiness: device bridge, `gh` auth, browser signed in to Medium and LinkedIn, toolchains installable user-locally (no admin).

Print the wave-ordered task table with tier and model per task (Phase 3 lanes `standard`; transcription and script runs `light`).

## Phase 1 - Example Spec And Golden Table

Write the shared example spec and golden table as `EXAMPLE-SPEC.md` in the work folder (template: `skills/multi-language-study-repo/references/golden-table-spec.md`): golden table with edge cases, exact demo output text. Copy its human-readable parts to `docs/03-application-example.md`; the naming map, layout, and toolchain targets stay in `EXAMPLE-SPEC.md` only. Every language's tests assert every golden row and every demo prints the identical text. Freeze the spec before any language lane starts; changes go through the root.

## Phase 2 - Repo Bootstrap And Protection

1. Create the public repo (owner-only write: no collaborators) with a seed commit (contents: the layout reference); `ci.yml` arrives in the first PR.
2. Protect `main` with no required checks yet: PR required (0 approvals when solo), enforce for admins, no force-push or deletion, conversation resolution. Repo settings: squash-only, delete branch on merge.

From here on every change is a branch plus PR; work for Phases 3-5 goes on one ticket-named branch, `<TICKET-ID>-initial-content` (no ticket: ask for an issue or a user-picked name; never a generic one). Recipes: `skills/multi-language-study-repo/references/repo-layout-and-protection.md`.

## Phase 3 - Per-Language Lanes

One lane per chosen language, in parallel, write ownership limited to that language's directory. Input: frozen spec and golden table. Output: idiomatic code, tests for every golden row, build file with lockfile, run instructions. Lanes check what they can in the sandbox and report `mistake: <signature> - <line>` lines.

The root syncs lane output as one archive and runs the definitive build and tests on the user's machine. A read-only judge compares each language against the golden table; demos must match byte for byte.

## Phase 4 - Diagrams

Needed: a generic diagram, an application diagram, and an architecture view when applicable. Use `skills/diagram-authoring` with `skills/diagram-authoring/references/publication-diagram-style.md`.

1. Keep sources in `docs/diagrams/`; hand-author SVG when the diagram tool cannot draw the notation.
2. Pilots first: render 2-3 in the candidate style and show the user before restyling all.
3. Render all publication PNGs in one environment (the one QA inspects) and commit them.
4. Independent visual QA by a validator that did not produce the images, per `skills/image-quality-inspection` and its `references/destination-legibility.md` (legible at the Medium column width and LinkedIn feed size). Iterate until pass, max 5 rounds.
5. Push the branch and check the diagrams as GitHub renders them.

## Phase 5 - Docs And Videos

Write the README and the `docs/` pages of the content checklist in `skills/multi-language-study-repo/SKILL.md`: explanation, diagrams, example, principles page `docs/06-design-principles.md` (`skills/multi-language-study-repo/references/design-principles-doc.md`; article section: `skills/medium-publishing/references/content-angle.md`), architecture page with cited framework claims, run steps, videos, generated code-by-component page. Run the drift guards (`check_docs.py`, then `gen_code_by_component.py --check`; see the skill's Scripts section). Curate one video per chosen language with `skills/youtube-video-curation` (from the user's machine), verifying every id through oEmbed; never invent ids. Run `documentation-reviewer` per `rules/documentation-review-required.md`. Derive the tag list from the finished docs (repo topics, approval); extend it at the article and post drafts (Medium's five, hashtags): `skills/multi-language-study-repo/references/tags-and-topics.md`.

## Phase 6 - CI, Required Checks, Merge

Open the first PR with the code, docs, and `ci.yml`: one job per chosen language plus a docs-guard job. After the first green run, read the real job names, add them as required checks, and verify they gate the PR.

Merge rule (here and in Phases 8 and 10): merge only after the user names the specific PR number and base branch in the current session; when CI is green, state both and ask (the Phase 0 list is not that approval). Merge with squash.

## Phases 7-10 - Medium, README Links, LinkedIn, Back-Links

Run the **study-publication-medium-linkedin** workflow (workflows/study-publication-medium-linkedin.md) in full: Medium draft, approval and publish (7), README link PR (8), LinkedIn post with diagram (9), back-links (10). Its Known pitfalls apply to this run; the merge rule of Phase 6 binds Phases 8 and 10.

## Known pitfalls

- Treat sandbox checks as best-effort; build definitively on the user's machine. (sig: env-constraint/sandbox-egress-blocks-registries)
- Write each device commit to a fresh filename and verify it on the machine (a PNG by decoded pixels); an existing path can keep the old bytes. (sig: coordination/device-commit-stale-bytes)
- Keep Mermaid sources on `Arial, Helvetica, sans-serif`, swap fonts only in the PNG renderer, and check labels on GitHub. (sig: platform-quirk/github-mermaid-font-clipping)
- Name required checks after stable single jobs, never matrix-expanded names, and confirm they report. (sig: tool-misuse/required-check-matrix-job-name)
- Pipe `gh api` into `ConvertFrom-Json` in PowerShell instead of using `gh --jq`. (sig: tool-misuse/powershell-gh-jq-quoting)
- Check each diagram at the destination size (Medium column, LinkedIn feed), not only on GitHub. (sig: quality-defect/diagram-illegible-at-destination)
- Drop a removed CI job from the required checks BEFORE merging the PR that removes it. (sig: coordination/required-check-removed-job)
- Correlate every pattern with design and architecture principles (SOLID etc.) and their tension: principles page, article section, post line. (sig: spec-gap/pattern-not-correlated-with-principles)
