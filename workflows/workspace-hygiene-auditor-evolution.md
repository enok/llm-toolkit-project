---
description: Improve the Workspace Hygiene Auditor specialist from validated misses, noisy findings, and routing gaps
---

# Workspace Hygiene Auditor Evolution

Use this workflow when the Workspace Hygiene Auditor specialist needs a durable improvement.

## Steps

1. Capture concrete evidence of the miss, noisy output, stale routing, or token
   inefficiency.
2. Classify the fix across the prompt, workflow, skill, routing map, client
   overlays, or validation gate.
3. Make the smallest generic update.
4. Run `node scripts/validate-specialist-agent.js workspace-hygiene-auditor`.
5. Sync provider surfaces and run the repository validation required by the task.
6. Report the evidence, updated files, validation, and residual risk.
