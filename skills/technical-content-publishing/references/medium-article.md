---
title: Medium-style long-form technical article
tags: [medium, article, technical-writing, evidence, seo, disclosure]
---

# Medium-style long-form technical article

Companion to `skills/technical-content-publishing/SKILL.md`. Use it to draft `article.md` from a verified `fact-sheet.md`. Draft only: nothing here authorizes publishing.

## Platform facts (verified 2026-10-01)

Status legend: **primary** = the platform's own help or documentation page; **third-party** = secondary source, platform page not found or not fetchable; **unverified** = no usable source found, do not rely on it. Re-verify values before relying on them after a few months.

| Item | Value | Status | Source (verified 2026-10-01) |
| --- | --- | --- | --- |
| Tags per story | Up to 5 ("You can add up to five topics per post") | primary | https://help.medium.com/hc/en-us/articles/214741038-Tags ; https://medium.com/blog/tips-and-tricks-for-medium-writers-1d79498101c3 |
| Display title and subtitle | Editable from the story's menu ("Change display title/subtitle"); no character limit is published | primary for the feature; limit unverified | https://medium.com/blog/tips-and-tricks-for-medium-writers-1d79498101c3 |
| SEO title / SEO description | Separate fields under the story menu, "More settings"; they do not replace the visible title and subtitle. Google truncates SEO titles over 60 characters and SEO descriptions over 156; if omitted, Google builds one from content or subtitle | primary (Medium handbook posts, undated) | https://medium.com/medium-handbook/seo-tips-to-make-your-stories-discoverable-and-grow-your-readership-b0c8230a8200 ; https://medium.com/medium-handbook/how-to-use-medium-seo-settings-to-reach-more-readers-97facde95e83 |
| Image formats and size | Editor accepts .JPG, .JPEG, .GIF, .PNG up to 25 MB (WebP and SVG are not listed: do not deliver them) | primary | https://help.medium.com/hc/en-us/articles/215679797-Images |
| Image minimum width | At least 1192 px wide for all placement options to appear; Medium's SEO post says at least 1200 px | primary | https://help.medium.com/hc/en-us/articles/215679797-Images ; SEO handbook post above |
| Image recommended widths | 1400 px column-wide, 2040 px outset, 2500 px screen-wide; content column about 700 px | third-party | https://mediumcourse.com/how-to-format-images-in-medium-articles/ ; https://medium.com/geekculture/how-featured-images-work-on-medium-how-to-set-the-focal-point-3bcba35755dc |
| Image size choices, alt text | Editor offers three sizes per image; alt text and captions supported; italics are not supported in captions | primary | https://medium.com/blog/tips-and-tricks-for-medium-writers-1d79498101c3 ; https://help.medium.com/hc/en-us/articles/215679797-Images |
| Code blocks | New line, then type three backticks, or use the `{ }` button in the plus menu; inline code uses single backticks; syntax highlighting exists; code blocks are not supported in responses. Language selection: unverified | primary | https://help.medium.com/hc/en-us/articles/35756844492439-Using-code-blocks-and-inline-code |
| Embeds | Pasting a link and pressing enter embeds supported services (the guide lists Tweets, Threads, Skeets, Medium stories, YouTube, Vimeo, Facebook video, SoundCloud, Spotify). Gist embeds: unverified | primary | https://medium.com/blog/tips-and-tricks-for-medium-writers-1d79498101c3 |
| Import from URL | Stories (your stories page) > Import a story > paste URL > Import. Backdates to the original date and adds a canonical link to the source. Only for content you have the right to import. If the page cannot be interpreted you may see a blank page or an error; then move the content manually | primary | https://help.medium.com/hc/en-us/articles/214550207-Importing-a-post-to-Medium ; https://help.medium.com/hc/en-us/articles/360033931713-Trouble-importing-content-using-the-import-tool |
| Ideal reading time | No current official figure. A 2013 platform analysis found 7-minute posts captured the most total reading time on average, with an explicit warning that variance is large and quality matters more than length | primary but old (2013); not a rule | https://medium.com/data-lab/the-optimal-post-is-7-minutes-74b9f41509b |
| Words per minute used for the "min read" label | unverified | unverified | none |
| AI content policy | AI-generated writing must be disclosed within the first two paragraphs (example wording: "This story was written with the assistance of an AI writing program."); AI-generated images need a caption note; assistive uses (the page lists outlining, grammar, fact verification) need no disclosure, a carve-out this toolkit applies to grammar and spelling help only; undisclosed AI writing gets "Network Only" distribution; fabricated statistics or hallucinated information are prohibited | primary (undated page) | https://help.medium.com/hc/en-us/articles/22576852947223-Artificial-Intelligence-AI-content-policy |

Toolkit estimates (not Medium values): assume roughly 200-250 words per minute, so a 5-9 minute read is about 1,100-2,000 words. Treat this as a planning range, not a target to stretch to.

## Deliverable format

`article.md` starts with a metadata block (removed from the paste copy), then the body:

```markdown
<!-- NOT POSTED - draft for human review -->
<!--
display_title:   <claim-style title>
subtitle:        <one sentence: stake or proof>
seo_title:       <= 60 chars, keyword near the start
seo_description: <= 156 chars, main idea first
tags:            <= 5, specific first
cover:           visuals/cover.png  | alt: <one sentence>
canonical_url:   <only if first published elsewhere>
disclosure:      <line, or "none - grammar/spelling help only">
pinned_ref:      <short SHA or tag + date>
-->
# <Title>
...body with <!-- F12 --> fact markers after claims...
```

Images use relative paths under `visuals/`. Keep Markdown as the source of truth. Whether the Medium editor converts pasted Markdown syntax is unverified: also render a formatted preview (HTML) the human can copy from, and have the human check headings, code blocks, and image placement in the editor before publishing.

## Title and subtitle

- Title: a specific claim or a specific question the piece answers. Keep it short enough to read in one glance; keep the SEO title within 60 characters.
- Subtitle: adds the stake or the proof (for example a verified number with its scope); never restates the title.
- Honest title shapes (examples are placeholders):
  - Contrarian: "<Common practice> is the wrong default for <situation>"
  - Failure-first: "What broke when we <did X>, and the check that now catches it"
  - Mechanism: "How <system> decides <thing> without <expensive step>"
  - Number: "<Computed count> <things> in <scope>: what the shape tells us"
  - Meta: "The pipeline that produced this article, and where it failed"
- Avoid: "ultimate guide", "N things you must", unqualified superlatives, all caps, a title promising a number the piece does not contain.

## Structure

Budgets are planning ranges for a 1,100-2,000 word piece.

1. **Lede (60-120 words).** The hook from `SKILL.md`, the stake, and a promise the reader can check. If the human wants a disclosure line, it sits within the first two paragraphs.
2. **The problem as a scene (150-250).** A concrete failing artifact, command, or situation. No abstractions before the first example.
3. **The idea (250-400).** The mechanism in plain words, with the hero diagram. One idea; name its parts once and keep the names.
4. **Proof (300-500).** Real code, config, or output from the pinned ref; numbers with scope and method. Show the artifact, then say what it means.
5. **What went wrong (150-300).** A real failure and its fix, sourced from artifacts. This section is what makes the rest believable.
6. **Trade-offs and limits (100-200).** When not to use it, what it costs, what you did not test.
7. **Try it (80-150).** Commands the reader can run, a pinned permalink, and what output to expect.
8. **Close (40-80).** One takeaway and the one call to action, the same as in the post and carousel (try a command, read a path, or answer one specific question). No recap of the sections.

If a section has no evidence, merge or cut it. Do not pad to reach a length.

## Craft

- Headers state claims ("The validator must not be the producer"), not labels ("Validation").
- One idea per section; end each section on its consequence for the reader.
- Replace adjectives with artifacts: a path, a diff, a number, a log line.
- Numbers carry unit, scope, and ref ("`<N>` tracked files at `<ref>`, counted with `git ls-files`").
- Use first person singular only for author-confirmed experience; describe the project in the third person ("the repo does X"). Avoid unexplained "we".
- Write opinions as opinions and predictions as predictions.
- Vary sentence length; cut stacked triads and filler transitions. Common machine-sounding words to avoid: "game-changer", "revolutionary", "delve", "seamless", "supercharge", "unlock", "in today's fast-paced world".
- Explain every term the target audience may not know once, at first use, in half a sentence.
- Every claim a skeptic might doubt gets its evidence in the same paragraph.

## Code and diagrams

- Code comes from the pinned ref and was run. Show the command and real output. Trim with `...` markers and say so. For anything longer than about 20 lines (toolkit heuristic), link a permalink to the path at the ref instead.
- Never include real hostnames, tokens, account IDs, usernames, or local paths in code or output; redact in the source and re-run.
- One hero diagram built per `skills/diagram-authoring` (every node proven by a path), exported as PNG at the widths in `references/visual-assets.md`. Caption states what it shows and the ref; add alt text.
- Do not rely on syntax-highlight language labels or embeds that are marked unverified above; the human checks them in the editor.

## SEO and discovery

- SEO title and description: write them deliberately, keyword natural and early, main idea inside the first 156 characters.
- Tags: use all five when relevant, specific before broad; pick tags that match real topics the author has confirmed exist on the platform.
- Alt text on every image. Cover image at least 1200 px wide.
- Links: the repo at a pinned permalink, plus one or two primary sources. No link lists.

## Import versus paste

- Import-from-URL is for content already published elsewhere that the author owns (for example a personal site post); it backdates and adds a canonical link. It is not part of a first-publication path for a never-posted draft.
- If cross-posting from the author's own site, set the canonical URL in the metadata block and tell the human which path to use.
- For a fresh draft, the human pastes into the editor. Import failures (blank page, error) fall back to manual paste.

## Disclosure

Follow the policy row in the platform table. The toolkit rubric expects a plain disclosure that matches what happened, so by default:

- If the assistant drafted the prose, include a one-line note within the first two paragraphs (Medium's policy position), wording approved by the author, for example "This story was written with the assistance of an AI writing program." or a more specific line such as "Drafted with AI assistance; every claim was checked against the linked source."
- The only waiver is Medium's assistive-use exemption, which this toolkit applies to grammar and spelling help only. Outlining, drafting, rewriting, or restructuring prose by the assistant is AI-generated writing: include the disclosure.
- Disclose AI-generated images in the caption ("This image was created using an AI image creation program." is the policy's example). Cover and diagrams rendered from code are not AI-generated images.
- Disclosure does not excuse unverified facts: the policy also prohibits fabricated statistics and hallucinated information.

## Limit checks (run before handoff)

Measure, do not eyeball; record results in `HANDOFF.md`.

| Check | Pass condition | How |
| --- | --- | --- |
| Tags | At most 5 | Count the metadata block |
| SEO title / description | At most 60 / 156 characters | `python3 -c "print(len('<text>'))"` or a character-count command |
| Reading time | Planning range 1,100-2,000 words (estimate, not a Medium rule) | `wc -w` on the body without metadata and comments |
| Images | PNG or JPG (or GIF) only; each at most 25 MB; each at least 1200 px wide; alt text present | Header dimensions or `identify`; `ls -l` |
| Code | Every block was run at the pinned ref; no secrets, hosts, or local paths | Re-run commands; grep |
| Fact markers | Every `F<n>` in the draft resolves to a shippable row (verified or author-confirmed) | grep the markers against `fact-sheet.md` |
| Links | Every link resolves (read-only check) and the repo permalink is pinned | HEAD or GET requests |
| Disclosure | Present as decided, within the first two paragraphs when required | Read the first 200 words |

## Paste and upload steps (copy into `HANDOFF.md`)

The assistant does not perform these. The human does, in the editor, after approving the exact text.

1. Open the Medium editor and paste the paste copy (metadata block, header, and fact markers removed) or the rendered preview. Check headings, lists, quotes, and code blocks; re-create code blocks with the editor's `{ }` button or three backticks if they did not convert.
2. Set the title and subtitle; if the display title differs from the SEO title, use the story menu's "Change display title/subtitle".
3. Insert each image from `visuals/` (PNG or JPG), pick its size, add alt text and a caption (plain text; no italics in captions). Add the AI-image caption note if applicable.
4. Story menu, "More settings": enter the SEO title and description.
5. On publish, add up to five tags when prompted.
6. Confirm the disclosure line; preview on desktop and phone; then publish only on an explicit current instruction naming the platform, the account, the exact text, and the assets.
7. If the article was first published on the author's own site, use "Import a story" with that URL instead of pasting (backdates and adds a canonical link); if the import shows a blank page or an error, paste manually.

## Pre-handoff checklist

- [ ] Display title, subtitle, SEO title (60), SEO description (156), up to 5 tags written
- [ ] Every number and quote maps to a shippable fact-sheet row (verified or author-confirmed) at the pinned ref
- [ ] Code ran; output pasted from the real run; no secrets or local paths
- [ ] Cover and hero diagram rendered and inspected (`skills/image-quality-inspection`); PNG or JPG only
- [ ] Alt text and captions written; disclosure decided
- [ ] Genericity sweep clean across text, images, alt text
- [ ] Length and reading time within the planning range
- [ ] `NOT POSTED` header present; scored with `rubrics/technical-content.md`
