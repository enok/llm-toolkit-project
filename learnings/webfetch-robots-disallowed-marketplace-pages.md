---
title: WebFetch returns robots_disallowed on marketplace and price-comparison pages
category: environment
created: 2026-11-26
tags: [webfetch, robots, marketplace, price-comparison, specs, research, manual-pdf]
---

# Problem
While checking product compatibility, `WebFetch` on large marketplace and price-comparison
product pages returned `robots_disallowed`, so the spec table the answer depended on could not
be read from the page the search had surfaced.

# Failed Approaches
- Retrying the same URL, or the same page through another URL form: the block is a
  site-level robots rule, so it repeats.
- Answering from the search snippet alone: snippets carry a few specs, not the full table
  (variant, connectors, dimensions) that a compatibility verdict needs.

# Solution
- Search for the same model and variant on other retailers: their product pages usually fetch
  fine and carry the full specification table.
- Fetch the manufacturer's manual or datasheet PDF directly; it is the primary source for
  ports, dimensions and supported modes.
- Confirm that the variant in the fetched page matches the one the user owns or plans to buy
  before using any value.
- Say in the answer which source each value came from.

# Why
`robots_disallowed` is the fetch tool honouring the site's robots policy, not a transient
error, so waiting or rephrasing does not help. Other retailers and the manufacturer publish
the same specifications without that restriction. Inference: marketplaces block automated
fetching more often than manufacturer or single-retailer pages; this was seen on one
session's pages, not measured across sites.
