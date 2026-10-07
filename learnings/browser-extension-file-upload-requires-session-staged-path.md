---
title: The browser tool's file upload accepts only a session-staged path
category: environment
created: 2026-10-07
tags: [browser-automation, file-upload, session-staging, drag-and-drop, datatransfer, linkedin]
---

# Problem

Attaching a PNG to a LinkedIn post composer through browser automation: the browser
tool's file-upload action accepted only a path inside the session's uploads folder
(`/mnt/user-data/uploads/...`), not the container outputs path and not the user's local
Windows path (`<windows-path>\diagram.png`).

# Failed Approaches

- File upload from the container outputs path: not accepted.
- File upload from the Windows path: not accepted.
- Pasting the image from the OS clipboard into the composer: failed.
- Reading the image with a page `fetch`: failed (the page's content security policy).

# Solution

1. Stage the PNG into the session's uploads folder (copy it from the machine with the
   device bridge). Use a fresh filename for every revision of the image.
2. Add a temporary light-DOM `<input type=file>` to the page and fill it with the browser
   tool's file-upload action, passing the session-staged path:

```js
const input = document.createElement('input');
input.type = 'file';
input.id = 'tmp-upload-proxy';
document.body.appendChild(input);
```

3. Read the file from that input and dispatch dragenter, dragover and drop events that
   carry a `DataTransfer` onto the composer's `.ql-editor` (`editor` is the element you
   found earlier with a shadow-aware query scoped to the "Create post" dialog):

```js
const file = document.getElementById('tmp-upload-proxy').files[0];
if (!file) throw new Error('the upload did not reach the proxy input');
const dt = new DataTransfer();
dt.items.add(file);
for (const type of ['dragenter', 'dragover', 'drop']) {
  editor.dispatchEvent(new DragEvent(type, {
    bubbles: true, cancelable: true, composed: true, dataTransfer: dt }));
}
```

4. Remove the proxy input afterwards (`document.getElementById('tmp-upload-proxy')?.remove()`).

Durable guidance: skills/linkedin-publishing/references/image-attach-recipe.md

# Why

The session recorded which paths the tool accepted, not why (only the root session holds
the device bridge to the user's machine). Inference: the upload action can only read files
already inside the session's uploads area, so the file must be staged there first.
