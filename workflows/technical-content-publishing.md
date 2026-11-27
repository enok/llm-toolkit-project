---
description: Turn a software project into an evidence-grounded article, social post, carousel, and visuals - drafted and validated, never posted
---

# Technical Content Publishing Workflow

**Goal:** Produce a content set for a software project: a long-form article (Medium-style), a short social post, a document carousel, a cover image, and an architecture diagram. Every claim is traced to evidence, every asset is validated by someone other than its producer, and **nothing is posted** - the output is a reviewed draft bundle plus handoff.

Use to write about a project the author can inspect. Not for unverifiable marketing, posting or scheduling (Phase 6), or plain documentation (`workflows/document-creation.md`).

Platform specifics (lengths, truncation, formatting, slide counts, image sizes, paste steps) live in the skill, not here:

- `skills/technical-content-publishing/SKILL.md`
- `skills/technical-content-publishing/references/medium-article.md`
- `skills/technical-content-publishing/references/linkedin-post-and-carousel.md`
- `skills/technical-content-publishing/references/visual-assets.md`

Scoring lives in `rubrics/technical-content.md`.

---

## Principles

1. **Evidence first.** No number, quote, name, or "first/only" claim appears without a fact-sheet entry.
2. **Honest hooks.** A true, specific claim the evidence supports - not an invented statistic or clickbait.
3. **Generic by default.** No private names (employers, clients, internal projects, hostnames, people). The denylist is consumer-supplied at run time and never written into tracked files.
4. **Producer is never validator** (`workflows/task-quality-loop.md`); **draft, never post** (`rules/external-write-authorization.md`).
5. **Disk over memory.** State lives in a working directory/ledger outside tracked toolkit paths, so a lost session resumes from files.

---

## Phase 0 - Scope (human answers)

Ask once, batched. Start Phase 1 once items 1-5 are answered or recorded as `unconfirmed` assumptions:

1. **Audience** - who reads this and what they already know.
2. **Language** (and locale/spelling).
3. **Angle candidates** - the story or claim to tell; a rough idea is fine.
4. **Assets wanted** - article, post, carousel, cover, diagram (default: all).
5. **Publish targets** - which platforms and byline conventions.
6. **Project visibility** - public or private; what may be named and linked.
7. **AI-assistance disclosure** - required whenever AI drafted any of the text; propose a plain line, the author edits it. The sole waiver is Medium's assistive-use exemption (grammar/spelling help only), recorded in `HANDOFF.md`.
8. **Denylist location** - the path or secret store holding forbidden terms. Record only the *location*, never the terms.

Record answers in the ledger.

---

## Phase 1 - Evidence

Build `fact-sheet.md` in the working directory. Pin the subject first and record it at the top (for a repo: `git rev-parse --short HEAD`, `git log -1 --format=%cs`, visibility, license).

| ID | Claim as it will appear | Type | Evidence | How verified | Status |
| --- | --- | --- | --- | --- | --- |

`Status` is `verified`, `author-confirmed`, or `cut`; only the first two ship. Type values and column rules: `SKILL.md`, Evidence-first rule.

Rules:

- Counts, sizes, and dates come from a command run on the pinned version (`git ls-files | wc -l`, `wc -c`), not from READMEs or an agent's own report.
- Quotes carry file path and line; paraphrases name the source file.
- Anecdotes need an artifact (commit, log, ledger entry, run output) or `author-confirmed` status. Neither, no anecdote.
- **Landscape sources:** for any "state of the field" or novelty claim, collect at least 3 sources (URL, title, publisher, publication date, retrieval date), preferring primary ones; otherwise drop or soften the claim.
- Record open gaps; do not paper over them in drafts.

---

## Phase 2 - Angle and hook selection

From the fact sheet and the Phase 0 angle candidates, write `angle.md`:

1. **Thesis** in one sentence, backed by listed fact IDs.
2. **At least 3 hook candidates**, each with the fact IDs that make it true and the type of reader it targets. Discard any hook that needs an unsupported number.
3. **Selection** - the chosen hook and a stated reason (evidence strength, specificity, audience fit, distance from the landscape sources). Keep the runner-up and next-best as the two alternate post openers.
4. **Outline** - 3-6 sections mapped to fact IDs, the one call to action, and the agreed disclosure line.

If the author fixed the angle, hooks are variations of it; still record all candidates, and show the pick only if it departs from that angle.

---

## Phase 3 - Drafting (article first)

From `fact-sheet.md` + `angle.md`; each lane writes only its own file:

1. **Article** - `article.md`, the canonical long form, per `references/medium-article.md`.
2. **Post** (`post.md`, plus two alternate openers) and **carousel copy** (`carousel.md`: slide text + per-slide text alternatives) per `references/linkedin-post-and-carousel.md`. Both are derived from the finished article and run in parallel with each other.

Constraints for every lane:

- Add no facts; a derived asset never carries a claim the article's fact IDs do not. Tag claims with fact IDs (`<!-- F12 -->` in the article; an Evidence map block at the end of the post and carousel); strip tags only in the final paste copy.
- Same thesis, numbers, CTA, and disclosure everywhere.
- A missing fact goes back to Phase 1; never invent or round it.

---

## Phase 4 - Visuals

Follow `skills/technical-content-publishing/references/visual-assets.md`.

- **Diagram:** apply `skills/diagram-authoring/SKILL.md`; labels come only from fact-sheet entries; the diagram source is the source of truth.
- **Cover:** built from the chosen hook/thesis.
- **Carousel render:** render `carousel.md` to the platform's page format; export all pages.
- Write alt text for every image and a text alternative per slide.
- **Image gate (mandatory):** inspect 100% of generated images and carousel pages as rendered (sharp, uncropped, legible at the destination size, current). An image that cannot be inspected is a blocker.

Diagram and cover need only `angle.md`, so they run in parallel with the article. The carousel render waits for `carousel.md`.

---

## Phase 5 - Validation

Run `workflows/task-quality-loop.md` per check, with acceptance criteria written first. Validators are read-only and never produced what they judge (the fact checker is not a Phase 1 lane either).

| Check | Method | Validator |
| --- | --- | --- |
| **Fact check** | Re-run the recorded command for every quantitative claim; confirm each quote/name against its source; every figure maps to a fact ID; flag unsupported superlatives | `verifier` |
| **Genericity / privacy** | Case-insensitive grep of every deliverable (copy, alt text, fact sheet, filenames, PDF/image metadata) with the consumer-supplied denylist (pass its path, not its terms), plus local paths, emails, hostnames, tokens, ticket keys. Report `file:line` and match count only - never echo denylist terms | grep lane (`light`); on any hit (grep or Visual QA), `documentation-reviewer` gives the privacy verdict (`deep`) |
| **Rubric score** | Score every criterion in `rubrics/technical-content.md` with cited evidence | `task-quality-judge` |
| **Platform limits** | Run the limit checks defined in the two platform references (length, truncation point, format, page count, file size) | `light` script lane (read-only) |
| **Visual QA** | Image gate on 100% of images and carousel pages; read all text inside them against the same denylist and patterns (report page and match count only); alt-text presence | `diagram-creation-specialist` |

Rules:

- Any privacy leak or fabricated figure is an automatic fail; fix at the source, then re-run the **whole** privacy grep.
- Any copy edit after the fact check re-opens it for the changed lines.
- Deterministic checks (grep, limits) use budget 1; judgment checks the default of 5. An exhausted budget means `escalated` to the root (accept-with-risk, re-scope, reassign, or ask the author).
- Save each verdict under `validation/` in the package; record iteration counts in the ledger.

---

## Phase 6 - Handoff (NOT POSTED)

Deliver to the author's chosen folder (never tracked toolkit paths): all drafts, carousel PDF, cover, diagram (source + export), `alt-text.md`, `fact-sheet.md`, `validation/`, and `HANDOFF.md` (file list with status, paste steps from the references, disclosure line or recorded waiver, open risks, the checklist below).

Every `*.md` deliverable starts with a `NOT POSTED` header line (the root prepends it to saved `validation/` verdicts); binaries (PNG, PDF) and source files (`slides.html`, diagram source, render scripts) are listed with their status in `HANDOFF.md`. Never publish via platform APIs, browser automation, or schedulers; read-only checks (links resolve) are fine.

**Posting checklist (for the author):**

- [ ] Re-read the final text; every number still matches the fact sheet at the pinned version.
- [ ] Links resolve; repo visibility and license match the copy.
- [ ] No private names remain; images and PDF metadata checked.
- [ ] Disclosure line present and accurate, or the assistive-use waiver recorded.
- [ ] Alt text pasted for each image; carousel title and description set.
- [ ] Post and article cross-link as planned; call to action works.
- [ ] The author gave an explicit current instruction naming the platform, the account, the exact text, and the assets, and approved that exact text.

---

## Orchestration hints

Tiers follow `rules/request-orchestration.md`; assign model and effort per task before dispatch.

| Phase | Task type | Tier | Parallel? |
| --- | --- | --- | --- |
| 0 | Questions, ledger update | root, local | No |
| 1 | Repo fact retrieval, source search, command runs | `light` | Yes - one lane per source group |
| 1 | Fact-sheet reduction and dedup | `standard` | After retrieval |
| 2 | Hook candidates | `standard` | Single lane |
| 2 | Hook selection, final angle | root synthesis | No |
| 3 | Article | `standard` | First (canonical); alongside Phase 4 visuals |
| 3 | Post, carousel copy | `standard` | After the article; the two lanes in parallel |
| 4 | Diagram, cover | `standard` | Yes, alongside the article |
| 4 | Carousel render, export, file copying | `light` | After `carousel.md` |
| 5 | Denylist grep, limit checks, command re-runs | `light` | Yes, all at once |
| 5 | Privacy verdict on any grep hit | `deep` | After the grep |
| 5 | Fact check, rubric score, visual QA | `standard` | Yes - separate validators |
| 6 | Bundle copy; `HANDOFF.md` drafting | `light`; `standard` | No |

Escalate only on the triggers in `rules/request-orchestration.md` (two consecutive `reasoning` failures; PII or security-sensitive judgment, hence the `deep` privacy verdict).

## Common mistakes

- Counts taken from docs or a lane's summary instead of a command at the pinned version.
- The denylist written into a tracked file, a committed prompt, or a report.
- Derived assets drifting from the article (number, CTA, disclosure).
- Skipping alt text, or omitting disclosure with no recorded waiver.
- Treating "validated" as "approved to post".

## Related

- Skill: `skills/technical-content-publishing/SKILL.md`
- Rubric: `rubrics/technical-content.md`
- Workflows: `workflows/task-quality-loop.md`, `workflows/document-creation.md`
- Rules: `rules/external-write-authorization.md`, `rules/request-orchestration.md`

---

## Final Step - Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow. Feed in recurring validator defects, failed hooks, and platform limit or paste problems that belong in the references.
