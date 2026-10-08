---
title: A device-bridge transfer can re-encode a PNG, so compare decoded pixels, not byte hashes
category: environment
created: 2026-10-07
tags: [device-bridge, file-transfer, png, re-encode, checksum, pixels, verification, linkedin]
---

# Problem

A PNG crossed the device bridge. The copy on the other side hashed differently although the
picture was the same: the transfer had re-encoded the PNG. A byte hash of the original
therefore does not prove or disprove what arrived.

# Failed Approaches

- Comparing byte hashes of the PNG before and after the transfer: they differed even though
  the pixels matched, so the comparison could not tell a re-encode from a bad copy.

# Solution

Compare the decoded image, not the file bytes: image size plus a hash of the decoded pixels,
computed the same way on both sides. Illustrative sketch (needs Pillow; the session recorded
the principle, not a tool):

```python
import hashlib
from PIL import Image

def pixel_digest(path: str) -> str:
    img = Image.open(path).convert("RGBA")
    return "%dx%d %s" % (img.size[0], img.size[1], hashlib.sha256(img.tobytes()).hexdigest()[:12])
```

Equal digests mean the same picture; different digests mean a different or stale image. The
author of this learning ran the sketch on two encodings of one image (default and
uncompressed): the byte hashes differed and the pixel digests were equal.

Keep the other transfer rules: write each revision under a fresh filename and check on the
machine that the file is the new one
(learnings/device-commit-to-existing-path-can-keep-stale-bytes.md). For a PNG, make that check
the pixel digest instead of a byte hash.

Durable guidance: skills/linkedin-publishing/references/image-attach-recipe.md

# Why

The session observed that the transfer re-encoded the PNG (different bytes, equal pixels) and
settled on pixels as the comparison. It did not identify which layer re-encoded the file.
Inference: pixels are the property that matters for a diagram about to be uploaded.
