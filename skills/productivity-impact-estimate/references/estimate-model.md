# Estimate model

Read this before presenting numbers from `scripts/productivity_estimate.py`, and
when the user wants to replace the default week with their own. The model is
deliberately small so every number can be traced and challenged.

## Contents

1. What the model is
2. The baseline week and saving bands
3. Roll-ups and rounding
4. Replacing the defaults
5. Sources behind the bands (all unverified)
6. Wording rules for the result

## 1. What the model is

A manual 40-hour week is split by activity. For each activity two saving
percentages are applied, a conservative one and a likely one (0 to 40 percent).
The saved hours add up to a weekly figure, which rolls up to month, year and
team size. It estimates the effect of using the toolkit's skills, workflows and
agents on top of a plain assistant; it does not measure anyone's real week.

## 2. The baseline week and saving bands

Defaults used when no `--rows` file is given. Assets are checked against this
repository; re-check them with `ls` before quoting, because assets move.

| Activity | Manual h/week | Conservative % | Likely % | Assets behind it |
|---|---|---|---|---|
| Ticket research and context gathering | 3.5 | 10 | 25 | skills/task-starter, ticket-research, design-driven-dev, cross-repo-impact |
| Coding + tests | 9.0 | 8 | 20 | workflows/ticket-implementation.md, new-backend-feature.md; best-practices skills; skills/test-plan |
| Pre-PR self-checks | 1.5 | 10 | 30 | skills/pre-pr-check, changed-code-quality-gate, run-tests |
| Reviewing teammates' PRs | 3.0 | 0 | 15 | skills/ticket-review, pr-validator, java-change-validator |
| Addressing review comments | 2.0 | 10 | 25 | workflows/gh-address-comments.md, pr-automation-review.md; skills/fix |
| CI failure triage and fix | 1.5 | 5 | 20 | workflows/gh-fix-ci.md; skills/ci-watcher; tool-subagents/ci-triage.md |
| Ops: logs, alarms, incidents | 4.0 | 3 | 15 | workflows/log-investigation.md; skills/aws-alarm-investigator, incident-ops |
| Documentation | 1.5 | 20 | 40 | skills/update-docs, doc-delta, confluence-documentation, runbook-authoring, diagram-authoring |
| Infra and data-pipeline changes | 2.0 | 3 | 12 | skills/terraform-specialist, terraform-change-safety, dag-glue-specialist |
| Releases and verification | 1.0 | 3 | 10 | skills/release-manager; tool-subagents/release-coordinator.md; skills/e2e-release-verification |
| Env setup and onboarding | 1.0 | 15 | 30 | scripts/bootstrap-dev.sh; skills/local-env-bootstrap, environment-diagnose, project-discovery |
| Meetings and other | 10.0 | 0 | 2 | little toolkit effect |

The hours are an assumed split, not a survey of any team. Do not describe them
as what a typical engineer does; say "an assumed week".

## 3. Roll-ups and rounding

- Weeks per year 46 (52 minus vacation and holidays); weeks per month 4.33.
- Team sizes 1, 5 and 10; FTE equivalent = saved hours divided by 40.
- Percent of engineering time excludes activities whose name starts with
  "Meetings".
- Decimal half-up rounding (not binary floats) keeps the table reproducible:
  2.625 rounds to 2.63 every time.

## 4. Replacing the defaults

When the team knows its own split, replace the defaults; a measured baseline
beats the assumed one. Pass `--rows <file.json>`:

```json
[
  {"activity": "Code review", "manual_h": 6, "conservative_pct": 5, "likely_pct": 15, "assets": "skills/pr-validator"},
  {"activity": "Meetings and other", "manual_h": 12, "conservative_pct": 0, "likely_pct": 2}
]
```

Rules: `0 <= conservative_pct <= likely_pct <= 100`; keep percentages inside the
0 to 40 band unless the team has evidence for more; name non-engineering time
"Meetings ..." so it is excluded from the engineering percentage.

## 5. Sources behind the bands (all unverified)

The bands were set by reading published studies in a sandbox that could not
open them. Every citation below is **unverified — verify before quoting**:
open the source, confirm the finding and the date, and quote the source's own
numbers, not this model's.

| Source (as remembered) | Used for | Status |
|---|---|---|
| "Time Warp" developer time study, arXiv 2502.15287 | Baseline split of a developer week | unverified — verify before quoting |
| IDC 2024 developer time-split report | Baseline split | unverified — verify before quoting |
| Google randomized controlled trial of AI assistance, 2024 | Coding-time savings band | unverified — verify before quoting |
| Cui et al. field experiments on AI coding assistants | Coding-time savings band | unverified — verify before quoting |
| METR studies on AI and developer speed | Lower bound (savings can be zero or negative) | unverified — verify before quoting |
| DORA reports 2024 and 2025 | Delivery-performance context | unverified — verify before quoting |
| Atlassian developer-experience report | Documentation and review bands | unverified — verify before quoting |
| DX research on AI-assisted engineering | Per-activity bands | unverified — verify before quoting |
| JetBrains and Stack Overflow developer surveys, 2025 | Adoption and perceived savings | unverified — verify before quoting |

Until verified, treat the bands as the author's judgment informed by that
literature, not as findings.

## 6. Wording rules for the result

- Call it an estimate in the first sentence and again next to every headline
  number. Never write "saves" without "an estimated".
- Show both bands (conservative to likely) and the baseline they came from.
- Say that the bands include the effect of a plain AI assistant, so the
  toolkit's own share is smaller and unmeasured.
- Offer to replace the default week with the team's own baseline; use theirs
  when given.
- Do not quote a study from section 5 in the answer unless it was verified in
  this session; if quoted, give its date and link.
