---
title: When the official source is unreachable, cross-check with independent pages and label provenance on the deliverable
category: toolchain
created: 2026-11-26
tags: [egress, blocked-source, provenance, cross-check, verification, deliverable, evidence]
---

# Problem
A deliverable needed a figure published by an official rate source, but the site was unreachable
from both the cloud sandbox and the device sandbox (the proxy refused it). The user asked
several times to "check this again".

# Failed Approaches
- Retrying the blocked host or hunting for a way around the proxy.
- Using an unverified figure without saying where it came from.
- Answering a re-check request from memory of the first answer.

# Solution
- Compare several independent pages that republish the official figure against the previously
  saved official file.
- Write the provenance on the deliverable itself, for example: "value from saved official file
  dated X; official site unreachable; matches N independent pages".
- On each re-check request, repeat the comparison and restate the provenance and the fetch
  status; say plainly if nothing changed.
- Report the block once, with the hosts tried, and do not loop.
- Related: `cloud-sandbox-egress-blocks-registries-verify-on-user-machine.md`.

# Why
A reader of the deliverable cannot see the fetch history, so the document must carry the
evidence level. Independent mirrors raise confidence but are not the primary source; the label
keeps that difference visible.
