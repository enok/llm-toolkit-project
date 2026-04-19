# Review-and-fix workflow — multi-agent execution

Use when running `workflows/ticket-review-and-fix.md` or a project copy under `.windsurf/workflows/ticket-review-and-fix.md` with **multiple LLM agents** (parallel subagents).

## Emit phase results as you go

After each phase completes, output a short **Phase N result** block (bullet summary + tables). Do not wait until the end of the run to show Phase 1–3. This matches reviewer expectations and catches scope mistakes early.

### Phase result template (copy per phase)

```markdown
### Phase N — <Name> — **DONE**
- **Outcome:** …
- **Artifacts / commands:** …
- **Blockers for next phase:** none | …
```

## GitHub CLI — PR fields that break `gh pr view --json`

- `reviewThreads` is **not** a valid `--json` field on current `gh` (use API below).
- For inline review comments:  
  `gh api repos/<owner>/<repo>/pulls/<N>/comments`
- For issue-style comments:  
  `gh pr view <N> --json comments`
- For reviews list:  
  `gh pr view <N> --json reviews,latestReviews`

## Parallel agent split (Phase 2)

| Agent | Signal | Task |
|-------|--------|------|
| A | **S1** | Map ticket ACs to code paths + tests; flag missing implementation/tests. |
| B | **S2** | PR comments / review threads vs current diff (use `gh pr view` in the **orchestrator**, not assumed by subagents unless they can run it). |
| C | **S3** | Rubric/security pass on changed files; SDK errors by `Error["Code"]`, not `__class__.__name__`; log redaction. |

Subagents **must read files from disk** in the repo path provided. Treat subagent summaries as **hypotheses** until the orchestrator spot-checks cited lines.

## Pitfalls (from production runs)

### Shell on Windows (PowerShell)

- Do **not** use Bash-only chaining: `&&`, `||`, `2>nul` as on `cmd` may not parse in older PowerShell.
- Prefer: `Set-Location <repo>; <cmd>` on separate statements or use `;` between commands.
- When computing merge-base for `git diff`, resolve the base ref first, then pass it to `git diff` (avoid nested `$(...)` that assumes Bash).

### Python exception handling

- A broad `except Exception` after `raise SomeDomainException(...)` **will catch that same exception** if it propagates through an inner call in some layouts. Prefer `except LambdaException: raise` (or your domain base) **before** the generic handler when intentional domain exceptions must escape.
- **Non-200 persistence / missing return:** if a `try` block only `return`s inside `if status == 200`, a non-200 path can fall through and return `None`. Always `raise` or `return` explicitly.

### Subagent accuracy

- Subagents may **hallucinate** line numbers or “already fixed” status. The orchestrator should **open the file** for any Blocker before editing.
- If the repo’s **canonical workflow** lives in a **separate dev-tools / skills repository** but the project only has `.windsurf/workflows/ticket-review-and-fix.md`, keep them in sync when process rules change.

### Datetime testing (Python 3.12+)

- Prefer `datetime.datetime.fromtimestamp(..., tz=datetime.timezone.utc).astimezone(tz)` over deprecated `utcfromtimestamp`.
- **Python 3.14+:** `unittest.mock.patch.object(datetime.datetime, "now", ...)` can fail (`immutable type`). Prefer:
  - deterministic tests using a **fixed `TS`** in the payload, or
  - dependency-injecting a clock, or
  - `freezegun` if the project already depends on it — not `patch` on built-in `datetime.datetime.now`.

### Phase 9 (git reset + five commits + force push)

- The workflow may mandate `git reset --mixed origin/<base>` and push to `stage`. These are **destructive** on shared branches. The orchestrator should **confirm with the user** before rewriting history or force-pushing, unless the user explicitly ordered full Phase 9.

### Allowlist-style HTTP gateways

- See **`rules/allowlist-controller-review-pitfalls.md`** — runtime allowlists vs test fixtures, logging around redirects/tokens, Windows build-plugin noise.

## Related

- `rules/ci-feedback-loop.md` — after CI failures, capture learnings in rules.
- `rules/allowlist-controller-review-pitfalls.md` — allowlist + test alignment and logging pitfalls.
- `workflows/ticket-review-and-fix.md` — full phase list and 5-category commit table.
