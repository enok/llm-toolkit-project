---
title: Email-driven automation must authenticate senders and allow-list links before filing anything
category: security
created: 2026-11-26
tags: [email, automation, spoofing, dmarc, dkim, authentication-results, allowlist, untrusted-input, gmail]
---

# Problem

A scheduled job filed attachments by sender (for example "documents from sender X go to
folder Y"). A display name or a look-alike address is trivial to forge, and a crafted
`Authentication-Results` header can fake a passing check, so matching on the visible sender
alone lets anyone drop files into the owner's folders or steer the job.

# Failed Approaches

- Matching the display name or a substring of the address.
- Trusting any header line that contains `dmarc=pass`: comments and quoted strings inside the
  header can embed that text.
- Feeding the email subject or body to the model so it can "decide" what to do: the text is
  attacker-controlled and becomes a prompt-injection path.
- Following any link found in a link-only email.

# Solution

- Match the sender address with an exact full-match (`fullmatch`), per rule.
- Require a passing `dmarc` or `dkim` result from the topmost `Authentication-Results` header
  for the rule's own `auth_domain`; otherwise mark the item `unverified` and do not file it.
- Before parsing that header, strip comments (parentheses) and quoted strings, and require
  exactly one `dmarc` result; more than one is a reject.
- For link-only items, copy a URL only if it full-matches the rule's per-rule URL allowlist;
  otherwise report it for the owner and fetch nothing.
- Keep untrusted subject and body text away from the model. A script writes the email files;
  the model only sees fixed fields the script produced.
- Rules the job learns itself (exact address plus `auth_domain`) stay in a "confirm" state
  until the owner confirms them.

# Why

Each check closes one forgery route: exact address stops look-alikes, header authentication
stops spoofed senders, comment stripping stops header injection, the allowlist stops
redirects to attacker pages, and keeping the text away from the model stops instructions
hidden in an email from reaching a tool-using agent. Hardening of the unattended update task
(formula-safe cells, hash-pinned scripts) is in `chained-email-ingest-and-workbook-update-tasks.md`.
Related:
`learnings/gmail-raw-for-attachments-plain-text-costs-tokens.md`,
`rules/security-check-required.md`, `workflows/automation-maintenance.md`.
