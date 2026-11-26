---
title: Link audit for a plan or document with many links
tags: [link-audit, youtube, study-plan, verification, review-lanes]
---

# Link audit for a plan or document with many links

Use when a study plan, README or document carries tens or hundreds of links
and the owner asks "check that all links still work" or "do these links match
their rows". Single-video proof stays in `SKILL.md` (`verify`); this is the
procedure around it.

1. **Extract every unique URL** from both the link annotations and the printed
   text (a PDF or document can show a URL that is not the real target, and the
   reverse). Keep, per URL, the rows that use it.
2. **Classify by kind** and check each with the right method: video (oEmbed,
   `verify`), course lecture, problem page, shared drive file, generic page.
3. **Login-gated links are "not checked", not broken.** A 401, a 403 or a bot
   wall (Cloudflare, an auth redirect) means the page exists behind a login.
   List them separately and verify them in the owner's signed-in browser; run
   the batch on the owner's machine, because sandbox egress often blocks the
   check itself.
4. **Semantic check.** For each URL, compare the target's title with the title
   of every row that uses it: a live link to the wrong lesson is a defect that
   a status code never shows.
5. **Review lanes must receive the FULL row text.** When the semantic check is
   split across lanes, build the input with the complete row, not a truncated
   excerpt. In one audit, truncated text left 31 of 276 records "unclear" and the
   root had to close them deterministically from the full source. Return
   per-record verdicts (match, mismatch, unclear) with the quoted evidence.
6. **A dead video id is often a 1-2 character typo of a live one.** Before
   replacing it, search the site that embeds the video (the origin page) for the
   real id. Replace from the canonical publisher only when no live variant exists.
7. **Verify the replacement independently** (`verify`, plus the title check
   from step 4), and apply it as the same-length edit in every copy (annotation,
   spreadsheet, generator source, JSON), as `SKILL.md` step 5 says.

Report counts per class: ok, not checked (login-gated), broken, mismatched,
replaced, and the list the owner must verify by hand.
