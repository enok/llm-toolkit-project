---
title: LinkedIn share post and document carousel
tags: [linkedin, post, carousel, pdf, hashtags, link-preview, evidence]
---

# LinkedIn share post and document carousel

Companion to `skills/technical-content-publishing/SKILL.md`. Use it to draft `post.md` and `carousel.md` (and the carousel PDF) from a verified `fact-sheet.md`. Draft only: nothing here authorizes posting.

## Platform facts (verified 2026-10-01)

Status legend: **primary** = platform help or developer documentation; **third-party** = consistent across several secondary sources, but the platform's own member help page could not be fetched (its robots.txt blocks fetching); **contested** = sources disagree or rely on unconfirmed analysis; **unverified** = no usable source. Re-verify before relying on a value after a few months.

| Item | Value | Status | Source (verified 2026-10-01) |
| --- | --- | --- | --- |
| Post text limit | 3,000 characters (spaces, emoji, and line breaks count). The official Posts API documentation states no number | third-party | https://authoredup.com/blog/linkedin-character-limit ; https://contentin.io/blog/linkedin-post-specs/ ; https://espirian.co.uk/linkedin-document-posts/ |
| "See more" truncation | Roughly 210 characters on desktop and 140 on mobile; it varies with device and formatting and is an approximation | third-party | https://authoredup.com/blog/linkedin-character-limit ; https://contentin.io/blog/linkedin-post-specs/ |
| Comment length | 1,250 characters | third-party | https://authoredup.com/blog/linkedin-character-limit |
| Hashtags | "3-5 per post" is the common figure but traces to marketing guides, not a platform help page. Another analysis claims hashtags no longer help reach and suggests 1-2 inline | contested | https://contentin.io/blog/linkedin-post-specs/ ; https://www.dataslayer.ai/blog/linkedin-algorithm-february-2026-whats-working-now ; https://connectsafely.ai/articles/linkedin-hashtags |
| Links in the post | Third-party analyses report roughly 60% less reach for posts with an external link, and say the "link in first comment" workaround is now penalized too. The platform has not confirmed this; the true size is unknown | contested | https://www.feedboss.ai/blog/do-linkedin-links-reduce-reach ; https://www.dataslayer.ai/blog/linkedin-algorithm-february-2026-whats-working-now |
| Document formats | PDF, PPT, PPTX, DOC, DOCX | primary | https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/documents-api |
| Document size and pages | Cannot exceed 100 MB and 300 pages | primary (API docs; member help page not fetchable, third-party sources agree) | https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/documents-api ; https://espirian.co.uk/linkedin-document-posts/ |
| Recommended page size | The platform publishes no pixel size; every page must be the same size. Third-party guidance: 1080x1350 (4:5 portrait) or 1080x1080; 16:9, 9:16, 1:1, and 4:5 are reported as supported | third-party | https://heymark.ai/en/solutions/linkedin-carousel-pdf/ ; https://contentin.io/blog/linkedin-post-specs/ ; https://connectsafely.ai/articles/linkedin-document-posts-pdf-guide-2026 ; https://espirian.co.uk/linkedin-document-posts/ |
| Ideal slide count | No platform figure. One third-party guide suggests 5-10 slides, 15 as an upper bound | unverified (heuristic) | https://connectsafely.ai/articles/linkedin-document-posts-pdf-guide-2026 |
| Document title and conversion | A document title is entered at upload; DOCX and PPTX are converted to PDF | third-party (single source) | https://espirian.co.uk/linkedin-document-posts/ |
| Document posting restrictions | One source says document posts are created from the desktop site and cannot be scheduled by third-party tools | unverified (single source; check at post time) | https://espirian.co.uk/linkedin-document-posts/ |
| Link-preview image | 1200x627 px (1.91:1), center-cropped; minimum width 200 px or it shows as a small thumbnail; up to 5 MB; JPEG, PNG, WebP, GIF; `og:image` must be an absolute, public, HTTPS URL. A single source says organic posts moved to smaller thumbnail layouts in 2024 | third-party | https://opengraphplus.com/consumers/linkedin/images ; https://kinsta.com/blog/linkedin-debugger/ ; https://contentin.io/blog/linkedin-post-specs/ |
| Link-preview refresh | LinkedIn caches previews; the Post Inspector tool refreshes the cache. Cache duration: unverified | third-party | https://kinsta.com/blog/linkedin-debugger/ |
| Single-image post | Width 1080 px or more; 1080x1350 or 1080x1080 recommended; supported ratios 3:1 to 4:5; minimum 552x276 | third-party | https://contentin.io/blog/linkedin-post-specs/ |
| AI-generated image labels | Images with C2PA provenance metadata can be labelled as AI-generated (announced May 2024). Text posts: not addressed | third-party news | https://commsroom.co/linkedin-enhances-ai-transparency-with-new-content-labels/ |

Treat any engagement statistic from these vendor sources (for example claims that documents outperform other formats) as marketing data, not as evidence for your content decisions, and never quote it in a post.

## Link placement (the debate)

Evidence is third-party and contested: some analyses say an external link in the body suppresses reach, and that the first-comment workaround no longer avoids it. None of it is confirmed by the platform.

Practice that holds up either way:

1. Write the post so it delivers its full value without the link.
2. Produce two versions and let the human choose: (A) link at the end of the body, one line saying what the reader gets; (B) no link in the body, link in a first-comment draft.
3. Do not promise the human a reach outcome for either choice. Record the decision in `HANDOFF.md`.
4. A carousel carries its value inside the document; the article link is optional there.

## Hashtags

- Default: zero to three, topical, at the end, in PascalCase (`#SoftwareEngineering`); never a stack of generic tags.
- Reason: the "3-5" rule is a marketing convention and another analysis argues tags no longer drive reach; the cost of one to three relevant tags is low.
- Never invent a branded tag; check that a tag is used for the same topic before suggesting it (human checks on the platform).

## Post anatomy

Plain text; assume no Markdown rendering. Short paragraphs separated by blank lines. Decorative Unicode "bold" or "italic" letters may read poorly with screen readers (commonly reported, unverified): avoid them.

| Part | Rule |
| --- | --- |
| Hook (first line or two) | The claim itself, inside the first ~140 characters so it survives both truncation points; must stand alone and be checkable. No "I'm excited to announce", no throat-clearing |
| Scene or proof (3-6 short lines) | One real fact from the fact sheet, with scope: what, where, how counted |
| Insight (2-3 lines) | The non-obvious takeaway; opinion labelled as opinion |
| Call to action (1 line) | Exactly one, the same as in the article and carousel: read or try something specific (what the reader gets at the link or in the first comment, or "details in the carousel"), or answer one specific question a practitioner can answer from experience; never "Agree?" |
| Disclosure (1 line) | The plain AI-assistance note the author approved (see below), before the hashtags |
| Hashtags | 0-3, last line |

- Length: 1,000-1,800 characters by default (toolkit heuristic); hard cap 3,000. Shorter is fine when the hook carries it.
- Variants: write the main post plus two alternate openers (different patterns from `SKILL.md`), each with the fact IDs it relies on.
- Banned: engagement bait ("comment YES", "repost if"), tagging people or companies without the human's approval, claims not in the fact sheet, fake scarcity, outrage framing, screenshots of private tools, the author's employer or clients.
- Emoji: none or very sparing; never as bullet decoration across the whole post.
- Alt text for every attached image.
- Evidence map: end `post.md` with a block mapping each claim to `F<n>`; remove it from the paste copy.

### Disclosure

No LinkedIn rule on disclosing AI-assisted text was found (verified 2026-10-01), but the toolkit rubric expects a plain disclosure that matches what happened in every asset. Put the author-approved line in the post (short, before the hashtags) and on the closing carousel slide or its footer. Do not strip provenance metadata from AI-generated images: the platform can label images that carry C2PA metadata (third-party news, May 2024).

### First-comment draft

Optional, up to 1,250 characters (third-party limit): the link, one extra verified fact or "how to run it" line, and an invitation to ask. Labelled `NOT POSTED`. Replies to readers' comments are separate human-facing writes (`rules/human-comment-reply-gate.md`); do not draft them in advance as if approved.

## Carousel (document post)

A carousel is a PDF whose pages are slides. Build it from HTML (`references/visual-assets.md`).

| Slide | Role | Rule |
| --- | --- | --- |
| 1 | Cover | The claim as a title (about 10 words or fewer), a short subtitle, a swipe cue. No employer or client branding |
| 2 | Problem | One concrete failing scene or artifact |
| 3 | Idea | The mechanism; a simplified version of the hero diagram, redrawn from the same source with larger text |
| 4 to N-3 | Proof (2-4 slides) | One fact per slide: a big verified number with scope, or a short code or output snippet (about 8 lines at most); source tag in the footer (`path @ ref`) |
| N-2 | What went wrong or trade-off | A real failure or limit |
| N-1 | Try it | Up to three commands and the expected result |
| N | Call to action | The one ask (same as in the post and article) and where the article lives; author handle only if supplied |

- Slides: 8-10 by default (six fixed slides plus 2-4 proof slides); third-party guide: 5-10, max 15. Footer page marker `n/N`, filled in by the renderer (`references/visual-assets.md`), never typed by hand.
- Words: about 35 per slide at most (heuristic). One idea per slide; the headline carries it.
- Page size: identical for every page; default 1080x1350 px (4:5). The platform publishes no pixel size, so this is a third-party-backed choice.
- File: PDF under 100 MB and 300 pages (the platform maximum); aim far below it. The text must be selectable (checked with `pdftotext` when present, else `pypdf` or a PDF viewer's text selection) for accessibility and search.
- Type floors at 1080 px wide (a phone shows the slide about 375 px wide, roughly 0.35x): headline 72 px or more, body 40 px or more, code 32 px or more, footer 24 px or more. Margins 96 px. Body contrast at least 4.5:1. Never convey meaning by colour alone.
- Each slide must make sense alone: a skimmer sees slides out of order.
- Text alternative: `carousel.md` holds the slide-by-slide copy plus one text alternative per slide (what a screen-reader user needs to get the slide), and the PDF keeps selectable text. The post may carry a one-sentence summary of the deck.
- Document title entered at upload: write it in `HANDOFF.md` (claim-style, no hashtags).
- Metadata: set a neutral PDF title; no author path or tool-chain paths.
- Accompanying post: hook within 140 characters, one sentence on what the deck shows, optional link choice as above, 0-3 hashtags.

## Limit checks (run before handoff)

Measure with a script or command, not by eye; record the numbers in `HANDOFF.md`.

| Check | Pass condition | How |
| --- | --- | --- |
| Post length | At most 3,000 characters, counting spaces, emoji, and line breaks | `python3 -c "import sys;print(len(open(sys.argv[1],encoding='utf-8').read()))" <paste-copy>` on the paste copy (without the evidence map and header); counts code points, so it may over-count emoji |
| Hook before truncation | The claim sits inside the first 140 characters; nothing essential is only after about 210 | Print the first 140 and 210 characters and read them alone |
| Hashtags | 0-3, final line, PascalCase | Read the last line |
| First comment | At most 1,250 characters (third-party limit) | Same count as above |
| Link variant | One of A or B chosen and recorded; the post works without the link | Read the post with the URL removed |
| Document format | PDF; at most 100 MB and 300 pages | `pdfinfo <file>.pdf` and `ls -l` |
| Page size | Every page identical; default 1080x1350 px = nominally 810 x 1012.5 pt at 96 dpi (Chromium may round, for example 1013.04 pt; check identical and within about 1 pt) | `pdfinfo -f 1 -l <N> <file>.pdf` when present, else the Python-stdlib `/MediaBox` fallback in `references/visual-assets.md` |
| Slide text | Selectable, in reading order; at most ~35 words per slide | `pdftotext -layout <file>.pdf -` when present, else `pypdf`; if neither exists, report "not run" |
| Alt text | Every attached image and every slide has a text alternative | Count entries in `alt-text.md` and `carousel.md` |
| Link preview (only if a link is shared) | `og:image` 1200x627, public HTTPS, under 5 MB | Fetch the page's `og:image`; check dimensions and size |

### Carousel checks before handoff

- [ ] Same page size on every page and the expected page count (`pdfinfo -f 1 -l <N> <file>.pdf`, or the stdlib fallback)
- [ ] Every page rendered (`pdftoppm -r 80 -png`) and inspected (image quality check); no clipped, overlapping, or tiny text
- [ ] Slide text is extractable in reading order (`pdftotext` or `pypdf`)
- [ ] Every number and quote on a slide maps to a shippable fact-sheet row (verified or author-confirmed)
- [ ] Genericity sweep over slide text, notes, alt text, and PDF metadata
- [ ] Viewed at phone width: body text still legible

## Paste and upload steps (copy into `HANDOFF.md`)

The assistant does not perform these. The human does, on the platform, after approving the exact text.

1. Start a post on the author's profile. Paste the paste copy of `post.md` (no evidence map, no header, no fact markers). Check line breaks and that no raw Markdown characters show.
2. Preview truncation on desktop and on a phone; the claim must be visible before "see more".
3. Link: apply the chosen variant. If the link is in the body, check the preview card; refresh a stale or wrong card with the platform's Post Inspector tool (described in the Kinsta guide cited above; the tool's own URL was not fetched, so locate it from the platform).
4. Carousel: add a document to the post, upload `<slug>-carousel.pdf`, set the document title from `HANDOFF.md`. Document posts are reportedly desktop-only (unverified); check what the author's client allows at post time.
5. Add alt text for any standalone image; confirm the disclosure line is present.
6. Review the final post once more against `fact-sheet.md`, then publish only on an explicit current instruction naming the platform, the account, the exact text, and the assets. Post the first comment, if used, as a separate approved action.

## Packaging (`NOT POSTED`)

`post.md` starts with `NOT POSTED - draft for human review` and contains: main post, two alternate openers, link variant A/B, first-comment draft, hashtag set, disclosure line, evidence map. `HANDOFF.md` lists the paste and upload steps above, the limit-check results, the decisions the human must make (link variant, disclosure wording, hashtags), and open risks. The assistant stops at the draft.
