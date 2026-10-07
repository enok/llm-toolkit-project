---
title: LinkedIn image attach recipe
tags: [linkedin, browser-automation, file-upload, drag-and-drop, hazard]
---

# LinkedIn image attach recipe

Use this reference to attach a PNG to the "Create post" composer when the browser tool can
upload to a normal file input but LinkedIn's own file picker is out of reach. It is the recipe
that worked; the approaches that failed are listed so they are not retried.

Read the HAZARD section first. Read [composer-automation.md](composer-automation.md) for the
`deep` helper and the composer lookup used below.

## HAZARD: messaging file inputs

`input[id^="attachment-input"]` belongs to the MESSAGING overlay, not to the post composer.
Forwarding the image to that input attaches it to whatever chat draft is open.

- Scope every query to the "Create post" dialog; never query `document` for
  `input[type=file]` and pick the first hit.
- Use only the proxy input you create yourself as the upload target, and never forward a file
  to any pre-existing file input.
- Never click Send in messaging.
- If an attachment lands in a chat draft: click that draft's remove-attachment control so
  nothing is sent, confirm the draft no longer shows the attachment, and tell the user what
  happened.

## What worked

1. **Stage the PNG in the browser tool's session uploads folder.** Use the bridge that copies a
   file into the session's uploads area (in the recorded setup the staged path looked like
   `/mnt/user-data/uploads/<folder>/<file>.png`). The browser tool's file upload accepted only
   this session-staged path. As a precaution, use a fresh filename for every revision of the
   image: a file transfer to an already-existing path once kept the old bytes (see
   `learnings/device-commit-to-existing-path-can-keep-stale-bytes.md`). Confirm the size or a
   checksum of what the browser actually receives.

2. **Add a temporary light-DOM proxy input** (light DOM so ordinary element references can
   target it):

   ```js
   (() => {
     const input = document.createElement('input');
     input.type = 'file';
     input.accept = 'image/png';
     input.id = 'tmp-upload-proxy';
     input.style.cssText = 'position:fixed;top:0;left:0;z-index:2147483647;';
     document.body.appendChild(input);
     return 'proxy added';
   })()
   ```

3. **Upload to the proxy** with the browser tool's file-upload action, targeting the proxy's
   element reference (find it with the tool's element finder) and passing the session-staged
   path. Confirm the file reached the input:

   ```js
   document.getElementById('tmp-upload-proxy').files[0]?.name
   ```

4. **Drop the file onto the composer** with synthetic drag events carrying a `DataTransfer`
   that holds the File. In the working run the three events below were dispatched together, in
   this order, on the composer's `.ql-editor` (found with `deep` and verified to be inside the
   "Create post" dialog). Whether each event is individually required was not tested; keep
   all three:

   ```js
   (() => {
     const file = document.getElementById('tmp-upload-proxy').files[0];
     const dt = new DataTransfer();
     dt.items.add(file);
     const target = composerEditor; // the .ql-editor proven to be in the Create post dialog (editors[0] in composer-automation.md)
     for (const type of ['dragenter', 'dragover', 'drop']) {
       target.dispatchEvent(new DragEvent(type, {
         bubbles: true, cancelable: true, composed: true, dataTransfer: dt
       }));
     }
     return 'drop dispatched';
   })()
   ```

5. **Verify the preview.** Take a screenshot and check that an image preview now appears
   inside the "Create post" composer (not in a chat panel). If LinkedIn shows an intermediate
   media step, complete it and re-check. Then paste the approved text and run the hash check
   from [composer-automation.md](composer-automation.md); re-run it after any later change to
   the composer.

6. **Remove the proxy** once the preview is confirmed (also if the attempt failed):

   ```js
   document.getElementById('tmp-upload-proxy')?.remove()
   ```

## What did not work

| Attempt | Result |
| --- | --- |
| Browser tool upload from a container outputs path | Rejected; only the session-staged path was accepted |
| Browser tool upload from a Windows or other host path | Rejected |
| Pasting the image from the OS clipboard into the composer | Nothing attached |
| `fetch` of the image from inside the page | Blocked by the page's content security policy |
| Forwarding to `input[id^="attachment-input"]` | Attached to a messaging draft (see HAZARD) |

## Checklist before Post

- [ ] The preview shows inside the "Create post" composer.
- [ ] No messaging draft gained an attachment (check the overlay if one was open).
- [ ] The proxy input is removed.
- [ ] The text hash still matches the approved text.
- [ ] The user has approved the exact text and the image, and has given the go-ahead to Post.
