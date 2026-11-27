---
description: Mandatory gate before adding a toolkit resource - race it against the plain model on a blind, realistic task and add it only if it wins
---

# Resource Value Check Workflow

A toolkit resource earns its place only if a model that has it loaded does the job
better than the same model without it. If the plain model (no custom harness) does
as well or better, the resource is not added: it would only grow context and can
hold the model back.

## When it applies

- **Mandatory** before adding any new skill, workflow, tool-subagent (agent) or rule,
  however it is created (by hand, by a factory script, by intake of an external
  skill, or by promotion from chat evidence).
- On request for an existing resource (an audit, a slimming pass, a suspected
  regression).
- **Exempt:** `learnings/` files. They record evidence of what happened, not
  behaviour to load; record them as `exempt` only if a gate asks for a row.
- Owner-mandated contract files (for example the orchestration contract set) are
  measured and slimmed, never removed by this gate.

## Roles

| Role | Who | Must not |
| --- | --- | --- |
| Case designer | A helper that did not author the resource | See the runs before writing the case |
| Runner (two) | Two isolated helpers, same model, same helper type | See each other, the case expectations, or other toolkit files |
| Judge | A helper that did not design the case or run an arm | Know which output came from which arm |

The coordinating session dispatches every role and reads only short returns.

## Steps

### 1. Design the case (before any run)

Write `case.md` in a scratch workspace outside the repository with:

- `task`: ONE realistic, specific, multi-step request a user would actually make
  that the resource claims to help with, hard enough that a strong model could do
  it worse without help. It must be doable with file tools and a shell only (no
  browser, accounts or network): ask for a concrete artifact (a plan, a review, a
  script, a document, a decision with evidence). Put inputs under `files/`. Never
  name the resource, the toolkit or its vocabulary in the task.
- `expectations` (hidden from runners): 5 to 7 objectively checkable statements
  about the RESULT, as a demanding domain expert would judge it (correctness,
  safety, completeness, usefulness). They must not reward following the
  resource's own steps, names or format: a plain expert answer must be able to
  pass all of them. **At least two** are about a failure the resource claims to
  prevent.
- `resource_files`: what the with-arm loads (skill: its `SKILL.md`, which may
  point to references; agent: its `.md`; rule or workflow: the file).
- `context_cost_bytes`: bytes always loaded (an always-on rule: the whole file; a
  skill: its description) and bytes loaded on use.

### 2. Run both arms

- Same model, same helper type, same task text, each arm on its own copy of the
  input files, in the same dispatch turn.
- WITH arm: "Read <resource_files> first and apply it." PLAIN arm: no resource.
- Both arms: do not use any skill-loading tool, do not read the toolkit tree or
  any toolkit file other than the stated resource, write deliverables to
  `<arm>/outputs/`, return three lines only.

### 3. Judge blind

1. Before reading any output, the judge writes a sealed map file with a coin flip
   (for example Python `secrets.choice`) deciding which arm becomes `A/` and
   which `B/`, then copies the outputs accordingly.
2. Grade A and B against every expectation. Verify claims by running things on
   copies (run the script, apply the patch, parse the file); never trust an
   output's own statement that it works.
3. Give a holistic blind verdict, then unseal the map and write one verdict:
   `resource, winner (with|plain|tie), margin (clear|slight|none),
   expectations_passed {with, plain, of}, reason (<= 40 words),
   failure_prevented (yes|no), recommendation`.

## Decision rule

| Result | Decision |
| --- | --- |
| With wins (clear) | Add (`keep`). |
| With wins (slight) | Add; slim it first if it is large or always-on (`keep-slim`). |
| Tie | Do not add (`remove`). Exception: if the resource encodes environment knowledge the plain run tripped on (a tool quirk, a local convention the model cannot know), add it only as on-demand content (`on-demand`). One retest on a smaller model is allowed (`retest`); add only if it lifts that model. |
| Plain wins | Do not add (`remove`). For an existing resource, repoint or remove its dependents first. |
| Owner-mandated contract file | Measure and slim (`slim` or `keep-slim`); never `remove`. |
| Twin forms of one procedure (skill and workflow, or skill and agent) | Race every form and the plain run in the same case. Add only the best form; cut the other to a short pointer into it (`keep-slim`) or leave it out (`remove`). |

A resource whose value is environment knowledge is judged on whether the plain
arm actually hit the documented pitfall, not on general answer quality.

## Record

Add one row per resource to `docs/llm/value-checks.csv`, header:

```text
resource,kind,date,model,winner,margin,with_passed,plain_passed,of,decision,evidence,note
```

- `resource`: repository-relative path (for a skill, its `SKILL.md`).
- `kind`: `skill`, `workflow`, `agent` or `rule`. `date`: `YYYY-MM-DD`.
- `winner`: `with`, `plain` or `tie`; `margin`: `clear`, `slight` or `none`.
- `decision`: one of `keep`, `keep-slim`, `on-demand`, `slim`, `remove`,
  `retest`, `exempt`. The check passes `keep`, `keep-slim` and `exempt`, and
  passes `on-demand` only once the file's frontmatter says `trigger: model_decision`.
- `evidence`: where the case, outputs and verdict live (a run id or a path in
  the scratch workspace; never a machine-specific absolute path). `note`: short.

Keep the case files and outputs out of the repository unless the owner asks for
them; the CSV row is the durable record.

## Mechanical check

```bash
python3 scripts/check_value_checks.py --base <ref>
```

Exit 0 when every resource added since `<ref>` (renames into a resource folder
count as added) has a row whose decision passes as described under Record; exit 1
otherwise. Run it in **pre-pr-check**
with the PR base (`origin/main` unless the PR targets another branch). On
Windows use `py -3` or `python` in place of `python3`.

## Cost control

- Use the smallest helper type that has file tools and a shell; a large
  general-purpose type multiplies idle cost across every lane.
- Slim briefs: the task, the paths, the return contract. No background essays.
- Short returns (three lines for runners; the verdict file for the judge).
- One batch at a time (up to five resources), so a flawed case design is caught
  before it is repeated.
- Log tokens per lane and total them per batch.

## Fairness pitfalls

- The harness may refuse a file write, or a mock destructive call, in one arm
  only. That run measures the harness, not the resource: rerun **both** arms.
- A helper type's role prompt can bias a run (for example a testing-oriented role
  on a non-testing task). Say so in the brief ("this is not a testing task") and
  use the same type for both arms.
- An answer may reveal which arm it is (it quotes the resource's vocabulary).
  The judge notes it in the verdict and does not penalise it.
- Helpers usually cannot start helpers; the coordinating session dispatches every
  lane itself.
- Agent types load at session start; do not plan on a neutral helper type created
  mid-session.

## Report

Return: resource, verdict line, decision, CSV row added, check-command result,
tokens per batch.
