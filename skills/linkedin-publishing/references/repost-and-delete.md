---
title: Repost and delete a LinkedIn post
tags: [linkedin, repost, delete, approval-gate, back-links]
---

# Repost and delete

Use this reference when a published post must be replaced, most often because it went out
without its image. Media cannot be added after publishing, so the only fix is a new post with
the image followed by deleting the old post. Both are external writes with separate approvals.

## Decide first

1. Confirm the gap: the published post lacks the image it should carry.
2. Open the old post and note its reactions and comments. Deleting it discards them and any
   replies from other people; tell the user this before asking for the delete approval
   (`rules/human-comment-reply-gate.md`).
3. Offer the alternative of leaving the old post in place and posting nothing new, and let the
   user choose.

## Procedure

1. **Repost with the image.** Run the normal flow from `SKILL.md`: show the full text and image
   as `NOT POSTED`, get explicit approval, attach the image
   ([image-attach-recipe.md](image-attach-recipe.md)), verify the text hash
   ([composer-automation.md](composer-automation.md)), post, and read the new `<post-url>`.
   Verify the new post renders text, image, and article link.
2. **Ask for delete approval separately.** In its own message state: the old post's URL
   (`<old-post-url>`), the new post's URL (`<post-url>`), what will be lost (reactions,
   comments), and that deletion cannot be undone. Wait for an explicit approval that names the
   old post. Approval for the repost does not cover the delete.
3. **Delete the old post.** Open `<old-post-url>`, use the post's "..." (control) menu, choose
   "Delete post", and confirm in the dialog. Do not delete the new post by mistake: check the
   URL in the address bar before opening the menu.
4. **Verify.** Navigate to `<old-post-url>` again; the page should read "Post not found". If it
   still renders, report that the delete did not complete.
5. **Repoint back-links.** Replace `<old-post-url>` with `<post-url>` everywhere it was
   published:
   - the article (edit the published article's LinkedIn link);
   - the repository README (through a pull request when the default branch is protected);
   - any other doc or post that referenced it.

   Each edit is an external write: draft it, show it, and get approval before applying it.
6. **Check bidirectionality.** The new post links to the article; the article and README link
   to `<post-url>`; no reference to `<old-post-url>` remains.

## Report to the user

Return a short table: old URL (deleted, "Post not found" confirmed), new URL, each back-link
location and its status (updated, pending approval, or pull request open).

## Avoiding the repost

Most reposts are avoidable. Before the first Post click, tick the checklist at the end of
[image-attach-recipe.md](image-attach-recipe.md): image preview inside the composer, text hash
matches, user approval of exact text and image.
