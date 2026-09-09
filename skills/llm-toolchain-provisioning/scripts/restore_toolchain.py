#!/usr/bin/env python3
"""Diff a toolchain manifest against this workstation and plan a restore.

Dry-run by default: prints the commands a restore would run. `--apply` is
accepted but deliberately still does not execute installs — it prints a
copy-paste block instead, because installing software into an operator's
environment needs their review (rules/external-write-authorization.md).

  python restore_toolchain.py --manifest toolchain.json
  python restore_toolchain.py --manifest toolchain.json --apply
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from toolchain_lib import build_manifest
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from toolchain_lib import build_manifest

# Install command templates per provider. Extend alongside toolchain_lib.PROVIDERS.
_INSTALL_TEMPLATES = {
    "claude-code": "claude plugin install {name}@{source}",
    "cursor": "cursor --install-extension {name}{version_suffix}",
    "windsurf": "windsurf --install-extension {name}{version_suffix}",
}
_SOURCE_TEMPLATES = {
    "claude-code": "claude plugin marketplace add {url}",
}


def _index(manifest: dict) -> dict[str, dict]:
    """Flatten to {provider: {extension_id: extension}} for comparison."""
    return {
        provider["provider"]: {e["id"]: e for e in provider.get("extensions", [])}
        for provider in manifest.get("providers", [])
    }


def _plan_provider(name: str, wanted: dict, present: dict) -> dict:
    missing, mismatched = [], []
    for ext_id, extension in sorted(wanted.items()):
        current = present.get(ext_id)
        if current is None:
            missing.append(extension)
            continue
        want_pin = extension.get("pin") or extension.get("version")
        have_pin = current.get("pin") or current.get("version")
        if want_pin and have_pin and want_pin != have_pin:
            mismatched.append({"id": ext_id, "want": want_pin, "have": have_pin})
    # Extras are reported, never removed: an extension present locally but
    # absent from the manifest is usually a deliberate local addition.
    extra = sorted(set(present) - set(wanted))
    return {"provider": name, "missing": missing, "mismatched": mismatched, "extra": extra}


def _commands(manifest: dict, plans: list[dict]) -> list[str]:
    commands: list[str] = []
    sources_by_provider = {
        p["provider"]: p.get("sources", []) for p in manifest.get("providers", [])
    }
    for plan in plans:
        provider = plan["provider"]
        if not plan["missing"] and not plan["mismatched"]:
            continue
        # Register sources before installing from them.
        template = _SOURCE_TEMPLATES.get(provider)
        if template:
            needed = {e.get("source_name") for e in plan["missing"] if e.get("source_name")}
            for source in sources_by_provider.get(provider, []):
                if source.get("name") in needed and source.get("url"):
                    commands.append(template.format(url=source["url"]))
        install = _INSTALL_TEMPLATES.get(provider)
        if not install:
            commands.append(f"# {provider}: no install command known; restore manually")
            continue
        for extension in plan["missing"]:
            version = extension.get("version")
            commands.append(
                install.format(
                    name=extension["name"],
                    source=extension.get("source_name") or "",
                    version_suffix=f"@{version}" if version else "",
                )
            )
    return commands


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan a toolchain restore from a manifest.")
    parser.add_argument("--manifest", type=Path, required=True, help="Manifest to restore from.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Print a copy-paste install block. Still does not execute installs.",
    )
    parser.add_argument("--json", action="store_true", help="Emit the plan as JSON.")
    args = parser.parse_args(argv)

    if not args.manifest.is_file():
        print(f"error: manifest not found: {args.manifest}", file=sys.stderr)
        return 2
    try:
        with args.manifest.open("r", encoding="utf-8-sig") as handle:
            manifest = json.load(handle)
    except json.JSONDecodeError as exc:
        print(f"error: manifest is not valid JSON: {exc}", file=sys.stderr)
        return 2

    wanted_all = _index(manifest)
    present_all = _index(build_manifest())
    plans = [
        _plan_provider(name, wanted, present_all.get(name, {}))
        for name, wanted in sorted(wanted_all.items())
    ]
    commands = _commands(manifest, plans)

    if args.json:
        print(json.dumps({"plans": plans, "commands": commands}, indent=2, sort_keys=True))
        return 0

    print(f"Restore plan from {args.manifest}\n")
    for plan in plans:
        counts = (
            f"{len(plan['missing'])} missing, "
            f"{len(plan['mismatched'])} version-mismatched, "
            f"{len(plan['extra'])} extra"
        )
        print(f"{plan['provider']}: {counts}")
        for extension in plan["missing"]:
            pin = extension.get("pin") or extension.get("version") or "unpinned"
            print(f"    missing     {extension['id']} ({pin})")
        for item in plan["mismatched"]:
            print(f"    mismatched  {item['id']}: want {item['want']}, have {item['have']}")
        for ext_id in plan["extra"]:
            print(f"    extra       {ext_id} (kept; not removed)")

    if commands:
        header = "Commands to run" if args.apply else "Dry run — commands that would run"
        print(f"\n{header}:\n")
        for command in commands:
            print(f"  {command}")
        if not args.apply:
            print("\nRe-run with --apply to get a copy-paste block.")
        print("\nAfter restoring, re-export and compare; anything that did not take is a finding.")
    else:
        print("\nNothing to do — this workstation already matches the manifest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
