---
name: doc-delta
description: "Suggest or apply documentation updates from staged changes. Use after code changes when the user wants to 'update docs,' 'document my changes,' or keep README/config in sync."
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Documentation Delta (in-agent)

Suggest or apply documentation updates (e.g. README, config docs) based on the staged diff. You perform the analysis and edits using the IDE's LLM; no external CLI.

## When to Apply

- User says "update docs" or "document my changes"
- After adding or changing APIs, config, or behavior that should be documented
- User wants to keep README or `docs/` in sync with code

## Steps

1. **Get staged diff.** Use `git diff --cached` or the IDE's staged-file context to see what changed.
2. **Identify doc impact.** Determine which docs are affected (README, config docs, API docs, etc.) and what should be added or updated. When build manifests or shared config change (`pom.xml`, Gradle files, package manifests, CI profiles, env vars), check setup docs, agent guidance, project conventions, and validation notes in the same pass.
   - For API contract or runtime behavior changes, also check OpenAPI/Swagger,
     examples, architecture or sequence diagrams, performance/metrics docs, and
     PR-facing descriptions. Keep durable docs and the PR body aligned with the
     current head SHA and validation result after every pushed follow-up.
3. **Suggest or apply.** Using the IDE's LLM, propose concrete doc changes. If the user asked to apply, edit the files (e.g. README.md, `docs/`) to reflect the new behavior. If only suggesting, present the edits as a clear list or diff.
4. **Follow repo conventions.** Match the project's docs layout and style. Do not invent new sections or files unless the user asks.
5. **Check encoding before broad edits.** For Markdown touched by Windows tools or generated LLM surfaces, detect UTF-8 BOMs and mojibake markers such as `â`, `Ã`, or `Â` before making semantic edits. Repair at the byte/encoding level, write UTF-8 without BOM, and keep LF line endings; do not rely on one-off visible text replacements.
6. **Ticket artifacts go to `docs/jira/<TICKET>/`.** When generating output files (reports, plans, etc.), write them to `docs/jira/<TICKET>/` — infer `<TICKET>` from the branch name, or use `docs/jira/review/` when no ticket is clear. Do not write to hidden/gitignored directories. Keep committed documentation updates in normal tracked docs such as `README.md` or `docs/`.

After running, the user can review and tweak.
