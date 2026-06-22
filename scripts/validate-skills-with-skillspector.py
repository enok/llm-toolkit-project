#!/usr/bin/env python3
"""Run SkillSpector static scans across toolkit skills.

The scanner is optional at the repository level. When installed, this script
validates every `skills/<name>/` directory that contains a SKILL.md file and
fails on HIGH/CRITICAL findings by default.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


DEFAULT_FAIL_SEVERITIES = "CRITICAL,HIGH"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate toolkit skills with SkillSpector static analysis."
    )
    parser.add_argument(
        "--skills-dir",
        default="skills",
        help="Directory containing one subdirectory per skill. Default: skills",
    )
    parser.add_argument(
        "--report-dir",
        default=None,
        help="Directory for per-skill JSON reports. Default: temporary directory",
    )
    parser.add_argument(
        "--allowlist",
        default="scripts/skillspector-allowlist.json",
        help=(
            "JSON file of reviewed findings to ignore. "
            "Default: scripts/skillspector-allowlist.json when present"
        ),
    )
    parser.add_argument(
        "--fail-severities",
        default=os.environ.get("SKILLSPECTOR_FAIL_SEVERITIES", DEFAULT_FAIL_SEVERITIES),
        help=(
            "Comma-separated issue/risk severities that fail validation. "
            "Default: CRITICAL,HIGH"
        ),
    )
    parser.add_argument(
        "--with-llm",
        action="store_true",
        help="Enable SkillSpector semantic LLM analysis. Default is static-only.",
    )
    parser.add_argument(
        "--keep-temp-reports",
        action="store_true",
        help="Keep the temporary report directory when --report-dir is not set.",
    )
    return parser.parse_args()


def has_skillspector() -> bool:
    return importlib.util.find_spec("skillspector") is not None


def normalize_severities(value: str) -> set[str]:
    return {item.strip().upper() for item in value.split(",") if item.strip()}


def is_git_ignored(path: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def skill_dirs(root: Path) -> list[Path]:
    skills: list[Path] = []
    for path in sorted(root.iterdir()):
        skill_file = path / "SKILL.md"
        if not skill_file.is_file():
            continue
        if is_git_ignored(skill_file):
            print(f"SKIP: {path.name} (git-ignored)")
            continue
        skills.append(path)
    return skills


def scanner_command(skill_dir: Path, report_path: Path, with_llm: bool) -> list[str]:
    command = [
        sys.executable,
        "-c",
        "from skillspector.cli import app; app()",
        "scan",
        str(skill_dir),
        "--format",
        "json",
        "--output",
        str(report_path),
    ]
    if not with_llm:
        command.append("--no-llm")
    return command


def load_allowlist(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        return []

    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    entries = data.get("findings", data if isinstance(data, list) else [])
    if not isinstance(entries, list):
        raise ValueError(f"allowlist must contain a findings array: {path}")
    return [entry for entry in entries if isinstance(entry, dict)]


def issue_is_allowlisted(
    skill_name: str,
    issue: dict[str, object],
    allowlist: list[dict[str, object]],
) -> bool:
    location = issue.get("location") or {}
    if not isinstance(location, dict):
        location = {}

    issue_file = location.get("file")
    issue_line = location.get("start_line")

    for entry in allowlist:
        if entry.get("skill") != skill_name:
            continue
        if entry.get("id") != issue.get("id"):
            continue
        if entry.get("file") != issue_file:
            continue
        if entry.get("pattern") != issue.get("pattern"):
            continue

        allow_line = entry.get("line")
        if allow_line is not None and allow_line != issue_line:
            continue
        return True

    return False


def report_findings(
    skill_name: str,
    report_path: Path,
    fail_severities: set[str],
    allowlist: list[dict[str, object]],
) -> tuple[int, int, int, list[str]]:
    with report_path.open(encoding="utf-8") as handle:
        report = json.load(handle)

    risk = report.get("risk_assessment") or {}
    risk_severity = str(risk.get("severity", "")).upper()
    issues = report.get("issues") or []

    fail_count = 0
    allowlisted_count = 0
    warnings: list[str] = []

    if risk_severity:
        warnings.append(
            f"risk severity {risk_severity} score={risk.get('score', 'unknown')}"
        )

    for issue in issues:
        severity = str(issue.get("severity", "")).upper()
        if severity not in fail_severities:
            continue

        if issue_is_allowlisted(skill_name, issue, allowlist):
            allowlisted_count += 1
            continue

        fail_count += 1
        location = issue.get("location") or {}
        file_name = location.get("file", "<unknown>")
        line = location.get("start_line")
        suffix = f":{line}" if line else ""
        warnings.append(
            f"{issue.get('id', '<no-id>')} {severity} {file_name}{suffix} "
            f"{issue.get('pattern', '<no-pattern>')}"
        )

    return len(issues), fail_count, allowlisted_count, warnings


def main() -> int:
    args = parse_args()

    if not has_skillspector():
        print(
            "SKIP: SkillSpector is not installed. Install from "
            "https://github.com/NVIDIA/SkillSpector and re-run this script."
        )
        return 127

    repo_root = Path.cwd()
    skills_root = (repo_root / args.skills_dir).resolve()
    if not skills_root.is_dir():
        print(f"FAIL: skills directory not found: {skills_root}", file=sys.stderr)
        return 1

    fail_severities = normalize_severities(args.fail_severities)
    if not fail_severities:
        print("FAIL: --fail-severities must include at least one severity", file=sys.stderr)
        return 1

    allowlist_path = (repo_root / args.allowlist).resolve()
    allowlist = load_allowlist(allowlist_path)
    if allowlist:
        print(f"Allowlist: {allowlist_path} ({len(allowlist)} reviewed finding(s))")

    temp_dir: Path | None = None
    if args.report_dir:
        report_dir = Path(args.report_dir).resolve()
        report_dir.mkdir(parents=True, exist_ok=True)
    else:
        temp_dir = Path(tempfile.mkdtemp(prefix="skillspector-"))
        report_dir = temp_dir

    skills = skill_dirs(skills_root)
    if not skills:
        print(f"FAIL: no skills with SKILL.md found under {skills_root}", file=sys.stderr)
        return 1

    total_issues = 0
    total_failures = 0
    total_allowlisted = 0
    failed_scans: list[str] = []

    print(
        "SkillSpector validation: "
        f"{len(skills)} skills, mode={'llm' if args.with_llm else 'static-only'}, "
        f"fail_severities={','.join(sorted(fail_severities))}"
    )
    print(f"Reports: {report_dir}")

    try:
        for skill in skills:
            report_path = report_dir / f"{skill.name}.json"
            result = subprocess.run(
                scanner_command(skill, report_path, args.with_llm),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=180,
            )
            if result.returncode != 0:
                if not report_path.is_file():
                    failed_scans.append(f"{skill.name}: scanner exited {result.returncode}")
                    print(result.stdout.rstrip())
                    continue
                print(f"NOTE: {skill.name} scanner exited {result.returncode}; parsing report")

            issue_count, fail_count, allowlisted_count, warnings = report_findings(
                skill.name, report_path, fail_severities, allowlist
            )
            total_issues += issue_count
            total_failures += fail_count
            total_allowlisted += allowlisted_count

            status = "FAIL" if fail_count else "OK"
            print(
                f"{status}: {skill.name} "
                f"({issue_count} issue(s), {fail_count} blocker(s), "
                f"{allowlisted_count} allowlisted)"
            )
            for warning in warnings[:8]:
                print(f"  - {warning}")
            if len(warnings) > 8:
                print(f"  - ... {len(warnings) - 8} more blocker(s)")

        if failed_scans:
            print("FAIL: SkillSpector scan failures:", file=sys.stderr)
            for failure in failed_scans:
                print(f"  - {failure}", file=sys.stderr)
            return 1

        if total_failures:
            print(
                f"FAIL: SkillSpector found {total_failures} blocker(s) "
                f"across {total_issues} total issue(s).",
                file=sys.stderr,
            )
            return 1

        print(
            f"OK: SkillSpector scanned {len(skills)} skill(s); "
            f"{total_issues} total issue(s), 0 blocker(s), "
            f"{total_allowlisted} allowlisted."
        )
        return 0
    finally:
        if temp_dir and not args.keep_temp_reports:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
