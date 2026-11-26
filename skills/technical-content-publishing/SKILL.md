---
name: technical-content-publishing
description: Turn a software project into evidence-grounded public technical content - a Medium-style long-form article, a LinkedIn share post, a LinkedIn PDF carousel, a cover image, and an architecture diagram - as reviewed drafts, never posted. Use whenever the user asks to write a technical blog post, Medium article, LinkedIn post or carousel, a project launch, case-study, "how it works" or "what we learned" write-up, a cover or hero diagram for one, or to promote a repository, tool, or engineering practice publicly, even if they only say "announce this" or "write something about this repo". Not for product marketing without engineering evidence, comment replies, or repo documentation.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.1.0"
---

# Technical Content Publishing

Turn real engineering work into public writing that a skeptical engineer still finishes reading. Method: pin the source, build a fact sheet, choose an honest angle, draft from the facts, render visuals, sweep for privacy, validate, and hand over a package labelled `NOT POSTED`.

> Gates, lanes, and loop bounds: `workflows/technical-content-publishing.md`. Scoring: `rubrics/technical-content.md`. If either disagrees with this file, the workflow and rubric win. This skill supplies the method and the platform facts those two files point to.

## Non-negotiables

1. **Evidence first.** Every number, quote, date, and behavioural claim traces to `path:line @ <ref>` or a dated URL in the fact sheet. No invented metrics, testimonials, quotes, anecdotes, or timelines.
2. **Generic and private-safe.** No employer, client, internal project, team, person, hostname, ticket, account, or secret in any output. See [Genericity and privacy](#genericity-and-privacy).
3. **Draft only.** Posting, scheduling, submitting to a publication, commenting, tagging people, or editing a live post is an external write. Bind it to an explicit current user instruction (`rules/external-write-authorization.md`, `rules/human-comment-reply-gate.md`). Default result: deliverables labelled `NOT POSTED`.
4. **Honest hooks.** Curiosity must be paid off by something the reader can check. No fake urgency, fake scale, or fake stories.
5. **Disclosed assistance.** The human decides the disclosure wording; the assistant never writes first-person experience the human has not confirmed.

## Scope

The description lists when this skill applies. Hand off instead of drafting for: product marketing with no engineering evidence, replies to comments (`rules/human-comment-reply-gate.md`), repo documentation (`document-creation`), and content needing legal or PR sign-off (flag it and stop at the draft).

## Required inputs

Ask one batched question for anything missing; if the user says "you decide", use the default and list it in the package so the human can veto.

| Input | Default when unspecified |
| --- | --- |
| Audience (role, seniority, prior knowledge) | Working engineers who know the domain but not this project |
| Language | Language of the request; code, identifiers, and quotes stay in the original language |
| Angle: one sentence the piece defends | Offer 2-3 candidates drawn from the fact sheet; recommend the strongest the evidence supports |
| Source and pinned ref (path/URL, tag or commit) | Current HEAD, recorded as short SHA plus date |
| Assets (article, post, carousel, cover, diagram) | All five |
| Publish targets and byline convention | Medium article plus LinkedIn post and carousel, author's own byline; nothing is published by the assistant |
| Voice and length | First person singular only for author-confirmed experience; plain; 5-9 minute read |
| Exclusions (names or topics that must never appear) | Keep this list outside tracked files; never paste it into a deliverable |
| Disclosure wording | A plain one-line AI-assistance note proposed by the assistant; the author edits the wording |
| Output folder | A scratch or drafts folder outside the repo being written about |

## Process

1. **Authorize and scope.** State "drafts only, `NOT POSTED`". If publishing is requested, ask for the exact target and final text first.
2. **Pin the source.** Record ref (short SHA or tag), date, visibility (public/private), and license. Private or unlicensed code is described generically; quote it only with the owner's go-ahead.
3. **Build the fact sheet** (`fact-sheet.md`; see [Evidence-first rule](#evidence-first-rule)). Mine README, docs, entry points, tests, CI config, commit history, issue and learnings logs, and anything you can re-run. Collect more candidates than you will use; keep what serves the angle.
4. **Choose angle and hook** (`angle.md`) from [Honest hook patterns](#honest-hook-patterns). Record at least 3 candidates, each with the fact IDs that make it true; pick one with a stated reason and keep the runner-up and the next-best as the two alternate post openers.
5. **Draft the article first** (canonical long form), then derive the post and carousel copy from the same fact IDs, thesis, call to action, and disclosure. A derived asset never introduces a claim that is not in the fact sheet.
6. **Render visuals** per `references/visual-assets.md`. The cover and hero diagram need only `angle.md`, so they run in parallel with the article; carousel slides render after `carousel.md` exists.
7. **Sweep** for genericity, secrets, banned claims, broken links, platform limits, and reading time.
8. **Validate** with `rubrics/technical-content.md` under `workflows/technical-content-publishing.md`. The validator is not the producer; loops are bounded by the workflow.
9. **Package and hand off.** Deliver the folder below with a `HANDOFF.md` that lists contents, defaults assumed, open decisions, per-platform paste and upload steps (from the references), a pre-publish checklist for the human, and the `NOT POSTED` label.

```
<out>/                   # outside tracked toolkit paths; names match the workflow
  HANDOFF.md             # manifest, assumptions, open decisions, paste steps, NOT POSTED
  fact-sheet.md          # source of truth for every claim
  angle.md               # thesis, hook candidates, pick, outline
  article.md             # Medium-style draft + publishing metadata block
  post.md                # main post, two alternate openers, first-comment draft
  carousel.md            # slide-by-slide copy + per-slide text alternatives
  carousel/              # slides.html, <slug>-carousel.pdf, slide-NN.png
  visuals/               # cover.png, architecture.(svg|png) + source
  alt-text.md            # one alt text per image
  validation/            # validator verdicts (*.md; the root prepends the NOT POSTED header)
```

## Skeletons

Keep each short; the workflow and rubric define what must be in them. Every `*.md` deliverable starts with a `NOT POSTED` header line.

`fact-sheet.md` row (`status` must be `verified` or `author-confirmed` to ship):

```
| ID  | Claim as it will appear        | Type  | Evidence                | How verified                   | Status   |
| F12 | "<N> tracked files at <ref>"   | count | `git ls-files` @ <ref>  | `wc -l` on it, run <date>: <N> | verified |
```

`angle.md`:

```
# Angle - NOT POSTED
Thesis: <one sentence> [F3, F7]
Hooks: H1 <pattern>: <text> [F3] / H2 ... / H3 ...      (at least 3, each with fact IDs)
Pick: H<n> because <evidence strength, specificity, audience fit>; H<m>, H<k> = the two alternate openers
Outline: 1 <section> [F..] ... (3-6 sections)
CTA: <the one action, same in every asset>    Disclosure: <author-approved line>
```

`carousel.md` (one block per slide; the renderer fills the `n/N` footer):

```
# Carousel - NOT POSTED - <slug>, 1080x1350, N slides
## 1/N Cover
Copy: <claim, 10 words or fewer> / <short subtitle>
Alt: <what a screen-reader user needs from this slide>
Facts: F3
## 2/N Problem ...
```

`alt-text.md`:

```
# Alt text - NOT POSTED
visuals/cover.png: <one sentence: what it shows and why it is there>
visuals/architecture.png: <one sentence naming the parts and the flow>
carousel/slide-01.png ... slide-NN.png: see carousel.md
```

`HANDOFF.md`:

```
# HANDOFF - NOT POSTED
Pinned: <ref>, <date>; visibility <public|private>; license <id>
Files: <path> - <md|binary|source> - <draft|inspected|validated>    (binaries, PDFs, and source files are listed here with their status)
Defaults assumed: <list for the human to veto>
Limit checks: <check> = <value> -> <pass|fail>
Validation: validation/<verdict> - <Pass|Fail|Escalate> <score>
Decisions for the human: link variant, disclosure wording, hashtags, ...
Paste/upload steps and posting checklist: <from the references>
```

## Evidence-first rule

Fact sheet (`fact-sheet.md`) row: `ID | claim as it will appear | type | evidence | how verified | status`.

- **type**: `count`, `quote`, `date`, `behaviour`, `code`, `author-statement`, `opinion`.
- **evidence**: `path:line @ <ref>` for repo facts; URL plus retrieval date for external facts; commit SHA for history; the exact command for computed facts.
- **how verified**: the command run (with scope, for example "tracked files at `<ref>`") or the file re-read. Record output and date.
- **status**: `verified`, `author-confirmed`, `cut`. Anything else cannot ship.

Rules:

1. Compute counts with a command in the pinned ref; never recall them, round them up, or reuse a number a sub-agent or tool reported without re-running it. State scope and ref next to the number.
2. Quotes are verbatim with `path:line`. A paraphrase gets no quotation marks. Never repair wording inside a quote.
3. Testimonials, user counts, stars, downloads, benchmarks, and timings exist only if a dated public source or a re-runnable command produced them. Otherwise omit.
4. Anecdotes (failures, incidents, "the night it broke") come from artifacts (history, logs, issues, learnings notes) or are marked `author-confirmed`. If neither, cut.
5. Comparative, novelty, or "state of the field" claims ("first", "only", "faster than", "nobody does X") need a comparison you ran or at least 3 dated sources (URL, title, publisher, publication date, retrieval date), preferring primary ones; otherwise soften to what you observed.
6. Opinions are written as opinions. Predictions are labelled as predictions.
7. In drafts, mark claims with `<!-- F12 -->` comments in `article.md` and an "Evidence map" block at the end of `post.md` and `carousel.md`. Strip comments only in the final paste copy.
8. Re-verify every fact at the pinned ref right before handoff; line numbers drift.

## Honest hook patterns

Pick one; do not stack. Test: *can a skeptical reader verify the opening claim in the repo or the cited source within five minutes?*

| Pattern | Shape | Honesty test |
| --- | --- | --- |
| Contrarian claim | A position that cuts against common practice, stated plainly, then defended | You can show the mechanism and a case where the common practice fails |
| Real failure story | What broke, what it cost, what the fix was | Comes from artifacts, not memory or embellishment |
| "The system that wrote this" | The article exists because the described process was actually used on it | Process evidence exists (ledger, history, logs); the claim is about mechanism, not magic |
| Surprising number | A computed count or ratio that changes how the reader sees the thing | Command and scope are in the fact sheet |
| Before/after diff | A real change shown side by side | Both sides are real outputs from the pinned ref |

Refuse: invented scale ("analyzed 10,000 repos"), invented urgency, fake dialogue, unnamed-expert authority, outrage bait, "you won't believe", and any hook the body does not pay off. No real failure story or measurable number? Use a reproducible demo (command plus real output), a real before/after diff, or a design trade-off with its evidence; never invent one.

```
Bad:  "I analyzed 10,000 repos and found the one trick that doubles your velocity."   (invented scale; nothing to check)
Good: "An assistant approved its own change and skipped the one test that failed. The repo now forbids it: <path>:<line>."   (checkable in five minutes)
```

## Article, post, carousel

Details and platform values live in the references; keep these shapes.

- **Article** (`references/medium-article.md`): title and subtitle, lede with the hook and a checkable promise, the problem as a concrete scene, the design with one diagram, proof on real code and output, what went wrong, trade-offs and limits, "try it" with commands, a short close. Target 1,100-2,000 words (estimate: 5-9 minutes). Up to five tags; SEO title and description set deliberately.
- **LinkedIn post** (`references/linkedin-post-and-carousel.md`): the first ~140 characters carry the claim; one real number with scope; one insight; exactly one call to action, the same as in the other assets; link placement decided with the human; at most three relevant hashtags at the end; no engagement bait; no tagging without approval. 1,000-1,800 characters by default; hard platform cap 3,000.
- **Carousel** (`references/linkedin-post-and-carousel.md`): PDF, identical page size on every page (default 1080x1350), 8-10 slides: cover claim, problem, idea, 2-4 proof slides (one fact each, source tag in the footer), what went wrong or trade-off, try it, one call to action (six fixed slides plus the proof slides). Footer page marker `n/N`, filled in by the renderer. At most ~35 words per slide; each slide has a text alternative in `carousel.md`.
- **Platform numbers** are time-sensitive; each carries its source URL and verification date in the references (dated 2026-10-01). Verify before use: re-check any value against the platform's current help page when it is older than a few months, and treat `unverified` as unknown.

## Visual assets

- Cover image, hero architecture diagram, and carousel slides follow `references/visual-assets.md`.
- Reuse existing skills instead of duplicating them: `skills/diagram-authoring` for the diagram source, rendering, and export rules; `skills/image-quality-inspection` for the mandatory inspection of every generated image and PDF page; `skills/markdown-pdf-export` if a PDF of the article itself is needed.
- Portable path: author HTML/CSS and render with headless Chromium to PNG and PDF using `scripts/render_assets.py` (Playwright for Python; it checks slide overflow and fills the `n/N` markers) or the browser CLI fallback in the reference; this needs only Python and a Chromium build. Poppler tools (`pdfinfo`, `pdftoppm`, `pdftotext`) run the checks when present; `references/visual-assets.md` gives a Python-stdlib page-size fallback. A check that cannot run is reported as not run, never as passed.
- Never state that a visual passed inspection unless the actual rendered file was opened and checked.

## Genericity and privacy

The output must read as if written by an outsider with no private context.

- Remove or generalize: employers, clients, internal projects, products, team names, people (colleagues, reviewers, mentors, managers), ticket IDs, internal URLs, hostnames, IPs, account or bucket or queue names, usernames, emails, and local paths.
- Examples use neutral placeholders (`<project>`, `example.com`, `acme-service`) or the public project itself.
- Do not mention the author's employment, studies, job search, or personal situation unless the human puts it in the brief.
- Secrets: scan article, code snippets, terminal captures, diagrams, and slide text for keys, tokens, and connection strings. Redact in the source, then re-render.
- Check rendered artifacts too: PDF text (`pdftotext` when present), image text, alt text, PDF and image metadata (author, creator, local paths).
- Run the exclusion-list grep from a list kept outside tracked files and outside the deliverables; report only the hit count and locations.
- Quoting someone else's public words requires a public, dated, linkable source and a real need for the quote; otherwise omit the person.

## AI-assistance disclosure

- Propose a plain one-line note that matches what actually happened and let the author edit the wording. Example: "Drafted with AI assistance; every claim was checked against the linked source." Include it in the article and the other assets as the platform references direct; the rubric treats a missing or misleading disclosure as a blocker. The only waiver is Medium's assistive-use exemption, which this toolkit applies to grammar and spelling help only.
- Medium's policy asks for a disclosure line within the first two paragraphs of AI-generated writing and a caption on AI-generated images; undisclosed AI writing gets reduced distribution (source in `references/medium-article.md`).
- LinkedIn: no text-disclosure rule was found; AI-generated images may carry provenance metadata (C2PA) that the platform can label, so do not strip it.
- Disclosure never replaces verification.

## Never post

- `*.md` deliverables carry a `NOT POSTED` header line (the root prepends it to `validation/` verdicts); binaries (PNG, PDF) and source files (`slides.html`, diagram source, render scripts) are listed with their status in `HANDOFF.md`. Do not call platform APIs, paste into a logged-in browser, schedule, or email drafts to third parties.
- To publish, the human gives an explicit current instruction naming the platform, the account, the exact text, and the assets; show that exact text in its own message and wait for approval. Material edits need a new approval.
- Pre-publish checks that need the platform (link-preview refresh, mobile truncation, tag lookup) are listed in `HANDOFF.md` for the human.

## Validation

- Score every deliverable with `rubrics/technical-content.md`; follow `workflows/technical-content-publishing.md` for who validates, how many fix loops are allowed, and what evidence to report.
- Mechanical checks before review: every `F<n>` resolves to a shippable row (verified or author-confirmed); the limit checks in both platform references; code snippets run at the pinned ref; links resolve (read-only); dimensions and page sizes; image inspection log; genericity grep clean over text, alt text, filenames, metadata, and text rendered in images, re-run after the last edit.

## Common failure modes

| Failure | Prevention |
| --- | --- |
| Inflated or stale numbers | Recompute at the pinned ref; scope next to the number |
| Plausible but invented quote or anecdote | Verbatim with `path:line`, or cut |
| Hook not paid off | Rewrite the hook to match the body, not the reverse |
| Generic AI cadence (stacked triads, "game-changer", "delve") | Concrete nouns, real artifacts, varied sentence length |
| Diagram nodes not in the code | Prove each node with a path (`skills/diagram-authoring`) |
| Carousel text too small on a phone | Type floors in `references/visual-assets.md`; view at phone width |
| Private detail in a screenshot, PDF metadata, or alt text | Sweep rendered artifacts, not only sources |
| Posting by accident | `NOT POSTED` headers and `HANDOFF.md` status; no publish tooling in the run |

## References

- `references/medium-article.md` - read before drafting `article.md`: Medium specs (verified 2026-10-01), article anatomy, craft, SEO, disclosure.
- `references/linkedin-post-and-carousel.md` - read before drafting `post.md` and `carousel.md`: LinkedIn specs (verified 2026-10-01), post and carousel anatomy, link and hashtag practice.
- `references/visual-assets.md` - read at step 6: cover, diagram, slide design, rendering, inspection.
- `scripts/render_assets.py` - run to render `slides.html` to the carousel PDF and PNGs, or a cover HTML to `cover.png`.
- Draft here, publish there: this skill produces reviewed drafts only. Pasting and publishing a finished article or post in the author's own logged-in browser is `skills/medium-publishing/SKILL.md` and `skills/linkedin-publishing/SKILL.md`, and only after the explicit approval described in Never post.
- Related: `skills/diagram-authoring`, `skills/image-quality-inspection`, `skills/markdown-pdf-export`, `skills/agent-orchestrator` (separate producer and validator lanes).
