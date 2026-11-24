"""Toolkit knowledge-base HTTP service (JSON over HTTP, port 8011 in the container).

Request handling lives in :class:`KBApp`, which needs only a store object with
``search``/``nearest``/``count`` and an optional scanner, so it is unit-tested
with fakes. The HTTP layer only reads the body (bounded) and writes JSON.

Security posture:
- The host publishes the port on 127.0.0.1 only; in addition any request whose
  ``Host`` header is not ``localhost`` / ``127.0.0.1`` gets 403 (DNS-rebinding guard),
  any request carrying an ``Origin`` header gets 403 (browsers send one on
  cross-site requests; the CLI and the hook never do), and a POST without
  ``Content-Type: application/json`` gets 415.
- Request bodies are never logged; only method, path and status are.
- Indexed passages are returned as data and never interpreted; the hook serves
  reviewed (``repo``) passages only, quoted under a header saying they are
  reference data, not instructions.
"""

from __future__ import annotations

import json
import logging
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import kb_core

log = logging.getLogger("kb.service")

MAX_BODY = 256 * 1024
MAX_K = 20
MAX_QUERY_CHARS = 2000
MAX_DEDUPE_PIECES = 32
VERIFY_SAMPLE = 3
VERIFY_MAX_SELF_DISTANCE = 0.001
LISTEN_PORT = 8011
# Inside the container the server must listen on all container interfaces so the
# published port works; compose publishes it on the host as 127.0.0.1 only.
LISTEN_HOST = "0.0.0.0"  # nosec - container-internal, see compose ports
ALLOWED_HOSTS = frozenset({"localhost", "127.0.0.1"})


class BadRequest(Exception):
    pass


def _host_allowed(host_header) -> bool:
    if not host_header:
        return False
    host = str(host_header).strip().lower()
    if host.startswith("["):
        return False
    name = host.rsplit(":", 1)[0] if ":" in host else host
    if ":" in host:
        port = host.rsplit(":", 1)[1]
        if port and not port.isdigit():
            return False
    return name in ALLOWED_HOSTS


def _header(headers, name: str):
    if headers is None:
        return None
    getter = getattr(headers, "get", None)
    if getter is not None:
        value = getter(name)
        if value is not None:
            return value
    try:
        for key, value in headers.items():
            if str(key).lower() == name.lower():
                return value
    except AttributeError:
        pass
    return None


def _int_param(payload: dict, key: str, default: int) -> int:
    value = payload.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BadRequest(f"'{key}' must be a number")
    return max(1, min(MAX_K, int(value)))


def _float_param(payload: dict, key: str, default: float) -> float:
    value = payload.get(key)
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BadRequest(f"'{key}' must be a number")
    return float(value)


def _text_param(payload: dict, key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise BadRequest(f"'{key}' must be a non-empty string")
    return value


class KBApp:
    def __init__(self, store, config: kb_core.ServiceConfig | None = None, scanner=None):
        self.store = store
        self.config = config or kb_core.ServiceConfig()
        self.scanner = scanner
        self.stats = {"searches": 0, "hits": 0, "misses": 0}
        self._stats_lock = threading.Lock()
        self.routes = {
            ("GET", "/health"): self.health,
            ("POST", "/search"): self.search,
            ("POST", "/dedupe"): self.dedupe,
            ("POST", "/hook"): self.hook,
            ("POST", "/reindex"): self.reindex,
            ("POST", "/verify"): self.verify,
        }

    # ---------------------------------------------------------------- dispatch

    def handle(self, method: str, raw_path: str, headers, body: bytes, content_length: int | None = None):
        """Return ``(status, payload_dict)``. Never raises; never logs the body."""
        method = (method or "").upper()
        path = (raw_path or "/").split("?", 1)[0].split("#", 1)[0]
        if len(path) > 1:
            path = path.rstrip("/")
        status, payload = self._handle(method, path, headers, body or b"", content_length)
        log.info("%s %s %d", method, path[:64], status)
        return status, payload

    def _handle(self, method, path, headers, body, content_length):
        if not _host_allowed(_header(headers, "Host")):
            return 403, {"error": "forbidden host"}
        if _header(headers, "Origin") is not None:
            return 403, {"error": "cross-origin requests are not accepted"}
        size = max(len(body), content_length or 0)
        if size > MAX_BODY:
            return 413, {"error": f"request body larger than {MAX_BODY} bytes"}
        route = self.routes.get((method, path))
        if route is None:
            if any(p == path for (_m, p) in self.routes):
                return 405, {"error": "method not allowed"}
            return 404, {"error": "not found"}
        if method == "POST":
            ctype = str(_header(headers, "Content-Type") or "").split(";", 1)[0].strip().lower()
            if ctype != "application/json":
                return 415, {"error": "Content-Type must be application/json"}
        payload: dict = {}
        if method == "POST" and body.strip():
            try:
                payload = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                return 400, {"error": "invalid JSON body"}
            if not isinstance(payload, dict):
                return 400, {"error": "JSON body must be an object"}
        try:
            return 200, route(payload)
        except BadRequest as exc:
            return 400, {"error": str(exc)}
        except Exception as exc:  # noqa: BLE001 - never leak a traceback to the client
            log.error("%s %s failed: %s", method, path, type(exc).__name__)
            return 500, {"error": "internal error"}

    def _count(self, hits: list) -> None:
        with self._stats_lock:
            self.stats["searches"] += 1
            self.stats["hits" if hits else "misses"] += 1

    # ---------------------------------------------------------------- endpoints

    def health(self, _payload: dict) -> dict:
        try:
            chunks = self.store.count()
        except Exception as exc:  # noqa: BLE001
            chunks = None
            log.warning("count failed: %s", type(exc).__name__)
        scanner = self.scanner
        with self._stats_lock:
            stats = dict(self.stats)
        return {
            "collection": self.config.collection,
            "chunks": chunks,
            "files": scanner.files if scanner else None,
            "last_scan": scanner.last_scan if scanner else None,
            "last_indexed": scanner.last_indexed if scanner else None,
            "quarantined": dict(scanner.quarantined) if scanner else {},
            "errors": list(scanner.errors) if scanner else [],
            "stats": stats,
        }

    def search(self, payload: dict) -> dict:
        q = _text_param(payload, "q")[:MAX_QUERY_CHARS]
        k = _int_param(payload, "k", 5)
        max_distance = _float_param(payload, "max_distance", self.config.max_distance)
        kinds = payload.get("kind")
        if kinds is not None:
            if isinstance(kinds, str):
                kinds = [kinds] if kinds else None
            elif isinstance(kinds, list) and all(isinstance(x, str) for x in kinds):
                kinds = [x for x in kinds if x] or None
            else:
                raise BadRequest("'kind' must be a string or a list of strings")
        source = payload.get("source")
        if source is not None and not isinstance(source, str):
            raise BadRequest("'source' must be a string")
        hits = self.store.search(q=q, k=k, max_distance=max_distance, kinds=kinds, source=source or None)
        self._count(hits)
        return {"hits": hits}

    def dedupe(self, payload: dict) -> dict:
        text = _text_param(payload, "text")
        k = _int_param(payload, "k", 3)
        source = payload.get("source")
        if source is not None and not isinstance(source, str):
            raise BadRequest("'source' must be a string")
        pieces = kb_core.split_text(text)[:MAX_DEDUPE_PIECES] or [text[: kb_core.CHUNK_SIZE]]
        nearest = self.store.nearest(pieces, k=k, source=source or None)
        best = min((n["distance"] for n in nearest if n.get("distance") is not None), default=None)
        verdict = kb_core.dedupe_verdict(best, self.config.dup_distance, self.config.near_distance)
        return {"verdict": verdict, "nearest": nearest[:k]}

    def hook(self, payload: dict) -> dict:
        prompt = payload.get("prompt")
        if not isinstance(prompt, str) or len(prompt.strip()) < 3:
            return {}
        try:
            # only reviewed knowledge reaches the agent unasked; pending inbox items stay out
            hits = self.store.search(
                q=prompt[:MAX_QUERY_CHARS],
                k=kb_core.HOOK_MAX_HITS,
                max_distance=self.config.max_distance,
                source="repo",
            )
        except Exception as exc:  # noqa: BLE001 - the prompt hook must never block the user
            log.warning("hook search failed: %s", type(exc).__name__)
            return {}
        self._count(hits)
        context = kb_core.build_hook_context(hits)
        if not context:
            return {}
        return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": context}}

    def reindex(self, _payload: dict) -> dict:
        if self.scanner is None:
            return {"indexed": []}
        report = self.scanner.scan(delete_missing=False)
        return {"indexed": report["indexed"]}


    def verify(self, _payload: dict) -> dict:
        """Read back stored vectors: non-zero, and each one finds itself. Returns no vectors or text."""
        chunks = self.store.count()
        if not chunks:
            return {"ok": False, "chunks": 0, "checked": 0, "detail": "collection is empty"}
        sample = self.store.sample_embeddings(VERIFY_SAMPLE)
        if not sample:
            return {"ok": False, "chunks": chunks, "checked": 0, "detail": "no stored vectors could be read back"}
        checked = 0
        for n, (rid, vector) in enumerate(sample, 1):
            if not vector:
                return {"ok": False, "chunks": chunks, "checked": checked,
                        "detail": f"stored vector {n} has no values"}
            if not any(abs(x) > 0.0 for x in vector):
                return {"ok": False, "chunks": chunks, "checked": checked,
                        "detail": f"stored vector {n} is all zeros (index damaged; rebuild with a full index)"}
            found = self.store.query_vector(vector, k=1)
            if not found:
                return {"ok": False, "chunks": chunks, "checked": checked,
                        "detail": f"self-query of stored vector {n} returned nothing"}
            top_id, distance = found[0]
            if top_id != rid or distance >= VERIFY_MAX_SELF_DISTANCE:
                return {"ok": False, "chunks": chunks, "checked": checked,
                        "detail": f"self-query of stored vector {n} did not return itself "
                                  f"(distance {distance:.4f}, same id: {top_id == rid})"}
            checked += 1
        return {"ok": True, "chunks": chunks, "checked": checked,
                "detail": f"{checked} stored vectors read back, non-zero, "
                          f"self-query distance < {VERIFY_MAX_SELF_DISTANCE}"}


class Handler(BaseHTTPRequestHandler):
    server_version = "llm-toolkit-kb"
    sys_version = ""
    timeout = 15

    def _dispatch(self, method: str) -> None:
        raw_length = self.headers.get("Content-Length")
        try:
            length = int(raw_length) if raw_length else 0
            if length < 0:
                raise ValueError
        except ValueError:
            self._send(400, {"error": "invalid Content-Length"})
            return
        body = b""
        if length and length <= MAX_BODY:
            body = self.rfile.read(length)
        if length > MAX_BODY:
            self.close_connection = True  # the oversized body is not read
        status, payload = self.server.app.handle(method, self.path, self.headers, body, content_length=length)
        self._send(status, payload)

    def _send(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        self._dispatch("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch("POST")

    def log_message(self, format, *args) -> None:  # noqa: A002 - KBApp logs method/path/status only
        return


def _background_scan(scanner, seconds: int, stop: threading.Event) -> None:
    while not stop.is_set():
        try:
            scanner.scan(delete_missing=False)
        except Exception as exc:  # noqa: BLE001
            log.warning("background scan failed: %s", type(exc).__name__)
        stop.wait(seconds)


def main() -> int:
    kb_core.configure_logging()
    cfg = kb_core.service_config()
    import ingest
    import store as store_mod  # vector-store adapter, loaded only when actually running

    try:
        kb = store_mod.connect_with_retry(cfg)
    except RuntimeError as exc:
        log.error("%s", exc)
        return 2
    scanner = ingest.Scanner(kb, {"repo": cfg.repo_root, "inbox": cfg.inbox_root, "archive": cfg.archive_root})
    app = KBApp(kb, cfg, scanner)
    stop = threading.Event()
    threading.Thread(target=_background_scan, args=(scanner, cfg.scan_seconds, stop), daemon=True).start()
    server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), Handler)
    server.daemon_threads = True
    server.app = app
    log.info("serving collection %s on container port %d", cfg.collection, LISTEN_PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
