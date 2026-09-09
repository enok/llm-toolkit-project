"""Shared discovery logic for LLM assistant toolchain export/restore.

Portable across Windows, Linux, and macOS: all filesystem access goes through
pathlib, no shell-outs, no OS-specific flags. Read-only by construction — this
module never writes to assistant state.

Providers are described declaratively so support for another assistant is a
table entry, not new code.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

MANIFEST_VERSION = 1

# Values matching these key names are replaced with a placeholder on export.
_SECRET_KEY_PATTERN = re.compile(
    r"token|secret|password|passwd|credential|api[-_]?key|authorization|signature",
    re.IGNORECASE,
)
REDACTED = "<redacted>"

# Install scratch directories an interrupted install leaves behind.
_TRANSIENT_PATTERN = re.compile(r"^temp_(git|subdir)_\d+", re.IGNORECASE)


def home() -> Path:
    """User home directory, overridable for tests."""
    override = os.environ.get("LLM_TOOLCHAIN_HOME")
    return Path(override) if override else Path.home()


def redact(value: Any) -> Any:
    """Recursively replace secret-looking values, preserving structure."""
    if isinstance(value, dict):
        return {
            key: (REDACTED if _SECRET_KEY_PATTERN.search(str(key)) else redact(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def read_json(path: Path) -> Any | None:
    """Parse JSON, returning None when absent or malformed rather than raising.

    Assistant state files are written by other tools and may be mid-write or
    hand-edited; a broken file is a finding, not a crash.
    """
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None


def is_transient(name: str) -> bool:
    """True for interrupted-install scratch directories, which are excluded."""
    return bool(_TRANSIENT_PATTERN.match(name))


def link_target(path: Path) -> str | None:
    """Resolved target if the path is a symlink or reparse point, else None.

    A linked extension directory is a checkout of an already-tracked
    repository, so it is recorded by reference and never copied or descended
    into. Detection must not follow the link.
    """
    try:
        if path.is_symlink():
            return str(path.resolve())
    except OSError:
        return None
    # Windows junctions are not symlinks to pathlib; st_reparse_tag identifies
    # them on Python 3.12+, and a mismatch between lstat and stat catches the
    # rest without following the link.
    try:
        stat_info = path.lstat()
        if getattr(stat_info, "st_reparse_tag", 0):
            return str(path.resolve())
    except OSError:
        return None
    return None


@dataclass
class Finding:
    """Something the operator should look at, not a fatal error."""

    severity: str  # "info" | "warning"
    provider: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"severity": self.severity, "provider": self.provider, "message": self.message}


@dataclass
class ProviderResult:
    provider: str
    present: bool
    extensions: list[dict[str, Any]] = field(default_factory=list)
    sources: list[dict[str, Any]] = field(default_factory=list)
    local_artifacts: list[dict[str, Any]] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "present": self.present,
            "extensions": self.extensions,
            "sources": self.sources,
            "local_artifacts": self.local_artifacts,
        }


def _classify(source_kind: str | None) -> str:
    """Bucket an extension by where it came from.

    Drives the migration decision: only 'local' content needs a home in
    version control. See the skill's authorship section.
    """
    if source_kind is None:
        return "unknown"
    if source_kind in {"git", "url", "npm", "registry"}:
        return "upstream"
    if source_kind in {"local", "path"}:
        return "local"
    return "unknown"


def discover_claude(root: Path) -> ProviderResult:
    """Claude Code: plugins, marketplaces, enablement, and loose commands."""
    result = ProviderResult(provider="claude-code", present=root.is_dir())
    if not result.present:
        return result

    plugins_dir = root / "plugins"
    installed = read_json(plugins_dir / "installed_plugins.json") or {}
    marketplaces = read_json(plugins_dir / "known_marketplaces.json") or {}
    settings = read_json(root / "settings.json") or {}
    enabled_map = settings.get("enabledPlugins") or {}

    # Registered sources, keyed on URL because names differ between the local
    # state file and centrally managed policy.
    for name, entry in marketplaces.items():
        if not isinstance(entry, dict):
            continue
        source = entry.get("source") or {}
        result.sources.append(
            {
                "name": name,
                "kind": source.get("source"),
                "url": source.get("url"),
                "aliases": [name],
            }
        )

    # Centrally managed policy may register the same source under another name.
    managed = read_json(root / "remote-settings.json") or {}
    for name, entry in (managed.get("extraKnownMarketplaces") or {}).items():
        url = ((entry or {}).get("source") or {}).get("url")
        match = next((s for s in result.sources if s.get("url") and s["url"] == url), None)
        if match:
            if name not in match["aliases"]:
                match["aliases"].append(name)
                result.findings.append(
                    Finding(
                        "warning",
                        "claude-code",
                        f"source {url} is registered under differing names "
                        f"({', '.join(match['aliases'])}); key automation on the URL",
                    )
                )
        else:
            result.sources.append(
                {"name": name, "kind": (entry or {}).get("source", {}).get("source"),
                 "url": url, "aliases": [name], "managed": True}
            )

    source_kinds = {s["name"]: s.get("kind") for s in result.sources}

    for key, entries in (installed.get("plugins") or {}).items():
        if not isinstance(entries, list) or not entries:
            continue
        entry = entries[0] if isinstance(entries[0], dict) else {}
        name, _, marketplace = key.partition("@")
        install_path = entry.get("installPath")
        linked = link_target(Path(install_path)) if install_path else None
        result.extensions.append(
            {
                "id": key,
                "name": name,
                "source_name": marketplace or None,
                "origin": _classify(source_kinds.get(marketplace)),
                "version": entry.get("version"),
                "pin": entry.get("gitCommitSha"),
                "scope": entry.get("scope"),
                "enabled": bool(enabled_map.get(key, False)),
                "linked_to": linked,
            }
        )

    for extension in result.extensions:
        if extension["origin"] == "upstream" and not extension["pin"] and not extension["version"]:
            result.findings.append(
                Finding("warning", "claude-code",
                        f"{extension['id']} records neither version nor commit pin; "
                        "restore cannot reproduce it exactly")
            )

    # A source registered but never installed from is worth surfacing.
    installed_sources = {e["source_name"] for e in result.extensions}
    for source in result.sources:
        if source["name"] not in installed_sources:
            result.findings.append(
                Finding("info", "claude-code",
                        f"source '{source['name']}' is registered but nothing is installed from it")
            )

    # Enabled-but-absent is the inverse failure and explains missing capability.
    installed_ids = {e["id"] for e in result.extensions}
    for key, is_enabled in enabled_map.items():
        if is_enabled and key not in installed_ids:
            result.findings.append(
                Finding("warning", "claude-code",
                        f"{key} is enabled but not installed")
            )

    result.local_artifacts.extend(_discover_loose(root, ("commands", "skills", "agents")))
    return result


def _discover_loose(root: Path, subdirs: Iterable[str]) -> list[dict[str, Any]]:
    """Hand-authored files that belong to no extension.

    These are the only genuinely local-authored artifacts, and a linked
    directory is recorded by reference rather than descended into.
    """
    artifacts: list[dict[str, Any]] = []
    for subdir in subdirs:
        path = root / subdir
        linked = link_target(path)
        if linked:
            artifacts.append({"path": f"{subdir}/", "kind": "link", "target": linked})
            continue
        if not path.is_dir():
            continue
        try:
            entries = sorted(path.iterdir(), key=lambda item: item.name)
        except OSError:
            continue
        for entry in entries:
            if is_transient(entry.name):
                continue
            entry_link = link_target(entry)
            artifacts.append(
                {
                    "path": f"{subdir}/{entry.name}",
                    "kind": "link" if entry_link else ("dir" if entry.is_dir() else "file"),
                    "target": entry_link,
                }
            )
    return artifacts


def _discover_vscode_like(root: Path, provider: str) -> ProviderResult:
    """Cursor, Windsurf, and other VS Code derivatives share an extensions dir."""
    result = ProviderResult(provider=provider, present=root.is_dir())
    if not result.present:
        return result

    extensions_dir = root / "extensions"
    catalog = read_json(extensions_dir / "extensions.json")
    if isinstance(catalog, list):
        for entry in catalog:
            if not isinstance(entry, dict):
                continue
            identifier = (entry.get("identifier") or {}).get("id")
            if not identifier:
                continue
            result.extensions.append(
                {
                    "id": identifier,
                    "name": identifier,
                    "source_name": "marketplace",
                    "origin": "upstream",
                    "version": entry.get("version"),
                    "pin": None,
                    "scope": "user",
                    "enabled": True,
                    "linked_to": None,
                }
            )
    elif extensions_dir.is_dir():
        result.findings.append(
            Finding("info", provider,
                    "extensions directory present but no extensions.json catalog; "
                    "version pins unavailable")
        )

    result.local_artifacts.extend(_discover_loose(root, ("rules", "workflows", "skills")))
    return result


def _discover_config_only(root: Path, provider: str) -> ProviderResult:
    """Assistants configured by files rather than an installed extension set."""
    result = ProviderResult(provider=provider, present=root.is_dir())
    if result.present:
        result.local_artifacts.extend(
            _discover_loose(root, ("agents", "skills", "prompts", "commands"))
        )
    return result


# Provider table: adding an assistant is an entry here.
PROVIDERS: tuple[tuple[str, str, Any], ...] = (
    ("claude-code", ".claude", discover_claude),
    ("cursor", ".cursor", lambda root: _discover_vscode_like(root, "cursor")),
    ("windsurf", ".windsurf", lambda root: _discover_vscode_like(root, "windsurf")),
    ("codex", ".codex", lambda root: _discover_config_only(root, "codex")),
    ("gemini", ".gemini", lambda root: _discover_config_only(root, "gemini")),
    ("opencode", ".opencode", lambda root: _discover_config_only(root, "opencode")),
)


def build_manifest(base: Path | None = None, providers: Iterable[str] | None = None) -> dict[str, Any]:
    """Inventory every known provider under `base` (default: home).

    Returns a manifest dict. Absolute paths are deliberately omitted from the
    payload: they are workstation-specific and never portable.
    """
    base = base or home()
    wanted = set(providers) if providers else None
    results: list[ProviderResult] = []

    for name, subdir, discover in PROVIDERS:
        if wanted and name not in wanted:
            continue
        results.append(discover(base / subdir))

    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "providers": [r.as_dict() for r in results if r.present],
        "findings": [f.as_dict() for r in results for f in r.findings],
    }
    return redact(manifest)


def summarize(manifest: dict[str, Any]) -> dict[str, Any]:
    """Counts for human-readable output and for restore-diff headers."""
    totals = {"providers": 0, "extensions": 0, "enabled": 0, "local_artifacts": 0}
    by_origin: dict[str, int] = {}
    for provider in manifest.get("providers", []):
        totals["providers"] += 1
        for extension in provider.get("extensions", []):
            totals["extensions"] += 1
            if extension.get("enabled"):
                totals["enabled"] += 1
            origin = extension.get("origin", "unknown")
            by_origin[origin] = by_origin.get(origin, 0) + 1
        totals["local_artifacts"] += len(provider.get("local_artifacts", []))
    return {"totals": totals, "by_origin": by_origin}
