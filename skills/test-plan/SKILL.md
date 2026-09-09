---
name: test-plan
description: "Generate a test plan from staged changes or a branch diff using the IDE's LLM. Use when the user wants test suggestions, 'what tests should I add,' 'test plan for my changes,' 'what edge cases am I missing,' or needs acceptance criteria mapped to test cases before writing tests."
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Test Plan (in-agent)

Generate a test plan (suggested test cases, areas to cover) from the current staged diff. You produce the plan using the IDE's LLM; no external CLI.

## When to Apply

- User asks "what tests should I add?" or "test plan for my changes"
- User wants to write or update tests and needs guidance
- User is adding a new feature and wants test coverage suggestions

## Steps

1. **Get staged diff.** Use `git diff --cached` or the IDE's staged-file context. If nothing is staged and the user asked about "this branch," use `git diff <base>...HEAD` (default base `origin/main` else `main`).
2. **Produce plan.** Using the IDE's LLM, generate a concise test plan: suggested test cases, edge cases, regression areas, and alignment with the changed behavior. Map each acceptance criterion to at least one named test (see `skills/testing/rules/ac-mapping.md`). Output as a clear list or write to a file (e.g. `docs/jira/<TICKET>/test-plan.md`) if the user or project expects an artifact.
3. **Actionable.** The output should be usable to add or extend unit tests in the repo's test framework.

## When implementing the test plan

- **Artifacts:** When writing the test plan to `docs/jira/<TICKET>/test-plan.md`, infer `<TICKET>` from the branch name, or use `docs/jira/test-plan.md` when no ticket is clear. Create the directory if it does not exist.
- **Node/npm:** If you add or extend tests and introduce **Node/npm** (e.g. `package.json`, `npm test`, jsdom, or other Node-based tooling), ensure the repo's **.gitignore** includes `node_modules/` so dependencies are not committed. If the repo has no .gitignore yet, create one; if it exists, add `node_modules/` only if missing. This avoids accidentally committing dependencies after "implement the test plan" or similar flows.

For running the project's actual test suite, use the repo's normal test command (e.g. `mvn test`, `pnpm test`). For full pre-PR including tests and review, use **pre-pr-check**.

## Related

- `skills/testing/SKILL.md` — the testing discipline and rule set the plan should satisfy
- `skills/run-tests/SKILL.md` / `workflows/run-tests.md` — execute the repo's suite
- `skills/task-starter/SKILL.md` — the implementation plan this test plan complements
- `skills/pre-pr-check/SKILL.md` — validations + changed-code quality gate + review before the PR
