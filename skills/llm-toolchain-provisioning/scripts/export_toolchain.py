#!/usr/bin/env python3
"""Export installed LLM assistant extensions to a portable manifest.

Read-only: inspects assistant state files and writes only the manifest.

  python export_toolchain.py                     # summary to stdout
  python export_toolchain.py --out toolchain.json
  python export_toolchain.py --provider claude-code --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from toolchain_lib import PROVIDERS, build_manifest, summarize
except ImportError:  # invoked from another directory
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from toolchain_lib import PROVIDERS, build_manifest, summarize


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export installed LLM assistant extensions to a manifest."
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Write the manifest here. Choose a git-ignored path: the manifest "
             "records one workstation's state and must not be committed.",
    )
    parser.add_argument(
        "--provider",
        action="append",
        choices=[name for name, _, _ in PROVIDERS],
        help="Limit to one provider; repeatable. Default: all detected.",
    )
    parser.add_argument("--json", action="store_true", help="Print the manifest to stdout.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = build_manifest(providers=args.provider)
    stats = summarize(manifest)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        # LF regardless of platform so the file hashes identically everywhere
        # (see rules/cross-platform-scripts.md).
        with args.out.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True)
            handle.write("\n")

    if args.json:
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0

    totals = stats["totals"]
    print("LLM toolchain export")
    print(f"  providers detected : {totals['providers']}")
    print(f"  extensions         : {totals['extensions']} ({totals['enabled']} enabled)")
    for origin, count in sorted(stats["by_origin"].items()):
        print(f"    {origin:<10} : {count}")
    print(f"  local artifacts    : {totals['local_artifacts']}")

    findings = manifest.get("findings", [])
    if findings:
        print(f"\nFindings ({len(findings)}):")
        for finding in findings:
            print(f"  [{finding['severity']}] {finding['provider']}: {finding['message']}")

    if args.out:
        print(f"\nManifest written to {args.out}")
        print("Do not commit it — it records this workstation only.")
    else:
        print("\nNo --out given; nothing written.")

    if totals["extensions"] and not stats["by_origin"].get("local"):
        print(
            "\nEvery extension is upstream or organization-published: reproduce by "
            "re-installing at the recorded pins. Copying the content into a "
            "repository would vendor third-party code."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
