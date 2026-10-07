---
title: LinkedIn cannot add media to a post after it is published
category: toolchain
created: 2026-10-07
tags: [linkedin, media, publishing, repost, delete, approval-gate, back-links]
---

# Problem

A LinkedIn post that is already live without its image cannot be repaired in place:
media cannot be added to a post after publishing. Every LinkedIn post in this flow
should carry a high-quality diagram or visual.

# Failed Approaches

None recorded in the session notes; the default behaviour produced the failure described above.

# Solution

Prevent it first, repost only if it already happened.

1. Before the first Post click, check that an image preview shows inside the "Create post"
   composer. The first URL in the text adds a link-preview card, and LinkedIn hides the
   media buttons while that card is shown: attach the image first or remove the card with
   its x. (That is a pre-publish state; it is not the post-publish limit.)
2. If the post is already live without the image, write a new post with text and image.
   Show the full text and the image, get explicit approval, then post and read the new
   post URL from the "View post" link. Decline the paid boost prompt ("No thanks").
3. Ask for a separate approval to delete the old post (each external write was approved
   separately in this flow). Then use the post's "..." menu, Delete post, confirm.
   Verify the old URL now shows "Post not found".
4. Repoint every back-link from the old URL to the new one, each as its own approved write:
   edit the published Medium story (use "Save and publish") and open a README link PR.

Durable guidance: skills/linkedin-publishing/references/repost-and-delete.md

# Why

The session recorded the limitation, not the product reason behind it, so treat it as a
fixed property of LinkedIn and plan around it. The bidirectional links between the story
and the post are why step 4 exists: the old URL is gone after the delete. General
guidance, not observed in this session: deleting the old post also discards whatever
reactions and comments it had, so tell the user before asking for the delete approval.
Cheapest fix is step 1, because the image is easy to attach before publishing and
impossible to add afterwards.
