#!/usr/bin/env python3
"""Weekly time-saving ESTIMATE for a manual week versus a toolkit-assisted week.

The output is an estimate built from stated assumptions, not a measurement.
Baseline hours and saving percentages are defaults; replace them with the
team's own numbers with --rows (see references/estimate-model.md).

Usage:
  python3 productivity_estimate.py --out estimate.csv
  python3 productivity_estimate.py --out estimate.csv --json
  python3 productivity_estimate.py --out estimate.csv --rows my_baseline.json

--rows is a JSON list of objects with keys activity, manual_h,
conservative_pct, likely_pct and optional assets. An activity whose name
starts with "Meetings" is treated as non-engineering time.

Stdlib only. Rounding is decimal half-up so the table is reproducible.
"""
import argparse
import csv
import json
import sys
from decimal import Decimal as D, ROUND_HALF_UP

WEEKS_PER_YEAR = D(46)    # 52 minus vacation and holidays
WEEKS_PER_MONTH = D("4.33")
HOURS_PER_FTE_WEEK = D(40)

# activity, manual hours per week, conservative %, likely %, assets behind it
DEFAULT_ROWS = [
    ("Ticket research & context gathering", 3.5, 10, 25,
     "skills/task-starter, skills/ticket-research, skills/design-driven-dev, skills/cross-repo-impact"),
    ("Coding + tests", 9.0, 8, 20,
     "workflows/ticket-implementation.md, workflows/new-backend-feature.md, "
     "skills/java-best-practices, skills/python-best-practices, skills/js-ts-best-practices, skills/test-plan"),
    ("Pre-PR self-checks", 1.5, 10, 30,
     "skills/pre-pr-check, skills/changed-code-quality-gate, skills/run-tests"),
    ("Reviewing teammates' PRs", 3.0, 0, 15,
     "skills/ticket-review, skills/pr-validator, skills/java-change-validator"),
    ("Addressing review comments", 2.0, 10, 25,
     "workflows/gh-address-comments.md, workflows/pr-automation-review.md, skills/fix"),
    ("CI failure triage & fix", 1.5, 5, 20,
     "workflows/gh-fix-ci.md, skills/ci-watcher, tool-subagents/ci-triage.md, skills/maven-build-troubleshooting"),
    ("Ops: logs, alarms, incidents", 4.0, 3, 15,
     "workflows/log-investigation.md, skills/aws-alarm-investigator, skills/incident-ops"),
    ("Documentation (wiki, runbooks, diagrams)", 1.5, 20, 40,
     "skills/update-docs, skills/doc-delta, skills/confluence-documentation, "
     "skills/runbook-authoring, skills/diagram-authoring"),
    ("Infra (Terraform) & data-pipeline changes", 2.0, 3, 12,
     "skills/terraform-specialist, skills/terraform-change-safety, skills/dag-glue-specialist, "
     "workflows/data-pipeline-change.md"),
    ("Releases & verification", 1.0, 3, 10,
     "skills/release-manager, tool-subagents/release-coordinator.md, skills/e2e-release-verification"),
    ("Env setup & onboarding", 1.0, 15, 30,
     "scripts/bootstrap-dev.sh, skills/local-env-bootstrap, skills/environment-diagnose, skills/project-discovery"),
    ("Meetings & other", 10.0, 0, 2, "(little toolkit effect)"),
]


def r(x, q="0.1"):
    """Round half-up on exact decimals and return a float."""
    return float(D(x).quantize(D(q), rounding=ROUND_HALF_UP))


def load_rows(path):
    if not path:
        return [dict(activity=a, manual_h=h, conservative_pct=c, likely_pct=l, assets=s)
                for a, h, c, l, s in DEFAULT_ROWS]
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)
    need = {"activity", "manual_h", "conservative_pct", "likely_pct"}
    for i, row in enumerate(rows):
        missing = need - set(row)
        if missing:
            sys.exit(f"--rows entry {i} is missing: {', '.join(sorted(missing))}")
        row.setdefault("assets", "")
        if not 0 <= row["conservative_pct"] <= row["likely_pct"] <= 100:
            sys.exit(f"--rows entry {i} ({row['activity']}): need 0 <= conservative_pct <= likely_pct <= 100")
    return rows


def build(rows):
    out = []
    total = cons = like = D(0)
    eng_total = eng_cons = eng_like = D(0)
    for row in rows:
        h = D(str(row["manual_h"]))
        cs = h * D(str(row["conservative_pct"])) / 100
        ls = h * D(str(row["likely_pct"])) / 100
        total += h
        cons += cs
        like += ls
        if not row["activity"].lower().startswith("meetings"):
            eng_total += h
            eng_cons += cs
            eng_like += ls
        out.append(dict(
            activity=row["activity"], manual_h=float(h),
            conservative_pct=row["conservative_pct"], likely_pct=row["likely_pct"],
            toolkit_h_conservative=r(h - cs, "0.01"), toolkit_h_likely=r(h - ls, "0.01"),
            saved_h_conservative=r(cs, "0.001"), saved_h_likely=r(ls, "0.001"),
            assets=row["assets"]))
    pct = lambda part, whole: [r(100 * part[0] / whole), r(100 * part[1] / whole)] if whole else [0, 0]
    summary = {
        "label": "ESTIMATE, not a measurement",
        "manual_week_h": float(total),
        "saved_week_h": {"conservative": r(cons, "0.001"), "likely": r(like, "0.001")},
        "saved_week_pct_of_baseline": dict(zip(("conservative", "likely"), pct((cons, like), total))),
        "toolkit_week_h": {"conservative": r(total - cons), "likely": r(total - like)},
        "saved_month_h": {"conservative": r(cons * WEEKS_PER_MONTH), "likely": r(like * WEEKS_PER_MONTH)},
        "saved_year_h": {"conservative": r(cons * WEEKS_PER_YEAR, "1"), "likely": r(like * WEEKS_PER_YEAR, "1")},
        "saved_year_workweeks": {"conservative": r(cons * WEEKS_PER_YEAR / HOURS_PER_FTE_WEEK),
                                 "likely": r(like * WEEKS_PER_YEAR / HOURS_PER_FTE_WEEK)},
        "engineering_hours_per_week": float(eng_total),
        "saved_pct_of_engineering_time": dict(zip(("conservative", "likely"),
                                                  pct((eng_cons, eng_like), eng_total))),
        "team": {str(n): {
            "saved_week_h": {"conservative": r(cons * n), "likely": r(like * n)},
            "fte_equivalent": {"conservative": r(cons * n / HOURS_PER_FTE_WEEK, "0.01"),
                               "likely": r(like * n / HOURS_PER_FTE_WEEK, "0.01")},
            "saved_year_h": {"conservative": r(cons * n * WEEKS_PER_YEAR, "1"),
                             "likely": r(like * n * WEEKS_PER_YEAR, "1")},
        } for n in (1, 5, 10)},
    }
    return out, summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True, help="CSV file to write (one row per activity)")
    ap.add_argument("--rows", help="JSON file with the team's own baseline rows")
    ap.add_argument("--json", action="store_true", help="print the summary as JSON (default: short text)")
    args = ap.parse_args(argv)

    table, summary = build(load_rows(args.rows))
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0].keys()))
        w.writeheader()
        w.writerows(table)

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        s = summary
        print("ESTIMATE, not a measurement")
        print(f"Baseline week: {s['manual_week_h']} h; saved per week: "
              f"{s['saved_week_h']['conservative']} to {s['saved_week_h']['likely']} h "
              f"({s['saved_week_pct_of_baseline']['conservative']}% to {s['saved_week_pct_of_baseline']['likely']}%)")
        print(f"Per year (46 weeks): {s['saved_year_h']['conservative']} to {s['saved_year_h']['likely']} h per person")
        print(f"Table written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
