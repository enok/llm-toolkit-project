#!/usr/bin/env python3
"""Summarize a JMeter CSV JTL file from Windows, Linux, or macOS."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 2)
    rank = (pct / 100.0) * (len(ordered) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return round((ordered[lower] * (1 - weight)) + (ordered[upper] * weight), 2)


def summarize(rows: list[dict[str, str]], source: str) -> dict:
    elapsed = [float(row["elapsed"]) for row in rows if row.get("elapsed")]
    success_rows = [row for row in rows if row.get("success", "").lower() == "true"]
    status_distribution: dict[str, int] = {}
    label_rows: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        status_distribution[row.get("responseCode", "")] = status_distribution.get(row.get("responseCode", ""), 0) + 1
        label_rows.setdefault(row.get("label", ""), []).append(row)

    labels = []
    for label, grouped in sorted(label_rows.items()):
        label_elapsed = [float(row["elapsed"]) for row in grouped if row.get("elapsed")]
        label_success = [row for row in grouped if row.get("success", "").lower() == "true"]
        labels.append({
            "label": label,
            "count": len(grouped),
            "success": len(label_success),
            "failure": len(grouped) - len(label_success),
            "avg_ms": round(statistics.fmean(label_elapsed), 2) if label_elapsed else None,
            "p50_ms": percentile(label_elapsed, 50),
            "p95_ms": percentile(label_elapsed, 95),
            "p99_ms": percentile(label_elapsed, 99),
            "max_ms": round(max(label_elapsed), 2) if label_elapsed else None,
        })

    return {
        "jtl": source,
        "total": len(rows),
        "success": len(success_rows),
        "failure": len(rows) - len(success_rows),
        "success_rate": round((len(success_rows) / len(rows)) * 100, 2) if rows else 0,
        "avg_ms": round(statistics.fmean(elapsed), 2) if elapsed else None,
        "p50_ms": percentile(elapsed, 50),
        "p95_ms": percentile(elapsed, 95),
        "p99_ms": percentile(elapsed, 99),
        "max_ms": round(max(elapsed), 2) if elapsed else None,
        "status_distribution": dict(sorted(status_distribution.items())),
        "labels": labels,
    }


def markdown(summary: dict) -> str:
    lines = [
        "# JMeter Summary",
        "",
        f"- Source: `{summary['jtl']}`",
        f"- Total: {summary['total']}",
        f"- Success: {summary['success']}",
        f"- Failure: {summary['failure']}",
        f"- Success rate: {summary['success_rate']}%",
        f"- Avg ms: {summary['avg_ms']}",
        f"- P50 ms: {summary['p50_ms']}",
        f"- P95 ms: {summary['p95_ms']}",
        f"- P99 ms: {summary['p99_ms']}",
        f"- Max ms: {summary['max_ms']}",
        "",
        "## Status Distribution",
        "",
    ]
    for status, count in summary["status_distribution"].items():
        lines.append(f"- `{status}`: {count}")
    lines.extend([
        "",
        "## By Label",
        "",
        "| Label | Count | Success | Failure | Avg ms | P50 ms | P95 ms | P99 ms | Max ms |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for label in summary["labels"]:
        lines.append(
            f"| {label['label']} | {label['count']} | {label['success']} | {label['failure']} | "
            f"{label['avg_ms']} | {label['p50_ms']} | {label['p95_ms']} | {label['p99_ms']} | {label['max_ms']} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jtl", required=True)
    parser.add_argument("--out-json", default="")
    parser.add_argument("--out-md", default="")
    args = parser.parse_args(argv)

    jtl = Path(args.jtl).expanduser().resolve()
    with jtl.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit(f"ERROR: no rows found in {jtl}")

    summary = summarize(rows, str(jtl))
    output_json = json.dumps(summary, indent=2)
    if args.out_json:
        Path(args.out_json).write_text(output_json + "\n", encoding="utf-8")
    if args.out_md:
        Path(args.out_md).write_text(markdown(summary), encoding="utf-8")
    print(output_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
