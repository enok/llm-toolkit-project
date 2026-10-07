---
title: A LinkedIn image change needs a new post, with a "More..." pointer edited into the old one
category: toolchain
created: 2026-10-07
tags: [linkedin, edit-post, image-change, new-post, more-pointer, back-links, approval-gate]
---

# Problem

A published LinkedIn post needed a different image. LinkedIn's editor for a published post
changes its text and its image alt text only, never the media. Two plans in the same flow
missed what the user wanted: one planned a new post to swap the image although the user had
asked for the existing posts to be edited; another edited only the text, which kept the old
image although the user wanted a new post carrying the new diagram, with the old post
pointing to it.

# Failed Approaches

- Planning a new post when the user asked to edit the existing posts: the editor can change
  the text and the alt text, so that part belongs in an in-place edit and the platform limit
  (no media swap) should have been stated instead of proposing a repost.
- A text-only edit of the old post when the image had to change: the old image stayed.

# Solution

1. State the limit up front: the editor of a published post changes text and alt text, not
   media.
2. Text-only or alt-text change: edit the existing post in place; no new post.
3. The image must change: publish a NEW post with the new image (show the full text and the
   image as `NOT POSTED`, get approval, verify the text hash, post, read the new post URL).
4. Then edit the OLD post's text so it opens with a line `More... <new-post-url>` (show the
   exact edited text, get approval, save, read the old post back).
5. Repoint the article link and the README link from the old post to the new one, each as its
   own approved write.
6. Do not delete the old post unless the user asks for that; a delete is a separate approval.

Each external write (new post, pointer edit, each link edit) needs its own approval.

Durable guidance: skills/linkedin-publishing/references/repost-and-delete.md

# Why

The session recorded the editor limit and the user's two corrections: edit what can be
edited, and for an image change use a new post plus a pointer, "not a delete". It did not
record why the pointer was preferred. Inference: the old post keeps its reactions and
comments and its URL keeps resolving, while the new post carries the image. This replaces
the "repost, then delete the old post" default of
learnings/linkedin-cannot-attach-media-after-publishing.md (its step 3 now states the pointer
as the default and the delete as the optional alternative); the prevention in its step 1
(attach the image before the first Post click) stands.
