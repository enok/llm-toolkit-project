---
description: Publish a merged study repo as a short system-design-first Medium article and a LinkedIn teaser post per the consumer's positioning profile, gated by a shape check and a profile check, with drafts-only mode, README link PRs, back-links, a replacement path, and separate approval gates
---

# Study Publication: Medium And LinkedIn

Runs once the study repo is merged and green. Output: a Medium story and a LinkedIn teaser post that link to the repo and to each other in both directions, with the README links merged. Positioning (target role, primary focus, budgets, hashtag cap, approval mode) comes from the consumer's profile, not from this file (`rules/publication-positioning.md`).

Route through `rules/request-orchestration.md`. The root agent owns all writes, external mutations, and user communication. Constraints: `rules/external-write-authorization.md`, `rules/human-comment-reply-gate.md`, `rules/git-conventions.md`. Browser steps run on the user's machine in the signed-in session; bot checks and captchas go to the user.

Inputs: the merged repo (default branch, merge commit SHA), the tag list, the fact table and principles page, the intake answers (target role, content angle, approval gates), the profile (path, budgets, approval mode: `gated` or `drafts-only`), and the study topic's name (the term the title, subtitle, and post hook must not contain). Check diagram size at the destination and device-commit filenames.

Merge rule (Phases 8 and 10): merge only after the user names the specific PR number and base branch in the current session; when CI is green, state both and ask (the intake gate list is not that approval). Merge with squash.

## Validation Gate (before every draft is shown as ready)

Applies to the Phase 7 article, the Phase 9 post, a replacement draft, and a retrofit edit.

1. Shape check: `python scripts/check_publication.py article <draft> --profile <P> --title "<title>" --subtitle "<subtitle>" --forbid-title "<topic>"` and `... post <draft> --profile <P> --forbid "<topic>" --require-link <article-url>`; exit 0 required (1: a rule failed, 2: usage or file error; use `python3` where `python` is not Python 3). It checks, against the profile's budgets: article title <= 100 and subtitle <= 140 characters, neither holding the study topic's name; word, code-block, code-line and image counts inside the budgets; a "next step" heading; no Markdown leftovers such as `](http` in HTML. Post: total and hook length inside the budgets, no study topic in the hook, at most the hashtag cap with each hashtag backed by body text, and the article link present. Every failure blocks.
2. Profile check: the drafting assistant (or a separate read-only validator lane when the orchestrator dispatches one) checks the draft against the consumer's publication profile and `rubrics/technical-content.md` if that file exists. Fix every defect found; supply any missing input; run both checks again.
3. Show with the draft: the profile used (path, budgets), the AIDA stage map, the shape-check result, the profile-check result. A draft that has not passed both is not shown as ready; it stays `NOT POSTED` until the owner approves.

## Phase 7 - Medium Draft, Approval, Publish

Build from the merged repo content, never from memory, as a short system-design article, inside the profile's budgets and framed by AIDA (Attention, Interest, Desire, Action):

- title and subtitle name the system design problem or capability at the target role's level, never the study topic's name;
- the study topic appears once, in one short body section, as the mechanism, with one sentence naming the main principles (from the repo's principles page);
- 2-3 diagrams led by the hero system-design diagram, pinned to the merged commit SHA; when the repo lacks it, add it through a pull request first;
- at most one short snippet, a "Your next step" section, then the repo, post, and video links.

A profile that asks for a full tutorial keeps the tutorial order the profile names. Build paste-ready HTML with `python3 scripts/medium_paste_html.py build <draft.html> -o <draft.paste.html>`, then `python3 scripts/medium_paste_html.py check <draft.paste.html> --repo-raw-prefix <commit-pinned raw URL prefix>` (exit 0 required before anything is pasted).

1. Run the Validation Gate. `gated`: show title, subtitle, topics, preview image, stage map, and the full article text, labelled `NOT POSTED`, in its own message; ask for approval in a separate turn before creating anything. `drafts-only`: creating the draft is pre-approved; the same package goes in the report with the draft.
2. Paste into a new story and verify in the editor DOM: image count, code-block count and languages, SHA-256 of each block against its repo file, no Markdown leftovers.
3. Fill the publish dialog (title <= 100 characters, subtitle <= 140, <= 5 topics read back as chips; hero diagram as preview) and stop. In `drafts-only` mode the story stays a draft: record its draft link `https://medium.com/p/<story-id>` from the editor address and go to Phase 9.
4. Publish only after explicit approval of that action, in either mode (material edits need a new approval). Verify the public page after the redirect, record `<story-url>`.

## Phase 8 - README Link PR

Needs `<story-url>`, so it follows the publish. Branch plus PR that adds it to the repo README. CI green, then merge under the merge rule.

## Phase 9 - LinkedIn Teaser Post With Hero Diagram

1. Draft the teaser per the profile, in AIDA order: total length and hook (the first paragraph) inside the budgets (toolkit defaults 1,300 and 200 characters), hook at the system-design concept without the study topic's name, Interest in 2-3 lines, Desire as two or three short items from the repo or fact table, Action as `<story-url>` (the one primary call to action; the repo link is optional and secondary) plus one specific question, hashtags last, at most the profile's cap (default 5), each backed by text in the post. Image: the hero system-design diagram, re-checked at feed size.
2. Run the Validation Gate (in `drafts-only` mode `--require-link` takes the draft link from Phase 7).
3. `gated`: show the full text, stage map, and image, labelled `NOT POSTED`, in their own message; ask for approval in a separate turn. After approval, in the composer: image first, text verified by hash; report the hash match and image preview, get a separate go-ahead to click Post, then post, record `<post-url>`, decline boost prompts.
4. `drafts-only`: creating the LinkedIn draft is pre-approved. Attach the image and verify the text by hash, do not click Post, save the composer as a draft, reopen it and check text and image (wording and image retention are unverified, report what the screen offered). Report both draft locations and every action still pending approval (story publish, post, Phase 8, Phase 10); then stop. Continue from the action the user approves by name.
5. Earlier post: edit text or alt text in place. New image: post anew, edit a `More... <post-url>` first line into the old post, repoint the article and README links; delete the old post only if asked (`learnings/linkedin-image-change-needs-new-post-with-more-pointer.md`). Each is its own approval.

## Phase 10 - Back-Links

Edit the Medium story to add `<post-url>`: show the exact change labelled `NOT POSTED`, get approval, apply, "Save and publish", verify on the public page. Open a README PR adding `<post-url>`, CI green, merge under the merge rule. Final check: all six links resolve (repo, Medium, LinkedIn each point to the other two).

Adding AIDA or a positioned title to an already published story or post is the same kind of edit, in place.

## Replacement Path

When a published story and its posts miss the profile (wrong level, tutorial length, the study topic in the title), replace them instead of retitling. Every step is its own approval; `drafts-only` pre-approves only the two new drafts.

1. Build the new article and teaser through Phases 7 and 9, with the Validation Gate and any repo prerequisite by pull request.
2. Publish the new story, then the new post; edit the new story to link the new post.
3. Old story: add an "Updated version: `<story-url>`" paragraph, save, verify, then unlist it (unverified: report what the screen offers; if no option exists, stop and ask; never delete instead).
4. Each old post: edit the first line to `More... <new post-url>`; the old image stays.
5. Repoint README and doc links by pull request; grep the repo and published pages for the old URLs.

## Known pitfalls

- Put a single space on blank lines inside code blocks before pasting into Medium, then check one code box per listing. (sig: platform-quirk/medium-blank-line-splits-code-block)
- Run `python scripts/check_upload_target.py <snippet-file>` on every upload snippet before running it (exit 0 required); it checks that the snippet forwards the file only to the composer's own file input, never through a document-wide `input[type=file]` query or an `attachment-input` element (those belong to the messaging overlay); never click Send. (sig: safety-near-miss/linkedin-file-input-is-messaging) See `learnings/linkedin-composer-file-inputs-belong-to-messaging-overlay.md`.
- Click the exact topic suggestion in Medium's publish dialog and read the chips back; Enter adds the first suggestion. (sig: platform-quirk/medium-topic-autocomplete-swaps-topic) See `learnings/medium-change-topics-popover-enter-adds-first-suggestion.md`.
- Attach the LinkedIn diagram before pressing Post; media cannot be added afterwards. (sig: platform-quirk/linkedin-no-media-after-publishing) See `learnings/linkedin-cannot-attach-media-after-publishing.md`.
- Entity-encode non-ASCII characters before putting HTML on the Windows PowerShell 5.1 clipboard. (sig: env-constraint/powershell-clipboard-html-mangles-non-ascii)
- Scan the editor's rendered HTML, not only the source Markdown, for leftovers such as `](http`. (sig: validation-gap/markdown-leftovers-in-rendered-html)
- Structure every article and post as Attention, Interest, Desire, Action, show the stage map with the draft, and title it at the highest-level concept the body supports. (sig: spec-gap/post-missing-aida-structure)
- Read the positioning profile before drafting and run the shape check plus the profile check before showing a draft: a complete, cited draft can still be a long tutorial with the study topic in the title. (sig: spec-gap/publication-not-positioned-for-target-role) See `learnings/study-posts-system-design-first-short-teaser.md`.
