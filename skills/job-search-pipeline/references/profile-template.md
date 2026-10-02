---
title: Job search profile template
tags: [job-search, profile, configuration, template]
---

# Candidate profile (template)

1. Copy this file next to the candidate's tracker, for example
   `<job-search-folder>/job-search-profile.md`.
2. Replace every `<...>` placeholder.
3. Point the routine prompt at the file.

The profile is personal data, so keep it out of shared repositories. The
workflow reads its criteria from this file only: anything not written here is
not a rule. A missing `# required` field puts the run in report-only mode.
Values marked `# example` show the format; replace them.

```yaml
profile_version: 1
candidate:
  name: "<first name>"                       # digest greeting only
  digest_to: "<email or channel id>"         # required
  timezone: "<IANA tz, e.g. Europe/Berlin>"  # example
  location: "<country / region the candidate works from>"   # required
  cv: "<path to current CV (PDF/DOCX/MD)>"    # required
  standard_answers: "<path to screening answers: years per skill, notice period, work authorization, salary policy, links>"
paths:
  tracker: "<path>/job-tracker.xlsx"          # required
  backup_dir: "<path>/backups"
  working_dir: "<scratch folder: known.json, job-scan-state.json, lane JSON, copies>"   # required
cadence:
  schedule: "<e.g. Mon-Fri 08:00 or weekly Fri 08:00>"
  window: "<fallback inbox window when no state file exists, e.g. 3 days>"
  stale_days: 30                              # example: posting closed + no reply this long -> Closed / No response
search:                                      # required
  boards: [linkedin]                          # see board-playbook.md; other boards need their own how-to here
  posted_within_days: <max posting age>
  per_run_window: "<e.g. 24h for daily runs, 7d for weekly>"
  workplace: <remote | hybrid | onsite | any>   # maps to the board's workplace filter
  geo: "<board geo id or location string>"
  queries:
    - "<role keyword 1>"
    - "<role keyword 2>"
criteria:                                    # required
  pay:
    currency: "<ISO code>"
    period: <month | year | hour>
    floor: <number>                          # include if the max of the posted range >= floor
    target: <number>
    unknown_pay: flag                        # flag | exclude
    normalize_to: "<currency used in the Est. columns, e.g. USD>"   # example
  seniority: ["<e.g. Senior>", "<e.g. Staff>"]
  fit_min: <0-100>
  tiers: {A: <score>, B: <score>, C: <score>}
  hard_rules:                                # each rule removes a posting; check structured fields AND full text
    - id: workplace                          # example
      rule: "<e.g. exclude workplace types the candidate does not accept>"
      exceptions: "<e.g. mentions that do not apply to the role itself - interview logistics, office stipends>"
      terms: ["<keywords to scan for, in every language postings use>"]
    - id: contract                           # example
      rule: "<e.g. exclude contract types the candidate does not accept>"
      terms: []
    - id: language                           # example
      rule: "<e.g. the candidate's primary language must be among accepted languages; none stated = keep + flag>"
      terms: []
  preferences:                               # soft rules: rank down, or include only when matches are few
    - "<e.g. avoid role type X; tag it in Red flags>"
  exclude_also: ["<stacks, currencies, industries>"]
cv_skills:                                   # single source for 'Experience (CV)'; regexes, conservative
  - "<regex for a skill the CV states explicitly>"
inbox:
  provider: "<mail connector, e.g. gmail>"
  confirmations: ["<provider query for board application confirmations>"]
  ats_domains: ["<ATS sender domains to watch>"]
  watch: []                                  # people or threads to report on (e.g. a pending referral)
apply:
  board_quick_apply: allowed_with_standard_answers   # or: never
  external_ats: fill_without_login_else_owner
  never: ["create accounts", "enter passwords", "accept terms", "solve CAPTCHAs", "guess missing answers"]
  owner_rules: []                            # e.g. "never apply to <company> through <portal>"
study_plan:
  mode: none                                 # none | gaps | command
  rules: "<path>/skill-rules.json"           # mode gaps (schema in tracker-schema.md)
  command: ""                                # mode command: custom cross-reference, run in working_dir
  inputs: []                                 # files copied into working_dir for the command
  commit_back: []                            # files the command may write back; nothing else
  retired: []                                # scripts or id schemes that must never be used again
side_gigs:
  enabled: false
  currency: "<ISO code>"
  floor: <hourly number>
  platforms: []
  mirror_json: ""                            # optional JSON kept in sync with the Side Gigs sheet
notify:
  channel: email                             # email | push | both
  subject: "Job Scan - {date}"
  last_line: "Time spent on this run: {elapsed}"
```

## Field notes

- The workflow evaluates `hard_rules` in order against the full description
  and scans for each rule's `terms`. Write the rule that excluded a posting
  into the Excluded `Reason`.
- `cv_skills` is the only source for `Experience (CV)`. Pass it with
  `append --cv-skill`. When `study_plan.mode: gaps` is set, copy the same list
  into `skill-rules.json`.
- `standard_answers` needs an answer for every question you want answered
  automatically. A question without one is skipped and reported.
- Paths may be local (desktop bridge) or cloud (drive connector). The
  workflow uses whichever the session can reach. When it can reach neither,
  the run reports that.
- The tracker's money columns are labelled USD by default. Set
  `criteria.pay.normalize_to` and rename the columns if the candidate
  normalizes to another currency.
