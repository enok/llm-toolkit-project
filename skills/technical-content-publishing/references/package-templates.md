---
name: package-templates
description: Package tree, fact-sheet row, angle/carousel/alt-text/HANDOFF skeletons, and the honest-hook pattern table for technical-content-publishing
---

# Package templates and hook patterns

Companion to `skills/technical-content-publishing/SKILL.md`. Moved out of the skill body to keep it short; nothing here changes the rules. Every `*.md` deliverable starts with a `NOT POSTED` header line. The workflow and rubric define what must be in each file.

## Package layout

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

## Honest hook patterns

Pick one; do not stack. Test: can a skeptical reader verify the opening claim in the repo or the cited source within five minutes?

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
