#!/usr/bin/env python3
"""Run a fail-closed Semgrep gate on Git-added or modified code only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MAX_CONFIG_BYTES = 64 * 1024
MAX_OUTPUT_BYTES = 4 * 1024 * 1024
MAX_SOURCE_BYTES = 10 * 1024 * 1024
SEMGREP_SUFFIXES = {".cjs", ".cts", ".java", ".js", ".jsx", ".mjs", ".mts", ".py", ".ts", ".tsx"}
SCRIPT_SUFFIXES = {".ps1", ".sh"}
SUPPORTED_SUFFIXES = SEMGREP_SUFFIXES | SCRIPT_SUFFIXES
KNOWN_CODE_SUFFIXES = SUPPORTED_SUFFIXES | {
    ".c", ".cc", ".clj", ".cljc", ".cpp", ".cs", ".dart", ".ex", ".exs",
    ".fs", ".fsx", ".go", ".groovy", ".h", ".hpp", ".hrl", ".hs", ".java",
    ".kt", ".kts", ".lua", ".m", ".mm", ".php", ".pl", ".ps1", ".r", ".rb",
    ".rs", ".scala", ".sh", ".sol", ".sql", ".svelte", ".swift", ".vb", ".vbs",
    ".vue", ".zsh",
}
NON_CODE_SUFFIXES = {
    ".bmp", ".cfg", ".conf", ".csv", ".gif", ".ico", ".ini", ".jpeg", ".jpg",
    ".json", ".jsonl", ".lock", ".md", ".pdf", ".png", ".pyc", ".svg", ".toml", ".tsv",
    ".txt", ".webp", ".xml", ".yaml", ".yml",
}
KNOWN_CODE_NAMES = {"dockerfile", "gemfile", "makefile", "rakefile"}
NON_CODE_NAMES = {
    ".cursorignore", ".cursorindexingignore", "agents", "claude", "license",
    "readme", "rules", "skills", "workflows",
}
BLOCKING_SKIP_REASONS = {
    "binary file",
    "source file exceeds 10 MiB",
    "unrecognized changed file type",
    "unsafe changed source symlink",
    "unsupported code language",
}
DEFAULT_EXCLUDES: tuple[str, ...] = ()
TOP_LEVEL_KEYS = {"version"}
HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


class GateError(Exception):
    """A configuration or scope error with a stable process exit code."""

    def __init__(self, message: str, exit_code: int = 2) -> None:
        super().__init__(message)
        self.exit_code = exit_code


@dataclass(frozen=True)
class Scope:
    base: str | None
    head: str
    files: tuple[str, ...]
    lines: dict[str, tuple[tuple[int, int], ...]]
    skipped: dict[str, str]


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise GateError(f"duplicate configuration key: {key}")
        result[key] = value
    return result


def load_config(root: Path, path: Path | None) -> dict[str, Any]:
    config_path = path or root / ".changed-code-quality-gate.json"
    if not config_path.is_file():
        return {"version": 1}
    if config_path.stat().st_size > MAX_CONFIG_BYTES:
        raise GateError("quality-gate configuration exceeds 64 KiB")
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicates)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GateError(f"invalid quality-gate configuration: {exc}") from exc
    if not isinstance(data, dict):
        raise GateError("quality-gate configuration must be a JSON object")
    unknown = set(data) - TOP_LEVEL_KEYS
    if unknown:
        raise GateError(f"unknown configuration keys: {', '.join(sorted(unknown))}")
    if data.get("version") != 1:
        raise GateError("quality-gate configuration version must be 1")
    return data


def git(root: Path, *args: str, binary: bool = False) -> str | bytes:
    result = subprocess.run(
        ["git", *args], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=not binary, check=False, shell=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", "replace") if binary else result.stderr
        raise GateError(f"git {' '.join(args[:2])} failed: {str(stderr).strip()}")
    return result.stdout


def resolve_commit(root: Path, ref: str) -> str:
    resolved = str(git(root, "rev-parse", "--verify", f"{ref}^{{commit}}")).strip()
    if not SHA_RE.fullmatch(resolved):
        raise GateError(f"ref did not resolve to a commit: {ref}")
    return resolved.lower()


def resolve_range(root: Path, args: argparse.Namespace, config: dict[str, Any]) -> tuple[str | None, str]:
    head = resolve_commit(root, args.head or "HEAD")
    if args.head and resolve_commit(root, "HEAD") != head:
        raise GateError(f"{args.event} checkout does not match the event head SHA")
    if args.event == "pull_request":
        if not args.base or not args.head:
            raise GateError("pull_request mode requires --base and --head commit SHAs")
        base = resolve_commit(root, args.base)
        requested_head = resolve_commit(root, args.head)
        if head != requested_head:
            raise GateError("pull_request checkout does not match the event head SHA")
        return str(git(root, "merge-base", base, requested_head)).strip(), requested_head
    if args.event == "push":
        if not args.base or not args.head:
            raise GateError("push mode requires --base and --head commit SHAs")
        if set(args.head) == {"0"}:
            raise GateError("push event head SHA is zero")
        if set(args.base) == {"0"}:
            raise GateError("branch-creation push requires an explicit trusted base run")
        return resolve_commit(root, args.base), head
    base_ref = args.base
    if base_ref:
        base_commit = resolve_commit(root, str(base_ref))
        return str(git(root, "merge-base", base_commit, head)).strip(), head
    return None, head


def nul_paths(output: bytes) -> set[str]:
    return {item.decode("utf-8", "surrogateescape") for item in output.split(b"\0") if item}


def changed_paths(root: Path, base: str | None, head: str) -> set[str]:
    paths: set[str] = set()
    if base:
        paths |= nul_paths(git(root, "diff", "--name-only", "-z", "--diff-filter=ACMRT", f"{base}..{head}", binary=True))
    paths |= nul_paths(git(root, "diff", "--name-only", "-z", "--diff-filter=ACMRT", binary=True))
    paths |= nul_paths(git(root, "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMRT", binary=True))
    paths |= nul_paths(git(root, "ls-files", "--others", "--exclude-standard", "-z", binary=True))
    paths |= nul_paths(git(root, "ls-files", "--others", "--ignored", "--exclude-standard", "-z", binary=True))
    return paths


def safe_code_file(root: Path, relative: str, patterns: tuple[str, ...]) -> tuple[Path | None, str | None]:
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise GateError(f"changed path escapes repository: {relative}")
    root = Path(os.path.realpath(root))
    candidate = root / relative
    suffix = candidate.suffix.lower()
    name = candidate.name.lower()
    if candidate.is_symlink():
        if suffix in NON_CODE_SUFFIXES or name in NON_CODE_NAMES:
            return None, "non-code symlink"
        return None, "unsafe changed source symlink"
    resolved = Path(os.path.realpath(candidate))
    root_text = os.path.normcase(str(root))
    if os.path.commonpath((root_text, os.path.normcase(str(resolved)))) != root_text:
        raise GateError(f"changed path resolves outside repository: {relative}")
    if not resolved.is_file():
        return None, "missing or non-file"
    if resolved.stat().st_size > MAX_SOURCE_BYTES:
        return None, "source file exceeds 10 MiB"
    if suffix in KNOWN_CODE_SUFFIXES and suffix not in SUPPORTED_SUFFIXES:
        return None, "unsupported code language"
    if suffix in NON_CODE_SUFFIXES or name in NON_CODE_NAMES:
        return None, "non-code file"
    if suffix not in SUPPORTED_SUFFIXES:
        return None, "unrecognized changed file type"
    with resolved.open("rb") as source:
        sample = source.read(8192)
    if b"\0" in sample:
        return None, "binary file"
    return resolved, None


def added_ranges(root: Path, relative: str, base: str | None, head: str) -> tuple[tuple[int, int], ...]:
    ranges: list[tuple[int, int]] = []
    commands: list[tuple[str, ...]] = []
    if base:
        commands.append(("diff", "--text", "--unified=0", "--no-ext-diff", "--no-textconv", f"{base}..{head}", "--", relative))
    commands.extend([
        ("diff", "--text", "--unified=0", "--no-ext-diff", "--no-textconv", "--", relative),
        ("diff", "--cached", "--text", "--unified=0", "--no-ext-diff", "--no-textconv", "--", relative),
    ])
    for command in commands:
        for line in str(git(root, *command)).splitlines():
            match = HUNK_RE.match(line)
            if match and int(match.group(2) or "1") > 0:
                start, count = int(match.group(1)), int(match.group(2) or "1")
                ranges.append((start, start + count - 1))
    if not ranges:
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", "--", relative], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if tracked.returncode != 0:
            count = len((root / relative).read_text(encoding="utf-8", errors="replace").splitlines())
            ranges.append((1, max(1, count)))
    return tuple(sorted(set(ranges)))


def build_scope(root: Path, args: argparse.Namespace, config: dict[str, Any]) -> Scope:
    base, head = resolve_range(root, args, config)
    patterns = tuple(DEFAULT_EXCLUDES)
    files: list[str] = []
    lines: dict[str, tuple[tuple[int, int], ...]] = {}
    skipped: dict[str, str] = {}
    for relative in sorted(changed_paths(root, base, head)):
        _, reason = safe_code_file(root, relative, patterns)
        if reason:
            skipped[relative] = reason
            continue
        file_ranges = added_ranges(root, relative, base, head)
        if not file_ranges:
            skipped[relative] = "no added or modified lines"
            continue
        files.append(relative.replace("\\", "/"))
        lines[relative.replace("\\", "/")] = file_ranges
    return Scope(base, head, tuple(files), lines, skipped)


def overlaps(ranges: tuple[tuple[int, int], ...], finding_start: int, finding_end: int) -> bool:
    return any(start <= finding_end and finding_start <= end for start, end in ranges)


def subscope(scope: Scope, suffixes: set[str]) -> Scope:
    files = tuple(path for path in scope.files if Path(path).suffix.lower() in suffixes)
    return Scope(scope.base, scope.head, files, {path: scope.lines[path] for path in files}, {})


def sanitized_env() -> dict[str, str]:
    allowed = {"PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "TMPDIR", "HOME", "USERPROFILE", "LANG", "LC_ALL"}
    return {key: value for key, value in os.environ.items() if key.upper() in allowed}


def run_semgrep(root: Path, policy_root: Path, scope: Scope) -> dict[str, Any]:
    executable = shutil.which("semgrep")
    if not executable:
        return {"status": "unavailable", "required": "always", "reason": "semgrep executable not found", "findings": []}
    rules = policy_root / ".semgrep.yml"
    if not rules.is_file() or rules.is_symlink():
        return {"status": "error", "required": "always", "reason": "trusted policy .semgrep.yml is missing", "findings": []}
    command = [
        executable, "scan", "--strict", "--disable-nosem", "--no-git-ignore",
        "--x-ignore-semgrepignore-files",
        "--config", str(rules), "--json", "--error", "--", *scope.files,
    ]
    try:
        result = subprocess.run(command, cwd=root, env=sanitized_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300, check=False, shell=False)
    except subprocess.TimeoutExpired:
        return {"status": "error", "required": "always", "reason": "semgrep timed out", "findings": []}
    if len(result.stdout) > MAX_OUTPUT_BYTES or len(result.stderr) > MAX_OUTPUT_BYTES:
        return {"status": "error", "required": "always", "reason": "semgrep output exceeded 4 MiB", "findings": []}
    try:
        payload = json.loads(result.stdout.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        return {"status": "error", "required": "always", "reason": f"invalid semgrep JSON: {exc}", "findings": []}
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list) or not isinstance(payload.get("errors"), list):
        return {"status": "error", "required": "always", "reason": "invalid semgrep result structure", "findings": []}
    if payload["errors"]:
        return {"status": "error", "required": "always", "reason": "semgrep reported analysis errors", "findings": []}
    paths = payload.get("paths")
    if not isinstance(paths, dict) or not isinstance(paths.get("scanned"), list):
        return {"status": "error", "required": "always", "reason": "invalid semgrep coverage metadata", "findings": []}
    skipped_paths = paths.get("skipped", [])
    if not isinstance(skipped_paths, list):
        return {"status": "error", "required": "always", "reason": "invalid semgrep skipped-path metadata", "findings": []}
    scanned: set[str] = set()
    for raw_path in paths["scanned"]:
        if not isinstance(raw_path, str):
            return {"status": "error", "required": "always", "reason": "invalid semgrep scanned path", "findings": []}
        normalized = raw_path.replace("\\", "/")
        while normalized.startswith("./"):
            normalized = normalized[2:]
        scanned.add(normalized)
    if scanned != set(scope.files) or skipped_paths:
        return {"status": "error", "required": "always", "reason": "semgrep did not scan every scoped file", "findings": []}
    scoped: list[dict[str, Any]] = []
    broader = 0
    for finding in payload.get("results", []):
        if not isinstance(finding, dict) or not isinstance(finding.get("start"), dict) or not isinstance(finding.get("end"), dict):
            return {"status": "error", "required": "always", "reason": "invalid semgrep finding structure", "findings": []}
        if not isinstance(finding.get("extra", {}), dict):
            return {"status": "error", "required": "always", "reason": "invalid semgrep finding metadata", "findings": []}
        path = str(finding.get("path", "")).replace("\\", "/")
        raw_line = finding["start"].get("line")
        raw_end_line = finding["end"].get("line")
        if not isinstance(raw_line, int) or not isinstance(raw_end_line, int) or raw_line <= 0 or raw_end_line < raw_line:
            return {"status": "error", "required": "always", "reason": "invalid semgrep finding line", "findings": []}
        line = raw_line
        end_line = raw_end_line
        if path in scope.lines and overlaps(scope.lines[path], line, end_line):
            scoped.append({
                "analyzer": "semgrep", "ruleId": str(finding.get("check_id", "unknown")),
                "path": path, "startLine": line, "endLine": end_line,
                "messageHash": hashlib.sha256(str(finding.get("extra", {}).get("message", "")).encode()).hexdigest()[:16],
            })
        else:
            broader += 1
    if result.returncode not in {0, 1}:
        return {"status": "error", "required": "always", "reason": f"semgrep exited {result.returncode}", "findings": scoped, "broaderRunOutOfScope": broader}
    return {"status": "findings" if scoped else "pass", "required": "always", "reason": "", "findings": scoped, "broaderRunOutOfScope": broader}


SCRIPT_POLICY = {
    ".sh": (
        ("changed-code-shell-eval", re.compile(r"(^|[;&|]\s*)eval(?:\s|$)")),
        ("changed-code-shell-remote-pipe", re.compile(r"\b(?:curl|wget)\b[^|]*\|\s*(?:ba)?sh\b")),
        ("changed-code-shell-network-download", re.compile(r"\b(?:curl|wget)\b")),
    ),
    ".ps1": (
        ("changed-code-powershell-invoke-expression", re.compile(r"\b(?:Invoke-Expression|iex)\b", re.IGNORECASE)),
        ("changed-code-powershell-encoded-command", re.compile(r"-(?:EncodedCommand|enc)\b", re.IGNORECASE)),
        ("changed-code-powershell-scriptblock-create", re.compile(r"\[?scriptblock\]?::Create\b", re.IGNORECASE)),
        ("changed-code-powershell-network-download", re.compile(r"\b(?:Invoke-WebRequest|iwr|Invoke-RestMethod|irm|curl(?:\.exe)?|wget(?:\.exe)?|Start-BitsTransfer)\b", re.IGNORECASE)),
    ),
}


def _script_syntax_command(path: Path) -> list[str] | None:
    if path.suffix.lower() == ".sh":
        executable = shutil.which("bash")
        # Git paths are POSIX paths. Keep forward slashes when a Windows Python
        # process invokes Git Bash or WSL bash.
        return [executable, "-n", "--", path.as_posix()] if executable else None
    executable = shutil.which("pwsh") or shutil.which("powershell")
    if not executable:
        return None
    parser = (
        "$tokens=$null;$errors=$null;"
        "[System.Management.Automation.Language.Parser]::ParseFile($env:CHANGED_CODE_QUALITY_GATE_SCRIPT,[ref]$tokens,[ref]$errors)|Out-Null;"
        "if($errors.Count -gt 0){exit 1}"
    )
    return [executable, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", parser]


def run_script_policy(root: Path, scope: Scope) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    for relative in scope.files:
        path = root / relative
        command = _script_syntax_command(Path(relative))
        if command is None:
            return {"status": "unavailable", "required": "always", "reason": f"syntax analyzer not found for {path.suffix.lower()}", "findings": []}
        try:
            environment = sanitized_env()
            environment["CHANGED_CODE_QUALITY_GATE_SCRIPT"] = relative
            result = subprocess.run(command, cwd=root, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, check=False, shell=False)
        except subprocess.TimeoutExpired:
            return {"status": "error", "required": "always", "reason": "script syntax analysis timed out", "findings": []}
        if len(result.stdout) > MAX_OUTPUT_BYTES or len(result.stderr) > MAX_OUTPUT_BYTES:
            return {"status": "error", "required": "always", "reason": "script syntax analyzer output exceeded 4 MiB", "findings": []}
        if result.returncode != 0:
            return {"status": "error", "required": "always", "reason": f"script syntax analysis failed for {relative}", "findings": []}
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            return {"status": "error", "required": "always", "reason": f"cannot read script source: {exc}", "findings": []}
        for line_number, line in enumerate(lines, start=1):
            if not overlaps(scope.lines[relative], line_number, line_number):
                continue
            for rule_id, pattern in SCRIPT_POLICY[path.suffix.lower()]:
                if pattern.search(line):
                    findings.append({
                        "analyzer": "script-policy", "ruleId": rule_id, "path": relative,
                        "startLine": line_number, "endLine": line_number,
                        "messageHash": hashlib.sha256(rule_id.encode()).hexdigest()[:16],
                    })
    return {"status": "findings" if findings else "pass", "required": "always", "reason": "", "findings": findings, "broaderRunOutOfScope": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="Trusted base ref/SHA for committed branch changes")
    parser.add_argument("--head", help="Trusted event head SHA")
    parser.add_argument("--event", choices=("local", "pull_request", "push"), default="local")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Candidate Git repository to scan")
    parser.add_argument("--policy-root", type=Path, help="Trusted directory containing config and Semgrep policy")
    parser.add_argument("--scope-only", action="store_true", help="Print scope without claiming analyzer coverage")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        requested_root = args.repo.resolve()
        root = Path(str(git(requested_root, "rev-parse", "--show-toplevel")).strip()).resolve()
        if os.path.normcase(str(root)) != os.path.normcase(str(requested_root)):
            raise GateError("--repo must name the candidate repository root")
        policy_root = (args.policy_root or root).resolve()
        config_path = args.config or policy_root / ".changed-code-quality-gate.json"
        config = load_config(policy_root, config_path)
        scope = build_scope(root, args, config)
        report: dict[str, Any] = {"status": "not_applicable", "base": scope.base, "head": scope.head, "files": list(scope.files), "lines": scope.lines, "skipped": scope.skipped, "analyzers": []}
        unsupported = [path for path, reason in scope.skipped.items() if reason in BLOCKING_SKIP_REASONS]
        if unsupported:
            report["status"] = "blocked"
            report["reason"] = "changed source cannot be safely covered by the configured analyzer"
            print(json.dumps(report, indent=2, sort_keys=True))
            return 3
        if args.scope_only or not scope.files:
            print(json.dumps(report, indent=2, sort_keys=True))
            return 0
        semgrep_scope = subscope(scope, SEMGREP_SUFFIXES)
        script_scope = subscope(scope, SCRIPT_SUFFIXES)
        if semgrep_scope.files:
            report["analyzers"].append(run_semgrep(root, policy_root, semgrep_scope))
        if script_scope.files:
            report["analyzers"].append(run_script_policy(root, script_scope))
        findings = [item for analyzer in report["analyzers"] for item in analyzer.get("findings", [])]
        blocking_unavailable = any(item["status"] == "unavailable" and item["required"] in {"always", "ci"} for item in report["analyzers"])
        errors = any(item["status"] == "error" for item in report["analyzers"])
        coverage = any(item["status"] in {"pass", "findings"} for item in report["analyzers"])
        if errors:
            report["status"] = "error"
            exit_code = 4
        elif blocking_unavailable or not coverage:
            report["status"] = "blocked"
            exit_code = 3
        elif findings:
            report["status"] = "fail"
            exit_code = 1
        else:
            report["status"] = "pass"
            exit_code = 0
        print(json.dumps(report, indent=2, sort_keys=True))
        return exit_code
    except GateError as exc:
        print(json.dumps({"status": "scope_or_config_error", "reason": str(exc)}, indent=2), file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
