import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


SCAN_ROOTS = (
    "AGENTS.md",
    "CLAUDE.md",
    "INTENTS.md",
    "README.md",
    "docs",
    "integrations",
    "rubrics",
    "rules",
    "skills",
    "tool-subagents",
    "workflows",
    "consumer-profiles",
    ".codex",
)

TEXT_EXTENSIONS = {".md", ".toml", ".txt", ".yaml", ".yml"}
SKIP_DIRS = {
    ".git",
    ".github",
    ".agents",
    ".agent",
    ".claude",
    ".cursor",
    ".gemini",
    ".opencode",
    ".windsurf",
    "__pycache__",
    "node_modules",
}

DEFENSIVE_CONTEXT = (
    "avoid",
    "block",
    "blocks",
    "blocked",
    "detect",
    "do not",
    "don't",
    "fail",
    "flag",
    "forbid",
    "must not",
    "never",
    "refuse",
    "reject",
    "should not",
    "unsafe",
    "insecure",
    "untrusted",
    "vulnerable",
    "wrong",
)

DEFENSIVE_LINE_CONTEXT = (
    "avoid",
    "block",
    "blocks",
    "blocked",
    "detect",
    "does not",
    "do not",
    "don't",
    "fail",
    "flag",
    "forbid",
    "must not",
    "never",
    "refuse",
    "reject",
    "should not",
    "unsafe",
    "insecure",
    "untrusted",
    "vulnerable",
    "wrong",
)


@dataclass(frozen=True)
class PatternRule:
    name: str
    regex: re.Pattern[str]
    message: str
    allow_defensive_context: bool = True


PATTERNS = (
    PatternRule(
        "instruction-override",
        re.compile(
            r"\b(ignore|disregard|override|bypass)\b.{0,60}"
            r"\b(previous|prior|above|system|developer|tool|safety|security)\b.{0,50}"
            r"\b(instruction|prompt|rule|policy|guardrail)s?\b",
            re.IGNORECASE,
        ),
        "possible prompt-injection instruction override",
    ),
    PatternRule(
        "secret-exfiltration",
        re.compile(
            r"("
            r"\b(reveal|print|dump|show|exfiltrate|leak)\b.{0,80}"
            r"\b(secret|token|credential|api[-_ ]?key|password|private key|env(?:ironment)? variable)s?\b"
            r"|"
            r"\b(send|upload)\b.{0,25}"
            r"\b(secret|token|credential|api[-_ ]?key|password|private key|env(?:ironment)? variable)s?\b"
            r")",
            re.IGNORECASE,
        ),
        "possible instruction to expose or exfiltrate secrets",
    ),
    PatternRule(
        "concealed-action",
        re.compile(
            r"\b(secretly|silently|without (?:the )?(?:user|developer|reviewer|auditor) knowing)\b.{0,80}"
            r"\b(run|execute|change|modify|delete|send|upload|exfiltrate)\b",
            re.IGNORECASE,
        ),
        "possible concealed action instruction",
    ),
    PatternRule(
        "download-execute",
        re.compile(
            r"\b(curl|wget|iwr|Invoke-WebRequest)\b.{0,160}"
            r"(\|\s*(sh|bash|zsh|pwsh|powershell)|Invoke-Expression|\biex\b)",
            re.IGNORECASE,
        ),
        "possible download-and-execute command",
    ),
    PatternRule(
        "encoded-powershell",
        re.compile(r"\b(powershell|pwsh)(?:\.exe)?\b.{0,80}\s-(enc|encodedcommand)\b", re.IGNORECASE),
        "possible encoded PowerShell execution",
    ),
    PatternRule(
        "destructive-root-delete",
        re.compile(
            r"(rm\s+-rf\s+/(?:\s|$)|Remove-Item\b.{0,80}\b-Recurse\b.{0,80}\b-Force\b.{0,80}\b[A-Za-z]:\\)",
            re.IGNORECASE,
        ),
        "possible destructive filesystem instruction",
    ),
)


def is_defensive(line: str, previous_context: str) -> bool:
    lower_line = line.lower()
    lower_context = previous_context.lower()
    return any(marker in lower_context for marker in DEFENSIVE_CONTEXT) or any(
        marker in lower_line for marker in DEFENSIVE_LINE_CONTEXT
    )


def iter_files(root: Path):
    for rel in SCAN_ROOTS:
        path = root / rel
        if not path.exists():
            continue
        if path.is_file():
            if path.suffix.lower() in TEXT_EXTENSIONS:
                yield path
            continue
        for current_root, dirnames, filenames in os.walk(path, followlinks=False):
            dirnames[:] = [
                name
                for name in dirnames
                if name not in SKIP_DIRS and not (Path(current_root) / name).is_symlink()
            ]
            for filename in filenames:
                candidate = Path(current_root) / filename
                if candidate.is_symlink() or candidate.suffix.lower() not in TEXT_EXTENSIONS:
                    continue
                yield candidate


def scan_file(root: Path, path: Path):
    findings = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    for index, line in enumerate(lines, start=1):
        context_start = max(0, index - 8)
        context = "\n".join(lines[context_start : index - 1])
        if "llm-surface-security: allow" in line.lower() or "llm-surface-security: allow" in context.lower():
            continue
        for pattern in PATTERNS:
            if not pattern.regex.search(line):
                continue
            if pattern.allow_defensive_context and is_defensive(line, context):
                continue
            findings.append((path.relative_to(root), index, pattern.name, pattern.message, line.strip()))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan LLM-loaded toolkit surfaces for prompt-injection and malicious-instruction patterns."
    )
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    all_findings = []
    for path in iter_files(root):
        all_findings.extend(scan_file(root, path))

    if all_findings:
        print("BLOCKED: possible prompt-injection or malicious-instruction patterns found:", file=sys.stderr)
        for rel_path, line_no, name, message, line in all_findings:
            print(f"{rel_path}:{line_no}: {name}: {message}: {line}", file=sys.stderr)
        print(
            "If a finding is a defensive example, rewrite it with clear safe context or add "
            "`llm-surface-security: allow` on the preceding line with justification.",
            file=sys.stderr,
        )
        return 1

    print("PASS: LLM surface prompt-injection and malicious-instruction scan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
