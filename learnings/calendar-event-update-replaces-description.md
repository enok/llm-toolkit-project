---
title: Updating a calendar event replaces its description - read and merge first
category: api
created: 2026-11-26
tags: [calendar, google-calendar, update_event, description, merge, data-loss]
---

# Problem
Updating a calendar event with a new description through the calendar connector replaced the
whole description. Links, agenda text and notes that the owner had written were lost.

# Failed Approaches
- Sending only the new text in the description field: the update treats it as the full value.
- Assuming that "update" patches individual fields of the description: it does not.

# Solution
- Read the event first (`get_event`) and keep its current description.
- Build the new value as the old text plus the change (append a line, or edit one section),
  then send the merged text.
- After the update, read the event again and report exactly what changed.
- If the old text cannot be read, stop and ask the user before overwriting.

# Why
The description is one string, so a write replaces it. Reading and merging is a few seconds of
work; recovering overwritten text is often impossible unless the calendar keeps a history.
Untested: whether every calendar provider behaves the same way; this was seen through one
connector.
