---
title: Replace a published study publication with a new story and a new post
tags: [medium, linkedin, replace, unlist, pointer, more-pointer, back-links, drafts-only, approval-gate, readme]
---

# Replace a published study publication

Use this when a published story and its LinkedIn post(s) no longer fit their purpose (wrong
level, a tutorial where a short system design story is wanted, a title that names the study
topic) and the fix is a new piece with new URLs, not an edit. The old story points to the new one
and is unlisted; the old posts get a "More..." pointer; the repo README links are repointed.
Nothing is deleted unless the user asks separately.

Edit in place instead when only the title, subtitle, opening or closing change and the shape
survives ([aida-narrative.md](aida-narrative.md), retrofitting). A published LinkedIn post cannot
change its image, but its text can
(`skills/linkedin-publishing/references/repost-and-delete.md`).

## 1. Approvals and modes

Every step below is an external write with its own approval; approval of one does not cover another
(`rules/external-write-authorization.md`, `rules/human-comment-reply-gate.md`). Show each exact
text or change in its own message labelled `NOT POSTED`, then ask in a separate turn.

The approval mode comes from the profile ([positioning-profile.md](positioning-profile.md)); there
are exactly two names.

- **`gated` (default):** the user approves each step, draft creation included, as it comes up.
- **`drafts-only`:** creating the Medium draft and the LinkedIn draft is pre-approved; then stop for
  review (section 4). Publishing, posting, edits, pointer edits, unlisting, README changes and
  deletes always wait for the user's explicit approval of that action.

Public URLs of new pieces do not exist until they are published, so pointer lines and back-links
can only be written after the publish steps; do not put placeholders in anything that goes live.

## 2. Preparation (nothing public changes)

1. Read the profile; build the new article and post to its budgets
   ([system-design-article.md](system-design-article.md)); run `check_publication.py` on both and the
   `publication-reviewer` agent; show the drafts with the stage map.
2. Repo prerequisites go through pull requests on the protected default branch (for example the
   hero system-design diagram). Image URLs in the article are pinned to the merged commit SHA.
3. Draft the three follow-up texts now so they can be approved together, with their URL fields
   still open: the pointer line for the old story, the "More..." line for each old post, and the
   README link changes. Fill them after the new URLs exist.

## 3. Order of operations (`gated` mode, and after review in `drafts-only` mode)

1. **Publish the new story.** The normal flow of `skills/medium-publishing/SKILL.md`: draft shown,
   approved, pasted, verified, publish dialog filled, explicit approval of the Publish click.
   Read the new `<story-url>`.
2. **Publish the new post.** Text with `<story-url>` as the one call to action; image attached;
   text hash verified; approval of the Post click (`skills/linkedin-publishing/SKILL.md`). Read the
   new `<post-url>`.
3. **Link the new pair.** Edit the new story to link `<post-url>` (one-link edit,
   [publish-dialog.md](publish-dialog.md) sections 5 and 6; "Save and publish" needs the explicit go).
4. **Old story: pointer, then unlist.**
   - Add an opening paragraph "Updated version: `<story-url>`" at the top of the old story with
     the editor's insert recipe ([publish-dialog.md](publish-dialog.md) section 5), approval of the
     exact text, "Save and publish", and a read-back on the post-redirect page.
   - Then unlist the old story in Medium's story settings. **Unverified:** no real run has recorded
     this. Expected path: open the story, the "..." menu, the story settings or visibility option,
     choose the unlisted setting, save. Read the labels on screen, change nothing else, and report
     what the screen offers. If no unlist option exists for a published story, stop and ask; do not
     delete the story instead.
   - Pointer first, unlist second: an unlisted story stays reachable by its old URL, so readers
     following old links still reach the pointer.
5. **Old posts: "More..." pointer.** For each old post, edit its text in place so the first line is
   `More... <post-url>` followed by the original text, as in
   `skills/linkedin-publishing/references/repost-and-delete.md` (default flow, steps 2 and 3). The
   old image stays.
6. **Repoint the README and other links by pull request.** Replace the old story and old post URLs
   with `<story-url>` and `<post-url>` in the repo README and any doc that links them. The default
   branch is protected: branch, pull request, merge only after the user names that pull request
   (`rules/git-conventions.md`).
7. **Verify bidirectionality.** The new story links to the new post and the repo; the new post links
   to the new story; the repo README links to both; the old story and old posts carry their
   pointers; no other file links an old URL. Grep the repo and the published pages for the old URLs.

## 4. Drafts-only mode

1. Create the Medium draft: paste, verify, fill the publish dialog, and stop before Publish
   ([paste-recipe.md](paste-recipe.md), [editor-verification.md](editor-verification.md),
   [publish-dialog.md](publish-dialog.md)). The draft stays in the user's Medium account. Read its
   story id from the editor address (`https://medium.com/p/<story-id>/edit`).
2. Create the LinkedIn draft: its article link is `https://medium.com/p/<story-id>` (Medium
   redirects that link to the story's final URL once it is published; **verify after publishing**
   that it does, and if it does not, edit the post text to the final URL as its own approved write),
   so `check_publication.py post --require-link https://medium.com/p/<story-id>` works before
   anything is published. Open the composer, attach the image, put the text in it and verify the hash (`skills/linkedin-publishing/SKILL.md`, steps 2 to 4). Do not click Post. Close
   the composer and choose to save it as a draft. **Unverified:** the dialog's wording and whether a
   saved draft keeps the attached image have not been recorded in a real run; reopen the draft and
   check text and image, and report what the screen offered.
3. Report both draft locations, the profile used, the `check_publication.py` output, the reviewer
   verdict, the stage map, and the list of actions that wait for approval (steps 1 to 7 of
   section 3). Then stop.
4. After the user reviews and approves an action by name, continue section 3 from that action.
   Edits the user requests to the drafts are made in the drafts, and the checks are run again.

## 5. Report

A short table: old story URL (pointer added, unlisted or not), new story URL, old post URLs
(pointer added), new post URL, each repo link location with its pull request status, and every step
left pending approval or marked unverified.

## 6. Pitfalls

- Do not unlist before the new story is published and the pointer is saved: readers of the old
  URL would find nothing.
- Do not delete the old story or posts to "clean up"; reactions and comments are lost and the old
  URLs stop resolving. Deleting an old post is the separate optional flow of
  `skills/linkedin-publishing/references/repost-and-delete.md`.
- Re-run the checks after every change to a draft; a budget that held before the edit may not hold
  after it.
