#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reorg_scan.py - read-only inventory and reference scan for a folder reorganization.

Requires Python 3.9 or newer, standard library only.  Reads the tree and writes only the output
files named on the command line.  Shares its path rules with reorg_exec.py (same directory).

    python reorg_scan.py inventory --root ROOT --out-dir DIR --label LABEL [options]
    python reorg_scan.py refscan   --root ROOT (--pathmap MAP.csv | --pattern REGEX ...) --out OUT.tsv
                                   [--historical GLOB ...] [options]

Subcommands
  inventory  list every file under --root (the --out-dir is left out when it lies inside --root):
               <label>-inventory.tsv    rel_path<TAB>bytes<TAB>mtime_utc<TAB>kind  (reorg_exec.py --inventory)
               <label>-area-totals.tsv  area<TAB>files<TAB>bytes, one row per top-level entry, then TOTAL
             A file that cannot be stat'ed gets bytes -1 and kind "ERR <reason>"; the run then exits 1
             (reorg_exec.py refuses an inventory with error rows).
  refscan    find references to old paths in text files and in the XML members of Office files:
               OUT.tsv  file<TAB>line<TAB>class<TAB>pattern<TAB>snippet   (class: live | historical)
             --pathmap derives one pattern per old_path exactly as `reorg_exec.py verify` does;
             --pattern adds a raw regular expression (repeatable).  At least one is required; both may
             be combined.  Binary files are skipped.

Options (both subcommands)
  --ignore GLOB             repeatable; files and directories left out
                            (always added: desktop.ini, Thumbs.db, .DS_Store)
  --no-default-ignore       do not add those three default ignore globs
  --skip-dir NAME           repeatable; directory names that are not entered
                            (refscan always skips .git __pycache__ node_modules .idea .mvn)
  --case-insensitive MODE   auto | yes | no (default auto: probes --root, falls back to the OS)
Options (refscan only)
  --historical GLOB         repeatable; files whose hits are classed "historical" instead of "live"

Glob rules (same as reorg_exec.py): a pattern without '/' is tested against every path component,
a pattern with '/' against every leading and every trailing part of the relative path.
Exit codes: 0 ok, 1 problem or failure, 2 usage error.
Formats and a worked example: skills/folder-reorganization/references/data-formats.md
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import re
import sys
import types
import zipfile

sys.dont_write_bytecode = True  # importing reorg_exec must not leave a __pycache__ next to the scripts

HERE = os.path.dirname(os.path.abspath(__file__))


def _load_exec():
    """reorg_exec.py from this directory: one source of truth for globs, the old-path regex and
    the text/binary/Office classification."""
    path = os.path.join(HERE, "reorg_exec.py")
    spec = importlib.util.spec_from_file_location("reorg_exec_shared", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rx = _load_exec()
Fail = rx.Fail
LABEL_RE = re.compile(r"[A-Za-z0-9._-]+")
SNIPPET = 200
CONTEXT = 80


# --------------------------------------------------------------------------- helpers
def clean(s):
    """A value safe for one TSV field."""
    return re.sub(r"[\t\r\n]+", " ", s)


def resolve_ci(a, root):
    if a.case_insensitive == "auto":
        return rx.detect_ci(root)
    return a.case_insensitive == "yes"


def ignore_globs(a, ci):
    pats = ([] if a.no_default_ignore else list(rx.DEFAULT_IGNORE)) + list(a.ignore)
    return rx.Globs(pats, ci)


def real_key(p):
    return os.path.normcase(os.path.realpath(p))


def walk_files(root, ci, ignore, skip_dirs, skip_real=(), skip_files=(), onerror=None):
    """Yield (rel, full) for every file under root, sorted per directory.  A directory is not entered
    when its name is in skip_dirs, its relative path matches the ignore globs, or its real path is
    in skip_real; files matching the ignore globs or listed in skip_files are left out."""
    skip_real = set(skip_real)
    skip_files = set(os.path.normcase(os.path.abspath(f)) for f in skip_files)
    for dp, dns, fns in os.walk(root, onerror=onerror):
        keep = []
        for d in sorted(dns):
            full = os.path.join(dp, d)
            if (d.lower() if ci else d) in skip_dirs or ignore.match(os.path.relpath(full, root)):
                continue
            if skip_real and real_key(full) in skip_real:
                continue
            keep.append(d)
        dns[:] = keep
        for fn in sorted(fns):
            full = os.path.join(dp, fn)
            rel = os.path.relpath(full, root)
            if ignore.match(rel):
                continue
            if skip_files and os.path.normcase(os.path.abspath(full)) in skip_files:
                continue
            yield rel, full


def write_tsv(path, header, rows):
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(header) + "\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")


# --------------------------------------------------------------------------- inventory
def cmd_inventory(a):
    root = os.path.abspath(a.root)
    if not os.path.isdir(root):
        raise Fail("root is not a directory: %s" % root)
    if not LABEL_RE.fullmatch(a.label):
        raise Fail("--label may contain only letters, digits, '.', '_' and '-'")
    ci = resolve_ci(a, root)
    out_dir = os.path.abspath(a.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    skip = set(s.lower() if ci else s for s in a.skip_dir)
    rows = []

    def err_row(path, ex):
        rel = os.path.relpath(path, root) if path else "?"
        rows.append((clean(rx.posix(rel)), -1, "", "ERR " + clean(str(ex))[:200]))

    def on_dir_error(ex):
        err_row(getattr(ex, "filename", None), ex)

    for rel, full in walk_files(root, ci, ignore_globs(a, ci), skip, [real_key(out_dir)], (), on_dir_error):
        name = rx.posix(rel)
        if clean(name) != name:
            err_row(full, "file name contains a tab or a line break")
            continue
        try:
            st = os.lstat(full)
        except OSError as ex:
            err_row(full, ex)
            continue
        rows.append((name, st.st_size, rx.fmt_mtime(st.st_mtime), "file"))
    rows.sort(key=lambda r: r[0])

    totals, errors = {}, 0
    for name, size, _, kind in rows:
        if kind != "file":
            errors += 1
            continue
        area = name.split("/", 1)[0] if "/" in name else "(root files)"
        t = totals.setdefault(area, [0, 0])
        t[0] += 1
        t[1] += size
    nfiles = sum(t[0] for t in totals.values())
    nbytes = sum(t[1] for t in totals.values())
    inv_path = os.path.join(out_dir, a.label + "-inventory.tsv")
    area_path = os.path.join(out_dir, a.label + "-area-totals.tsv")
    write_tsv(inv_path, ("rel_path", "bytes", "mtime_utc", "kind"), rows)
    write_tsv(area_path, ("area", "files", "bytes"),
              [(k, v[0], v[1]) for k, v in sorted(totals.items())] + [("TOTAL", nfiles, nbytes)])
    print("inventory: %d files, %d bytes, %d top-level areas, %d error row(s) under %s"
          % (nfiles, nbytes, len(totals), errors, root))
    print("wrote %s" % inv_path)
    print("wrote %s" % area_path)
    if errors:
        print("%d ERR row(s): reorg_exec.py refuses this inventory; fix access and run again" % errors,
              file=sys.stderr)
        return 1
    return 0


# --------------------------------------------------------------------------- refscan
def build_finder(a, ci):
    """-> find(text) returning [(pattern_label, match)].  Path-map patterns are labelled with the
    old_path they stand for (forward slashes); raw --pattern regexes with the regex itself."""
    finders = []
    if a.pathmap:
        ops = rx.load_ops(a.pathmap)
        ctx = types.SimpleNamespace(args=types.SimpleNamespace(old_pattern=[]), ops=ops, ci=ci)
        matcher = rx.build_matcher(ctx)
        if matcher is None:
            raise Fail("path map has no move or rename ops: no old paths to look for")
        labels = {}
        for op in ops:
            if rx.is_move(op):
                labels.setdefault(rx.norm_key("/".join(rx._segs(op.old)), ci), rx.posix(op.old))

        def from_map(text):
            return [(labels.get(rx.norm_key(m.group(0), ci), m.group(0)), m) for m in matcher.finditer(text)]
        finders.append(from_map)
    for p in a.pattern:
        try:
            r = re.compile(p)
        except re.error as ex:
            raise Fail("--pattern %r: invalid regular expression: %s" % (p, ex))

        def from_regex(text, r=r, p=p):
            return [(p, m) for m in r.finditer(text) if m.end() > m.start()]
        finders.append(from_regex)

    def find(text):
        out = []
        for f in finders:
            out += f(text)
        return out
    return find


def snippet_of(text, m):
    s = text.strip()
    if len(s) <= SNIPPET:
        return clean(s)
    return clean(text[max(0, m.start() - CONTEXT): m.end() + CONTEXT])


def cmd_refscan(a):
    root = os.path.abspath(a.root)
    if not os.path.isdir(root):
        raise Fail("root is not a directory: %s" % root)
    ci = resolve_ci(a, root)
    find = build_finder(a, ci)
    hist = rx.Globs(a.historical, ci)
    skip = set(s.lower() if ci else s for s in list(rx.DEFAULT_SKIP_DIRS) + list(a.skip_dir))
    rows, notes = [], []
    nfiles = nbin = 0

    def on_dir_error(ex):
        rows.append((clean(rx.posix(os.path.relpath(ex.filename, root))) if getattr(ex, "filename", None) else "?",
                     "0", "live", "scan-error", clean(repr(ex))[:SNIPPET]))

    for rel, full in walk_files(root, ci, ignore_globs(a, ci), skip, (), [a.out], on_dir_error):
        name = clean(rx.posix(rel))
        cls = "historical" if hist.match(rel) else "live"
        try:
            size = os.path.getsize(full)
            kind = rx.classify_file(full, size)
            if kind is None:
                nbin += 1
                continue
            nfiles += 1
            if kind == "large":
                rows.append((name, "0", cls, "not-scanned", "%d bytes is above the scan limit" % size))
                notes.append(name)
            elif kind == "text":
                with open(full, "rb") as f:
                    text = f.read().decode("utf-8", errors="replace")
                for ln, line in enumerate(text.splitlines(), 1):
                    seen = set()
                    for label, m in find(line):
                        if label not in seen:
                            seen.add(label)
                            rows.append((name, str(ln), cls, clean(label), snippet_of(line, m)))
            else:
                with zipfile.ZipFile(full) as z:
                    for info in z.infolist():
                        if not info.filename.endswith((".xml", ".rels")):
                            continue
                        data = z.read(info).decode("utf-8", errors="replace")
                        for label, m in find(data):
                            rows.append((name, clean(info.filename), cls, clean(label),
                                         clean(data[max(0, m.start() - CONTEXT): m.end() + CONTEXT])))
        except (zipfile.BadZipFile, OSError, RuntimeError, ValueError) as ex:
            rows.append((name, "0", cls, "scan-error", clean(repr(ex))[:SNIPPET]))
    nerr = sum(1 for r in rows if r[3] == "scan-error")
    hits = [r for r in rows if r[3] not in ("scan-error", "not-scanned")]
    write_tsv(a.out, ("file", "line", "class", "pattern", "snippet"), rows)
    live = sum(1 for r in hits if r[2] == "live")
    print("refscan: %d files scanned, %d binary skipped; %d hits in %d files (%d live, %d historical)"
          % (nfiles, nbin, len(hits), len(set(r[0] for r in hits)), live, len(hits) - live))
    for n in notes:
        print("note: not scanned (too large): %s" % n)
    print("wrote %s" % os.path.abspath(a.out))
    if nerr:
        print("%d file(s) could not be scanned (scan-error rows): the scan is incomplete" % nerr, file=sys.stderr)
        return 1
    return 0


# --------------------------------------------------------------------------- main
def build_parser():
    ap = argparse.ArgumentParser(prog="reorg_scan.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", required=True, help="folder to scan")
    common.add_argument("--ignore", action="append", default=[], metavar="GLOB",
                        help="repeatable; files and directories left out")
    common.add_argument("--no-default-ignore", action="store_true",
                        help="do not add desktop.ini, Thumbs.db, .DS_Store")
    common.add_argument("--skip-dir", action="append", default=[], metavar="NAME",
                        help="repeatable; directory names that are not entered")
    common.add_argument("--case-insensitive", choices=("auto", "yes", "no"), default="auto")
    sub = ap.add_subparsers(dest="cmd", metavar="SUBCOMMAND")
    sub.required = True
    inv = sub.add_parser("inventory", parents=[common], help="write <label>-inventory.tsv and <label>-area-totals.tsv")
    inv.add_argument("--out-dir", required=True, help="folder for the two output files (created if missing)")
    inv.add_argument("--label", required=True, help="output file prefix, e.g. before or after")
    rs = sub.add_parser("refscan", parents=[common], help="find references to old paths; write one TSV")
    rs.add_argument("--pathmap", help="path map CSV; one pattern per old_path (as reorg_exec.py verify)")
    rs.add_argument("--pattern", action="append", default=[], metavar="REGEX",
                    help="repeatable; raw regular expression to look for")
    rs.add_argument("--out", required=True, help="output TSV")
    rs.add_argument("--historical", action="append", default=[], metavar="GLOB",
                    help="repeatable; files whose hits are classed historical")
    return ap


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = build_parser()
    a = ap.parse_args(argv)
    if a.cmd == "refscan" and not (a.pathmap or a.pattern):
        ap.error("refscan needs --pathmap or --pattern")
    try:
        return cmd_inventory(a) if a.cmd == "inventory" else cmd_refscan(a)
    except Fail as ex:
        print("FAIL: %s" % ex, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
