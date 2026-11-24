"""Corpus scanner and the one-shot full ingest job.

``Scanner.scan(delete_missing=False)`` is the incremental pass the service runs
in the background: it indexes new and changed files and never removes the
chunks of files that disappeared. ``python ingest.py`` runs a full pass with
``delete_missing=True`` so vanished files leave the index.

Files whose content matches a secret rule are quarantined: never indexed, and
only their path and the rule names are kept (never the matched text).
"""

from __future__ import annotations

import collections
import json
import logging
import os
import sys
import threading
import time

import kb_core

log = logging.getLogger("kb.ingest")

SOURCES = ("repo", "inbox")


def display_path(source: str, rel: str) -> str:
    return rel if source == "repo" else f"{source}/{rel}"


def utc_iso(ts: float | None = None) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() if ts is None else ts))


def build_records(source: str, rel: str, text: str, sha: str) -> list:
    """Chunk records ``(id, document, metadata)`` for one clean file."""
    front = kb_core.parse_front_matter(text)[0] if rel.lower().endswith(".md") else {}
    kind = kb_core.classify_kind(rel, front if source == "inbox" else None)
    chunks = kb_core.chunk_document(display_path(source, rel), text)
    total = len(chunks)
    status = "merged" if source == "repo" else "pending"
    records = []
    for n, chunk in enumerate(chunks):
        meta = {
            "source": source,
            "path": rel,
            "kind": kind,
            "title": str(chunk.get("title") or ""),
            "heading": str(chunk.get("heading") or ""),
            "chunk": n,
            "chunks": total,
            "file_sha": sha,
            "status": status,
        }
        records.append((kb_core.chunk_id(source, rel, n), chunk["text"], meta))
    return records


class Scanner:
    """Keeps the index in step with the corpus roots. Thread-safe (one scan at a time)."""

    def __init__(self, store, sources: dict):
        self.store = store
        self.sources = dict(sources)
        self.lock = threading.Lock()
        self.quarantined: dict = {}
        self.errors = collections.deque(maxlen=20)
        self.last_scan: str | None = None
        self.last_indexed: str | None = None
        self._stat: dict = {}
        self._files: dict = {}

    @property
    def files(self) -> int:
        return sum(self._files.values())

    def scan(self, delete_missing: bool = False) -> dict:
        with self.lock:
            report = {"indexed": [], "skipped": 0, "removed": [], "quarantined": {}, "errors": []}
            for source in SOURCES:
                root = self.sources.get(source)
                if not root:
                    continue
                if not os.path.isdir(root):
                    # a missing mount must never be read as "every file vanished"
                    self._error(report, f"{source}: root not found")
                    continue
                self._scan_source(source, root, delete_missing, report)
            report["quarantined"] = dict(self.quarantined)
            self.last_scan = utc_iso()
            if report["indexed"]:
                self.last_indexed = self.last_scan
            return report

    def _error(self, report: dict, message: str) -> None:
        report["errors"].append(message)
        self.errors.append(f"{utc_iso()} {message}")
        log.warning("scan error: %s", message)

    def _scan_source(self, source: str, root: str, delete_missing: bool, report: dict) -> None:
        existing = self.store.existing_files(source)
        tracked = set(existing)
        seen = set()
        for rel, full in kb_core.iter_corpus_files(root):
            seen.add(rel)
            shown = display_path(source, rel)
            key = (source, rel)
            try:
                st = os.lstat(full)
                stamp = (st.st_mtime_ns, st.st_size)
                if self._stat.get(key) == stamp and (rel in existing or shown in self.quarantined):
                    report["skipped"] += 1
                    continue
                with open(full, "rb") as fh:
                    data = fh.read(kb_core.MAX_FILE_BYTES + 1)
                if len(data) > kb_core.MAX_FILE_BYTES:
                    continue
                sha = kb_core.file_sha(data)
                if existing.get(rel, {}).get("file_sha") == sha:
                    self._stat[key] = stamp
                    self.quarantined.pop(shown, None)
                    report["skipped"] += 1
                    continue
                text = data.decode("utf-8", errors="replace")
                rules = kb_core.find_secrets(text)
                if rules:
                    self.quarantined[shown] = rules
                    if rel in existing:
                        # the file still exists; drop its stale chunks rather than serve an old version
                        self.store.delete_file(source, rel)
                        tracked.discard(rel)
                    self._stat[key] = stamp
                    log.warning("quarantined %s (%s)", shown, ", ".join(rules))
                    continue
                self.quarantined.pop(shown, None)
                records = build_records(source, rel, text, sha)
                if records:
                    self.store.upsert_file(source, rel, records)
                    tracked.add(rel)
                elif rel in existing:
                    self.store.delete_file(source, rel)
                    tracked.discard(rel)
                self._stat[key] = stamp
                report["indexed"].append(shown)
            except Exception as exc:  # noqa: BLE001 - one bad file must not stop the scan
                self._stat.pop(key, None)
                self._error(report, f"{shown}: {type(exc).__name__}")
        for rel in sorted(set(self._stat_paths(source)) - seen):
            self._stat.pop((source, rel), None)
        for shown in [q for q in self.quarantined if self._source_of(q) == source]:
            rel = shown if source == "repo" else shown[len(source) + 1:]
            if rel not in seen:
                self.quarantined.pop(shown, None)
        missing = sorted(set(existing) - seen)
        if delete_missing and missing:
            # S-M2: an empty or half-visible root (a bind source Docker created empty, a sync folder
            # still downloading) must never wipe the index; refuse and leave a visible error instead.
            if not seen:
                self._error(report, f"{source}: walk saw no files; {len(missing)} removals skipped")
                missing = []
            elif len(missing) * 2 > len(existing):
                self._error(
                    report,
                    f"{source}: refusing to remove {len(missing)} of {len(existing)} tracked files (over 50%)",
                )
                missing = []
        if delete_missing:
            for rel in missing:
                try:
                    self.store.delete_file(source, rel)
                    tracked.discard(rel)
                    report["removed"].append(display_path(source, rel))
                except Exception as exc:  # noqa: BLE001
                    self._error(report, f"{display_path(source, rel)}: {type(exc).__name__}")
        self._files[source] = len(tracked)

    def _stat_paths(self, source: str):
        return [rel for (src, rel) in self._stat if src == source]

    @staticmethod
    def _source_of(shown: str) -> str:
        for source in SOURCES:
            if source != "repo" and shown.startswith(f"{source}/"):
                return source
        return "repo"


def write_state(state_dir: str, report: dict) -> None:
    """Persist a content-free summary (paths and rule names only)."""
    try:
        os.makedirs(state_dir, exist_ok=True)
        payload = {
            "finished": utc_iso(),
            "indexed": len(report["indexed"]),
            "skipped": report["skipped"],
            "removed": report["removed"],
            "quarantined": report["quarantined"],
            "errors": report["errors"],
        }
        tmp = os.path.join(state_dir, "last-ingest.json.tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
        os.replace(tmp, os.path.join(state_dir, "last-ingest.json"))
    except OSError as exc:
        log.warning("could not write ingest state (%s)", type(exc).__name__)


def main() -> int:
    kb_core.configure_logging()
    cfg = kb_core.service_config()
    import store as store_mod  # vector-store adapter, loaded only when actually running

    try:
        kb = store_mod.connect_with_retry(cfg, attempts=30)
    except RuntimeError as exc:
        print(f"ingest: {exc}", file=sys.stderr)
        return 2
    scanner = Scanner(kb, {"repo": cfg.repo_root, "inbox": cfg.inbox_root})
    report = scanner.scan(delete_missing=True)
    write_state(cfg.state_dir, report)
    print(
        f"ingest: indexed={len(report['indexed'])} skipped={report['skipped']} "
        f"removed={len(report['removed'])} quarantined={len(report['quarantined'])} "
        f"errors={len(report['errors'])} chunks={kb.count()}"
    )
    for path, rules in sorted(report["quarantined"].items()):
        print(f"quarantined: {path} ({', '.join(rules)})")
    for message in report["errors"]:
        print(f"error: {message}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
