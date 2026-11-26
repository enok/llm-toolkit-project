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
  standard_answers:                          # a path string, or this mapping; keys below optional (Field notes)
    file: "<path to free-text screening answers: notice period, links, anything the keys below miss>"
    work_authorization: {"<country>": yes}   # example; country -> yes | no
    visa_sponsorship: {now: no, future: no}  # example; needs sponsorship now / in the future
    contract_types_accepted: ["<e.g. employee>", "<e.g. contractor>"]   # example
    english_level: {cefr: "<A1..C2>", picks: {}}   # picks: "<form scale>": "<option>" the owner confirmed
    years_by_skill: {"<skill>": <whole years>}     # from master-CV dates, owner-confirmed
    worked_here_before: ask                  # ask (default) | no
    interviewed_here_before: ask             # ask (default) | no
paths:
  tracker: "<path>/job-tracker.xlsx"          # required
  backup_dir: "<path>/backups"
  working_dir: "<scratch folder: known.json, job-scan-state.json, run-in-progress.lock, lane JSON, copies>"   # required
cadence:
  schedule: "<e.g. Mon-Fri 08:00 or weekly Fri 08:00>"
  window: "<fallback inbox window when no state file exists, e.g. 3 days>"
  stale_days: 30                              # example: posting closed + no reply this long -> Closed / No response
search:                                      # required
  boards:                                     # string or mapping per entry, see Field notes; linkedin | indeed, see board-playbook.md; other boards need their own how-to here
    - linkedin
    # - {name: indeed, site: "<board host, e.g. uk.indeed.com>", location: "<location text>", cadence: "weekly:<Mon..Sun>", queries: ["<query for this board>"]}   # example
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
    ask_policy:                              # optional: salary-expectation answers (Field notes)
      no_range: <number>                     # posting shows no pay
      fraction_of_posted_max: 0.9            # example; posted max known -> max(floor, fraction x max)
      floor: <number>                        # never answer below this
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
  blocked_companies: ["<company the candidate never applies to>"]   # optional; e.g. ExampleCorp. Matching ignores case, punctuation, spacing
  exclude_rejected_companies: false          # optional; true = also drop companies in known.json rejected_companies (Closed rows with Outcome Rejected)
  posting_languages: ["en"]                  # optional; ISO 639-1 codes the posting description may be written in; omit or [] = no language screen
targeting:                                   # optional: recruiter-view roles, see cv-tailoring.md
  refresh_days: 30                           # example: re-derive the roles after this many days, or when the CV changes
  queries_from_roles: false                  # true = scan queries come from the role titles below (de-duplicated with search.queries)
  roles:                                     # up to 20, strongest first
    - title: "<job title as postings write it>"
      ats_keywords: ["<exact ATS keyword the CV supports>"]
cv:                                          # optional: master CV and apply-kit settings
  master: "<path to master CV in the markdown format of cv-tailoring.md>"
  tailored_dir: "<folder that holds one apply-kit folder per posting>"
  formats: [docx, pdf]                       # formats rendered from each cv.md
  pdf_footer: "{page} of {total}"            # example; footer text for the PDF, omit for none
queue:                                       # optional: review queue limits for the For Approval sheet
  shortlist_size: <number>                   # rows the owner reviews per day (tracker_ops shortlist --size)
  expire_unreviewed_days: <number>           # unmarked rows older than this move to Excluded; omit = off
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
  never: ["create accounts", "enter passwords", "request verification codes", "accept terms", "solve CAPTCHAs", "record intros or take assessments", "guess missing answers"]
  owner_rules: []                            # e.g. "never apply to <company> through <portal>"
  kit_for: [approved]                        # optional: rows that get an apply kit; any of approved | tier_A | shortlist
  consent_boxes: owner                       # fixed: the owner ticks every consent, privacy, and terms box
  per_form_chat_ok: required                 # fixed: each form needs the owner's chat OK naming it
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

## Screening filter keys

Optional keys under `criteria` that turn the owner's screening rules into
configuration instead of prose (all default to off):

| Key | Effect |
| --- | --- |
| `exclude_contract_forms` | Drop postings with these employment forms (for example a local salaried-employee contract) |
| `exclude_workplace` | Drop postings whose workplace is on-site or hybrid, whatever the search filter said |
| `require_language_in_posting` | Drop postings whose language or skill list omits the required one |
| `prefer_stack_side` | Rank backend before front-end; add front-end only when few openings remain |
| `pay_floor` | Pay below this (max of the stated range) is kept and flagged, not dropped |

Answers to screening questions go into one block per job in the apply batch
message, so the owner approves them together with the form.

## Field notes

- The workflow evaluates `hard_rules` in order against the full description
  and scans for each rule's `terms`. Write the rule that excluded a posting
  into the Excluded `Reason`.
- `blocked_companies`, `exclude_rejected_companies` and `posting_languages` are
  screening options for the board lanes (L2, L5 in
  [lane-prompts.md](lane-prompts.md)). Each dropped posting goes into the
  lane's excluded list with its reason. Company matching is case-insensitive
  and ignores punctuation and spacing, so "Example Corp" matches
  "ExampleCorp". The rejected list is `rejected_companies` in `known.json`
  (see `known` in [tracker-schema.md](tracker-schema.md)), so the dedup file must
  be fresh. `posting_languages` checks the language the posting description is
  written in, not the title or the board interface; it is separate from a
  `language` hard rule, which is about languages the candidate must speak.
- `cv_skills` is the only source for `Experience (CV)`. Pass it with
  `append --cv-skill`. When `study_plan.mode: gaps` is set, copy the same list
  into `skill-rules.json`.
- `standard_answers` needs an answer for every question you want answered
  automatically. A question without one is skipped and reported. It is a path
  (the answers file) or a mapping whose `file` is that path and whose other
  keys are structured answers; a key wins over the file. A question nothing
  answers (self-ratings, essays) is `OWNER:`, never a guess.
  - `work_authorization`: country -> yes or no; an unlisted country is `OWNER:`.
  - `visa_sponsorship`: `now` and `future` answer "will you need sponsorship".
  - `contract_types_accepted`: a listed type is yes; any other is `OWNER:`.
  - `english_level`: map `cefr` to the form's scale by meaning: A1-A2 basic,
    B1 intermediate, B2 upper-intermediate or professional working, C1
    advanced or fluent, C2 proficient. "Native or bilingual" only when the
    owner says so. Between two options, pick the lower. Owner-confirmed
    `picks` (form scale -> option) win over this mapping.
  - `years_by_skill`: whole years, from the earliest master-CV role that shows
    the skill to the end of the latest one, rounded down. Leave out claims the
    CV audit flags as unconfirmed and skills the CV lacks; the owner confirms
    the list before use. An unlisted skill is `OWNER:`.
  - `worked_here_before`, `interviewed_here_before`: `ask` puts the question to
    the owner. `no` is a standing answer, except when the master CV or another
    Applied, Interviewing, or Closed row shows that company: then ask.
- `criteria.pay.ask_policy` answers salary-expectation fields and beats any
  salary anchor in the standard answers. No pay posted (a board estimate is not
  posted pay): `no_range`. A posted range or maximum:
  `fraction_of_posted_max` x that maximum, never below `floor` (a low posted
  maximum still answers `floor`). No policy: `OWNER:`. Match the form's
  currency and period; month to year is x 12, any other conversion is
  `OWNER:`. A numeric-only field takes one number (a range string fails as
  invalid input). Method: [apply-playbook.md](apply-playbook.md) section 1.
- `apply.consent_boxes: owner` and `apply.per_form_chat_ok: required` are fixed:
  they restate SKILL.md contract items 3 and 5. Another value is ignored and
  reported; neither the profile nor a routine prompt can relax them.
- `paths.working_dir` also holds `run-in-progress.lock`, the duplicate-run
  guard of `workflows/job-search-pipeline.md` Phase 1.
- Paths may be local (desktop bridge) or cloud (drive connector). The
  workflow uses whichever the session can reach. When it can reach neither,
  the run reports that.
- Each `search.boards` entry is a string (`linkedin`) or a mapping
  `{name, site, location, cadence, queries}`. A string is the board with the
  shared settings, run daily. In a mapping only `name` is required: `site` is
  the host to read (default: the board's site for `candidate.location`),
  `location` replaces `search.geo` for that board, `cadence` is `daily` or
  `weekly:<Mon..Sun>`, and `queries` replaces the shared `search.queries` for
  that board. A board lane runs only on its cadence day. Keys and cadence
  rules: [board-playbook.md](board-playbook.md).
- `targeting`, `cv`, `queue`, and `apply.kit_for` are optional. An absent key
  leaves its feature off: no targeting means no ATS score, no `cv.master` means
  no apply kit, no `queue.expire_unreviewed_days` means no expiry. The method
  behind them is in [cv-tailoring.md](cv-tailoring.md).
- `candidate.cv` is the CV the owner already has, in any format. `cv.master` is
  the markdown master that tailoring reads; it may be derived from it.
- `targeting.roles[].ats_keywords` lists only keywords the CV supports. Lanes use
  them as the candidate keyword set for the ATS match estimate.
- The tracker's money columns are labelled USD by default. Set
  `criteria.pay.normalize_to` and rename the columns if the candidate
  normalizes to another currency.
