---
trigger: always_on
description: Read the exact variant from the artifact and check a primary source before any compatibility or support verdict, and lead with an explicit correction when new evidence overturns an earlier claim
---

# Evidence before verdict

Apply this rule before answering "will X work with Y", "does X support Y",
"is this the right version or part", or any verdict another decision rests on,
for software and physical products alike.

- **Variant from the artifact.** Read the attributes that define the variant
  (version, model number, voltage or power rating, size, edition) from the
  artifact itself: the listing, a screenshot, a datasheet, a label, the
  lockfile. A product or package name is not a variant. If the artifact is
  unreadable, ask for it (a screenshot early beats a long guess) or state the
  variant you assumed in the verdict.
- **Primary source before a negative verdict.** Do not declare something
  incompatible, unsupported, or impossible from secondary text (retailer copy,
  search snippets, forum posts, summaries). Check the primary source first: the
  manufacturer's manual or spec sheet, the official reference documentation, or
  the source code. When a fetch is refused, use another publisher of the same
  primary document (the manufacturer's PDF, another retailer); never retry the refused page through another tool (see `learnings/webfetch-robots-disallowed-marketplace-pages.md`).
- **Verdict with its basis.** State the verdict together with the variant, the
  source checked, and every assumption it rests on. Code-level claims also follow
  "Source Code Verification" in `rules/code-rules.md`.
- **Lead with the correction.** When new evidence overturns an earlier claim,
  open the next reply with the explicit correction ("Correction: X does fit,
  because ..."), then continue. Never bury it or let the old claim stand.
- **Done-check is a remote check.** Asked "is this done?", verify the remote
  first (branch on origin, commit reachable from main, PR and checks state). A
  ledger saying "validated" is not delivery: say "validated but never pushed"
  explicitly, then finish the delivery or state the exact blocker.
- **Blocked primary source.** When the primary source is unreachable,
  cross-check independent mirrors of it against any saved copy and write the
  provenance and fetch status on the deliverable itself
  (`learnings/blocked-primary-source-cross-check-and-label-provenance.md`).

Examples: a dependency's version comes from the lockfile, not the manifest's
package name; "the API does not support this" needs the reference docs, not a
forum answer; "this part will not fit" needs the manufacturer's manual for the
exact variant, cross-checked against the other product's specs.
