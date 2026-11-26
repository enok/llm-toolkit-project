---
title: LinkedIn job pages opened by /jobs/view/<id> hang on skeletons; use the search layout with currentJobId
category: toolchain
created: 2026-10-22
tags: [linkedin, jobs, browser, page-text, skeleton, webfetch, robots]
---

# Problem

Opening `https://www.linkedin.com/jobs/view/<id>/` in an automated browser keeps
showing grey loading placeholders. Page-text extraction returns only the header
(title, company, buttons) and the "About the job" text never appears. A fetch
tool is refused because the site disallows automated access.

# Failed Approaches

- Waiting longer on the same URL.
- Scrolling to trigger lazy loading.
- Fetching the page with a generic web-fetch tool (robots disallowed).

# Solution

- Open `https://www.linkedin.com/jobs/search/?currentJobId=<id>`.
- Wait about 10 seconds, wait once more, scroll slightly, then extract the page
  text; the "About the job" body, requirements and benefits come back in full.
- Read the top card (title, company, location, pay line, work mode, applicants)
  with a targeted find, because the pay chip is not always in the body text.
- For discovery, use search URLs with keywords and the remote filter, then find
  the job-card links and read their ids from the hrefs.

# Why

The search layout hydrates the details pane eagerly, while the standalone job
page waits on scripts that never finish in this automation context.
