# Mistake taxonomy

A closed set of eleven categories. Classify by **root cause**, not by the
symptom or the step where it surfaced. When two categories fit, pick the one
whose fix would have prevented the mistake.

## Categories

| Category | Meaning | Generic examples |
| --- | --- | --- |
| `spec-gap` | requirement or acceptance criterion missing, ambiguous, or misread | a deliverable built without the required output format because no criterion named it; a "match the existing style" request implemented against the wrong reference file |
| `wrong-assumption` | acted on an unverified belief about code, data, environment, or API | assumed a CLI flag existed in the installed version; assumed a config key was read at startup when it is read per request |
| `env-constraint` | sandbox, egress, permissions, OS or shell differences | package registry blocked from a cloud sandbox, so the build had to run on the user's machine; a script relied on a POSIX tool missing on Windows |
| `tool-misuse` | wrong tool, flag, quoting, API call, or order of operations | shell quoting split an inline JSON filter into several arguments; a file was edited before it was read, so the edit tool rejected the change |
| `platform-quirk` | a third-party UI, editor, renderer, or service behaved non-obviously | an editor split one pasted code block at blank lines; a diagram renderer ignored a layout direction when nodes linked across groups |
| `quality-defect` | output below the bar: correctness, legibility, style, completeness | a diagram exported at a size unreadable at the destination; a code sample that did not compile against the stated language version |
| `validation-gap` | a defect escaped a validator, or a needed check did not exist | a validator checked the source but not the rendered output; tests passed because the new branch of logic had no test at all |
| `tier-misassignment` | model tier or effort wrong for the task shape | a `light` lane given cross-file architectural reasoning failed validation twice; a `deep` model assigned to a mechanical rename |
| `scope-drift` | work outside the asked scope, or asked scope silently dropped | refactored unrelated modules during a bug fix; one of four requested language versions quietly omitted |
| `coordination` | lane overlap, stale state or bytes, lost handoff, ledger drift | two lanes rediscovered the same blocker because the first finding never reached the ledger; a file copied over an existing path kept the old content and was used unchecked |
| `safety-near-miss` | a side effect hit or nearly hit the wrong target, or lacked approval | a post was about to be published before the approval gate; a push targeted the protected default branch instead of the feature branch |

Disambiguation:

- `spec-gap` vs `wrong-assumption`: if the requirement was knowable from what
  the user or ticket said, it is a `spec-gap` (misread); if it depended on a
  fact about the system that nobody checked, it is a `wrong-assumption`.
- `quality-defect` vs `validation-gap`: record the producing cause. Add a
  separate `validation-gap/...` entry only when an existing validator's
  criteria covered the case and it still passed, or when the missing check is
  what must be built. An escaped defect usually has both.
- `platform-quirk` vs `tool-misuse`: documented behaviour used wrongly is
  `tool-misuse`; surprising behaviour of someone else's product is
  `platform-quirk`.
- Under-reporting mistakes to improve metrics is a `validation-gap` of the
  retrospective itself.

## Signature naming

Format `<category>/<kebab-slug>`, matching
`^[a-z-]+/[a-z0-9]+(-[a-z0-9]+)*$`, at most 80 characters.

1. **Name the mechanism, not the incident.** Good:
   `platform-quirk/editor-paste-splits-code-block-at-blank-line`. Bad:
   `platform-quirk/article-3-broken`.
2. **Generic words only.** No project, client, person, repository, host, or
   ticket names; name the kind of tool (`editor`, `renderer`, `shell`,
   `ci-runner`) unless the product itself is the reusable lesson and already
   appears in a committed asset name.
3. **3 to 7 words** in the slug: subject + behaviour (+ trigger).
4. **Reuse before inventing.** List every recorded signature with
   `run_retro.py signatures` (all workflows: count of distinct runs,
   workflows, last seen, highest promoted level; `--workflow <name>` narrows
   it). When one has the same root cause, copy it byte for byte even if the
   symptom looks different. Recurrence, promotion, cross-workflow `rule`
   detection, and ineffective-prevention detection all key on the exact
   string. `preflight` and `summary` show only recurring or top signatures and
   are not a substitute. Fallback only when the script cannot run but the log
   is readable (log lines use canonical JSON, so a text match works):

   ```bash
   grep -o '"signature": "[^"]*"' "$LOG" | sort | uniq -c
   ```

   ```powershell
   Select-String -Path $log -Pattern '"signature": "[^"]*"' -AllMatches | % { $_.Matches.Value } | Group-Object | Sort-Object Count -Descending
   ```

5. **Never rename a recorded signature** to make a recurrence disappear.
   Merging a slip into the existing signature it should have reused is allowed
   (`run-record-schema.md`, Storage); otherwise keep the wrong name and explain
   in `notes`.

## Severity

| Severity | Use when | Promotion |
| --- | --- | --- |
| `low` | cosmetic or caught immediately; cost minutes | ladder from record |
| `medium` | cost a refinement iteration or a changed approach; no user-visible harm | ladder from record |
| `high` | reached the user, CI, or a shared surface; or cost a large share of the run | guard at first occurrence |
| `critical` | data loss, security exposure, a wrong external write, or broken production | guard at first occurrence, plus human escalation when a rule or redesign is needed |

Every `safety-near-miss` is treated as at least `high`, even when nothing
went wrong in the end.

## Source

`self-review` (you noticed), `validator` (a quality-loop verdict), `ci`,
`user`, `tool-error` (a failing tool call forced the discovery),
`post-release`. A mistake is an **escaped defect** when its source is `ci`,
`user`, or `post-release` and the task had already been marked done.
