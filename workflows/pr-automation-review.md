---
description: Triage and fix GitHub PR automation review bot findings (vendor-agnostic; check name varies by org)
---

# PR automation review workflow

Process and fix issues reported by an **automation PR review check** on GitHub. Check and bot names vary by organization; identify the failing check with `gh pr checks`. The bot typically categorizes findings into severity tiers; this workflow maps each tier to an action and loops until the check passes.

Trigger: user says "fix PR bot review", "PR validation", "fix automation review", or the automation review check fails on a PR.

---

## Phase 1 — Fetch Review Findings

**1. Identify the PR** — from current branch:
```bash
gh pr view --json number,title,url --jq '{number, title, url}'
```

**2. Fetch the automation review findings** — bots can post inline review
threads, top-level review submissions, PR comments, or a mixture. Inspect both
thread state and top-level reviews for the current head before concluding there
is nothing left to fix.

```bash
gh pr view <PR_NUMBER> --json reviews,latestReviews,comments,statusCheckRollup
```

For inline review threads, use GraphQL:

```bash
gh api graphql -f owner='<org>' -f repo='<repo>' -F number=<PR_NUMBER> -f query='
query($owner:String!, $repo:String!, $number:Int!) {
  repository(owner:$owner, name:$repo) {
    pullRequest(number:$number) {
      reviewThreads(first:100) {
        nodes { isResolved isOutdated path comments(first:10) { nodes { author { login } body url } } }
      }
    }
  }
}'
```

The bot often posts a single review comment with all findings. Example filters
(adjust `author.login` / patterns for your org's bot):
```bash
gh pr view <PR_NUMBER> --json comments --jq '.comments[] | select(.author.login == "cursor[bot]" or .author.login == "cursor-bot" or (.body | test("Review Outcome"))) | .body' | tail -1
```
If the CLI doesn't capture it, check PR reviews:
```bash
gh api repos/{owner}/{repo}/pulls/<PR_NUMBER>/reviews --jq '.[] | select(.user.login | test("cursor")) | .body'
```
If neither works, ask the user to paste the review comment or provide a screenshot.
Treat fresh top-level Yellow or warning findings as actionable unless a human
reviewer explicitly accepted the risk.

**3. Parse the review into a structured findings table.** The bot uses this format:

| Bot Section | Severity | Action |
|-------------|----------|--------|
| **Red (must fix before merge)** | Blocker | Must fix — PR cannot merge |
| **Yellow (should fix)** | Warning | Should fix — high-value improvements |
| **Green (nice-to-have)** | Suggestion | Optional — fix if low effort |
| **Assumptions / validation needed** | Info | Validate — confirm or refute each assumption |

---

## Phase 2 — Triage and Plan

**4. Build a findings table** from the bot comment:

```
## Automation review findings
**PR**: #N  **Check status**: FAIL / PASS

### Red — Must Fix
| # | Title | File(s) | Root Cause | Planned Fix |
|---|-------|---------|------------|-------------|

### Yellow — Should Fix
| # | Title | File(s) | Root Cause | Planned Fix |
|---|-------|---------|------------|-------------|

### Green — Nice to Have
| # | Title | File(s) | Effort | Fix? |
|---|-------|---------|--------|------|

### Assumptions to Validate
| # | Assumption | Valid? | Evidence |
|---|------------|--------|----------|
```

**5. For each Red finding**, verify the bot's analysis:
- Read the actual file(s) cited by the bot.
- Confirm the issue exists (bots can hallucinate — never trust blindly).
- If the issue is a **false positive**, document why and note it for the PR reply.
- If confirmed, plan the minimal fix.

**6. For each Yellow finding**, assess effort vs. value:
- If low effort and clearly beneficial → plan fix.
- If high effort or debatable → note as "deferred" with rationale.

**7. For each Green finding**, decide:
- If trivial (< 5 min) → include in this pass.
- Otherwise → skip and note as "future improvement."

**8. For each Assumption**, validate:
- Read the actual code/config referenced.
- State whether the assumption is correct or incorrect.
- If incorrect, note what the bot missed.

**9. Present the triage to the user** before proceeding. Pause if any Red finding requires a design decision.

---

## Phase 3 — Fix

**10. Fix confirmed Red findings first**, then Yellow, then Green. For each fix:
- Read the actual source file before editing.
- Apply minimal, targeted changes.
- Verify compilation after each fix:
  - Java: `mvn compile -pl . -q`
  - Python: `python -m py_compile <file>`
  - JS/TS: `npx tsc --noEmit`

**11. Address each Assumption** — if the bot's assumption is wrong, add a comment or code change to make the correct behavior explicit (e.g., add a code comment, a test, or a configuration guard).

**12. Track what was fixed vs. deferred:**

```
## Resolution Summary
| # | Severity | Title | Resolution | Commit |
|---|----------|-------|------------|--------|
| 1 | Red | ... | Fixed | `<SHA>` — Business logic + related unit tests |
| 2 | Red | ... | False positive — [reason] | N/A |
| 3 | Yellow | ... | Fixed | `<SHA>` — Configuration |
| 4 | Yellow | ... | Deferred — [reason] | N/A |
| 5 | Green | ... | Skipped — low priority | N/A |
```

---

## Phase 4 — Test

**13. Run the full test suite:**
```bash
# Java
mvn clean test

# Python
pytest

# JS/TS
npm test
```

**14. All tests must pass.** If any fail, fix immediately and re-run. Do NOT proceed until green.

---

## Phase 5 — User Approval Gate (MANDATORY)

**All fixes are complete and tests are green. STOP and present the resolution summary to the user.**

**Do NOT commit or push until the user explicitly approves.** If the user requests changes, go back to Phase 3. Skip this gate only if the user explicitly asked to skip approval.

---

## Phase 6 — Commit, Push, and Verify

**15. Stage and commit fixes** by running `workflows/commit-and-push.md` with
selective staging. Fold each fix into its existing category/subgroup; if it
belongs to an existing grouped commit, use the workflow's isolated
fixup/autosquash path. Never use a repository-wide `git add -A` shortcut unless
the complete worktree diff was proven to contain exactly one in-scope category
and subgroup with no pre-existing user work.

**16. Poll CI until the automation review check re-runs:**
```bash
gh pr checks <PR_NUMBER>
```
Wait for the relevant check (name depends on your org; often includes the vendor or product name and "Review" or similar) to complete.

**17. If check passes** → done. Notify user.

**18. If check fails again** → fetch the new review comment and loop back to Phase 1. New findings may appear after fixes.

---

## Phase 7 — Reply to Review

**19. Draft a summary comment on the PR** addressing the bot's findings. Because
the comment is human-facing, apply `rules/human-comment-reply-gate.md`: show the
exact target and body first, mark it `Posting status: NOT POSTED`, and do not
post until the user explicitly approves.

```bash
gh pr comment <PR_NUMBER> --body "## Automation review — resolution

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| 1 | Red | [title] | Fixed in [commit] |
| 2 | Yellow | [title] | Deferred — [reason] |
| 3 | Green | [title] | Skipped |

**Assumptions validated**: [list which were correct/incorrect]
"
```

---

## Phase 8 — CI Feedback Loop

**20. If any Red finding revealed a gap in existing rules or workflows**, update the corresponding rule file to prevent recurrence (see `rules/ci-feedback-loop.md`).

Common rule updates after automation review:
- Vulnerable dependency → update `skills/security/SKILL.md` or `skills/security-best-practices/SKILL.md` with version pinning guidance
- Payload logging → update language-specific best practices with log-safety rules
- Request body size → update `skills/best-practices/SKILL.md` with input validation patterns
- IMDS/startup fragility → update project-specific infra rules (see `rules/examples/infra-deployment.md` as a template)

---

## Notes

- **Never trust the bot blindly** — always verify findings against actual code. Bots can hallucinate file paths, line numbers, and even entire issues.
- **False positives are normal** — document them clearly so the team knows what was reviewed and dismissed.
- **The bot's "Red" != your project's "Red"** — use project context to re-classify if needed (e.g., a Log4j 1.x finding may be acceptable if the project intentionally pins it with SLF4J bridge).
- **Deferred items are OK** — not every Yellow/Green needs immediate action. Document the rationale.
- **Loop until the check is green** — the bot may find new issues after fixes. Keep iterating.

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
