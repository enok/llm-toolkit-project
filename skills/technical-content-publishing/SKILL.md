---
name: technical-content-publishing
description: Turn a software project into evidence-grounded public technical content - a Medium-style long-form article, a LinkedIn share post, a LinkedIn PDF carousel, a cover image, and an architecture diagram - as reviewed drafts, never posted. Use whenever the user asks to write a technical blog post, Medium article, LinkedIn post or carousel, a project launch, case-study, "how it works" or "what we learned" write-up, a cover or hero diagram for one, or to promote a repository, tool, or engineering practice publicly, even if they only say "announce this" or "write something about this repo". Not for product marketing without engineering evidence, comment replies, or repo documentation.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.2.0"
---

# Technical Content Publishing

Turn real engineering work into public writing a skeptical engineer still finishes: pin the source, build a fact sheet, choose an honest angle, draft from the facts, render visuals, sweep for privacy, validate, hand over a package labelled `NOT POSTED`.

> Gates, lanes, loop bounds: `workflows/technical-content-publishing.md`. Scoring: `rubrics/technical-content.md`. They win over this file; this skill supplies the method and platform facts they point to.

## Non-negotiables

1. **Evidence first.** Every number, quote, date, and behavioural claim traces to `path:line @ <ref>` or a dated URL in the fact sheet. No invented metrics, testimonials, quotes, anecdotes, or timelines.
2. **Generic and private-safe.** No employer, client, internal project, team, person, hostname, ticket, account, or secret in any output.
3. **Draft only.** Posting, scheduling, submitting to a publication, commenting, tagging people, or editing a live post is an external write needing an explicit current user instruction (`rules/external-write-authorization.md`, `rules/human-comment-reply-gate.md`). Default: deliverables labelled `NOT POSTED`.
4. **Honest hooks.** Curiosity must be paid off by something the reader can check.
5. **Disclosed assistance.** The human decides the disclosure wording; the assistant never writes first-person experience the human has not confirmed.

## Scope

Hand off instead of drafting: product marketing with no engineering evidence, comment replies (`rules/human-comment-reply-gate.md`), repo documentation (`document-creation`). Content needing legal or PR sign-off: flag it, stop at the draft.

## Required inputs

Ask one batched question for anything missing; on "you decide", use the default and list it in the package for veto.

| Input | Default when unspecified |
| --- | --- |
| Audience (role, seniority, prior knowledge) | Working engineers who know the domain but not this project |
| Language | Language of the request; code, identifiers, and quotes stay in the original language |
| Angle: one sentence the piece defends | Offer 2-3 candidates drawn from the fact sheet; recommend the strongest the evidence supports |
| Source and pinned ref (path/URL, tag or commit) | Current HEAD, recorded as short SHA plus date |
| Assets (article, post, carousel, cover, diagram) | All five |
| Publish targets and byline convention | Medium article plus LinkedIn post and carousel, author's own byline; nothing is published by the assistant |
| Voice and length | First person only for author-confirmed experience; plain; 5-9 minute read |
| Exclusions (names or topics that must never appear) | Keep this list outside tracked files; never paste it into a deliverable |
| Disclosure wording | A plain one-line AI-assistance note proposed by the assistant; the author edits the wording |
| Output folder | A scratch or drafts folder outside the repo being written about |

## Process

Method per step (gates and loop bounds: the workflow):

1. **Authorize and scope.** State "drafts only, `NOT POSTED`". If publishing is requested, ask for the exact target and final text first.
2. **Pin the source.** Record ref (short SHA or tag), date, visibility, and license. Private or unlicensed code is described generically; quote it only with the owner's go-ahead.
3. **Build the fact sheet** from README, docs, entry points, tests, CI config, history, issue and learnings logs, and anything you can re-run; collect more candidates than you will use.
4. **Choose angle and hook** (`angle.md`): at least 3 candidates with fact IDs, one pick with a stated reason; runner-up and next-best become the two alternate post openers.
5. **Draft the article first**, then derive post and carousel from the same fact IDs, thesis, call to action, and disclosure. A derived asset never adds a claim that is not in the fact sheet.
6. **Render visuals.** Cover and diagram need only `angle.md` (run beside the article); slides wait for `carousel.md`.
7. **Sweep, validate, hand off.** Sweep for genericity, secrets, banned claims, links, platform limits, reading time; validate (producer is not validator); package with a `HANDOFF.md` (contents, defaults, open decisions, paste steps, pre-publish checklist, `NOT POSTED`).

Package layout (`<out>/`, outside tracked toolkit paths; tree with notes in `references/package-templates.md`): `HANDOFF.md`, `fact-sheet.md`, `angle.md`, `article.md`, `post.md`, `carousel.md`, `alt-text.md`, `carousel/`, `visuals/`, `validation/`.

## Skeletons

Every `*.md` deliverable starts with a `NOT POSTED` header line. Fact-sheet row format and skeletons for `angle.md`, `carousel.md`, `alt-text.md`, `HANDOFF.md`: `references/package-templates.md`.

## Evidence-first rule

- **type**: `count`, `quote`, `date`, `behaviour`, `code`, `author-statement`, `opinion`.
- **evidence**: `path:line @ <ref>` for repo facts; URL plus retrieval date for external facts; commit SHA for history; the exact command for computed facts.
- **how verified**: the command run (with scope, for example "tracked files at `<ref>`") or the file re-read. Record output and date.
- **status**: `verified`, `author-confirmed`, `cut`. Anything else cannot ship.

Beyond the workflow's Phase 1 rules (counts by command at the pinned ref, quotes with path and line, anecdotes need an artifact, 3 dated sources for landscape claims):

1. Never recall, round, or reuse a number a sub-agent reported without re-running it; state scope and ref beside it.
2. Quotes are verbatim; a paraphrase gets no quotation marks; never repair wording inside a quote.
3. Testimonials, user counts, stars, downloads, benchmarks, and timings need a dated public source or a re-runnable command.
4. Comparative or novelty claims ("first", "only", "faster than") need a comparison you ran or the dated sources; otherwise soften to what you observed. Opinions and predictions are labelled as such.
5. Mark claims with `<!-- F12 -->` in `article.md` and an "Evidence map" block at the end of `post.md` and `carousel.md`; strip only in the final paste copy.
6. Re-verify every fact at the pinned ref right before handoff; line numbers drift.

## Honest hook patterns

Pick one pattern; do not stack. Test: *can a skeptical reader verify the opening claim in the repo or the cited source within five minutes?* The five patterns (contrarian claim, real failure story, "the system that wrote this", surprising number, before/after diff), each with its honesty test, and a good/bad example are in `references/package-templates.md`.

Refuse: invented scale ("analyzed 10,000 repos"), invented urgency, fake dialogue, unnamed-expert authority, outrage bait, and any hook the body does not pay off. No real failure story or number? Use a reproducible demo (command plus real output), a real before/after diff, or a design trade-off with its evidence.

## Genericity and privacy

The output must read as if written by an outsider with no private context.

- Remove or generalize: employers, clients, internal projects, products, teams, people (colleagues, reviewers, mentors, managers), ticket IDs, internal URLs, hostnames, IPs, account, bucket, or queue names, usernames, emails, local paths. Use neutral placeholders (`<project>`, `example.com`) or the public project itself.
- Do not mention the author's employment, studies, job search, or personal situation unless the human puts it in the brief.
- Scan text, snippets, captures, diagrams, and slides for keys, tokens, and connection strings; redact in the source, then re-render. Check rendered artifacts too: PDF and image text, alt text, metadata (author, creator, local paths).
- Run the exclusion-list grep from a list kept outside tracked files and deliverables; report only hit count and locations.
- Quote someone else's public words only with a public, dated, linkable source and a real need; otherwise omit the person.

## AI-assistance disclosure

Propose a plain one-line note that matches what happened; the author edits it (example: "Drafted with AI assistance; every claim was checked against the linked source."). Put it in every asset as the references direct; a missing or misleading one is a rubric blocker. The only waiver is Medium's assistive-use exemption, applied here to grammar and spelling help only. Do not strip C2PA metadata from AI images. Disclosure never replaces verification.

## Never post and validation

- Handoff and gates: workflow Phase 6. No platform APIs, logged-in browser pasting, scheduling, or emailing drafts to third parties.
- To publish, the human gives an explicit current instruction naming the platform, the account, the exact text, and the assets; show that exact text in its own message and wait for approval. Material edits need a new approval. Platform-only checks (link preview, mobile truncation, tag lookup) go in `HANDOFF.md` for the human.
- Score with `rubrics/technical-content.md` under the workflow. Mechanical checks first: every `F<n>` resolves to a shippable row; the limit checks in both platform references; snippets run at the pinned ref; links resolve (read-only); page sizes; image inspection log; genericity grep clean over text, alt text, filenames, metadata, and text in images, re-run after the last edit.

## Common failure modes

Stale numbers (recompute at the pinned ref); hook not paid off (rewrite the hook, not the body); generic AI cadence (stacked triads, "game-changer", "delve": use concrete nouns, real artifacts, varied sentence length); diagram nodes not in the code (prove each with a path); carousel text too small on a phone (type floors in `references/visual-assets.md`); private detail in screenshots, PDF metadata, or alt text (sweep rendered artifacts).

## References

Platform numbers are time-sensitive: each carries a source URL and verification date (2026-10-01); re-check against the platform's current help page when older than a few months; treat `unverified` as unknown.

- `references/medium-article.md` - before drafting `article.md`: Medium specs, anatomy (1,100-2,000 words, up to five tags), craft, SEO, disclosure.
- `references/linkedin-post-and-carousel.md` - before drafting `post.md` and `carousel.md`: LinkedIn specs; claim in the first ~140 characters, one call to action shared by all assets, at most three hashtags, no engagement bait, no tagging without approval; carousel 8-10 slides, one page size, at most ~35 words per slide.
- `references/visual-assets.md` - at step 6: cover, diagram, slide design, rendering, inspection. Reuse `skills/diagram-authoring` and `skills/markdown-pdf-export`; inspection of every generated image and PDF page is mandatory. A check that cannot run is reported as not run, never as passed; never state a visual passed inspection unless the rendered file was opened and checked.
- `scripts/render_assets.py` - renders `slides.html` to the carousel PDF and PNGs, or a cover HTML to `cover.png`.
- `references/package-templates.md` - package tree, skeletons, hook-pattern table.
- Publishing a finished draft (only after the approval in Never post): `workflows/study-publication-medium-linkedin.md` (Phases 7-10).
