#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reorg_exec.py - execute a pre-approved folder reorganization safely and resumably.

Requires Python 3.9 or newer, standard library only.  Never copies a data file: folders
and files are moved with os.rename (same volume).  The `run` mode never deletes anything.

    python reorg_exec.py MODE --root ROOT --meta META --pathmap MAP.csv
                         [--edits EDITS.json] [--inventory INV.tsv] [--tag TAG] [options]

Modes
  plan-check  simulate the path map against the inventory only (no tree needed): collisions,
              missing sources, missing parents, before/after totals per top-level folder.
  preflight   read-only: simulate every op against the real tree (sources exist, destinations
              absent, parents exist), lock files, path length, inventory drift, and a dry-run
              of every edit on the pre-move originals.  Writes nothing.
  snapshot    write <tag>-tree-before.txt and <tag>-rollback.ps1 under --meta.
  run         execute the path map in op order; resumable; stops at the first failure;
              refuses to start without a snapshot (override: --no-guard).
  edits       plan every edit first (nothing is written when anything is wrong), verify a
              backup per file, then overwrite the file IN PLACE; resumable.
  verify      (a) inventory vs final tree incl. sizes and an xlsx deep check, (b) old-path
              scan of text files and Office XML against the whitelist; writes <tag>-verify.txt.
  tree-after  write <tag>-tree-after.txt.
  rollback    restore edited files from their backups, then reverse the moves in reverse op
              order; --prune-empty also removes now-empty directories created by mkdir ops.

Options
  --tag TAG                 prefix of every file written under --meta (default: reorg)
  --case-insensitive MODE   auto | yes | no (default auto: probes --root, falls back to the OS)
  --strict-inventory        preflight: inventory drift is a problem, not a warning
  --force-snapshot          snapshot: keep the old tree-before under a timestamped name, write a new one
  --no-guard                run: do not require the snapshot files
  --stop-after OP           run: execute only ops whose id is <= OP (partial run; resume later)
  --prune-empty             rollback: rmdir now-empty directories created by mkdir ops
  --whitelist-extra JSON    verify: extra whitelist entries (same shape as in the edits file)
  --ignore GLOB             repeatable; names/paths ignored in verify, tree files and inventory
                            comparisons (always added: desktop.ini, Thumbs.db, .DS_Store)
  --no-default-ignore       do not add those three default ignore globs
  --allow-new GLOB          repeatable; verify: files that may appear without being in the inventory
  --old-pattern REGEX       repeatable; verify: old-path regex (default: built from the old_path
                            values of the path map, separator and word-boundary aware)
  --skip-dir NAME           repeatable; directory names the verify content scan does not enter
                            (always skipped: .git __pycache__ node_modules .idea .mvn and --meta)

Exit codes: 0 ok, 1 problem or failure, 2 usage error.
Formats and a worked example: skills/folder-reorganization/references/data-formats.md
"""
from __future__ import annotations

import argparse
import collections
import copy
import csv
import datetime
import fnmatch
import hashlib
import json
import os
import platform
import re
import shutil
import sys
import traceback
import zipfile

DEFAULT_TAG = "reorg"
DEFAULT_IGNORE = ("desktop.ini", "Thumbs.db", ".DS_Store")
DEFAULT_SKIP_DIRS = (".git", "__pycache__", "node_modules", ".idea", ".mvn")
LOCK_PATTERNS = ("~$*", ".~lock.*#")
TEXT_EXT = {
    ".md", ".txt", ".py", ".json", ".yaml", ".yml", ".csv", ".tsv", ".ps1", ".sh", ".bash",
    ".html", ".htm", ".ini", ".cfg", ".conf", ".toml", ".java", ".kt", ".js", ".ts", ".css",
    ".xml", ".bat", ".cmd", ".eml", ".sql", ".rst", ".tex", ".log", ".properties", ".gradle",
}
BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".pdf", ".zip", ".gz", ".tgz",
    ".7z", ".rar", ".jar", ".war", ".class", ".exe", ".dll", ".so", ".dylib", ".mp3", ".mp4",
    ".mov", ".avi", ".mkv", ".wav", ".flac", ".woff", ".woff2", ".ttf", ".otf", ".eot", ".pyc",
    ".o", ".bin", ".sqlite", ".db",
}
ZIP_EXT = {".xlsx", ".docx", ".pptx", ".odt", ".ods", ".odp"}
MAX_TEXT_BYTES = 20000000
MAX_ZIP_BYTES = 60000000
MODE_NEEDS = {
    "plan-check": ("pathmap", "inventory"),
    "preflight": ("root", "meta", "pathmap", "inventory"),
    "snapshot": ("root", "meta", "pathmap"),
    "run": ("root", "meta", "pathmap"),
    "edits": ("root", "meta", "edits"),
    "verify": ("root", "meta", "pathmap", "inventory"),
    "tree-after": ("root", "meta"),
    "rollback": ("root", "meta", "pathmap"),
}

Op = collections.namedtuple("Op", "id wave action old new")


class Fail(Exception):
    """A deliberate, already-explained failure."""


class Ctx(object):
    pass


# --------------------------------------------------------------------------- helpers
def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fmt_mtime(ts):
    return datetime.datetime.fromtimestamp(int(ts), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def nsep(p):
    """Path-map / JSON paths may use either slash; convert to the OS separator."""
    return p.replace("\\", os.sep).replace("/", os.sep)


def posix(p):
    """OS path -> forward-slash form, used in every file written under --meta."""
    return p.replace(os.sep, "/")


def clean_rel(raw, what):
    """Normalise a path that must be relative to --root.  '' stays ''."""
    s = (raw or "").strip()
    if not s:
        return ""
    s = nsep(s)
    if os.path.isabs(s) or s.startswith(os.sep) or (len(s) > 1 and s[1] == ":"):
        raise Fail("%s: path must be relative to --root: %r" % (what, raw))
    n = os.path.normpath(s)
    if n == ".":
        raise Fail("%s: path refers to the root itself: %r" % (what, raw))
    if n == ".." or n.startswith(".." + os.sep):
        raise Fail("%s: path escapes --root: %r" % (what, raw))
    return n


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def same_bytes(a, b):
    if os.path.getsize(a) != os.path.getsize(b):
        return False
    return sha256_file(a) == sha256_file(b)


def raise_err(e):
    raise e


def is_lock_name(name):
    return any(fnmatch.fnmatchcase(name, p) for p in LOCK_PATTERNS)


def detect_ci(root):
    """True when the filesystem under root is case-insensitive.  Probes without writing."""
    base = os.path.basename(root.rstrip("\\/"))
    if base and base.swapcase() != base:
        alt = os.path.join(os.path.dirname(root.rstrip("\\/")), base.swapcase())
        try:
            return os.path.exists(alt) and os.path.samefile(alt, root)
        except OSError:
            pass
    return os.name == "nt" or sys.platform == "darwin"


class Globs(object):
    """A set of glob patterns matched against a relative path.

    A pattern without '/' is tested against every path component (so '.git' ignores the whole
    directory and '*.log' every log file).  A pattern with '/' is tested against every leading
    and every trailing part of the path ('archive/*.log' matches 'archive/run.log')."""

    def __init__(self, patterns, ci):
        self.ci = ci
        self.names, self.paths = [], []
        for p in patterns:
            p = p.strip().replace("\\", "/").strip("/")
            if not p:
                continue
            rx = re.compile(fnmatch.translate(p.lower() if ci else p))
            (self.paths if "/" in p else self.names).append(rx)

    def __bool__(self):
        return bool(self.names or self.paths)

    def match(self, rel):
        if not (self.names or self.paths):
            return False
        r = posix(rel).strip("/")
        if self.ci:
            r = r.lower()
        parts = r.split("/")
        for rx in self.names:
            for part in parts:
                if rx.match(part):
                    return True
        if self.paths:
            cands = ["/".join(parts[:i]) for i in range(1, len(parts) + 1)]
            cands += ["/".join(parts[i:]) for i in range(1, len(parts))]
            for rx in self.paths:
                for cnd in cands:
                    if rx.match(cnd):
                        return True
        return False


# --------------------------------------------------------------------------- loaders
def load_ops(path):
    ops, seen = [], set()
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        missing = {"op", "action", "old_path", "new_path"} - set(rd.fieldnames or [])
        if missing:
            raise Fail("path map header must contain op,wave,action,old_path,new_path (missing: %s)"
                       % ", ".join(sorted(missing)))
        for r in rd:
            oid = (r.get("op") or "").strip()
            if not oid:
                continue
            if not re.fullmatch(r"\d+", oid):
                raise Fail("op id %r is not a number" % oid)
            if oid in seen:
                raise Fail("duplicate op id %s in path map" % oid)
            seen.add(oid)
            action = (r.get("action") or "").strip().lower()
            old = clean_rel(r.get("old_path"), "op %s old_path" % oid)
            new = clean_rel(r.get("new_path"), "op %s new_path" % oid)
            if action not in ("move", "rename", "mkdir"):
                raise Fail("op %s: unknown action %r (move, rename or mkdir)" % (oid, action))
            if action == "mkdir" and not (new and not old):
                raise Fail("op %s: mkdir needs new_path only" % oid)
            if action != "mkdir":
                if not (old and new):
                    raise Fail("op %s: %s needs old_path and new_path" % (oid, action))
                if old == new:
                    raise Fail("op %s: old_path and new_path are identical" % oid)
                if action == "rename" and os.path.dirname(old) != os.path.dirname(new):
                    raise Fail("op %s: rename must keep the parent directory (use move)" % oid)
            ops.append(Op(oid, (r.get("wave") or "").strip(), action, old, new))
    ids = [int(o.id) for o in ops]
    if ids != sorted(ids):
        raise Fail("path map ops are not in ascending op order")
    return ops


def _whitelist_item(w, what):
    if not isinstance(w, dict):
        raise Fail("%s: whitelist item must be an object" % what)
    w = dict(w)
    if ("file" in w) == ("file_prefix" in w):
        raise Fail("%s: whitelist item needs exactly one of file / file_prefix: %r" % (what, w))
    if not str(w.get("why") or "").strip():
        raise Fail("%s: whitelist item needs a 'why': %r" % (what, w))
    for k in ("file", "file_prefix"):
        if k in w:
            w[k] = nsep(str(w[k]).strip())
    return w


def load_edits(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        doc = json.load(f)
    if not isinstance(doc, dict):
        raise Fail("edits JSON must be an object with the keys 'edits' and 'whitelist'")
    odd = [k for k in doc if k not in ("edits", "whitelist") and not k.startswith("_")]
    if odd:
        raise Fail("edits JSON: unknown top-level key(s): %s" % ", ".join(odd))
    edits, wl = [], []
    for i, e in enumerate(doc.get("edits", []), 1):
        if not isinstance(e, dict):
            raise Fail("edit #%d must be an object" % i)
        e = dict(e)
        if not str(e.get("file") or "").strip():
            raise Fail("edit #%d has no 'file'" % i)
        e["file"] = clean_rel(e["file"], "edit #%d file" % i)       # a path field: separators converted
        if e.get("kind") not in ("text", "xlsx-xml"):
            raise Fail("edit %s: kind must be 'text' or 'xlsx-xml', got %r" % (posix(e["file"]), e.get("kind")))
        reps = e.get("replacements")
        if not isinstance(reps, list) or not reps:
            raise Fail("edit %s: 'replacements' must be a non-empty list" % posix(e["file"]))
        norm = []
        for j, r in enumerate(reps, 1):
            if not isinstance(r, dict) or not isinstance(r.get("old"), str) or not isinstance(r.get("new"), str) \
                    or not r["old"]:
                raise Fail("edit %s replacement #%d needs string 'old' (non-empty) and 'new'" % (posix(e["file"]), j))
            try:
                cnt = int(r.get("count", 1))
            except (TypeError, ValueError):
                raise Fail("edit %s replacement #%d: count is not an integer" % (posix(e["file"]), j))
            # old / new are literal text and are never separator-converted
            norm.append({"old": r["old"], "new": r["new"], "count": cnt})
        e["replacements"] = norm
        edits.append(e)
    seen = {}
    for e in edits:
        flat = bak_name(e["file"]).lower()
        if flat in seen:
            raise Fail("edits: %s and %s share a backup name (or are the same file)"
                       % (posix(seen[flat]), posix(e["file"])))
        seen[flat] = e["file"]
    for i, w in enumerate(doc.get("whitelist", []), 1):
        wl.append(_whitelist_item(w, "whitelist #%d" % i))
    return edits, wl


def load_inventory(path):
    rows = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for i, line in enumerate(f):
            line = line.rstrip("\r\n")
            if not line:
                continue
            col = line.split("\t")
            if i == 0:
                if col[0] != "rel_path":
                    raise Fail("inventory must start with the header rel_path<TAB>bytes<TAB>mtime_utc<TAB>kind")
                continue
            if len(col) < 2:
                raise Fail("inventory line %d: expected at least rel_path<TAB>bytes" % (i + 1))
            try:
                size = int(col[1])
            except ValueError:
                raise Fail("inventory line %d: bytes is not an integer: %r" % (i + 1, col[1]))
            kind = col[3] if len(col) > 3 and col[3] else "file"
            if kind.lower().startswith("err"):                 # reorg_scan.py writes "ERR <reason>"
                raise Fail("inventory line %d is an error row (%s): fix the inventory first" % (i + 1, kind))
            if kind == "dir":
                continue
            rows.append((clean_rel(col[0], "inventory line %d" % (i + 1)), size,
                         col[2] if len(col) > 2 else "", kind))
    return rows


def build_ctx(a):
    c = Ctx()
    c.mode, c.args, c.tag = a.mode, a, a.tag
    c.root = os.path.abspath(a.root) if a.root else None
    c.meta = os.path.abspath(a.meta) if a.meta else None
    if not re.fullmatch(r"[A-Za-z0-9._-]+", c.tag):
        raise Fail("--tag may contain only letters, digits, '.', '_' and '-'")
    if a.case_insensitive == "auto":
        c.ci = detect_ci(c.root) if c.root and os.path.isdir(c.root) else (os.name == "nt")
    else:
        c.ci = a.case_insensitive == "yes"
    ignore = ([] if a.no_default_ignore else list(DEFAULT_IGNORE)) + list(a.ignore)
    c.ignore = Globs(ignore, c.ci)
    c.allow_new = Globs(a.allow_new, c.ci)
    skip = list(DEFAULT_SKIP_DIRS) + list(a.skip_dir)
    c.skip_dirs = set(s.lower() if c.ci else s for s in skip)
    c.ops = load_ops(a.pathmap) if a.pathmap else []
    c.edits, c.whitelist = load_edits(a.edits) if a.edits else ([], [])
    if a.whitelist_extra:
        with open(a.whitelist_extra, "r", encoding="utf-8-sig") as f:
            extra = json.load(f)
        extra = extra.get("whitelist", []) if isinstance(extra, dict) else extra
        for i, w in enumerate(extra, 1):
            c.whitelist.append(_whitelist_item(w, "whitelist-extra #%d" % i))
    c.inventory = load_inventory(a.inventory) if a.inventory else []
    c.matcher = build_matcher(c)
    if c.meta:
        c.logpath = os.path.join(c.meta, c.tag + "-log.md")
        c.bakdir = os.path.join(c.meta, c.tag + "-edit-backups")
        c.tmpdir = os.path.join(c.meta, c.tag + "-tmp")
    c.header_done = False
    return c


def K(c, p):
    """comparison key for a relative path (case-folded on case-insensitive filesystems)"""
    return p.lower() if c.ci else p


def A(c, rel):
    return os.path.join(c.root, rel) if rel else c.root


def is_move(op):
    return op.action != "mkdir"


def is_case_only(c, op):
    """A rename whose old and new path differ only in letter case on a case-insensitive filesystem."""
    return (c.ci and is_move(op) and op.old != op.new and op.old.lower() == op.new.lower()
            and os.path.basename(op.old) != os.path.basename(op.new))


def log(c, line):
    """Append to the ledger.  The per-run header is written lazily, once, before the first line."""
    if not c.meta:
        return
    os.makedirs(c.meta, exist_ok=True)
    first = not os.path.exists(c.logpath)
    with open(c.logpath, "a", encoding="utf-8", newline="\n") as f:
        if first:
            f.write("# %s execution log\n\n" % c.tag)
        if not c.header_done:
            f.write("\n## %s  mode=%s  root=%s  meta=%s  host=%s  python=%s\n" % (
                now_utc(), c.mode, c.root, c.meta, platform.node(), platform.python_version()))
            c.header_done = True
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())


def log_op(c, op, result):
    arrow = "%s -> %s" % (posix(op.old), posix(op.new)) if is_move(op) else "-> %s" % posix(op.new)
    log(c, "- %s | op %s | %s | %s | %s" % (now_utc(), op.id, op.action, arrow, result))


def walk_tree(c, ignore=True):
    """-> (files [(rel, size, mtime)], dirs [rel]); excludes the meta dir; errors raise.
    Files matching the ignore globs are left out when ignore=True (directories are always listed)."""
    meta_real = os.path.normcase(os.path.realpath(c.meta)) if c.meta else None
    files, dirs = [], []
    for dp, dns, fns in os.walk(c.root, onerror=raise_err):
        dns[:] = sorted(d for d in dns
                        if meta_real is None
                        or os.path.normcase(os.path.realpath(os.path.join(dp, d))) != meta_real)
        for d in dns:
            dirs.append(os.path.relpath(os.path.join(dp, d), c.root))
        for fn in sorted(fns):
            full = os.path.join(dp, fn)
            rel = os.path.relpath(full, c.root)
            if ignore and c.ignore.match(rel):
                continue
            st = os.lstat(full)
            files.append((rel, st.st_size, st.st_mtime))
    return files, dirs


def map_path(c, rel):
    """final (post-move) relative path of an initial relative path, by applying the move ops in order"""
    p = rel
    for op in c.ops:
        if not is_move(op):
            continue
        ok, pk = K(c, op.old), K(c, p)
        if pk == ok or pk.startswith(ok + os.sep):
            p = op.new + p[len(op.old):]
    return p


def write_tree(c, name):
    files, _ = walk_tree(c)
    files.sort(key=lambda x: K(c, x[0]))
    out = os.path.join(c.meta, name)
    os.makedirs(c.meta, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("rel_path\tbytes\tmtime_utc\n")
        for rel, size, mt in files:
            f.write("%s\t%d\t%s\n" % (posix(rel), size, fmt_mtime(mt)))
    return out, len(files), sum(x[1] for x in files)


# --------------------------------------------------------------------------- old-path matcher
def _segs(rel):
    return [s for s in re.split(r"[\\/]+", rel) if s]


def _alt_for(segs):
    """Regex for one old path.  Separators match any run of / or \\.  A multi-segment path needs a
    non-name character before it and no name continuation after it.  A single segment (a bare
    folder name) only counts in a path context: followed by a separator, or preceded by one."""
    body = r"[\\/]+".join(re.escape(s) for s in segs)
    if len(segs) > 1:
        return r"(?<![\w.\-])" + body + r"(?![\w\-]|\.\w)"
    return r"(?:(?<![\w.\-])%s(?=[\\/])|(?<=[\\/])%s(?![\w\-]|\.\w))" % (body, body)


def norm_key(text, ci):
    s = re.sub(r"[\\/]+", "/", text)
    return s.lower() if ci else s


class OldMatcher(object):
    """Finds references to old paths.  A match that lies inside the NEW path of the op it belongs
    to (e.g. old 'foo' -> new 'x/foo') is not a hit."""

    def __init__(self, rxs, quick, shadows, ci):
        self.rxs, self.quick, self.shadows, self.ci = rxs, quick, shadows or {}, ci

    def finditer(self, text):
        if self.quick is not None and not self.quick.search(text):
            return []
        out = []
        for rx in self.rxs:
            for m in rx.finditer(text):
                if not self._shadowed(text, m):
                    out.append(m)
        return out

    def _shadowed(self, text, m):
        if not self.shadows:
            return False
        for rx in self.shadows.get(norm_key(m.group(0), self.ci), ()):
            lo, hi = max(0, m.start() - 300), min(len(text), m.end() + 300)
            for s in rx.finditer(text, lo, hi):
                if s.start() < m.end() and s.end() > m.start():
                    return True
        return False


def build_matcher(c):
    pats = list(c.args.old_pattern)
    if pats:
        try:
            return OldMatcher([re.compile(p) for p in pats], None, None, c.ci)
        except re.error as ex:
            raise Fail("--old-pattern: invalid regular expression: %s" % ex)
    moves = [o for o in c.ops if is_move(o)]
    if not moves:
        return None
    flags = re.IGNORECASE if c.ci else 0
    alts, seen, shadows, firsts = [], set(), {}, set()
    for op in sorted(moves, key=lambda o: (-len(o.old), o.id)):
        segs = _segs(op.old)
        key = norm_key("/".join(segs), c.ci)
        shadows.setdefault(key, []).append(
            re.compile(r"[\\/]+".join(re.escape(s) for s in _segs(op.new)), flags))
        if key in seen:
            continue
        seen.add(key)
        alts.append(_alt_for(segs))
        firsts.add(re.escape(segs[0]))
    return OldMatcher([re.compile("|".join(alts), flags)], re.compile("|".join(sorted(firsts)), flags),
                      shadows, c.ci)


# --------------------------------------------------------------------------- edit planning
def apply_replacements(text, reps, label):
    """Sequential (each count is evaluated on the text left by the previous replacement).
    -> (new_text, [applied|already|mismatch], [error strings])"""
    results, errors = [], []
    for i, r in enumerate(reps, 1):
        old, new, cnt = r["old"], r["new"], int(r["count"])
        n_old = text.count(old)
        if n_old == cnt:
            text = text.replace(old, new)
            results.append("applied")
        elif n_old == 0 and text.count(new) >= cnt:
            results.append("already")
        else:
            results.append("mismatch")
            errors.append("%s replacement #%d: expected %d x old, found %d x old (new present %d x): %r"
                          % (label, i, cnt, n_old, text.count(new), old[:90]))
    return text, results, errors


def split_member(old):
    member, text = old.split("|", 1)
    return member, text


def lint_edit(e):
    errs = []
    name = posix(e["file"])
    for i, r in enumerate(e["replacements"], 1):
        if int(r["count"]) < 1:
            errs.append("%s #%d: count < 1" % (name, i))
        old = r["old"]
        if e["kind"] == "xlsx-xml":
            if "|" not in old:
                errs.append("%s #%d: xlsx-xml old must be '<zip member>|<text>'" % (name, i))
                continue
            old = split_member(old)[1]
            if not old:
                errs.append("%s #%d: xlsx-xml old text after '|' is empty" % (name, i))
        if old in r["new"]:
            errs.append("%s #%d: old text is contained in new text (not idempotent)" % (name, i))
    return errs


def plan_edit(e, path, bak=None):
    """Pure (read-only) plan.  -> dict(state=pending|done|error, errors, warnings, results, payload).
    With bak given, a pending edit whose file differs from an existing backup is an error."""
    name = posix(e["file"])
    plan = {"edit": e, "path": path, "errors": lint_edit(e), "warnings": [], "results": [], "payload": None}
    if plan["errors"]:
        plan["state"] = "error"
        return plan
    if not os.path.isfile(path):
        plan["errors"].append("%s: file not found at %s" % (name, path))
        plan["state"] = "error"
        return plan
    try:
        if e["kind"] == "text":
            with open(path, "r", encoding="utf-8", newline="") as f:
                text = f.read()
            new_text, results, errors = apply_replacements(text, e["replacements"], name)
            if "\r\n" in text:
                for r in e["replacements"]:
                    if re.search(r"(?<!\r)\n", r["new"]):
                        plan["warnings"].append("%s: file uses CRLF but a replacement inserts a bare LF" % name)
                        break
            plan["payload"] = new_text
        else:
            by_member = collections.OrderedDict()
            for r in e["replacements"]:
                member, old = split_member(r["old"])
                by_member.setdefault(member, []).append({"old": old, "new": r["new"], "count": r["count"]})
            results, errors, payload = [], [], {}
            with zipfile.ZipFile(path) as z:
                names = set(z.namelist())
                for member, reps in by_member.items():
                    if member not in names:
                        errors.append("%s: zip member %s not found" % (name, member))
                        results += ["mismatch"] * len(reps)
                        continue
                    text = z.read(member).decode("utf-8")
                    new_text, res, errs = apply_replacements(text, reps, "%s [%s]" % (name, member))
                    results += res
                    errors += errs
                    if "applied" in res:
                        payload[member] = new_text.encode("utf-8")
            plan["payload"] = payload
    except (UnicodeDecodeError, zipfile.BadZipFile, OSError) as ex:
        plan["errors"].append("%s: cannot read/parse: %r" % (name, ex))
        plan["state"] = "error"
        return plan
    plan["results"] = results
    plan["errors"] += errors
    if plan["errors"]:
        plan["state"] = "error"
    elif all(x == "already" for x in results):
        plan["state"] = "done"
    else:
        plan["state"] = "pending"
        if bak and os.path.exists(bak) and not same_bytes(path, bak):
            plan["errors"].append("%s: file differs from its existing backup while edits are still pending "
                                  "(restore it with `rollback` or remove the stale backup)" % name)
            plan["state"] = "error"
    return plan


def bak_name(rel):
    return rel.replace(os.sep, "__")


# --------------------------------------------------------------------------- simulation
def simulate(c, vfs, problems):
    """Apply every op to a virtual tree ({key: is_dir}); report impossible ops.  -> (moves, mkdirs)"""
    nmoves = nmk = 0
    for op in c.ops:
        if not is_move(op):
            nmk += 1
            k = K(c, op.new)
            par = K(c, os.path.dirname(op.new))
            if k in vfs:
                problems.append("op %s mkdir: target already exists: %s" % (op.id, posix(op.new)))
            elif par and not vfs.get(par, False):
                problems.append("op %s mkdir: parent dir missing: %s" % (op.id, posix(os.path.dirname(op.new))))
            else:
                vfs[k] = True
            continue
        nmoves += 1
        ok, nk = K(c, op.old), K(c, op.new)
        par = K(c, os.path.dirname(op.new))
        bad = False
        if ok not in vfs:
            problems.append("op %s move: source missing: %s" % (op.id, posix(op.old)))
            bad = True
        if nk in vfs and ok != nk:                      # ok == nk only for a case-only rename (ci)
            problems.append("op %s move: destination already exists: %s" % (op.id, posix(op.new)))
            bad = True
        if par and not vfs.get(par, False):
            problems.append("op %s move: destination parent dir missing: %s"
                            % (op.id, posix(os.path.dirname(op.new))))
            bad = True
        if nk.startswith(ok + os.sep):
            problems.append("op %s move: destination is inside source" % op.id)
            bad = True
        if bad or ok == nk:
            continue
        if vfs[ok]:
            moved = [k2 for k2 in vfs if k2 == ok or k2.startswith(ok + os.sep)]
            items = [(k2, vfs.pop(k2)) for k2 in moved]
            for k2, v in items:
                vfs[nk + k2[len(ok):]] = v
        else:
            del vfs[ok]
            vfs[nk] = False
    return nmoves, nmk


def vfs_from_files(c, rels, dirs=()):
    vfs = {}
    for r in rels:
        parts = r.split(os.sep)
        for i in range(1, len(parts)):
            vfs[K(c, os.sep.join(parts[:i]))] = True
        vfs[K(c, r)] = False
    for d in dirs:
        vfs[K(c, d)] = True
    return vfs


def area_of(rel):
    return rel.split(os.sep)[0] if os.sep in rel else "(root files)"


# --------------------------------------------------------------------------- mode: plan-check
def mode_plan_check(c):
    problems, warns = [], []
    inv = [(r, b) for r, b, _, _ in c.inventory if not c.ignore.match(r)]
    keys = collections.Counter(K(c, r) for r, _ in inv)
    for k, n in keys.items():
        if n > 1:
            problems.append("inventory lists %s %d times" % (posix(k), n))
    vfs = vfs_from_files(c, [r for r, _ in inv])
    sim = []
    nmoves, nmk = simulate(c, vfs, sim)
    problems += sim
    finals = collections.defaultdict(list)
    for r, _ in inv:
        finals[K(c, map_path(c, r))].append(r)
    for fk, srcs in sorted(finals.items()):
        if len(srcs) > 1:
            problems.append("COLLISION: %d files end up at %s (e.g. %s)" % (len(srcs), posix(fk), posix(srcs[0])))
    final_files = set(k for k, v in vfs.items() if not v)
    if not sim and final_files != set(finals):
        problems.append("internal mismatch between the sequential simulation and the path mapping")
    for e in c.edits:
        if K(c, e["file"]) not in finals:
            problems.append("edit target is not produced by the moves: %s" % posix(e["file"]))
    print("plan-check: %d ops (%d moves, %d mkdirs) against an inventory of %d files, %d bytes"
          % (len(c.ops), nmoves, nmk, len(inv), sum(b for _, b in inv)))
    before = collections.defaultdict(lambda: [0, 0])
    after = collections.defaultdict(lambda: [0, 0])
    for r, b in inv:
        x = before[area_of(r)]
        x[0] += 1
        x[1] += b
        y = after[area_of(map_path(c, r))]
        y[0] += 1
        y[1] += b
    print("%-34s %8s %12s %8s %12s" % ("top-level area", "files", "bytes", "files", "bytes"))
    print("%-34s %21s %21s" % ("", "before", "after"))
    for area in sorted(set(before) | set(after)):
        b, a = before.get(area, [0, 0]), after.get(area, [0, 0])
        print("%-34s %8d %12d %8d %12d" % (area[:34], b[0], b[1], a[0], a[1]))
    print("%-34s %8d %12d %8d %12d" % ("TOTAL", len(inv), sum(b for _, b in inv), len(inv), sum(b for _, b in inv)))
    print("note: empty directories are invisible to an inventory; use `preflight` against the real tree for them")
    return problems, warns


# --------------------------------------------------------------------------- mode: preflight
def mode_preflight(c):
    problems, warns = [], []
    raw_files, dirs = walk_tree(c, ignore=False)
    files = [f for f in raw_files if not c.ignore.match(f[0])]
    print("tree: %d files (%d ignored), %d dirs under %s" % (len(files), len(raw_files) - len(files), len(dirs), c.root))

    # 1. lock files (looked for before any ignore filtering)
    for r in [r for r, _, _ in raw_files] + list(dirs):
        if is_lock_name(os.path.basename(r)):
            problems.append("lock file present (close the application that owns it): %s" % posix(r))

    # 2. simulate every op against the real tree
    vfs = vfs_from_files(c, [r for r, _, _ in files], dirs)
    nmoves, nmk = simulate(c, vfs, problems)
    print("simulated %d move ops + %d mkdir ops" % (nmoves, nmk))

    # 3. path length after the moves
    longest = max((len(c.root) + 1 + len(k2) for k2 in vfs), default=0)
    print("longest final absolute path: %d chars" % longest)
    if longest >= 260 and os.name == "nt":
        problems.append("a final path is %d chars (>= 260): may break without long path support" % longest)
    elif longest >= 240:
        warns.append("longest final path is %d chars" % longest)

    # 4. inventory drift (warning; --strict-inventory makes it fatal)
    inv = {K(c, r): (r, b) for r, b, _, _ in c.inventory if not c.ignore.match(r)}
    disk = {K(c, r): (r, s) for r, s, _ in files}
    miss = sorted(v[0] for k2, v in inv.items() if k2 not in disk)
    extra = sorted(v[0] for k2, v in disk.items() if k2 not in inv)
    diff = sorted(v[0] for k2, v in inv.items() if k2 in disk and disk[k2][1] != v[1])
    drift = []
    if miss:
        drift.append("%d inventory files missing on disk, e.g. %s" % (len(miss), posix(miss[0])))
    if extra:
        drift.append("%d files on disk not in inventory, e.g. %s" % (len(extra), posix(extra[0])))
    if diff:
        drift.append("%d files differ in size from inventory, e.g. %s" % (len(diff), posix(diff[0])))
    (problems if c.args.strict_inventory else warns).extend("inventory drift: " + d for d in drift)
    print("inventory: %d rows, disk %d files, missing %d, extra %d, size-diff %d"
          % (len(inv), len(disk), len(miss), len(extra), len(diff)))

    # 5. edit dry-run on the pre-move originals (counts); edit targets must exist after the moves
    final_to_initial = {K(c, map_path(c, r)): r for r, _, _ in files}
    for e in c.edits:
        src = final_to_initial.get(K(c, e["file"]))
        if src is None:
            problems.append("edit target is not produced by the moves: %s" % posix(e["file"]))
            continue
        p = plan_edit(e, A(c, src))
        problems += ["edit dry-run: " + x for x in p["errors"]]
        warns += ["edit dry-run: " + x for x in p["warnings"]]
        if p["state"] == "done":
            warns.append("edit dry-run: %s already looks edited" % posix(e["file"]))
        elif p["state"] == "pending":
            print("edit dry-run ok: %-50s %2d replacements (from %s)" % (posix(e["file"]), len(p["results"]), posix(src)))
    return problems, warns


# --------------------------------------------------------------------------- mode: snapshot
def psq(s):
    return "'" + s.replace("'", "''") + "'"


def gen_ps1(c):
    L = []
    a = L.append
    a("# %s rollback - generated by reorg_exec.py snapshot at %s" % (c.tag, now_utc()))
    a("# 1) restores every edited file from <meta>\\%s-edit-backups\\ IN PLACE and sets its original mtime back" % c.tag)
    a("# 2) reverses every move in REVERSE op order with Move-Item -LiteralPath")
    a("# 3) only with -PruneEmpty: removes directories created by mkdir ops, and only when they are empty")
    a("# Never deletes a file.  A move is skipped (and logged) when its new path is absent;")
    a("# it stops with an error if both the old and the new path exist.")
    a("param([switch]$PruneEmpty)")
    a("$ErrorActionPreference = 'Stop'")
    a("$Root = %s" % psq(c.root))
    a("$Meta = %s" % psq(c.meta))
    a("$Tag  = %s" % psq(c.tag))
    a("$Log  = Join-Path $Meta %s" % psq(c.tag + "-log.md"))
    a("$BakDir = Join-Path $Meta %s" % psq(c.tag + "-edit-backups"))
    a("function Log([string]$m) {")
    a("  $line = '- ' + (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') + ' | rollback.ps1 | ' + $m")
    a("  Add-Content -LiteralPath $Log -Value $line -Encoding UTF8")
    a("  Write-Host $line")
    a("}")
    a("function Restore-Edited([string]$rel, [string]$flat) {")
    a("  $bak = Join-Path $BakDir $flat")
    a("  $dst = Join-Path $Root $rel")
    a("  if (-not (Test-Path -LiteralPath $bak)) { Log \"restore skip (no backup): $rel\"; return }")
    a("  if (-not (Test-Path -LiteralPath $dst)) { Log \"restore skip (edited file absent at final path): $rel\"; return }")
    a("  $bytes = [System.IO.File]::ReadAllBytes($bak)")
    a("  $fs = [System.IO.File]::Open($dst, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)")
    a("  try { $fs.Write($bytes, 0, $bytes.Length); $fs.SetLength($bytes.Length); $fs.Flush() } finally { $fs.Dispose() }")
    a("  (Get-Item -LiteralPath $dst).LastWriteTimeUtc = (Get-Item -LiteralPath $bak).LastWriteTimeUtc")
    a("  Log \"restored from backup: $rel\"")
    a("}")
    a("function Reverse-Move([string]$op, [string]$oldRel, [string]$newRel) {")
    a("  $old = Join-Path $Root $oldRel")
    a("  $new = Join-Path $Root $newRel")
    a("  if (-not (Test-Path -LiteralPath $new)) { Log \"op $op skip: new path absent: $newRel\"; return }")
    a("  if (Test-Path -LiteralPath $old) { throw \"op $op conflict: both exist: $oldRel and $newRel\" }")
    a("  Move-Item -LiteralPath $new -Destination $old")
    a("  Log \"op $op reversed: $newRel -> $oldRel\"")
    a("}")
    a("function Reverse-CaseMove([string]$op, [string]$oldRel, [string]$newRel) {")
    a("  $old = Join-Path $Root $oldRel")
    a("  $new = Join-Path $Root $newRel")
    a("  $parent = Split-Path -Parent $new")
    a("  $oldLeaf = Split-Path -Leaf $old")
    a("  $newLeaf = Split-Path -Leaf $new")
    a("  $names = @(Get-ChildItem -LiteralPath $parent -Force -Name)")
    a("  if ($names -ccontains $oldLeaf) { Log \"op $op skip: already has the original case: $oldRel\"; return }")
    a("  if (-not ($names -ccontains $newLeaf)) { Log \"op $op skip: new path absent: $newRel\"; return }")
    a("  $tmp = Join-Path $parent ($newLeaf + '.' + $Tag + '-case-' + $op + '.tmp')")
    a("  Move-Item -LiteralPath $new -Destination $tmp")
    a("  Move-Item -LiteralPath $tmp -Destination $old")
    a("  Log \"op $op reversed (case-only rename): $newRel -> $oldRel\"")
    a("}")
    a("function Prune-Dir([string]$rel) {")
    a("  $d = Join-Path $Root $rel")
    a("  if (-not (Test-Path -LiteralPath $d -PathType Container)) { return }")
    a("  $n = @(Get-ChildItem -LiteralPath $d -Force).Count")
    a("  if ($n -gt 0) { Log \"prune skip (not empty): $rel\"; return }")
    a("  Remove-Item -LiteralPath $d")
    a("  Log \"pruned empty directory: $rel\"")
    a("}")
    a("try {")
    a("  Add-Content -LiteralPath $Log -Value (\"`n## \" + (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') + '  mode=rollback.ps1  root=' + $Root) -Encoding UTF8")
    a("  # step 1: edited files back to their pre-edit bytes (they are still at their FINAL paths here)")
    for e in c.edits:
        a("  Restore-Edited %s %s" % (psq(e["file"]), psq(bak_name(e["file"]))))
    a("  # step 2: reverse moves, last op first")
    for op in reversed(c.ops):
        if is_move(op):
            fn = "Reverse-CaseMove" if is_case_only(c, op) else "Reverse-Move"
            a("  %s %s %s %s" % (fn, psq(op.id), psq(op.old), psq(op.new)))
        else:
            a("  # op %s was mkdir %s (kept unless -PruneEmpty and empty)" % (op.id, posix(op.new)))
    a("  # step 3: optional, empty directories created by mkdir ops only (deepest first)")
    a("  if ($PruneEmpty) {")
    for op in reversed(c.ops):
        if not is_move(op):
            a("    Prune-Dir %s" % psq(op.new))
    a("  }")
    a("  Log 'rollback finished'")
    a("} catch {")
    a("  Log (\"FAILED: \" + $_.Exception.Message)")
    a("  exit 1")
    a("}")
    return "\r\n".join(L) + "\r\n"


def mode_snapshot(c):
    tb = os.path.join(c.meta, c.tag + "-tree-before.txt")
    os.makedirs(c.meta, exist_ok=True)
    if os.path.exists(tb):
        if c.args.force_snapshot:
            kept = tb[:-4] + "." + now_utc().replace(":", "") + ".txt"
            os.rename(tb, kept)
            print("existing tree-before kept as %s" % kept)
        else:
            print("tree-before already exists - NOT overwritten (use --force-snapshot to keep the old one "
                  "under a timestamped name and write a new one)")
            tb = None
    if tb:
        out, n, b = write_tree(c, c.tag + "-tree-before.txt")
        print("wrote %s  (%d files, %d bytes)" % (out, n, b))
        log(c, "- %s | snapshot | tree-before | %d files, %d bytes | ok" % (now_utc(), n, b))
    ps = os.path.join(c.meta, c.tag + "-rollback.ps1")
    with open(ps, "w", encoding="utf-8-sig", newline="") as f:      # UTF-8 with BOM for Windows PowerShell 5.1
        f.write(gen_ps1(c))
    print("wrote %s" % ps)
    if not c.edits:
        print("note: no --edits given, so rollback.ps1 will not restore any edited file")
    log(c, "- %s | snapshot | rollback.ps1 | %d move ops, %d edited files | ok"
        % (now_utc(), sum(1 for o in c.ops if is_move(o)), len(c.edits)))
    return [], []


# --------------------------------------------------------------------------- mode: run
def mode_run(c):
    if not c.args.no_guard:
        miss = [n for n in (c.tag + "-tree-before.txt", c.tag + "-rollback.ps1")
                if not os.path.isfile(os.path.join(c.meta, n))]
        if miss:
            raise Fail("refusing to run: snapshot not taken (missing %s in %s). Run `snapshot` first "
                       "(or --no-guard)." % (", ".join(miss), c.meta))
    todo = c.ops
    if c.args.stop_after is not None:
        try:
            limit = int(c.args.stop_after)
        except ValueError:
            raise Fail("--stop-after needs an op id (a number), got %r" % c.args.stop_after)
        todo = [op for op in c.ops if int(op.id) <= limit]
        print("partial run: ops with id <= %d (%d of %d)" % (limit, len(todo), len(c.ops)))
    counts = collections.Counter()
    for op in todo:
        try:
            if not is_move(op):
                dst = A(c, op.new)
                if os.path.isdir(dst):
                    log_op(c, op, "skip-done")
                    counts["skip-done"] += 1
                    continue
                if os.path.lexists(dst):
                    raise Fail("mkdir target exists and is not a directory: %s" % dst)
                if not os.path.isdir(os.path.dirname(dst)):
                    raise Fail("parent directory missing for mkdir: %s" % os.path.dirname(dst))
                os.makedirs(dst, exist_ok=False)
                result = "ok"
            elif is_case_only(c, op):
                # a direct rename would see its own destination: go through a temporary sibling name
                result = rename_case(c, op.id, os.path.dirname(A(c, op.new)),
                                     os.path.basename(op.old), os.path.basename(op.new))
                if result == "absent":
                    raise Fail("source missing and destination absent: %s" % A(c, op.old))
            elif c.ci and op.old.lower() == op.new.lower():
                result = "skip-done"                        # only a parent directory's case differs
            else:
                src, dst = A(c, op.old), A(c, op.new)
                s_there, d_there = os.path.lexists(src), os.path.lexists(dst)
                if not s_there and d_there:
                    result = "skip-done"
                else:
                    if not s_there:
                        raise Fail("source missing and destination absent: %s" % src)
                    if d_there:
                        raise Fail("destination already exists: %s" % dst)   # os.rename may overwrite on POSIX
                    if not os.path.isdir(os.path.dirname(dst)):
                        raise Fail("destination parent missing: %s" % os.path.dirname(dst))
                    os.rename(src, dst)
                    result = "ok"
            log_op(c, op, result)
            counts[result] += 1
        except Exception as ex:                              # stop at the FIRST failure, no retry
            log_op(c, op, "FAIL: %r" % (ex,))
            print("FAILED at op %s (%s): %r" % (op.id, op.action, ex), file=sys.stderr)
            print("done before failure: %s" % dict(counts))
            return ["op %s failed: %r" % (op.id, ex)], []
    print("ops: %d total, ok=%d, skip-done=%d" % (len(todo), counts["ok"], counts["skip-done"]))
    return [], []


# --------------------------------------------------------------------------- mode: edits
def overwrite_in_place(final, data):
    """Overwrite an existing file's bytes IN PLACE (same file identity: a cloud-sync client keeps
    the file ID; a rename-over could be seen as delete + create).  Verified by read-back."""
    with open(final, "r+b") as f:
        f.seek(0)
        f.write(data)
        f.truncate()
        f.flush()
        os.fsync(f.fileno())
    with open(final, "rb") as f:
        if f.read() != data:
            raise Fail("in-place write verification failed: %s" % final)


def rewrite_zip(src, dst_tmp, changes):
    """Write a copy of zip `src` to `dst_tmp` where only the members named in `changes` differ."""
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst_tmp, "w") as zout:
        zout.comment = zin.comment
        for info in zin.infolist():
            zi = copy.copy(info)
            if info.filename.endswith("/"):
                data = b""
            else:
                data = changes[info.filename] if info.filename in changes else zin.read(info)
            zout.writestr(zi, data, compress_type=info.compress_type)
    with zipfile.ZipFile(dst_tmp) as zt:                      # sanity: valid zip, same member list/order
        if zt.testzip() is not None:
            raise Fail("rewritten zip failed CRC test")
        with zipfile.ZipFile(src) as zin:
            if [i.filename for i in zt.infolist()] != [i.filename for i in zin.infolist()]:
                raise Fail("rewritten zip member list differs")


def mode_edits(c):
    plans = []
    for e in c.edits:
        plans.append(plan_edit(e, A(c, e["file"]), os.path.join(c.bakdir, bak_name(e["file"]))))
    errs = [x for p in plans for x in p["errors"]]
    for p in plans:
        for w in p["warnings"]:
            print("WARN " + w)
    if errs:
        for x in errs:
            print("ERROR " + x, file=sys.stderr)
            log(c, "- %s | edit | ERROR | %s" % (now_utc(), x))
        print("nothing written (all-or-nothing): %d problem(s)" % len(errs), file=sys.stderr)
        return errs, []
    nd = na = 0
    try:
        for p in plans:
            e, path = p["edit"], p["path"]
            rel = posix(e["file"])
            bak = os.path.join(c.bakdir, bak_name(e["file"]))
            if p["state"] == "done":
                nd += 1
                hasbak = os.path.exists(bak)
                log(c, "- %s | edit | %s | %s | already-applied (%d replacements) | backup=%s | skip-done"
                    % (now_utc(), rel, e["kind"], len(p["results"]), "yes" if hasbak else "NONE"))
                print("already-applied: %s%s" % (rel, "" if hasbak else "   (WARNING: no backup exists)"))
                continue
            try:
                st = os.stat(path)
                pre = "pre-mtime=%s pre-bytes=%d" % (fmt_mtime(st.st_mtime), st.st_size)
                if not os.path.exists(bak):
                    os.makedirs(c.bakdir, exist_ok=True)
                    part = bak + ".part"
                    shutil.copy2(path, part)                   # copy2 keeps the mtime for the restore
                    if not same_bytes(path, part):
                        raise Fail("backup verification failed for %s" % rel)
                    os.replace(part, bak)
                if not same_bytes(path, bak):                  # last guard right before the write
                    raise Fail("file changed since its backup was taken: %s" % rel)
                if e["kind"] == "text":
                    overwrite_in_place(path, p["payload"].encode("utf-8"))
                else:
                    os.makedirs(c.tmpdir, exist_ok=True)       # temp files live under --meta, never in the tree
                    tmp = os.path.join(c.tmpdir, bak_name(e["file"]) + ".new")
                    try:
                        rewrite_zip(path, tmp, p["payload"])
                        with open(tmp, "rb") as f:
                            data = f.read()
                        overwrite_in_place(path, data)
                    finally:
                        if os.path.exists(tmp):
                            os.remove(tmp)                     # our own temp file only
                na += 1
                log(c, "- %s | edit | %s | %s | applied %d replacements (%s) | backup=%s | ok"
                    % (now_utc(), rel, e["kind"], len(p["results"]), pre, os.path.basename(bak)))
                print("edited: %-50s %2d replacements" % (rel, len(p["results"])))
            except Exception as ex:
                log(c, "- %s | edit | %s | FAIL: %r" % (now_utc(), rel, ex))
                print("FAILED editing %s: %r" % (rel, ex), file=sys.stderr)
                return ["edit failed: %s: %r" % (rel, ex)], []
    finally:
        try:
            os.rmdir(c.tmpdir)                                 # only succeeds when empty
        except OSError:
            pass
    print("edits: %d files applied, %d already applied" % (na, nd))
    return [], []


# --------------------------------------------------------------------------- mode: verify
def expected_text_size(e, pre):
    d = 0
    for r in e["replacements"]:
        d += int(r["count"]) * (len(r["new"].encode("utf-8")) - len(r["old"].encode("utf-8")))
    return pre + d


def zipinfo_sig(i):
    return (i.filename, i.compress_type, i.date_time, i.external_attr, i.create_system, i.extra, i.comment)


def deep_check_xlsx(c, e, final_path):
    """Compare the final zip with its backup: untouched members identical, named members changed
    only by the expected text.  -> (problems, untouched_count, changed_count)"""
    out = []
    name = posix(e["file"])
    bak = os.path.join(c.bakdir, bak_name(e["file"]))
    if not os.path.isfile(bak):
        return ["%s: no backup, cannot deep-check" % name], 0, 0
    by_member = collections.OrderedDict()
    for r in e["replacements"]:
        m, old = split_member(r["old"])
        by_member.setdefault(m, []).append({"old": old, "new": r["new"], "count": r["count"]})
    ident = changed = 0
    with zipfile.ZipFile(bak) as zb, zipfile.ZipFile(final_path) as zf:
        bi, fi = zb.infolist(), zf.infolist()
        if [zipinfo_sig(i) for i in bi] != [zipinfo_sig(i) for i in fi]:
            out.append("%s: zip member list/order/compress_type/date/attrs differ from backup" % name)
        for i in bi:
            if i.filename.endswith("/"):
                continue
            exp = zb.read(i)
            if i.filename in by_member:
                t, res, errs = apply_replacements(exp.decode("utf-8"), by_member[i.filename], i.filename)
                if errs or "applied" not in res:
                    out.append("%s: cannot derive expected text for %s" % (name, i.filename))
                    continue
                exp = t.encode("utf-8")
                changed += 1
            else:
                ident += 1
            try:
                got = zf.read(i.filename)
            except KeyError:
                out.append("%s: member %s missing" % (name, i.filename))
                continue
            if got != exp:
                out.append("%s: member %s differs from expectation" % (name, i.filename))
    return out, ident, changed


def classify_file(full, size):
    """-> 'text', 'zip', 'large' or None (binary)"""
    ext = os.path.splitext(full)[1].lower()
    if ext in ZIP_EXT:
        return "zip" if size <= MAX_ZIP_BYTES else "large"
    if ext in BINARY_EXT:
        return None
    if size > MAX_TEXT_BYTES:
        return "large"
    if ext in TEXT_EXT:
        return "text"
    with open(full, "rb") as f:
        head = f.read(8192)
    return None if b"\x00" in head else "text"


def scan_old_paths(c):
    """-> (hits, notes); hit = (rel, where, matched, text_for_whitelist_matching, display)"""
    hits, notes = [], []
    if c.matcher is None:
        return hits, ["no old paths to look for (no move ops and no --old-pattern)"]
    meta_real = os.path.normcase(os.path.realpath(c.meta))
    for dp, dns, fns in os.walk(c.root, onerror=raise_err):
        dns[:] = [d for d in dns
                  if (d.lower() if c.ci else d) not in c.skip_dirs
                  and os.path.normcase(os.path.realpath(os.path.join(dp, d))) != meta_real]
        for fn in fns:
            full = os.path.join(dp, fn)
            rel = os.path.relpath(full, c.root)
            if c.ignore.match(rel):
                continue
            try:
                kind = classify_file(full, os.lstat(full).st_size)
                if kind == "large":
                    notes.append("skipped (too large to scan): %s" % posix(rel))
                elif kind == "text":
                    with open(full, "rb") as f:
                        text = f.read().decode("utf-8", errors="replace")
                    for ln, line in enumerate(text.splitlines(), 1):
                        for m in c.matcher.finditer(line):
                            hits.append((rel, "line %d" % ln, m.group(0), line, line.strip()[:200]))
                elif kind == "zip":
                    with zipfile.ZipFile(full) as z:
                        for info in z.infolist():
                            if not (info.filename.endswith(".xml") or info.filename.endswith(".rels")):
                                continue
                            text = z.read(info).decode("utf-8", errors="replace")
                            for m in c.matcher.finditer(text):
                                ctx = text[max(0, m.start() - 80): m.end() + 80]
                                hits.append((rel, "zip:" + info.filename, m.group(0), ctx, ctx.replace("\n", " ")))
            except (zipfile.BadZipFile, OSError) as ex:
                notes.append("could not scan %s: %r" % (posix(rel), ex))
    return hits, notes


def whitelisted(c, rel, line):
    for w in c.whitelist:
        if "file" in w and K(c, w["file"]) != K(c, rel):
            continue
        if "file_prefix" in w and not K(c, rel).startswith(K(c, w["file_prefix"])):
            continue
        if "contains" in w and w["contains"] not in line:
            continue
        return w
    return None


def mode_verify(c):
    problems, rep = [], []
    P = rep.append
    P("%s verify  %s  root=%s" % (c.tag, now_utc(), c.root))
    inv = [(r, b) for r, b, _, _ in c.inventory if not c.ignore.match(r)]
    edited = {K(c, e["file"]): e for e in c.edits}
    miss, badsize, ok, edited_ok = [], [], 0, 0
    expected_final = set()
    bytes_before = sum(b for _, b in inv)
    edit_delta = 0
    xl_problems = []
    for rel, size in inv:
        fin = map_path(c, rel)
        expected_final.add(K(c, fin))
        full = A(c, fin)
        if not os.path.isfile(full):
            miss.append((rel, fin))
            continue
        got = os.path.getsize(full)
        e = edited.get(K(c, fin))
        if e is None:
            if got == size:
                ok += 1
            else:
                badsize.append((rel, fin, size, got))
            continue
        edit_delta += got - size
        if e["kind"] == "text":
            exp = expected_text_size(e, size)
            if got == exp:
                edited_ok += 1
            else:
                badsize.append((rel, fin, exp, got))
        else:
            xp, ident, changed = deep_check_xlsx(c, e, full)
            xl_problems += xp
            edited_ok += 0 if xp else 1
            P("    xlsx deep-check %s: %d untouched members byte-identical, %d changed members as expected, "
              "%d problem(s)" % (posix(fin), ident, changed, len(xp)))
    files, _ = walk_tree(c)
    after_bytes = sum(s for _, s, _ in files)
    unexpected_all = sorted(posix(r) for r, _, _ in files if K(c, r) not in expected_final)
    allowed = [u for u in unexpected_all if c.allow_new.match(u)]
    unexpected = [u for u in unexpected_all if not c.allow_new.match(u)]
    P("(a) inventory vs final tree (ignored: %s)" % (", ".join(sorted(set(DEFAULT_IGNORE))) if not c.args.no_default_ignore
                                                      else "defaults off") + (" + %d custom" % len(c.args.ignore) if c.args.ignore else ""))
    P("    inventory rows            : %d" % len(inv))
    P("    present, identical size   : %d" % ok)
    P("    edited files as expected  : %d of %d" % (edited_ok, len(c.edits)))
    P("    missing                   : %d" % len(miss))
    P("    size mismatch             : %d" % len(badsize))
    P("    files before / after      : %d / %d" % (len(inv), len(files)))
    P("    bytes before / after      : %d / %d  (delta %+d; edited-file delta %+d; unexplained %+d)"
      % (bytes_before, after_bytes, after_bytes - bytes_before, edit_delta, after_bytes - bytes_before - edit_delta))
    P("    allowed new files         : %d" % len(allowed))
    P("    unexpected files on disk  : %d" % len(unexpected))
    for rel, fin in miss[:50]:
        P("      MISSING  %s  (expected at %s)" % (posix(rel), posix(fin)))
    for rel, fin, exp, got in badsize[:50]:
        P("      SIZE     %s -> %s expected %d got %d" % (posix(rel), posix(fin), exp, got))
    for u in unexpected[:50]:
        P("      EXTRA    %s" % u)
    for u in allowed[:50]:
        P("      ALLOWED  %s" % u)
    for x in xl_problems:
        P("      XLSX     %s" % x)
    if miss:
        problems.append("(a) %d missing file(s)" % len(miss))
    if badsize:
        problems.append("(a) %d size mismatch(es)" % len(badsize))
    if xl_problems:
        problems.append("(a) %d xlsx deep-check problem(s)" % len(xl_problems))
    if unexpected or len(files) - len(allowed) != len(inv):
        problems.append("(a) file count after (%d, %d allowed new) != before (%d) / %d unexpected file(s)"
                        % (len(files), len(allowed), len(inv), len(unexpected)))
    hits, notes = scan_old_paths(c)
    unc, cov = [], collections.Counter()
    for h in hits:
        w = whitelisted(c, h[0], h[3])
        if w:
            cov[posix(w.get("file_prefix") or (w.get("file") + " ~ " + w.get("contains", "")))] += 1
        else:
            unc.append(h)
    P("(b) old-path scan (text files + Office XML), skipping %s and the meta dir"
      % ", ".join(sorted(c.skip_dirs)))
    P("    total hits                : %d" % len(hits))
    P("    covered by whitelist      : %d" % sum(cov.values()))
    for k2, n in sorted(cov.items()):
        P("        %5d  %s" % (n, k2))
    P("    UNCOVERED hits            : %d" % len(unc))
    for rel, where, m, _, disp in unc[:400]:
        P("      HIT  %s  [%s]  %r  | %s" % (posix(rel), where, m, disp))
    for n_ in notes:
        P("    note: " + n_)
    if unc:
        problems.append("(b) %d uncovered old-path hit(s) in %d file(s)" % (len(unc), len({h[0] for h in unc})))
    P("RESULT: %s" % ("FAIL - " + "; ".join(problems) if problems else "OK"))
    out = os.path.join(c.meta, c.tag + "-verify.txt")
    os.makedirs(c.meta, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(rep) + "\n")
    print("\n".join(rep[:40]))
    print("full report: %s" % out)
    log(c, "- %s | verify | %s | %s" % (now_utc(), "FAIL" if problems else "OK", "; ".join(problems) or "no problems"))
    return problems, []


# --------------------------------------------------------------------------- mode: tree-after / rollback
def mode_tree_after(c):
    out, n, b = write_tree(c, c.tag + "-tree-after.txt")
    print("wrote %s  (%d files, %d bytes)" % (out, n, b))
    log(c, "- %s | tree-after | %d files, %d bytes | ok" % (now_utc(), n, b))
    return [], []


def rename_case(c, op_id, parent, from_leaf, to_leaf):
    """Case-only rename of one directory entry via a temporary sibling name (resumable).
    -> 'skip-done' (already has the target case), 'ok', or 'absent' (neither name nor temp name exists)"""
    if not os.path.isdir(parent):
        raise Fail("parent directory missing: %s" % parent)
    names = os.listdir(parent)
    tmp_leaf = "%s.%s-case-%s.tmp" % (to_leaf, c.tag, op_id)
    if to_leaf in names:
        return "skip-done"
    if from_leaf in names:
        tmp = os.path.join(parent, tmp_leaf)
        if os.path.lexists(tmp):
            raise Fail("temporary name already exists: %s" % tmp)
        os.rename(os.path.join(parent, from_leaf), tmp)
        os.rename(tmp, os.path.join(parent, to_leaf))
        return "ok"
    if tmp_leaf in names:                                   # an earlier run stopped between the two renames
        os.rename(os.path.join(parent, tmp_leaf), os.path.join(parent, to_leaf))
        return "ok"
    return "absent"


def mode_rollback(c):
    for e in c.edits:
        bak = os.path.join(c.bakdir, bak_name(e["file"]))
        dst = A(c, e["file"])
        name = posix(e["file"])
        if not os.path.isfile(bak):
            log(c, "- %s | rollback | restore skip (no backup) | %s" % (now_utc(), name))
            print("restore skip (no backup): %s" % name)
        elif not os.path.isfile(dst):
            log(c, "- %s | rollback | restore skip (absent at final path) | %s" % (now_utc(), name))
            print("restore skip (absent at final path): %s" % name)
        else:
            with open(bak, "rb") as f:
                overwrite_in_place(dst, f.read())           # in place: keeps the cloud file ID
            st = os.stat(bak)
            os.utime(dst, (st.st_atime, st.st_mtime))       # original mtime comes back with the bytes
            log(c, "- %s | rollback | restored from backup | %s" % (now_utc(), name))
            print("restored: %s" % name)
    n = 0
    for op in reversed(c.ops):
        if not is_move(op):
            continue
        old, new = A(c, op.old), A(c, op.new)
        if is_case_only(c, op):
            res = rename_case(c, op.id, os.path.dirname(old), os.path.basename(op.new), os.path.basename(op.old))
            if res == "absent":
                log_op(c, op, "rollback skip: new path absent")
            elif res == "skip-done":
                log_op(c, op, "rollback skip: already has the original case")
            else:
                log_op(c, op, "rolled back (case-only rename)")
                n += 1
            continue
        if c.ci and op.old.lower() == op.new.lower():
            log_op(c, op, "rollback skip: only a parent directory's case differs")
            continue
        if not os.path.lexists(new):
            log_op(c, op, "rollback skip: new path absent")
            continue
        if os.path.lexists(old):
            log_op(c, op, "rollback CONFLICT: both exist")
            raise Fail("op %s conflict: both %s and %s exist" % (op.id, posix(op.old), posix(op.new)))
        if not os.path.isdir(os.path.dirname(old)):
            raise Fail("op %s: parent of %s missing" % (op.id, posix(op.old)))
        os.rename(new, old)
        log_op(c, op, "rolled back")
        n += 1
    print("rolled back %d moves" % n)
    created = [op for op in reversed(c.ops) if not is_move(op)]
    if c.args.prune_empty:
        pruned = kept = 0
        for op in created:                                  # reverse op order: children before parents
            d = A(c, op.new)
            if not os.path.isdir(d) or os.path.islink(d):
                continue
            if os.listdir(d):
                kept += 1
                log_op(c, op, "prune skip: not empty")
                continue
            os.rmdir(d)
            pruned += 1
            log_op(c, op, "pruned empty directory")
        print("pruned %d empty mkdir-created directories, kept %d that are not empty" % (pruned, kept))
    else:
        left = [op.new for op in created if os.path.isdir(A(c, op.new))]
        if left:
            print("directories created by mkdir ops left in place: %d (use --prune-empty to remove the empty ones)"
                  % len(left))
    tb = os.path.join(c.meta, c.tag + "-tree-before.txt")
    out, nf, nb = write_tree(c, c.tag + "-tree-rolledback.txt")
    if os.path.isfile(tb):
        with open(tb, "r", encoding="utf-8", newline="") as f1, open(out, "r", encoding="utf-8", newline="") as f2:
            same = f1.read() == f2.read()
        print("tree vs tree-before snapshot: %s" % ("IDENTICAL (paths, bytes, mtimes)" if same else "DIFFERENT"))
        log(c, "- %s | rollback | tree vs snapshot | %s" % (now_utc(), "identical" if same else "DIFFERENT"))
        if not same:
            return ["rolled-back tree differs from tree-before"], []
    return [], []


# --------------------------------------------------------------------------- main
MODES = {"plan-check": mode_plan_check, "preflight": mode_preflight, "snapshot": mode_snapshot, "run": mode_run,
         "edits": mode_edits, "verify": mode_verify, "tree-after": mode_tree_after, "rollback": mode_rollback}


def build_parser():
    ap = argparse.ArgumentParser(prog="reorg_exec.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=sorted(MODES))
    ap.add_argument("--root", help="folder being reorganized")
    ap.add_argument("--meta", help="folder for the log, snapshots, backups and reports (kept out of every walk)")
    ap.add_argument("--pathmap", help="path map CSV: op,wave,action,old_path,new_path")
    ap.add_argument("--edits", help="edits JSON: {edits: [...], whitelist: [...]}")
    ap.add_argument("--inventory", help="inventory TSV (see reorg_scan.py inventory)")
    ap.add_argument("--tag", default=DEFAULT_TAG, help="prefix of every file written under --meta (default: reorg)")
    ap.add_argument("--case-insensitive", choices=("auto", "yes", "no"), default="auto")
    ap.add_argument("--strict-inventory", action="store_true", help="preflight: inventory drift is fatal")
    ap.add_argument("--force-snapshot", action="store_true", help="snapshot: replace an existing tree-before")
    ap.add_argument("--no-guard", action="store_true", help="run: do not require the snapshot files")
    ap.add_argument("--stop-after", metavar="OP", help="run: execute only ops with id <= OP (partial run)")
    ap.add_argument("--prune-empty", action="store_true",
                    help="rollback: rmdir now-empty directories created by mkdir ops (never deletes files)")
    ap.add_argument("--whitelist-extra", metavar="JSON", help="verify: extra whitelist entries")
    ap.add_argument("--ignore", action="append", default=[], metavar="GLOB",
                    help="repeatable; ignored in verify / tree files / inventory comparisons")
    ap.add_argument("--no-default-ignore", action="store_true", help="do not add desktop.ini, Thumbs.db, .DS_Store")
    ap.add_argument("--allow-new", action="append", default=[], metavar="GLOB",
                    help="repeatable; verify: files that may appear without being in the inventory")
    ap.add_argument("--old-pattern", action="append", default=[], metavar="REGEX",
                    help="repeatable; verify: old-path regex (default: built from the path map)")
    ap.add_argument("--skip-dir", action="append", default=[], metavar="NAME",
                    help="repeatable; directory names the verify content scan does not enter")
    return ap


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = build_parser()
    a = ap.parse_args(argv)
    missing = [n for n in MODE_NEEDS[a.mode] if not getattr(a, n)]
    if missing:
        ap.error("mode %s needs %s" % (a.mode, ", ".join("--" + n for n in missing)))
    c = None
    try:
        c = build_ctx(a)
        if c.root is not None and not os.path.isdir(c.root):
            raise Fail("root is not a directory: %s" % c.root)
        problems, warns = MODES[a.mode](c)
    except Fail as ex:
        print("FAIL: %s" % ex, file=sys.stderr)
        if c is not None and c.header_done:                  # only when this run already used the ledger
            try:
                log(c, "- %s | %s | FAIL: %s" % (now_utc(), a.mode, ex))
            except Exception:
                pass
        return 1
    except Exception as ex:
        traceback.print_exc()
        print("FAIL (unexpected): %r" % (ex,), file=sys.stderr)
        if c is not None and c.header_done:
            try:
                log(c, "- %s | %s | FAIL (unexpected): %r" % (now_utc(), a.mode, ex))
            except Exception:
                pass
        return 1
    for w in warns:
        print("WARN: " + w)
    if problems:
        print("%s: %d PROBLEM(S)" % (a.mode, len(problems)))
        for p in problems[:200]:
            print("  - " + p)
        if len(problems) > 200:
            print("  ... %d more" % (len(problems) - 200))
        return 1
    print("%s: OK" % a.mode)
    return 0


if __name__ == "__main__":
    sys.exit(main())
