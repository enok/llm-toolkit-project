---
title: Replace a LinkedIn post - new post with a pointer (optional delete)
tags: [linkedin, repost, more-pointer, edit-in-place, delete, approval-gate, back-links]
---

# Replace a post: new post with a pointer

Use this reference when something in a published post must change. The file keeps its old
name so existing links to it keep working; the default is no longer "repost and delete".

## What the editor can change

The editor of a published post changes its text and its image alt text only. It cannot change
or add media (`learnings/linkedin-cannot-attach-media-after-publishing.md`). So:

- **Text or alt text must change:** edit the existing post in place. Do not plan a new post,
  and tell the user the platform limit (no media swap) instead of proposing a repost.
- **The image must change:** use the default flow below. Say up front that the image cannot be
  swapped in place (`learnings/linkedin-image-change-needs-new-post-with-more-pointer.md`).
- **Leaving the post as it is** is always an option: offer it with the plan and let the user
  choose.

Every step below is an external write with its own approval
(`rules/external-write-authorization.md`, `rules/human-comment-reply-gate.md`): the new post,
the pointer edit, each back-link edit, and any delete. Approval of one does not cover another.

## Default flow: new post, pointer in the old post, repointed links

1. **Publish the new post with the new image.** Run the normal flow from `SKILL.md`: show the
   full text and image as `NOT POSTED` in their own message, get explicit approval, attach the
   image ([image-attach-recipe.md](image-attach-recipe.md)), verify the text hash
   ([composer-automation.md](composer-automation.md)), get the go-ahead to Post, post, and read
   the new `<post-url>`. Verify the new post renders text, image, and article link.
2. **Edit the old post so it points to the new one.** Draft the old post's new text: its
   existing text with a first line `More... <post-url>`. Show the exact edited text as
   `NOT POSTED` and get approval. Then open `<old-post-url>`, use the post's "..." (control)
   menu, choose the edit action (the label as the screen shows it), put the line at the top,
   and save. Check the text before saving the same way as for a new post
   ([composer-automation.md](composer-automation.md), when the edit dialog uses the same
   editor; otherwise compare the text on screen).
3. **Verify the old post.** Reload `<old-post-url>`: it must open with the `More...` line and
   the original text, and the link must be the new `<post-url>`. The old image stays; that is
   expected.
4. **Repoint back-links.** Replace `<old-post-url>` with `<post-url>` everywhere it was
   published, each as its own approved write:
   - the article (edit the published article's LinkedIn link; for Medium see
     `skills/medium-publishing/references/publish-dialog.md`);
   - the repository README (through a pull request when the default branch is protected);
   - any other doc or post that referenced it.
5. **Check bidirectionality.** The new post links to the article; the article and README link
   to `<post-url>`; no reference to `<old-post-url>` remains outside the pointer line.

Do not delete the old post unless the user asks for that.

## Optional alternative: delete the old post

Offer it only if the user wants the old post gone. It is irreversible and has its own
approval, in addition to the approvals above.

1. Open the old post and note its reactions and comments. Deleting discards them and any
   replies from other people; tell the user before asking for the approval.
2. Ask in its own message: the old post's URL, the new post's URL, what will be lost, and that
   deletion cannot be undone. Wait for an explicit approval that names the old post.
3. Repoint the back-links first (step 4 above); the pointer edit (step 2) is not needed.
4. Open `<old-post-url>`, use the "..." menu, choose "Delete post", and confirm. Check the URL
   in the address bar first so the new post is not deleted by mistake.
5. Navigate to `<old-post-url>` again; it should read "Post not found". If it still renders,
   report that the delete did not complete.

## Report to the user

A short table: old URL (pointer added, or deleted with "Post not found" confirmed), new URL,
each back-link location and its status (updated, pending approval, or pull request open).

## Avoiding the replacement

Most replacements are avoidable. Before the first Post click, tick the checklist at the end of
[image-attach-recipe.md](image-attach-recipe.md): image preview inside the composer, text hash
matches, user approval of exact text and image.
