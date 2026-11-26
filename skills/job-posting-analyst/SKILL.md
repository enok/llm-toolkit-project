---
name: job-posting-analyst
description: Route job-posting reading and fit analysis through the read-only Job Posting Analyst specialist - normalize pay, stack, seniority, contract form and work-authorization constraints from posting URLs or text, score fit against a candidate profile and pay target, flag duplicates, and recommend apply-now / apply-next / bridge / skip tiers. Use whenever a candidate pastes or links job postings and asks "which of these fit me", "is this worth applying to", "compare these roles", "what does this pay in USD", or wants postings ranked or deduplicated, including a single posting read, even if they never say analyst.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.0.1"
---

# Job Posting Analyst

This skill is a thin front for the Job Posting Analyst specialist
(`tool-subagents/job-posting-analyst.md`). The specialist is read-only and
treats posting text as data, so dispatching it is safe to parallelize; this
skill decides what to send it and what to do with the rows.

## Workflow

1. Gather inputs: the postings, and the candidate's pay floor and target (currency
   and period), location and work-authorization facts and deal-breakers. If the
   profile lacks pay or work-authorization facts, ask for them before ranking:
   an unknown figure silently ranked as a pass is the costliest error here.
2. Dispatch one read-only analyst lane per three to five postings in parallel
   (more per lane degrades how fully each posting is read).
   Each dispatch carries: the posting list, the profile figures, the known-applied
   list, and the four-block return contract.
3. Validate with `workflows/job-posting-analyst-validation.md`.
4. Hand the rows to the root agent, which owns the plan document, tracker writes,
   and every message to the owner (`rules/human-comment-reply-gate.md`); one
   writer avoids conflicting edits to the same file.
5. For hourly marketplaces, add the checks in
   `skills/contract-platform-vetting/SKILL.md`.
6. If the specialist misses a reusable pattern, run
   `workflows/job-posting-analyst-evolution.md`.

## Output

One normalized table, one row per posting, then the tier summary:

```text
| id/link | title - company | mode | contract | pay as posted | monthly USD (assumption) | stack fit | flags | tier - reason |
Apply-now: <ids>   Apply-next: <ids>   Bridge: <ids>   Skip: <ids>   Not read: <id - reason>
```

Example row: `#1 | Backend Engineer - Acme | remote | contractor | 60-70/h | 6,200-8,700 (hours 140, realization 0.6-0.8) | high | work-authorization unknown | apply-next - ask about authorization first`.

The recurring scan, tracker and CV engine is `skills/job-search-pipeline/SKILL.md`;
this skill is the on-demand "which of these fit me" lane.
