#!/usr/bin/env python3
"""Measure the instruction bytes each LLM tool loads in every session from a repo.

Read-only. Standard library only. Definitions follow the toolkit reorganization
baseline:

- Claude Code: ``CLAUDE.md`` plus every file it imports with ``@path``
  (recursive, at most 5 hops, imports inside code are ignored). The skill and
  agent description listings are printed separately because Claude Code loads
  them as listings, not as instruction files.
- Codex: ``AGENTS.md``. Codex stops reading at its default 32 KiB cap, so the
  bytes past the cap are reported as truncated.
- Cursor: ``AGENTS.md`` plus ``.cursor/rules/*.mdc`` rules with
  ``alwaysApply: true`` (Cursor ignores plain ``.md`` files there).
- Windsurf: ``AGENTS.md`` plus ``rules/*.md`` with ``trigger: always_on``.

``--check`` exits 1 when ``AGENTS.md`` is larger than ``--agents-max`` bytes
(default 24576) or, when ``--rules-budget`` is given, when the always-on rules
total is larger than that budget.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

AGENTS_MAX_DEFAULT = 24576
CODEX_CAP = 32768
MAX_IMPORT_HOPS = 5
IMPORT_RE = re.compile(r"(?:^|\s)@([A-Za-z0-9_./~-][^\s`]*)")


def file_bytes(path: Path) -> int:
    return path.stat().st_size if path.is_file() else 0


def frontmatter(path: Path) -> dict:
    """Return simple ``key: value`` frontmatter, folding block scalars."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return {}
    if not lines or lines[0].strip() != "---":
        return {}
    meta: dict = {}
    key = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            key, value = match.group(1), match.group(2).strip()
            if value in (">", "|", ">-", "|-"):
                value = ""
            meta[key] = value.strip("\"'")
        elif key and line.startswith((" ", "\t")):
            meta[key] = (meta[key] + " " + line.strip()).strip()
    return meta


def strip_code(text: str) -> str:
    text = re.sub(r"(?ms)^```.*?^```[^\n]*$", "", text)
    return re.sub(r"`[^`\n]*`", "", text)


def resolve_imports(root: Path, start: Path) -> list[Path]:
    """Return ``start`` and every file it imports, in load order, without repeats."""
    seen: list[Path] = []

    def walk(path: Path, depth: int) -> None:
        resolved = path.resolve()
        if resolved in seen or not path.is_file():
            return
        seen.append(resolved)
        if depth >= MAX_IMPORT_HOPS:
            return
        text = strip_code(path.read_text(encoding="utf-8", errors="replace"))
        for target in IMPORT_RE.findall(text):
            candidate = Path(target).expanduser()
            if not candidate.is_absolute():
                candidate = path.parent / candidate
            if candidate.is_file():
                walk(candidate, depth + 1)

    walk(start, 0)
    return seen


def always_on_rules(root: Path) -> list[Path]:
    rules_dir = root / "rules"
    if not rules_dir.is_dir():
        return []
    return sorted(
        p for p in rules_dir.glob("*.md")
        if p.name != "README.md" and frontmatter(p).get("trigger") == "always_on"
    )


def cursor_always_rules(root: Path) -> list[Path]:
    rules_dir = root / ".cursor" / "rules"
    if not rules_dir.is_dir():
        return []
    return sorted(
        p for p in rules_dir.glob("*.mdc")
        if frontmatter(p).get("alwaysApply", "").lower() == "true"
    )


def description_chars(paths: list[Path]) -> int:
    return sum(len(frontmatter(p).get("description", "")) for p in paths)


def measure(root: Path) -> dict:
    agents = root / "AGENTS.md"
    agents_bytes = file_bytes(agents)
    claude_files = resolve_imports(root, root / "CLAUDE.md")
    rules = always_on_rules(root)
    rules_bytes = sum(file_bytes(p) for p in rules)
    cursor_rules = cursor_always_rules(root)
    skills = sorted((root / "skills").glob("*/SKILL.md")) if (root / "skills").is_dir() else []
    subagents = sorted(
        p for p in (root / "tool-subagents").glob("*.md") if p.name != "README.md"
    ) if (root / "tool-subagents").is_dir() else []

    def rel(path: Path) -> str:
        try:
            return path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()

    return {
        "agents_md_bytes": agents_bytes,
        "always_on_rules": {"count": len(rules), "bytes": rules_bytes},
        "tools": {
            "Claude Code": {
                "bytes": sum(file_bytes(p) for p in claude_files),
                "files": [rel(p) for p in claude_files],
                "listings": {
                    "skills": len(skills),
                    "skill_description_chars": description_chars(skills),
                    "agents": len(subagents),
                    "agent_description_chars": description_chars(subagents),
                },
            },
            "Codex": {
                "bytes": min(agents_bytes, CODEX_CAP),
                "files": ["AGENTS.md"] if agents_bytes else [],
                "truncated_bytes": max(0, agents_bytes - CODEX_CAP),
            },
            "Cursor": {
                "bytes": agents_bytes + sum(file_bytes(p) for p in cursor_rules),
                "files": (["AGENTS.md"] if agents_bytes else []) + [rel(p) for p in cursor_rules],
            },
            "Windsurf": {
                "bytes": agents_bytes + rules_bytes,
                "files": (["AGENTS.md"] if agents_bytes else []) + [rel(p) for p in rules],
            },
        },
    }


def render(result: dict) -> str:
    lines = [f"{'Tool':<12} {'Bytes':>8}  Loaded every session"]
    for tool, data in result["tools"].items():
        files = data["files"]
        summary = ", ".join(files[:3]) + (f" (+{len(files) - 3} more)" if len(files) > 3 else "")
        lines.append(f"{tool:<12} {data['bytes']:>8,}  {summary or '-'}")
        if data.get("truncated_bytes"):
            lines.append(f"{'':<12} {'':>8}  truncated past the {CODEX_CAP:,} B cap: {data['truncated_bytes']:,} B")
        if "listings" in data:
            lst = data["listings"]
            lines.append(
                f"{'':<12} {'':>8}  listings: {lst['skills']} skill descriptions = "
                f"{lst['skill_description_chars']:,} chars; {lst['agents']} agent descriptions = "
                f"{lst['agent_description_chars']:,} chars"
            )
    lines.append(f"AGENTS.md: {result['agents_md_bytes']:,} B; always-on rules: "
                 f"{result['always_on_rules']['count']} files, {result['always_on_rules']['bytes']:,} B")
    return "\n".join(lines)


def check(result: dict, agents_max: int, rules_budget: int | None) -> list[str]:
    problems = []
    if result["agents_md_bytes"] == 0:
        problems.append("AGENTS.md is missing or empty")
    if result["agents_md_bytes"] > agents_max:
        problems.append(f"AGENTS.md is {result['agents_md_bytes']:,} B; limit is {agents_max:,} B")
    if rules_budget is not None and result["always_on_rules"]["bytes"] > rules_budget:
        problems.append(f"always-on rules total {result['always_on_rules']['bytes']:,} B; "
                        f"budget is {rules_budget:,} B")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]),
                        help="repository root to measure (default: this toolkit)")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a table")
    parser.add_argument("--check", action="store_true", help="exit 1 when a budget is exceeded")
    parser.add_argument("--agents-max", type=int, default=AGENTS_MAX_DEFAULT,
                        help=f"AGENTS.md byte limit for --check (default {AGENTS_MAX_DEFAULT})")
    parser.add_argument("--rules-budget", type=int, default=None,
                        help="always-on rules byte budget for --check (default: not checked)")
    args = parser.parse_args(argv)

    result = measure(Path(args.root))
    print(json.dumps(result, indent=2) if args.json else render(result))
    if args.check:
        problems = check(result, args.agents_max, args.rules_budget)
        for problem in problems:
            print(f"FAIL: {problem}", file=sys.stderr)
        if problems:
            return 1
        print("always-on size check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
