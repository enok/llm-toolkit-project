---
description: Improve the Job Posting Analyst specialist from validated misses - unreadable pages, wrong pay normalization, missed duplicates, noisy tiers, and routing gaps
---

# Job Posting Analyst Evolution

Use this workflow when the analyst needs a durable improvement.

## Steps

1. Capture concrete evidence: the posting, what the analyst reported, and what
   the source actually said (a page that never loaded, a misread currency, a
   duplicate that slipped through, a tier that disagreed with the profile).
2. Classify the fix: reading method (site-specific access trick), normalization
   rule (pay, FX, hours), duplicate rule, tier rule, prompt wording, or a new
   learning in `learnings/`.
3. Make the smallest generic update in `tool-subagents/job-posting-analyst.md`
   (and regenerate `tool-subagents/job-posting-analyst.toml` from the same body),
   or in `skills/job-search-pipeline/references/board-playbook.md` when the fix is
   about how a board is read. Keep every employer, person and candidate detail out.
4. Run `node scripts/validate-specialist-agent.js job-posting-analyst`.
5. Sync provider surfaces and run the repository validation required by the task.
6. Report the evidence, updated files, validation and residual risk.
