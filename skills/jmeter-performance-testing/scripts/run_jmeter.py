#!/usr/bin/env python3
"""Patch a copy of a JMeter test plan and run it, on Windows, Linux, or macOS.

Standard library only (no third-party dependencies). The source `.jmx` is
never modified: every run writes a patched copy plus a manifest, results, and
log into a fresh, timestamped results directory.

Typical use:

    python3 run_jmeter.py --jmx plan.jmx --base-url https://api.example.com \\
        --threads 20 --ramp-up 60 --duration 300 --dry-run

    python3 run_jmeter.py --jmx plan.jmx --base-url https://api.example.com \\
        --threads 20 --ramp-up 60 --duration 300 \\
        --auth-token-env API_TOKEN

Always dry-run first (`--dry-run`): it patches a copy of the `.jmx`, writes
`manifest.json` describing the resolved settings and the exact command, and
prints that command -- without generating any load or requiring JMeter to be
installed.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import NoReturn
import xml.etree.ElementTree as ET

REDACTED = "<redacted>"

# Maps a CLI override to the JMeter Thread Group `stringProp` it patches in
# the copied .jmx. These are plain literal overrides for plans that hardcode
# their Thread Group numbers; a plan that already reads
# `${__P(threads,...)}`-style properties does not need this at all.
THREAD_GROUP_PROPS = {
    "threads": "ThreadGroup.num_threads",
    "ramp_up": "ThreadGroup.ramp_time",
    "duration": "ThreadGroup.duration",
}


def fail(message: str) -> NoReturn:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def find_on_path(name: str) -> Path | None:
    found = shutil.which(name)
    return Path(found) if found else None


def resolve_jmeter_bin(explicit: str) -> Path | None:
    """Resolve the jmeter executable: --jmeter-bin, then PATH, then JMETER_HOME."""
    if explicit:
        candidate = Path(explicit).expanduser()
        return candidate if candidate.exists() else None
    for name in ("jmeter", "jmeter.bat"):
        found = find_on_path(name)
        if found:
            return found
    jmeter_home = os.environ.get("JMETER_HOME")
    if jmeter_home:
        for name in ("bin/jmeter.bat", "bin/jmeter"):
            candidate = Path(jmeter_home).expanduser() / name
            if candidate.exists():
                return candidate
    return None


def parse_property(raw: str) -> tuple[str, str]:
    if "=" not in raw or raw.startswith("="):
        fail(f"--property must be KEY=VALUE, got: {raw}")
    key, value = raw.split("=", 1)
    key = key.strip()
    if not key:
        fail(f"--property must be KEY=VALUE with a non-empty KEY, got: {raw}")
    return key, value


def load_jmx(source: Path) -> ET.ElementTree:
    # Preserve comments/PIs on the round trip so the patched copy stays close
    # to the source plan instead of silently dropping author notes.
    # The .jmx is a local, user-supplied file; Python's ElementTree does not
    # resolve external entities, and defusedxml is used when installed for
    # defence in depth (entity expansion / DTD retrieval hardening).
    parser = ET.XMLParser(
        target=ET.TreeBuilder(insert_comments=True, insert_pis=True)
    )
    try:
        try:
            from defusedxml.ElementTree import parse as defused_parse  # type: ignore

            return defused_parse(str(source), parser=parser)
        except ImportError:
            # nosemgrep: python.lang.security.use-defused-xml-parse.use-defused-xml-parse
            return ET.parse(source, parser=parser)
    except ET.ParseError as exc:
        fail(f"Could not parse {source} as XML: {exc}")


def patch_thread_group(root: ET.Element, prop_name: str, value: int) -> int:
    matches = [node for node in root.iter("stringProp") if node.get("name") == prop_name]
    for node in matches:
        node.text = str(value)
    return len(matches)


def run_name() -> str:
    return f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def redact_command(command: list[str]) -> list[str]:
    """Redact every -J property VALUE. Keys stay visible; values never do.

    This is deliberately blunt: the tool cannot tell which --property or
    --base-url values are sensitive, so every -J argument is treated as if it
    might be. The auth token is covered by the same rule, never as a special
    case that could be missed.
    """
    redacted: list[str] = []
    for arg in command:
        if arg.startswith("-J") and "=" in arg:
            key = arg[2:].split("=", 1)[0]
            redacted.append(f"-J{key}={REDACTED}")
        else:
            redacted.append(arg)
    return redacted


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--jmx", required=True, help="Path to the source .jmx test plan. Never modified.")
    parser.add_argument(
        "--base-url",
        default=None,
        help="Injected as the JMeter property 'base_url' (-Jbase_url=VALUE). "
        "Read it in the plan as ${__P(base_url,)}.",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=None,
        help="Override ThreadGroup.num_threads in the patched copy. Requires the plan to have that field.",
    )
    parser.add_argument(
        "--ramp-up",
        type=int,
        default=None,
        help="Override ThreadGroup.ramp_time in seconds in the patched copy.",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="Override ThreadGroup.duration in seconds in the patched copy (enable the Scheduler in the plan for this to take effect).",
    )
    parser.add_argument(
        "--property",
        dest="properties",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Extra JMeter property, injected as -JKEY=VALUE. Repeatable. Values are redacted in console output and the manifest.",
    )
    auth_group = parser.add_mutually_exclusive_group()
    auth_group.add_argument(
        "--auth-token",
        default=None,
        help="Auth token value, injected as the JMeter property 'auth_token' (-Jauth_token=VALUE). "
        "Visible in shell history and the local process list; prefer --auth-token-env. Never printed or written to the manifest.",
    )
    auth_group.add_argument(
        "--auth-token-env",
        metavar="ENV_VAR",
        default=None,
        help="Name of an environment variable holding the auth token. Read at run time and injected the same way as --auth-token, without ever appearing in your shell history.",
    )
    parser.add_argument(
        "--results-dir",
        default="perf-runs",
        help="Root directory for run output; a timestamped subdirectory is created under it for this run. Default: perf-runs",
    )
    parser.add_argument(
        "--jmeter-bin",
        default="",
        help="Path to the jmeter (or jmeter.bat) executable. Default: search PATH, then $JMETER_HOME/bin/.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Patch a copy of the .jmx and write manifest.json without executing JMeter or requiring it to be installed.",
    )
    return parser


def resolve_auth_token(args: argparse.Namespace) -> tuple[str | None, str | None]:
    """Returns (token_value, source_label). token_value is never logged by the caller."""
    if args.auth_token is not None:
        return args.auth_token, "--auth-token"
    if args.auth_token_env:
        value = os.environ.get(args.auth_token_env)
        if value is None:
            fail(f"--auth-token-env {args.auth_token_env}: environment variable is not set.")
        return value, f"--auth-token-env={args.auth_token_env}"
    return None, None


def main(argv: list[str]) -> int:
    args = build_arg_parser().parse_args(argv)

    source_jmx = Path(args.jmx).expanduser().resolve()
    if not source_jmx.is_file():
        fail(f"JMX file not found: {source_jmx}")

    for flag, value in (("--threads", args.threads), ("--ramp-up", args.ramp_up), ("--duration", args.duration)):
        if value is not None and value <= 0:
            fail(f"{flag} must be a positive integer, got: {value}")

    properties: list[tuple[str, str]] = [parse_property(raw) for raw in args.properties]
    auth_token, auth_token_source = resolve_auth_token(args)

    # Resolve JMeter up front for a real run so we fail before touching disk;
    # a dry run never requires JMeter to be installed at all.
    jmeter_bin = resolve_jmeter_bin(args.jmeter_bin)
    if not args.dry_run and jmeter_bin is None:
        fail(
            "Could not find JMeter. Install it, set JMETER_HOME, or pass --jmeter-bin. "
            "(--dry-run works without JMeter installed.)"
        )

    results_root = Path(args.results_dir).expanduser().resolve()
    run_dir = results_root / run_name()
    run_dir.mkdir(parents=True, exist_ok=True)

    tree = load_jmx(source_jmx)
    root = tree.getroot()

    overrides: dict[str, int] = {}
    for key, cli_value in (("threads", args.threads), ("ramp_up", args.ramp_up), ("duration", args.duration)):
        if cli_value is None:
            continue
        prop_name = THREAD_GROUP_PROPS[key]
        matched = patch_thread_group(root, prop_name, cli_value)
        if matched == 0:
            fail(
                f"Could not find {prop_name} in {source_jmx}; is this a JMeter Thread Group plan? "
                f"(--{key.replace('_', '-')} has nothing to patch)"
            )
        overrides[key] = cli_value

    patched_jmx = run_dir / f"patched-{source_jmx.name}"
    tree.write(patched_jmx, encoding="UTF-8", xml_declaration=True)

    results_jtl = run_dir / "results.jtl"
    jmeter_log = run_dir / "jmeter.log"
    manifest_path = run_dir / "manifest.json"

    jmeter_str = str(jmeter_bin) if jmeter_bin else "jmeter"
    command = [jmeter_str, "-n", "-t", str(patched_jmx), "-l", str(results_jtl), "-j", str(jmeter_log)]
    if args.base_url:
        command.append(f"-Jbase_url={args.base_url}")
    for key, value in properties:
        command.append(f"-J{key}={value}")
    if auth_token is not None:
        command.append(f"-Jauth_token={auth_token}")
    redacted_command = redact_command(command)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "jmx_source": str(source_jmx),
        "patched_jmx": str(patched_jmx),
        "results_dir": str(run_dir),
        "results_jtl": str(results_jtl),
        "jmeter_log": str(jmeter_log),
        "base_url": args.base_url,
        "overrides": overrides,
        "properties": {key: REDACTED for key, _ in properties},
        "auth_token": {"property": "auth_token", "source": auth_token_source} if auth_token is not None else None,
        "jmeter_bin": str(jmeter_bin) if jmeter_bin else None,
        "platform": platform.system(),
        "dry_run": bool(args.dry_run),
        "command": redacted_command,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    if args.dry_run:
        print(f"Dry run complete. Patched JMX: {patched_jmx}")
        print("Would run:")
        print(" ".join(redacted_command))
        print(f"Manifest: {manifest_path}")
        return 0

    print("Running JMeter:")
    print(" ".join(redacted_command))
    try:
        completed = subprocess.run(command, check=False)
    except OSError as exc:
        fail(f"Failed to launch JMeter ({jmeter_str}): {exc}")
    print(f"Exit code: {completed.returncode}")
    print(f"Results JTL: {results_jtl}")
    print(f"JMeter log: {jmeter_log}")
    print(f"Manifest: {manifest_path}")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
