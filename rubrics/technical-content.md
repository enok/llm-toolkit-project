# Technical Content Rubric

Score drafted technical content - a long-form article, a social post, a document carousel, and their cover/diagram visuals - before it is handed to a human for posting. Use this rubric as the scoring step of `workflows/technical-content-publishing.md` (Phase 5); platform specifics (limits, truncation, formatting, sizes) come from `skills/technical-content-publishing/references/` and are checked there, not restated here.

The validator is read-only and must not be the producer of the content it scores (`workflows/task-quality-loop.md`).

---

## Scoring Scale

Score each criterion for the whole content set; when assets differ, the criterion takes the **lowest** score among the in-scope assets it applies to.

| Score | Meaning |
|-------|---------|
| **2 - Pass** | Meets the pass definition for every applicable asset |
| **1 - Partial** | Meets the core intent with a fixable gap (listed as a Suggestion); not available to Gate criteria |
| **0 - Fail** | Meets a fail definition (any Blocker signal) |

Criteria marked **Gate** (2, 6, 7) accept only a 2 and are scored on **Blocker signals only**: any Blocker scores 0; Suggestion-level findings are reported but never lower a gate score below 2. Criteria marked **Auto-fail** fail the whole content set on a single occurrence, regardless of the total. Mark a criterion `N/A` only when no in-scope asset can be judged by it.

---

## 1. Hook

**Pass:** The opening (the portion visible before the platform truncates or the reader scrolls) states a specific claim or tension that the evidence supports, appears in every asset, and matches the thesis. At least 3 candidates and the reason for the pick are recorded.
**Fail:** Clickbait, a claim the fact sheet does not support, a generic opener, or a promise the body does not deliver.

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Hook depends on an unsupported number, quote, or superlative | Yes | |
| Hook promises something the content never delivers | Yes | |
| Fewer than 3 candidates, or no stated selection reason | | Yes |
| Opener is a generic scene-setter ("in today's fast-moving world") | | Yes |
| Hook differs between article, post, and carousel without reason | | Yes |

## 2. Evidence Traceability (Gate)

**Pass:** Every number, quote, name, date, command, and path in the copy and visuals maps to a fact-sheet row (`ID | claim as it will appear | type | evidence | how verified | status`) with status `verified` or `author-confirmed`, tied to a pinned version. No `cut` row appears in copy. Landscape claims cite at least 3 dated sources, or are softened or removed.
**Fail:** Any untraceable fact, a number computed at a different version than the one pinned, or a figure taken from documentation or an agent's self-report instead of a command.

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Figure with no fact-sheet ID, a `cut` or unverified row, or a result that does not reproduce when its command is re-run | Yes | |
| Quote without file path and line | Yes | |
| Anecdote with no backing artifact (commit, log, run output) and no `author-confirmed` status | Yes | |
| "First", "only", or "best" claim without landscape evidence | Yes | |
| Source missing publication or retrieval date | | Yes |
| Number stale after a later edit and not re-checked | Yes | |

## 3. Specificity and Novelty

**Pass:** Claims are concrete: named mechanisms, real paths or commands from the fact sheet, at least one non-obvious detail (a trade-off, failure, or measured result), and a stated limitation. The piece says something the landscape sources do not already say.
**Fail:** Interchangeable with any article on the topic; abstract benefits with no mechanism or example.

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| No concrete example, command, or artifact anywhere in the piece | Yes | |
| Content restates the landscape sources with no new angle | Yes | |
| No limitation or trade-off acknowledged | | Yes |
| Filler paragraphs that could be deleted without loss | | Yes |

## 4. Structure and Scannability

**Pass:** The article states its thesis in the first screen, uses descriptive headings, one idea per section, short paragraphs, and code or commands in blocks. The post leads with the hook and uses white space. The carousel has one idea per slide with a hook slide, a coherent arc, and a closing slide.
**Fail:** A wall of text, headings that do not describe their sections, or ideas spread across sections with no through-line.

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Thesis not stated until deep in the piece | | Yes |
| Section headings that are labels only ("Overview", "Conclusion") | | Yes |
| Carousel slide carrying multiple unrelated ideas | | Yes |
| No discernible structure (no headings, slides, or breaks) | Yes | |

## 5. Platform Fit

**Pass:** Every limit check in the platform references passes (length, truncation point, supported formatting, page count, file type and size), and each asset follows its platform's conventions without paste-time repair.
**Fail:** Any limit exceeded, unsupported formatting that would render as raw syntax, or an asset in the wrong format.

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| A platform limit check fails | Yes | |
| Formatting that does not render on the target (raw markup in a post) | Yes | |
| Key point sits beyond the truncation point | | Yes |
| `*.md` deliverable (including saved verdicts) without a `NOT POSTED` header line, or a binary or source file (`slides.html`, diagram source, render scripts) not listed with its status in `HANDOFF.md` | Yes | |
| Paste/upload steps missing from the handoff | | Yes |

## 6. Genericity and Privacy (Gate, Auto-fail)

**Pass:** A case-insensitive grep with the consumer-supplied denylist, plus generic patterns, finds nothing in copy, alt text, filenames, file metadata, or text inside images. The denylist itself appears in no tracked file or report.
**Fail:** Any private name (employer, client, internal project, person), internal hostname, ticket key, credential, email, or local absolute path anywhere in the deliverables.

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Denylist match in any deliverable or its metadata | Yes - auto-fail | |
| Local path, hostname, token, or ticket key in a screenshot or caption | Yes - auto-fail | |
| Denylist terms written into a tracked file, prompt, or report | Yes - auto-fail | |
| Privacy grep not re-run after the last edit | Yes | |
| Private detail about a third party, even if not on the denylist | Yes - auto-fail | |

## 7. Honesty (Gate, Auto-fail on fabrication)

**Pass:** No invented statistics, benchmarks, testimonials, or user counts; claims are phrased at the strength the evidence supports (measured vs. observed vs. believed). A plain-language AI-assistance disclosure that matches what actually happened is present whenever AI drafted any of the text (in the article and the other assets as the platform references direct). The sole waiver is Medium's assistive-use exemption (grammar/spelling help only), recorded in `HANDOFF.md`.
**Fail:** Any fabricated or unmeasured figure presented as measured, or a missing or misleading disclosure without that recorded waiver.

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Fabricated or unsourced statistic, benchmark, or testimonial | Yes - auto-fail | |
| Anecdote embellished beyond its artifact | Yes - auto-fail | |
| AI drafted any text and no disclosure or recorded waiver exists | Yes | |
| Disclosure implies the work was entirely manual, or a waiver is recorded though AI drafted text | Yes | |
| Opinion presented as fact; no hedge where evidence is thin | | Yes |
| Project status overstated (maturity, adoption, license, visibility) | Yes | |

## 8. Call to Action

**Pass:** One clear, low-friction, relevant action (read the repo, try a command, answer a specific question), consistent across assets, to a target verified to resolve.
**Fail:** No CTA, several competing CTAs, engagement bait, or a CTA pointing to something that does not exist or is not public.

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Link or target does not resolve or is not accessible to the audience | Yes | |
| Engagement bait ("comment YES", tag-a-friend demands) | | Yes |
| More than one primary CTA | | Yes |
| CTA differs between assets with no reason | | Yes |

## 9. Visuals Legibility

**Pass:** Cover, diagram, and every carousel page pass the image quality gate: text is readable at the size the platform displays it, nothing is cropped or overlapping, diagram labels match fact-sheet names, contrast is sufficient, and exports are fresh relative to the final copy.
**Fail:** Unreadable or cropped text, a label not backed by evidence, a stale export, or an image that was not inspected.

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Any generated image or carousel page not inspected | Yes | |
| Text clipped, overlapping, or below the minimum size in `references/visual-assets.md` | Yes | |
| Diagram label or component not supported by the fact sheet | Yes | |
| Export older than the last copy or source edit | Yes | |
| Cover relies on tiny detail that disappears in a feed thumbnail | | Yes |

## 10. Accessibility

**Pass:** Every image has alt text that states its content and purpose; the carousel has a per-slide text alternative; text contrast meets WCAG AA (4.5:1 body text, 3:1 large text); meaning is never carried by color alone; links have descriptive text; headings are hierarchical.
**Fail:** Missing alt text, an image-only carousel with no text alternative, or color-only encoding in a diagram.

| Signal | Blocker | Suggestion |
|--------|---------|------------|
| Image with no alt text | Yes | |
| Carousel with no text alternative | Yes | |
| Contrast below WCAG AA for body text | Yes | |
| Alt text that only says "image" or repeats the caption | | Yes |
| "Click here" link text, or skipped heading levels | | Yes |

---

## Overall Pass Rule

The content set **passes** only when all of the following hold:

1. No **Auto-fail** condition occurred (any privacy leak under criterion 6; any fabrication or embellishment under criterion 7).
2. Every **Gate** criterion (2, 6, 7) scored 2.
3. No criterion scored 0.
4. The total is at least **80%** of the available points (16 of 20 when none is `N/A`).

Otherwise the verdict is **fail**, or **escalate** when the criteria are contradictory or the same reasoning defect survives two consecutive iterations (`workflows/task-quality-loop.md`). One failed mandatory criterion means fail, however high the total.

---

## Response Format

Return a read-only verdict; never edit the content. The root prepends the `NOT POSTED` header line and saves each verdict under `validation/` in the package.

```text
## Content Verdict
**Content set**: <name>  **Pinned version**: <id/date>  **Verdict**: Pass / Fail / Escalate  **Score**: N/20

### Criteria
| # | Criterion | Asset(s) | Score (0-2) | Evidence (file:line) | Defect class |
|---|-----------|----------|-------------|----------------------|--------------|

### Defects
| # | Severity | File:Line | Criterion | Issue | Class | Remediation |
|---|----------|-----------|-----------|-------|-------|-------------|

### Auto-fail Conditions
<none, or criterion + file:line + match count; never quote denylist terms>

### Regressions vs previous iteration
<none, or list>
```

Classify each defect `mechanical` (instructions or rework fix it) or `reasoning` (judgment is wrong), as in `workflows/task-quality-loop.md`. For privacy findings report `file:line` and the match number only, so the report itself stays free of forbidden terms.
