---
description: Implement a ticket using its research output as input
---

# Implement Ticket Workflow

Implement a Jira ticket guided by its research documentation. Expects the **ticket-research** workflow to have already run, producing `docs/jira/<TICKET>/README.md` (implementation plan, files to modify, testing plan) and optionally `architecture.md`.

The user will provide a **ticket ID** (e.g., `ABC-1234`). Replace `<TICKET>` below with that ID.

---

## Phase 1 — Load Research and Validate

### 1. Read the research docs

- Read `docs/jira/<TICKET>/README.md` and `docs/jira/<TICKET>/architecture.md` (if present).
- Extract: acceptance criteria, implementation plan, files to modify, testing plan, open questions.
- If research docs are missing or stale, tell the user and suggest running `ticket-research` first.

### 2. Validate prerequisites

- [ ] Every acceptance criterion has a corresponding implementation step
- [ ] No open questions remain unresolved — if any exist, present them to the user and **stop until answered**
- [ ] All repos mentioned in the research are available locally
- [ ] The research was generated against the current branch state (check if key files have changed since research)

### 3. Confirm the plan with the user

Present a concise summary:
- Number of files to change and which repos
- Highest-risk step
- Proposed implementation order
- Estimated scope (small / medium / large)

**Do not start coding until the user approves.**

---

## Phase 2 — Branch Setup

### 4. Create or checkout the ticket branch

```bash
git fetch origin
git checkout -b <TICKET> origin/main   # or the appropriate base branch
```

If the branch already exists, check it out and rebase onto the base branch.

---

## Phase 3 — Implement

### 5. Follow the implementation plan step by step

For each step in the research README's **Implementation Plan**:

1. **Read the actual source file** before modifying — never code from memory or the research summary alone.
2. Apply the change following existing code style and project conventions.
3. After each logical unit of change, verify syntax or compilation:
   - Java: `mvn -pl <module> -DskipTests compile`
   - Python: `python -m py_compile <file>`
   - JS/TS: `npx tsc --noEmit` or the project's typecheck command
4. Move to the next step only after the current one compiles cleanly.

### 6. Update configuration and permissions

- Add required environment variables, secret references, feature flags, or config entries.
- Update DI configuration (XML, modules, annotations) if new beans or services are introduced.
- Keep secret material out of source control.

### 7. Update documentation

- Update `README.md`, architecture docs, or runbooks if behavior or operating model changed.
- Update API specs or contract files if endpoints or payloads changed.
- If the repo maintains paired or translated docs, update both sides or note the intentional drift.

---

## Phase 4 — Test

### 8. Write tests per the testing plan

Follow the research README's **Testing Plan**:

- **Unit tests**: create test file mirroring source path if none exists. Cover happy path, edge cases, error conditions, boundary values.
- **Regression test** (bugs only): write a test that fails without the fix and passes with it.
- **Integration / E2E tests**: add or update when the change touches APIs, cross-service flows, or persistence.

Map every AC to at least one test. Add an AC coverage comment at the top of the primary test file:
```
// AC Coverage for <TICKET>:
// AC-1: "<AC text>" → testMethodName()
// AC-2: "<AC text>" → testMethodName(), testEdgeCaseName()
```

### 9. Run tests and verify 100% pass

Run the project's standard test command. Fix any failures immediately — do not proceed until green.

### 10. Run full build

Run the full build or compilation step to catch anything missed:
```bash
mvn clean verify          # Java
npm run build && npm test # JS/TS
pytest                    # Python
```

If anything fails, fix and re-run. **Loop until green.**

---

## Phase 5 — User Approval Gate (MANDATORY)

**Implementation and tests are complete. STOP and present a summary to the user.**

Present:
- Files changed (grouped by category)
- Tests added/updated
- Any deviations from the research plan

**Do NOT commit or push until the user explicitly approves.** If the user requests changes, go back to Phase 3. Skip this gate only if the user explicitly asked to skip approval.

---

## Phase 6 — Commit, Push, and PR

### 11. Follow the 5-category commit structure

Use the commit structure from `rules/git-conventions.md`:

| Order | Category | What belongs here |
|-------|----------|-------------------|
| 1 | **LLM configs** | `.windsurf/`, `.cursor/`, `.agents/`, `.claude/`, `.codex/`, `AGENTS.md`, `CLAUDE.md`, `.gitignore` |
| 2 | **Documentation** | `README.md`, `docs/`, architecture diagrams, API specs |
| 3 | **Logs improvement** | Logger setup/format/level changes, log context, MDC |
| 4 | **Application configs/structure** | Build config, DI config, env config, dependency files |
| 5 | **Code changes** | Source code, business logic, tests for business logic |

Each commit prefixed with `<TICKET>: <description>`. Skip empty categories. Never mix categories.

### 12. Validate, rebase, and push

```bash
# Validate commit structure
git log --oneline $(git merge-base origin/<base-branch> HEAD)..HEAD

# Check for cloud-sync duplicates (blocking)
git ls-files | grep -E ' \([0-9]+\)\.' && echo "BLOCKED" && exit 1

# Rebase and push
git fetch origin
git rebase origin/<base-branch>
# Re-run tests after rebase
git push --force-with-lease
```

### 13. Open a draft PR

```bash
gh pr create --draft --title "<TICKET>: <summary>" --body "<link to ticket and brief description>"
```

---

## Phase 7 — Post-Implementation

### 14. Run pre-PR check

Suggest running the **pre-pr-check** workflow or the **ticket-review-and-fix** workflow to catch anything missed before marking the PR ready.

### 15. Update the research docs

If the implementation deviated from the original plan (different files, different approach, new discoveries):
- Update `docs/jira/<TICKET>/README.md` to reflect what was actually done.
- Note deviations and the reasons for them.

### 16. Present completion summary

- What was implemented (1-2 sentences per AC)
- Files changed (grouped by category)
- Tests added
- Any deviations from the original plan
- Remaining follow-ups or known limitations

---

## Notes

- **Always read actual code** before modifying — the research docs are a guide, not a substitute for reading the source.
- If the research is outdated (files moved, APIs changed), update the research docs and adjust the plan before implementing.
- If a step turns out to be more complex than the research estimated, pause and inform the user before proceeding.
- For multi-repo changes, implement and test in dependency order (upstream first).
