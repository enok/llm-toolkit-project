#!/usr/bin/env python3
"""Run many tracker_ops writes as one resumable batch.

Every `tracker_ops.py` write reloads and re-saves the whole workbook (3-4 s on a real
tracker), so a day's worth of moves and cell sets is slow and a single device/tool call
can time out while the work is still running. This runner takes the operations as data,
runs them one by one with the same guards `tracker_ops` has (--expect-mtime, --backup-dir),
and writes one JSON line per operation to a log file that can be polled or used to resume.
Standard library only, Python 3.9+. Windows, macOS and Linux.

Usage:
  python tracker_batch.py --tracker T.xlsx --ops ops.json --expect-mtime <m> \\
      --backup-dir ./backups --log batch.log [--resume] [--plan] [--tracker-ops PATH]

ops.json is a JSON list (or {"ops": [...]}) of operations, run in order:
  {"op": "move", "link": "<job url>", "to": "Applied|Interviewing|Closed|Excluded",
   "detail": ..., "channel": ..., "outcome": ..., "date": "YYYY-MM-DD",
   "interview_stage": ..., "interview_date": ..., "follow_up_days": 7,
   "allow_backward": false}                      (only op, link and to are required)
  {"op": "set", "link": "<job url>", "column": "<column>", "value": "<text>",
   "sheet": "<tab>"}                             (op, link, column and value are required)
Keys map one to one to the `tracker_ops move` / `tracker_ops set` flags (snake_case key,
dashed flag: interview_stage -> --interview-stage). Unknown ops or keys, missing or mistyped
values are all reported together, exit code 2, before anything runs.

What it does:
  * Runs tracker_ops.py (default: next to this script) once per operation with the same
    Python (sys.executable), decoding the child's output as UTF-8 (errors='replace') and
    forcing PYTHONIOENCODING=utf-8 / PYTHONUTF8=1 in the child, so a non-ASCII character
    (an en dash in a job title) cannot crash the run on a Windows code page.
  * Chains the `mtime` each write prints into the next operation's --expect-mtime. Before the
    first operation it copies the workbook to <backup-dir>/<name>.pre-batch-<stamp><ext>,
    one restore point for the whole batch (tracker_ops names its own backups per second).
  * Appends one JSON line per operation to --log and flushes it at once, so another call can
    poll the file while this one runs (indexes are 0-based positions in the ops list):
      {"i": 0, "op": "move", "link": "...", "ok": true, "mtime": 1760000000.12, "secs": 3.4}
      {"i": 2, "op": "move", "link": "...", "ok": false, "exit": 2, "error": "<tail of stderr>"}
    A batch that completes ends with {"done": true, "mtime": ...}; a failed one has no done line.
  * Stops at the first failure and exits with the child's exit code (2 usage/config, 3 tracker
    changed since --expect-mtime, 4 tracker locked, ...). Operations after it do not run.
  * Prints one JSON summary on stdout:
      {"ok": <ran ok>, "skipped": <skipped by --resume>, "failed": <index or null>,
       "mtime": <last mtime>, "backup": <pre-batch copy or null>}
    A validation failure (exit 2) adds "problems": [...].

--resume: after a failure (or a killed run), fix the problem (for example correct the bad
operation in ops.json) and run the same command again with --resume and --expect-mtime set
to the tracker's CURRENT mtime (the "mtime" of the last summary, or a fresh stat). Operations
already logged ok with the same index, op and link are skipped; everything else runs, and
new lines are appended to the same log. An ops file that now disagrees with an ok line (same
index, different op or link) is a validation error. Without --resume an existing non-empty
log is refused, so stale lines can never mask work that was not done. If a run was killed
while a write was in flight, that operation may be applied but not logged: re-running it
fails with exit 2 ("job not found" / "already in ..."); check the tracker, drop that
operation from ops.json and resume.

--plan: validate everything, print the commands that would run (and which are skipped when
combined with --resume) as JSON, run nothing, write no log and no backup.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

MOVE_TARGETS = ("Applied", "Interviewing", "Closed", "Excluded")
# ops.json key -> tracker_ops flag, for the optional free-text keys of `move`
MOVE_TEXT_KEYS = {"detail": "--detail", "channel": "--channel", "outcome": "--outcome", "date": "--date",
                  "interview_stage": "--interview-stage", "interview_date": "--interview-date"}
OP_KEYS = {
    "move": {"op", "link", "to", "allow_backward", "follow_up_days", *MOVE_TEXT_KEYS},
    "set": {"op", "link", "column", "value", "sheet"},
}
REQUIRED = {"move": ("link", "to"), "set": ("link", "column", "value")}
ERROR_TAIL = 800


class Problems(Exception):
    def __init__(self, problems):
        super().__init__("; ".join(problems))
        self.problems = list(problems)


def read_text_file(path: Path) -> str:
    """Decode a JSON file written by anything: UTF-8 (with or without BOM) or PowerShell's UTF-16."""
    raw = path.read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig")


def load_ops(path: Path) -> list:
    try:
        data = json.loads(read_text_file(path))
    except (OSError, ValueError) as e:  # UnicodeDecodeError and JSONDecodeError are ValueErrors
        raise Problems([f"cannot read ops file {path}: {e}"])
    problems = []
    if isinstance(data, dict):
        problems += [f"ops file: unknown top-level key '{k}' (only 'ops' is allowed)" for k in sorted(data) if k != "ops"]
        data = data.get("ops")
    if not isinstance(data, list) or not data:
        problems.append("ops file must be a non-empty list of operations (or {\"ops\": [...]})")
        raise Problems(problems)
    for i, op in enumerate(data):
        problems += check_op(i, op)
    if problems:
        raise Problems(problems)
    return data


def is_str(v) -> bool:
    return isinstance(v, str) and bool(v.strip())


def check_op(i: int, op) -> list:
    where = f"ops[{i}]"
    if not isinstance(op, dict):
        return [f"{where}: must be an object, got {type(op).__name__}"]
    kind = op.get("op")
    if kind not in OP_KEYS:
        return [f"{where}: unknown op {kind!r} (allowed: {', '.join(sorted(OP_KEYS))})"]
    out = [f"{where}: unknown key '{k}' for op '{kind}' (allowed: {', '.join(sorted(OP_KEYS[kind]))})"
           for k in sorted(set(op) - OP_KEYS[kind])]
    out += [f"{where}: op '{kind}' needs '{k}'" for k in REQUIRED[kind] if op.get(k) in (None, "")]
    if "link" in op and op["link"] not in (None, "") and not is_str(op["link"]):
        out.append(f"{where}: 'link' must be a non-empty string")
    if kind == "move":
        if op.get("to") not in (None, "") and op["to"] not in MOVE_TARGETS:
            out.append(f"{where}: 'to' must be one of {', '.join(MOVE_TARGETS)}, got {op['to']!r}")
        for k in MOVE_TEXT_KEYS:
            if op.get(k) is not None and not isinstance(op[k], str):
                out.append(f"{where}: '{k}' must be a string")
        if isinstance(op.get("date"), str):
            try:
                dt.date.fromisoformat(op["date"])
            except ValueError:
                out.append(f"{where}: 'date' must be YYYY-MM-DD, got {op['date']!r}")
        fud = op.get("follow_up_days")
        if fud is not None and (isinstance(fud, bool) or not isinstance(fud, int)):
            out.append(f"{where}: 'follow_up_days' must be an integer")
        if op.get("allow_backward") is not None and not isinstance(op["allow_backward"], bool):
            out.append(f"{where}: 'allow_backward' must be true or false")
    else:
        if op.get("column") not in (None, "") and not is_str(op["column"]):
            out.append(f"{where}: 'column' must be a non-empty string")
        v = op.get("value")
        if v not in (None, ""):
            if isinstance(v, bool) or not isinstance(v, (str, int, float)):
                out.append(f"{where}: 'value' must be a string or a number")
            elif not str(v).strip():
                out.append(f"{where}: 'value' must not be empty")
        if op.get("sheet") is not None and not is_str(op["sheet"]):
            out.append(f"{where}: 'sheet' must be a non-empty string")
    return out


def op_args(op: dict) -> list:
    """tracker_ops arguments for one validated operation. `--flag=value` keeps values that start with '-' intact."""
    args = [op["op"], f"--link={op['link']}"]
    if op["op"] == "move":
        args.append(f"--to={op['to']}")
        for key, flag in MOVE_TEXT_KEYS.items():
            if op.get(key) is not None:
                args.append(f"{flag}={op[key]}")
        if op.get("follow_up_days") is not None:
            args.append(f"--follow-up-days={op['follow_up_days']}")
        if op.get("allow_backward"):
            args.append("--allow-backward")
    else:
        args += [f"--column={op['column']}", f"--value={op['value']}"]
        if op.get("sheet") is not None:
            args.append(f"--sheet={op['sheet']}")
    return args


def build_cmd(tracker_ops: Path, tracker: str, op: dict, mtime: str, backup_dir: str, id_patterns: list) -> list:
    cmd = [sys.executable, str(tracker_ops), op["op"], f"--tracker={tracker}"]
    cmd += [f"--id-pattern={p}" for p in id_patterns]
    cmd += op_args(op)[1:]
    cmd += [f"--expect-mtime={mtime}", f"--backup-dir={backup_dir}"]
    return cmd


def read_log_ok(path: Path) -> dict:
    """index -> (op, link) of the latest ok line per index; unreadable lines (a torn last write) are ignored."""
    ok = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if isinstance(rec, dict) and rec.get("ok") is True and isinstance(rec.get("i"), int):
                ok[rec["i"]] = (rec.get("op"), rec.get("link"))
    return ok


def tail(text: str) -> str:
    text = (text or "").strip()
    return text[-ERROR_TAIL:]


def exit_code(rc: int) -> int:
    return rc if isinstance(rc, int) and 0 < rc < 256 else 1


def emit(obj) -> None:
    """One JSON line on stdout; ASCII-only so no console code page can break it."""
    sys.stdout.write(json.dumps(obj, ensure_ascii=True) + "\n")
    sys.stdout.flush()


def say(msg: str) -> None:
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="tracker_batch.py", formatter_class=argparse.RawDescriptionHelpFormatter, description=__doc__,
        epilog="Exit codes: 0 all ok; 2 invalid ops or usage (or tracker_ops' own usage error); 3 tracker "
               "changed (--expect-mtime mismatch); 4 tracker locked; 1 unexpected child result. A failing "
               "child's exit code is passed through.")
    ap.add_argument("--tracker", required=True, help="path of the .xlsx tracker")
    ap.add_argument("--ops", required=True, help="JSON file: a list (or {\"ops\": [...]}) of move/set operations")
    ap.add_argument("--expect-mtime", type=float,
                    help="the tracker's current mtime (from a prior write's JSON or a stat); required unless --plan")
    ap.add_argument("--backup-dir", help="folder for backups (a pre-batch copy plus tracker_ops' own); "
                                         "required unless --plan")
    ap.add_argument("--log", help="JSON-lines progress log, appended to and flushed per operation; "
                                  "required unless --plan")
    ap.add_argument("--resume", action="store_true",
                    help="skip operations already logged ok (same index, op, link); pass the tracker's CURRENT "
                         "mtime as --expect-mtime")
    ap.add_argument("--plan", action="store_true", help="validate and print the commands; run nothing")
    ap.add_argument("--tracker-ops", help="path of tracker_ops.py (default: next to this script)")
    ap.add_argument("--id-pattern", action="append", default=[],
                    help="regex forwarded to every tracker_ops call (repeatable), for job links the default "
                         "id patterns do not cover")
    return ap


def fail_validation(problems: list, mtime) -> int:
    say(f"tracker_batch: {len(problems)} problem(s), nothing was run:")
    for p in problems:
        say(f"  {p}")
    emit({"ok": 0, "skipped": 0, "failed": None, "mtime": mtime, "backup": None, "problems": problems})
    return 2


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):  # never die on printing a path or title in a legacy code page
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")
    ap = build_parser()
    a = ap.parse_args(argv)
    if not a.plan:
        missing = [f"--{n.replace('_', '-')}" for n in ("expect_mtime", "backup_dir", "log") if getattr(a, n) is None]
        if missing:
            ap.error(f"{', '.join(missing)} required unless --plan")
    if a.resume and not a.log:
        ap.error("--resume needs --log")
    if a.expect_mtime is not None and not math.isfinite(a.expect_mtime):
        ap.error("--expect-mtime must be a finite number")
    start_mtime = repr(float(a.expect_mtime)) if a.expect_mtime is not None else "<mtime>"
    summary_mtime = a.expect_mtime

    tracker_ops = Path(a.tracker_ops) if a.tracker_ops else Path(__file__).resolve().with_name("tracker_ops.py")
    problems = []
    if not Path(a.tracker).is_file():
        problems.append(f"tracker not found: {a.tracker}")
    if not tracker_ops.is_file():
        problems.append(f"tracker_ops.py not found: {tracker_ops} (use --tracker-ops)")
    try:
        ops = load_ops(Path(a.ops))
    except Problems as e:
        problems += e.problems
        ops = []
    log_path = Path(a.log) if a.log else None
    done_ok = {}
    if log_path is not None and log_path.exists() and log_path.stat().st_size > 0:
        if a.resume:
            done_ok = read_log_ok(log_path)
        elif not a.plan:
            problems.append(f"log {log_path} already has content; pass --resume to continue it or use a new --log")
    skip = set()
    for i, op in enumerate(ops):
        if i in done_ok:
            if done_ok[i] == (op["op"], op["link"]):
                skip.add(i)
            else:
                problems.append(f"ops[{i}] is {op['op']} {op['link']} but the log has it done as "
                                f"{done_ok[i][0]} {done_ok[i][1]}; the ops file changed - start a new log")
    if problems:
        return fail_validation(problems, summary_mtime)

    if a.plan:
        plan, current = [], start_mtime
        for i, op in enumerate(ops):
            entry = {"i": i, "op": op["op"], "link": op["link"], "skip": i in skip}
            if i not in skip:
                cmd = build_cmd(tracker_ops, a.tracker, op, current, a.backup_dir or "<backup-dir>", a.id_pattern)
                entry.update({"argv": cmd, "command": shlex.join(cmd)})
                current = "<mtime>"
            plan.append(entry)
        emit({"plan": plan, "ops": len(ops), "skipped": len(skip)})
        return 0

    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    current, n_ok, backup, failed, code = start_mtime, 0, None, None, 0
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8", newline="\n") as log:
        def write(rec: dict) -> None:
            log.write(json.dumps(rec, ensure_ascii=True) + "\n")
            log.flush()

        for i, op in enumerate(ops):
            if i in skip:
                continue
            if backup is None:  # lazily, so a fully skipped resume leaves no copy behind
                src = Path(a.tracker)
                stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
                Path(a.backup_dir).mkdir(parents=True, exist_ok=True)
                dest = Path(a.backup_dir) / f"{src.stem}.pre-batch-{stamp}{src.suffix}"
                shutil.copy2(src, dest)
                backup = str(dest)
            cmd = build_cmd(tracker_ops, a.tracker, op, current, a.backup_dir, a.id_pattern)
            t0 = time.monotonic()
            base = {"i": i, "op": op["op"], "link": op["link"]}
            try:
                proc = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace", env=env,
                                      stdin=subprocess.DEVNULL)
            except KeyboardInterrupt:
                write(dict(base, ok=False, exit=130, error="interrupted"))
                failed, code = i, 130
                break
            except OSError as e:
                write(dict(base, ok=False, exit=2, error=f"cannot start tracker_ops: {e}"))
                failed, code = i, 2
                break
            secs = round(time.monotonic() - t0, 2)
            new_mtime = None
            if proc.returncode == 0:
                try:
                    new_mtime = float(json.loads(proc.stdout)["mtime"])
                except (ValueError, KeyError, TypeError):
                    new_mtime = None
            if proc.returncode == 0 and new_mtime is not None:
                current = repr(new_mtime)
                summary_mtime = new_mtime
                n_ok += 1
                write(dict(base, ok=True, mtime=new_mtime, secs=secs))
                say(f"tracker_batch: [{i + 1}/{len(ops)}] {op['op']} ok ({secs}s)")
                continue
            if proc.returncode == 0:
                err = "tracker_ops exited 0 but printed no JSON mtime; the write may have been applied - " \
                      "re-read the tracker before --resume. Output: " + tail(proc.stdout)
                code = 1
            else:
                err = tail(proc.stderr) or tail(proc.stdout) or "no output"
                code = exit_code(proc.returncode)
            write(dict(base, ok=False, exit=code, error=err, secs=secs))
            say(f"tracker_batch: [{i + 1}/{len(ops)}] {op['op']} FAILED exit {code}: {err}")
            failed = i
            break
        else:
            write({"done": True, "mtime": summary_mtime})
    emit({"ok": n_ok, "skipped": len(skip), "failed": failed, "mtime": summary_mtime, "backup": backup})
    return code


if __name__ == "__main__":
    sys.exit(main())
