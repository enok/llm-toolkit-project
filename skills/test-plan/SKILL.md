---
name: test-plan
description: Generate a test plan from staged changes using the IDE's LLM. Use when the user wants test suggestions, "what tests should I add," or "test plan for my changes."
---

# Test Plan (in-agent)

Generate a test plan (suggested test cases, areas to cover) from the current staged diff. You produce the plan using the IDE's LLM; no external CLI.

## When to Apply

- User asks "what tests should I add?" or "test plan for my changes"
- User wants to write or update tests and needs guidance
- User is adding a new feature and wants test coverage suggestions

## Steps

1. **Get staged diff.** Use `git diff --cached` or Cursor's context over staged files.
2. **Produce plan.** Using the IDE's LLM, generate a concise test plan: suggested test cases, edge cases, regression areas, and alignment with the changed behavior. Output as a clear list or write to a file (e.g. `docs/jira/<TICKET>/test-plan.md`) if the user or project expects an artifact.
3. **Actionable.** The output should be usable to add or extend unit tests in the repo's test framework.

## When implementing the test plan

- **Committed docs:** When writing the test plan to `docs/jira/<TICKET>/test-plan.md`, infer `<TICKET>` from the branch name or ask the user. Create the directory if it does not exist.
- **Node/npm:** If you add or extend tests and introduce **Node/npm** (e.g. `package.json`, `npm test`, jsdom, or other Node-based tooling), ensure the repo's **.gitignore** includes `node_modules/` so dependencies are not committed. If the repo has no .gitignore yet, create one; if it exists, add `node_modules/` only if missing. This avoids accidentally committing dependencies after "implement the test plan" or similar flows.

For running the project's actual test suite, use the repo's normal test command (e.g. `mvn test`, `pnpm test`). For full pre-PR including tests and review, use **pre-pr-check**.
