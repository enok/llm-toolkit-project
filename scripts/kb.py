#!/usr/bin/env python3
"""Host command-line tool for the toolkit knowledge base (stdlib only).

Talks to the local KB service over HTTP on 127.0.0.1 and drives the Docker
compose stack. Shared pure helpers (secret detection, front matter, corpus
walking) come from kb/service/kb_core.py, imported by path and never copied.

Exit codes: search fallback 3; check 0 novel / 3 duplicate / 4 security /
5 near / 6 service unreachable; setup errors 2.
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import platform
import plistlib
import re
import shlex
import shutil
import subprocess
import sys
import time
import tempfile
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PROJECT = "llm-toolkit-kb"
LAUNCHD_LABEL = "dev.llm-toolkit.kb-sync"
WIN_TASK = "llm-toolkit-kb-sync"
CRON_MARKER = "# llm-toolkit-kb-sync"
HOOK_PREFIX = 'curl -sf --max-time 2 -H "Content-Type: application/json" http://localhost:'
HOOK_PREFIX_OLD = "curl -s --max-time 2 http://localhost:"
HOOK_SUFFIX = "/hook -d @-"
KINDS = ("rule", "workflow", "skill", "agent", "learning", "rubric", "integration", "doc", "script", "test",
         "client", "kb", "index")
TIMEOUT_DEFAULT = 120
TIMEOUT_GIT = 120
TIMEOUT_COMPOSE_UP = 600
TIMEOUT_INGEST = 1800
TIMEOUT_SURFACES = 300
DOCKER_WAIT_SECONDS = 180
HEALTH_WAIT_SECONDS = 120
WAIT_INTERVAL = 5
DEFAULT_HOURS = "8-20/2"
DEFAULT_DAYS = "1-5"

DEFAULTS = {
    "LLM_KB_DATA_DIR": "~/.llm-toolkit/kb-data",
    "LLM_KB_TOOLKIT_DIR": "",
    "LLM_KB_CORPUS_DIR": "",
    "LLM_KB_PORT": "8011",
    "LLM_KB_COLLECTION": "llm-toolkit",
    "LLM_KB_MAX_DISTANCE": "0.55",
    "LLM_KB_DUP_DISTANCE": "0.12",
    "LLM_KB_NEAR_DISTANCE": "0.30",
    "LLM_KB_SCAN_SECONDS": "30",
    "LLM_KB_SYNC_SAFE_INDEX": "1",
    "LLM_KB_HARVEST_SESSIONS": "0",
    "LLM_KB_REFRESH_SURFACES": "0",
}

# compose variable -> config key (exact names from the design contract)
COMPOSE_VARS = [
    ("KB_DATA_DIR", "LLM_KB_DATA_DIR"),
    ("KB_CORPUS_DIR", "LLM_KB_CORPUS_DIR"),
    ("KB_PORT", "LLM_KB_PORT"),
    ("KB_COLLECTION", "LLM_KB_COLLECTION"),
    ("KB_MAX_DISTANCE", "LLM_KB_MAX_DISTANCE"),
    ("KB_DUP_DISTANCE", "LLM_KB_DUP_DISTANCE"),
    ("KB_NEAR_DISTANCE", "LLM_KB_NEAR_DISTANCE"),
    ("KB_SCAN_SECONDS", "LLM_KB_SCAN_SECONDS"),
    ("KB_SYNC_SAFE_INDEX", "LLM_KB_SYNC_SAFE_INDEX"),
]
DATA_SUBDIRS = ("chroma", "inbox", "archive", "models", "state")
# plugin catalog cards (mounted read-only as the "plugins" source) and fetched plugins under review
PLUGIN_SUBDIRS = ("plugins/catalog", "plugins/quarantine")
SEARCH_SOURCES = ("repo", "inbox", "plugins", "all")
KNOWLEDGE_SOURCES = ("repo", "inbox")
FALLBACK_EXTENSIONS = {".md", ".txt", ".sh", ".ps1", ".py", ".js", ".json", ".yml", ".yaml", ".toml", ".cmd"}
FALLBACK_SKIP_DIRS = {"node_modules", "__pycache__"}
FALLBACK_SKIP_FILES = {"TASKS_TABLE.md", "CONTEXT_STATE.md", "LLM-STATE.md", "package-lock.json"}


class KBError(Exception):
    """User-facing setup error (exit 2)."""


class ServiceUnavailable(Exception):
    """The KB service could not be reached."""


# --------------------------------------------------------------------------- utils

def toolkit_root() -> Path:
    return Path(__file__).resolve().parents[1]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(value: str) -> datetime:
    text = str(value).strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        dt = datetime.strptime(text[:10], "%Y-%m-%d")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def posix_abs(p) -> str:
    return Path(os.path.expanduser(str(p))).resolve().as_posix()


def out(text: str = "") -> None:
    print(text)


def err(text: str) -> None:
    print(text, file=sys.stderr)


def sleep(seconds) -> None:
    """Indirection so tests never really wait."""
    time.sleep(seconds)


def run_cmd(cmd, **kwargs):
    """The single place that executes external commands (patched in tests).

    Every command has a timeout (a timeout is reported as return code 124) and git never prompts.
    """
    cmd = list(cmd)
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)
    kwargs.setdefault("encoding", "utf-8")
    kwargs.setdefault("errors", "replace")
    kwargs.setdefault("timeout", TIMEOUT_DEFAULT)
    if cmd and Path(str(cmd[0])).name in ("git", "git.exe"):
        env = dict(kwargs.get("env") or os.environ)
        env["GIT_TERMINAL_PROMPT"] = "0"
        kwargs["env"] = env
    try:
        return subprocess.run(cmd, **kwargs)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, 124, "", f"timed out after {kwargs['timeout']}s")
    except OSError as exc:
        return subprocess.CompletedProcess(cmd, 127, "", str(exc))


# --------------------------------------------------------------------------- config

def env_file_path(environ=None) -> Path:
    environ = os.environ if environ is None else environ
    custom = environ.get("LLM_KB_ENV_FILE")
    if custom:
        return Path(os.path.expanduser(custom))
    return Path.home() / ".llm-toolkit" / "kb.env"


def parse_env_text(text: str) -> dict:
    values = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        if key:
            values[key] = val
    return values


def read_env_file(path: Path) -> dict:
    try:
        return parse_env_text(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def update_env_file(path: Path, updates: dict) -> None:
    """Set keys in place, keep every other line (comments, unknown keys) untouched."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    pending = dict(updates)
    result = []
    for raw in lines:
        stripped = raw.strip()
        key = None
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].replace("export ", "", 1).strip()
        if key in pending:
            result.append(f"{key}={pending.pop(key)}")
        else:
            result.append(raw)
    for key, val in pending.items():
        result.append(f"{key}={val}")
    path.write_text("\n".join(result) + "\n", encoding="utf-8")


def load_config(environ=None) -> dict:
    """Defaults < env file < process env. Directory values are made absolute."""
    environ = os.environ if environ is None else environ
    cfg = dict(DEFAULTS)
    cfg.update({k: v for k, v in read_env_file(env_file_path(environ)).items() if k.startswith("LLM_KB_")})
    cfg.update({k: v for k, v in environ.items() if k.startswith("LLM_KB_") and k != "LLM_KB_ENV_FILE"})
    if not cfg["LLM_KB_TOOLKIT_DIR"]:
        cfg["LLM_KB_TOOLKIT_DIR"] = toolkit_root().as_posix()
    if not cfg["LLM_KB_CORPUS_DIR"]:
        cfg["LLM_KB_CORPUS_DIR"] = cfg["LLM_KB_TOOLKIT_DIR"]
    for key in ("LLM_KB_DATA_DIR", "LLM_KB_TOOLKIT_DIR", "LLM_KB_CORPUS_DIR"):
        cfg[key] = posix_abs(cfg[key])
    return cfg


def data_dir(cfg) -> Path:
    return Path(cfg["LLM_KB_DATA_DIR"])


def truthy(value) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def render_compose_env(cfg) -> str:
    lines = ["# generated by scripts/kb.py - do not edit"]
    for compose_name, key in COMPOSE_VARS:
        val = cfg[key]
        if key in ("LLM_KB_DATA_DIR", "LLM_KB_CORPUS_DIR"):
            val = posix_abs(val)
        lines.append(f"{compose_name}={val}")
    return "\n".join(lines) + "\n"


def write_compose_env(cfg) -> Path:
    state = data_dir(cfg) / "state"
    if not state.is_dir():
        raise KBError("data folder missing, run init")
    target = state / "compose.env"
    target.write_text(render_compose_env(cfg), encoding="utf-8")
    return target


def compose_command(cfg, *args) -> list:
    """Build (never execute) a docker compose invocation."""
    toolkit = Path(cfg["LLM_KB_TOOLKIT_DIR"])
    env_file = Path(cfg["LLM_KB_DATA_DIR"]) / "state" / "compose.env"
    return [
        "docker", "compose", "-p", PROJECT,
        "-f", (toolkit / "kb" / "docker-compose.yml").as_posix(),
        "--env-file", env_file.as_posix(),
        *args,
    ]


def run_compose(cfg, *args, **kwargs):
    write_compose_env(cfg)
    return run_cmd(compose_command(cfg, *args), **kwargs)


def corpus_has_content(corpus: Path) -> bool:
    if (corpus / "AGENTS.md").is_file():
        return True
    for root, dirs, names in os.walk(corpus, followlinks=False):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in FALLBACK_SKIP_DIRS]
        for name in names:
            p = Path(root) / name
            if not name.startswith(".") and not p.is_symlink() and p.suffix.lower() in FALLBACK_EXTENSIONS:
                return True
    return False


def ensure_ready(cfg) -> None:
    """Refuse to start/index against a missing data folder or a missing/empty corpus."""
    base = data_dir(cfg)
    if not (base / "chroma").is_dir() or not (base / "state").is_dir():
        raise KBError("data folder missing, run init")
    corpus = Path(cfg["LLM_KB_CORPUS_DIR"])
    if not corpus.is_dir() or not corpus_has_content(corpus):
        raise KBError(f"corpus folder missing or empty (needs AGENTS.md or an indexable file): {corpus.as_posix()}")
    # a data folder made by an older init lacks the plugin catalog; create it here so the
    # container engine never creates the bind source itself (it would belong to another user)
    for sub in PLUGIN_SUBDIRS:
        (base / sub).mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- core module

_CORE = None


def set_core(module) -> None:
    """Inject kb_core (tests) or reset with None."""
    global _CORE
    _CORE = module


def get_core(cfg=None):
    global _CORE
    if _CORE is not None:
        return _CORE
    toolkit = Path((cfg or load_config())["LLM_KB_TOOLKIT_DIR"])
    path = toolkit / "kb" / "service" / "kb_core.py"
    if not path.is_file():
        raise KBError(f"shared module not found: {path}")
    spec = importlib.util.spec_from_file_location("llm_kb_core", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("llm_kb_core", module)
    spec.loader.exec_module(module)
    _CORE = module
    return module


# --------------------------------------------------------------------------- http

def service_url(cfg, path) -> str:
    return f"http://127.0.0.1:{cfg['LLM_KB_PORT']}{path}"


def http_json(cfg, method, path, payload=None, timeout=10):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(service_url(cfg, path), data=data, method=method)
    if method == "POST":
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        raise ServiceUnavailable(f"HTTP {exc.code} from {path}") from exc
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise ServiceUnavailable(str(exc)) from exc


# --------------------------------------------------------------------------- init / stack

def cmd_init(args) -> int:
    if args.toolkit_dir:
        tk = Path(os.path.expanduser(args.toolkit_dir))
        if not (tk / "scripts" / "kb.py").is_file() or not (tk / "kb" / "docker-compose.yml").is_file():
            raise KBError(f"not a toolkit checkout (needs scripts/kb.py and kb/docker-compose.yml): {tk.as_posix()}")
    path = env_file_path()
    current = read_env_file(path)
    updates = {}
    if args.data_dir:
        updates["LLM_KB_DATA_DIR"] = posix_abs(args.data_dir)
    if args.corpus:
        updates["LLM_KB_CORPUS_DIR"] = posix_abs(args.corpus)
    if args.port:
        updates["LLM_KB_PORT"] = str(args.port)
    if args.toolkit_dir:
        updates["LLM_KB_TOOLKIT_DIR"] = posix_abs(args.toolkit_dir)
    if "LLM_KB_DATA_DIR" not in current and "LLM_KB_DATA_DIR" not in updates:
        updates["LLM_KB_DATA_DIR"] = posix_abs(os.environ.get("LLM_KB_DATA_DIR") or DEFAULTS["LLM_KB_DATA_DIR"])
    if "LLM_KB_TOOLKIT_DIR" not in current and "LLM_KB_TOOLKIT_DIR" not in updates:
        updates["LLM_KB_TOOLKIT_DIR"] = toolkit_root().as_posix()
    changed = {k: v for k, v in updates.items() if current.get(k) != v}
    if changed or not path.exists():
        update_env_file(path, changed)
    cfg = load_config()
    base = data_dir(cfg)
    for sub in DATA_SUBDIRS + PLUGIN_SUBDIRS:
        (base / sub).mkdir(parents=True, exist_ok=True)
    compose_env = write_compose_env(cfg)
    out(f"env file: {path}")
    out(f"data dir: {base.as_posix()}")
    out(f"compose env: {compose_env.as_posix()}")
    if args.toolkit_dir:
        reinstall_schedule(cfg)
    return 0


def cmd_up(args) -> int:
    cfg = load_config()
    ensure_ready(cfg)
    cmd = ["up", "-d"] + (["--build"] if args.build else [])
    return run_compose(cfg, *cmd, capture_output=False, timeout=TIMEOUT_COMPOSE_UP).returncode


def cmd_down(args) -> int:
    return run_compose(load_config(), "down", capture_output=False).returncode


def cmd_status(args) -> int:
    cfg = load_config()
    try:
        health = http_json(cfg, "GET", "/health", timeout=5)
    except ServiceUnavailable as exc:
        if args.json:
            out(json.dumps({"service": "down", "error": str(exc)}))
        else:
            out(f"service: down ({exc})")
        return 1
    if args.json:
        out(json.dumps({"service": "up", "health": health}, indent=2))
    else:
        out(f"service: up  collection={health.get('collection')} chunks={health.get('chunks')} "
            f"files={health.get('files')} last_scan={health.get('last_scan')}")
        quarantined = health.get("quarantined") or {}
        if quarantined:
            out(f"quarantined files: {len(quarantined)}")
    return 0


def cmd_index(args) -> int:
    cfg = load_config()
    ensure_ready(cfg)
    extra = ["-e", "KB_ALLOW_MASS_DELETE=1"] if args.allow_mass_delete else []
    return run_compose(cfg, "--profile", "tools", "run", "--rm", "-T", *extra, "ingest", capture_output=False,
                       timeout=TIMEOUT_INGEST).returncode


# --------------------------------------------------------------------------- search

_BASIC_SECRET_RULES = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key)[A-Za-z0-9_-]*\s*[:=]\s*['\"]?[^\s'\"<$]{16,}"),
]


def has_secret(text: str, core=None) -> bool:
    if core is not None and hasattr(core, "find_secrets"):
        return bool(core.find_secrets(text))
    return any(rx.search(text) for rx in _BASIC_SECRET_RULES)


def fallback_search(corpus: Path, query: str, core=None, limit=10) -> list:
    terms = [t for t in re.split(r"\W+", query.lower()) if t]
    results = []
    if not terms:
        return results
    files = []
    if core is not None and hasattr(core, "iter_corpus_files"):
        files = [(rel, Path(ab)) for rel, ab in core.iter_corpus_files(str(corpus))]
    else:
        for root, dirs, names in os.walk(corpus, followlinks=False):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in FALLBACK_SKIP_DIRS]
            for name in names:
                p = Path(root) / name
                if name.startswith(".") or name in FALLBACK_SKIP_FILES or p.is_symlink():
                    continue
                if p.suffix.lower() in FALLBACK_EXTENSIONS:
                    files.append((p.relative_to(corpus).as_posix(), p))
    for rel, path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if has_secret(text, core):
            continue  # same rule as the service: files with secret findings are never shown
        low = text.lower()
        score = sum(1 for t in terms if t in low)
        if not score:
            continue
        excerpt = ""
        for line in text.splitlines():
            if any(t in line.lower() for t in terms):
                excerpt = line.strip()[:300]
                break
        results.append((score, sum(low.count(t) for t in terms), rel, excerpt))
    results.sort(key=lambda r: (-r[0], -r[1], r[2]))
    return [{"path": r[2], "matched_terms": r[0], "excerpt": r[3]} for r in results[:limit]]


def cmd_search(args) -> int:
    cfg = load_config()
    payload = {"q": args.query, "k": args.k}
    if args.kind:
        payload["kind"] = args.kind
    if args.source:
        payload["source"] = args.source
    payload["max_distance"] = args.max_distance if args.max_distance is not None else float(cfg["LLM_KB_MAX_DISTANCE"])
    try:
        hits = http_json(cfg, "POST", "/search", payload).get("hits", [])
    except ServiceUnavailable as exc:
        err(f"service unreachable ({exc}); plain-text fallback over the corpus")
        try:
            core = get_core(cfg)
        except KBError:
            core = None
        root = data_dir(cfg) / "plugins" / "catalog" if args.source == "plugins" else Path(cfg["LLM_KB_CORPUS_DIR"])
        found = fallback_search(root, args.query, core)
        if args.json:
            out(json.dumps({"fallback": True, "hits": found}, indent=2))
        else:
            for item in found:
                out(f"{item['matched_terms']} terms  {item['path']}")
                if item["excerpt"]:
                    out(f"    {item['excerpt']}")
        return 3
    if args.json:
        out(json.dumps({"hits": hits}, indent=2))
        return 0
    for hit in hits:
        heading = hit.get("heading") or ""
        where = str(hit.get("path"))
        pending = hit.get("source") == "inbox" or hit.get("status") == "pending"
        if hit.get("source"):
            where = f"{hit['source']}:{where}"
        pointer = f"{where} › {heading}" if heading else where
        out(f"{float(hit.get('distance', 0)):.3f}  {hit.get('kind')}  {pointer}{'  [pending]' if pending else ''}")
        excerpt = " ".join(str(hit.get("text", "")).split())[:300]
        if excerpt:
            out(f"    {excerpt}")
    if not hits:
        out("no hits within the distance cut-off")
    return 0


# --------------------------------------------------------------------------- intake gate

def read_input(source: str) -> str:
    if source == "-":
        return sys.stdin.read()
    return Path(source).read_text(encoding="utf-8")


def scanner_rules(cfg, text: str) -> list:
    """Run the toolkit's surface scanner on the candidate; return rule names only."""
    script = Path(cfg["LLM_KB_TOOLKIT_DIR"]) / "scripts" / "scan-llm-surface-security.py"
    if not script.is_file():
        return []
    with tempfile.TemporaryDirectory(prefix="kb-check-") as tmp:
        target = Path(tmp) / "docs"
        target.mkdir()
        (target / "candidate.md").write_text(text, encoding="utf-8")
        proc = run_cmd([sys.executable, "-I", str(script), "--root", tmp])
    if proc.returncode == 0:
        return []
    rules = []
    for line in (proc.stderr or "").splitlines():
        m = re.match(r"^docs[\\/]candidate\.md:\d+: ([^:\s]+):", line)
        if m and m.group(1) not in rules:
            rules.append(m.group(1))
    return rules or ["surface-scan"]


def suggest_kind(text: str, front: dict) -> str:
    if front.get("kind"):
        return str(front["kind"])
    head = text[:800].lower()
    if "trigger:" in head and "description:" in head:
        return "rule"
    if front.get("name") and front.get("description"):
        return "skill"
    if re.search(r"^#+\s*(steps|procedure|workflow)\b", text, re.I | re.M):
        return "workflow"
    return "learning"


def run_check(cfg, text: str, source=None) -> dict:
    core = get_core(cfg)
    front, _body = core.parse_front_matter(text)
    result = {"exit_code": 0, "verdict": None, "rules": [], "nearest": [], "destination": suggest_kind(text, front or {})}
    rules = list(core.find_secrets(text))
    for rule in scanner_rules(cfg, text):
        if rule not in rules:
            rules.append(rule)
    if rules:
        result.update(exit_code=4, verdict="security", rules=rules)
        return result
    try:
        payload = {"text": text, "k": 3}
        if source:
            payload["source"] = source
        resp = http_json(cfg, "POST", "/dedupe", payload)
    except ServiceUnavailable as exc:
        result.update(exit_code=6, verdict="unreachable", error=str(exc))
        return result
    verdict = resp.get("verdict", "novel")
    result["verdict"] = verdict
    result["nearest"] = resp.get("nearest", [])
    result["exit_code"] = {"novel": 0, "duplicate": 3, "near": 5}.get(verdict, 0)
    return result


def print_check(result: dict, as_json: bool) -> None:
    if as_json:
        out(json.dumps(result, indent=2))
        return
    if result["verdict"] == "security":
        out("security: BLOCKED (nothing was saved). Rules: " + ", ".join(result["rules"]))
        return
    if result["verdict"] == "unreachable":
        out(f"service unreachable: {result.get('error')}")
        return
    out(f"verdict: {result['verdict']}")
    out(f"suggested destination: {result['destination']}")
    for item in result["nearest"]:
        out(f"  {float(item.get('distance', 0)):.3f}  {item.get('source')}:{item.get('path')} › {item.get('heading', '')}")


def cmd_check(args) -> int:
    cfg = load_config()
    result = run_check(cfg, read_input(args.file), args.source)
    print_check(result, args.json)
    return result["exit_code"]


def slugify(title: str) -> str:
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title).strip("-")[:60].strip("-")
    return slug or "note"


def build_inbox_text(title, kind, origin, created, body) -> str:
    return (
        "---\n"
        f"title: {json.dumps(title, ensure_ascii=False)}\n"
        f"kind: {kind}\n"
        f"origin: {json.dumps(origin, ensure_ascii=False)}\n"
        f"created: {created}\n"
        "status: pending\n"
        "---\n\n"
        f"{body.strip()}\n"
    )


def one_line(value: str) -> str:
    return " ".join(str(value).split())


def cmd_add(args) -> int:
    cfg = load_config()
    if args.kind is not None and args.kind not in KINDS:
        raise KBError(f"unknown --kind {one_line(args.kind)[:40]!r}; use one of: {', '.join(KINDS)}")
    inbox = data_dir(cfg) / "inbox"
    if not inbox.is_dir():
        raise KBError("data folder missing, run init")
    text = read_input(args.file)
    result = run_check(cfg, text)
    if result["exit_code"] == 4:
        print_check(result, False)
        err("refused: security findings")
        return 4
    if result["exit_code"] == 6:
        print_check(result, False)
        err("refused: service unreachable, dedupe could not run")
        return 6
    if result["exit_code"] == 3:
        print_check(result, False)
        err("refused: duplicate of existing knowledge")
        return 3
    if result["exit_code"] == 5 and not args.allow_near:
        print_check(result, False)
        err("refused: near match needs a merge decision (use --allow-near to add anyway)")
        return 5
    core = get_core(cfg)
    front, body = core.parse_front_matter(text)
    kind = args.kind or (front or {}).get("kind") or result["destination"]
    if kind not in KINDS:
        raise KBError(f"unknown kind {one_line(kind)[:40]!r}; use one of: {', '.join(KINDS)}")
    title = one_line(args.title)
    origin = one_line(args.origin or (front or {}).get("origin") or "manual")
    now = utcnow()
    rendered = build_inbox_text(title, kind, origin, iso(now), body)
    rules = list(core.find_secrets(rendered))
    if rules:  # title, origin and front matter are gated too, not only the body
        print_check({"verdict": "security", "rules": rules}, False)
        err("refused: security findings in the rendered inbox item")
        return 4
    stem = f"{now.strftime('%Y-%m-%d')}-{slugify(title)}"
    target = inbox / f"{stem}.md"
    n = 2
    while target.exists():
        target = inbox / f"{stem}-{n}.md"
        n += 1
    target.write_text(rendered, encoding="utf-8")
    out(f"added: {target.name} (kind={kind}, status=pending)")
    try:
        http_json(cfg, "POST", "/reindex", {}, timeout=30)
    except ServiceUnavailable:
        pass
    return 0


# --------------------------------------------------------------------------- inbox

def list_inbox(cfg) -> list:
    inbox = data_dir(cfg) / "inbox"
    items = []
    if not inbox.is_dir():
        return items
    core = None
    try:
        core = get_core(cfg)
    except KBError:
        pass
    for path in sorted(inbox.glob("*.md")):
        meta = {}
        if core is not None:
            meta, _ = core.parse_front_matter(path.read_text(encoding="utf-8", errors="replace"))
        items.append({"name": path.name, "title": (meta or {}).get("title", ""), "kind": (meta or {}).get("kind", ""),
                      "created": (meta or {}).get("created", ""), "status": (meta or {}).get("status", "")})
    return items


def archive_items(cfg, names) -> list:
    base = data_dir(cfg)
    archive = base / "archive"
    if not archive.is_dir():
        raise KBError("data folder missing, run init")
    moved = []
    for name in names:
        if Path(name).name != name or name in ("", ".", ".."):
            raise KBError(f"not an inbox item name: {name}")
        src = base / "inbox" / name
        if not src.is_file():
            raise KBError(f"not in inbox: {name}")
        dst = archive / name
        n = 2
        while dst.exists():
            dst = archive / f"{src.stem}-{n}{src.suffix}"
            n += 1
        shutil.move(str(src), str(dst))
        moved.append(dst.name)
    return moved


def cmd_inbox(args) -> int:
    cfg = load_config()
    rest = list(args.args)
    if rest and rest[0] == "archive":
        if len(rest) < 2:
            raise KBError("inbox archive needs at least one item name")
        for name in archive_items(cfg, rest[1:]):
            out(f"archived: {name}")
        return 0
    if rest:
        raise KBError(f"unknown inbox action: {rest[0]}")
    items = list_inbox(cfg)
    if args.json:
        out(json.dumps(items, indent=2))
    else:
        for item in items:
            out(f"{item['name']}  kind={item['kind']}  {item['title']}")
        if not items:
            out("inbox is empty")
    return 0


# --------------------------------------------------------------------------- sync-status

def run_log_path(environ=None) -> Path:
    environ = os.environ if environ is None else environ
    if environ.get("LLM_RUN_LOG"):
        return Path(os.path.expanduser(environ["LLM_RUN_LOG"]))
    return Path.home() / ".llm-toolkit" / "run-log.jsonl"


def record_time(rec: dict):
    for key in ("ts", "timestamp", "time", "created", "date"):
        if rec.get(key):
            try:
                when = parse_iso(rec[key])
            except (ValueError, TypeError):
                return None
            if len(str(rec[key]).strip()) == 10:
                # date-only value: count it as the end of that day so same-day
                # records still count after a same-day watermark
                when = when.replace(hour=23, minute=59, second=59, microsecond=999999)
            return when
    return None


def run_log_since(path: Path, watermark):
    """Return (records newer than watermark, undated count)."""
    records, undated = [], 0
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        return records, undated
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if not isinstance(rec, dict):
            continue
        when = record_time(rec)
        if when is None:
            undated += 1
        elif watermark is None or when > watermark:
            records.append(rec)
    return records, undated


def git_state(corpus: Path, fetch=True) -> dict:
    def git(*a, timeout=30):
        return run_cmd(["git", "-C", str(corpus), *a], timeout=timeout)
    try:
        if git("rev-parse", "--is-inside-work-tree").returncode != 0:
            return {"git": False}
        branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        clean = git("status", "--porcelain", "--untracked-files=no").stdout.strip() == ""
        if fetch:
            git("fetch", "--quiet", timeout=60)
        behind = None
        proc = git("rev-list", "--count", "HEAD..@{u}")
        if proc.returncode == 0:
            behind = int(proc.stdout.strip() or 0)
        return {"git": True, "branch": branch, "clean": clean, "behind": behind}
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        return {"git": False, "error": str(exc)}


def read_watermark(cfg):
    path = data_dir(cfg) / "state" / "sync-state.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8")).get("watermark")
        return parse_iso(value) if value else None
    except (OSError, ValueError):
        return None


def cmd_sync_status(args) -> int:
    started = utcnow()  # taken before anything is read, so a later --mark cannot skip new records
    if args.mark:
        try:
            parse_iso(args.mark)
        except ValueError:
            raise KBError(f"--mark needs an ISO date or time, got {one_line(args.mark)[:40]!r}")
    cfg = load_config()
    watermark = read_watermark(cfg)
    try:
        health = http_json(cfg, "GET", "/health", timeout=5)
        service = {"up": True, "chunks": health.get("chunks"), "files": health.get("files"),
                   "last_scan": health.get("last_scan"), "quarantined": sorted((health.get("quarantined") or {}).keys())}
    except ServiceUnavailable as exc:
        service = {"up": False, "error": str(exc)}
    records, undated = run_log_since(run_log_path(), watermark)
    report = {
        "service": service,
        "pending_inbox": list_inbox(cfg),
        "watermark": iso(watermark) if watermark else None,
        "run_log": {"new": len(records), "undated": undated, "records": records[-20:]},
        "corpus": git_state(Path(cfg["LLM_KB_CORPUS_DIR"]), fetch=not args.no_fetch),
    }
    if truthy(cfg["LLM_KB_HARVEST_SESSIONS"]):
        since = watermark or parse_iso("1970-01-01")
        report["sessions_changed"] = len(list(session_files(Path(os.path.expanduser("~/.claude/projects")), since)))
    report["now"] = iso(started)
    if args.mark is not None:
        state = data_dir(cfg) / "state"
        if not state.is_dir():
            raise KBError("data folder missing, run init")
        stamp = iso(parse_iso(args.mark)) if args.mark else iso(started)
        (state / "sync-state.json").write_text(json.dumps({"watermark": stamp}) + "\n", encoding="utf-8")
        report["marked"] = stamp
    if args.json:
        out(json.dumps(report, indent=2))
    else:
        out(f"now: {report['now']}")
        out(f"service: {'up' if service['up'] else 'down'}")
        out(f"pending inbox items: {len(report['pending_inbox'])}")
        out(f"run-log records since {report['watermark'] or 'the beginning'}: {len(records)}")
        corpus = report["corpus"]
        if corpus.get("git"):
            out(f"corpus: branch={corpus['branch']} clean={corpus['clean']} behind={corpus['behind']}")
        else:
            out("corpus: not a git checkout")
        if "sessions_changed" in report:
            out(f"session files changed: {report['sessions_changed']}")
    return 0


# --------------------------------------------------------------------------- sessions

def session_files(root: Path, since: datetime):
    if not root.is_dir():
        return
    for path in sorted(root.rglob("*.jsonl")):
        try:
            if path.is_symlink():
                continue
            if datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) >= since:
                yield path
        except OSError:
            continue


def message_text(rec: dict) -> tuple:
    role = rec.get("type") or (rec.get("message") or {}).get("role") or rec.get("role")
    msg = rec.get("message", rec)
    content = msg.get("content") if isinstance(msg, dict) else None
    text = ""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text = "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return role, text.strip()


def digest_session(path: Path, root: Path, core) -> dict:
    first_user, last_assistant = "", ""
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if not isinstance(rec, dict):
                continue
            role, text = message_text(rec)
            if not text:
                continue
            if role == "user" and not first_user and not text.startswith("<"):
                first_user = text
            elif role == "assistant":
                last_assistant = text
    try:
        project = path.relative_to(root).parts[0]
    except (ValueError, IndexError):
        project = path.parent.name
    return {
        "project": project,
        "session": path.stem,
        "first_prompt": core.mask_secrets(first_user)[:200],
        "last_assistant": core.mask_secrets(last_assistant)[:600],
    }


def cmd_sessions(args) -> int:
    cfg = load_config()
    if not (truthy(cfg["LLM_KB_HARVEST_SESSIONS"]) or args.force):
        err("refused: session harvesting is opt-in (set LLM_KB_HARVEST_SESSIONS=1 or pass --force)")
        return 2
    core = get_core(cfg)
    root = Path(os.path.expanduser(args.root)) if args.root else Path.home() / ".claude" / "projects"
    digests = [digest_session(p, root, core) for p in session_files(root, parse_iso(args.since))]
    if args.json:
        out(json.dumps(digests, indent=2, ensure_ascii=False))
    else:
        for d in digests:
            out(f"[{d['project']}] {d['session']}")
            out(f"  prompt: {d['first_prompt']}")
            out(f"  result: {d['last_assistant']}")
        if not digests:
            out("no session files changed since the given time")
    return 0


# --------------------------------------------------------------------------- scheduler (pure generators)

def parse_field(spec: str, lo: int, hi: int) -> list:
    """Parse cron-style 'a', 'a-b', 'a-b/s', 'a,b' lists into sorted ints."""
    values = set()
    for part in str(spec).split(","):
        part = part.strip()
        step = 1
        if "/" in part:
            part, _, s = part.partition("/")
            step = int(s)
        if part in ("", "*"):
            a, b = lo, hi
        elif "-" in part:
            x, _, y = part.partition("-")
            a, b = int(x), int(y)
        else:
            a = b = int(part)
        if step < 1 or a > b or a < lo or b > hi:
            raise KBError(f"invalid schedule field: {spec}")
        values.update(range(a, b + 1, step))
    return sorted(values)


def scheduler_command(cfg=None) -> list:
    """Command the scheduler runs: this interpreter and the configured toolkit's kb.py."""
    toolkit = Path((cfg or load_config())["LLM_KB_TOOLKIT_DIR"])
    return [sys.executable, str(toolkit / "scripts" / "kb.py"), "scheduled-run"]


EXTRA_PATH_DIRS = ("~/.docker/bin", "/usr/local/bin", "/opt/homebrew/bin")


def world_writable(path) -> bool:
    try:
        return bool(os.stat(path).st_mode & 0o002)
    except OSError:
        return False


def build_path(current=None, exists=None) -> str:
    """Install-time PATH plus the usual docker locations: only absolute, existing, not world-writable
    directories, de-duplicated, order kept."""
    exists = exists or os.path.isdir
    current = os.environ.get("PATH", "") if current is None else current
    parts = [p for p in current.split(os.pathsep) if p]
    for extra in EXTRA_PATH_DIRS:
        expanded = os.path.expanduser(extra)
        if exists(expanded):
            parts.append(expanded)
    seen, result = set(), []
    for part in parts:
        if not os.path.isabs(part) or not exists(part) or world_writable(part):
            continue
        if part not in seen:
            seen.add(part)
            result.append(part)
    return os.pathsep.join(result)


def scheduler_env(path_value=None) -> dict:
    """Environment baked into scheduler entries (PATH, and the env-file override when set)."""
    env = {"PATH": path_value if path_value is not None else build_path()}
    if os.environ.get("LLM_KB_ENV_FILE"):
        env["LLM_KB_ENV_FILE"] = os.path.abspath(os.path.expanduser(os.environ["LLM_KB_ENV_FILE"]))
    return env


def make_cron_line(hours: str, days: str, command: list, env=None) -> str:
    parse_field(hours, 0, 23)
    parse_field(days, 0, 7)
    env = scheduler_env() if env is None else env
    assigns = " ".join(f"{k}={shlex.quote(v)}" for k, v in env.items())
    body = f"{assigns} {' '.join(shlex.quote(c) for c in command)}".strip().replace("%", "\\%")
    return f"0 {hours} * * {days} {body} {CRON_MARKER}"


def make_launchd_plist(hours: str, days: str, command: list, log_path: str, env=None) -> dict:
    intervals = [{"Weekday": d % 7, "Hour": h, "Minute": 0}
                 for d in parse_field(days, 0, 7) for h in parse_field(hours, 0, 23)]
    return {
        "Label": LAUNCHD_LABEL,
        "ProgramArguments": list(command),
        "EnvironmentVariables": scheduler_env() if env is None else dict(env),
        "StartCalendarInterval": intervals,
        "StandardOutPath": log_path,
        "StandardErrorPath": log_path,
    }


WIN_DAYS = {0: "SUN", 1: "MON", 2: "TUE", 3: "WED", 4: "THU", 5: "FRI", 6: "SAT", 7: "SUN"}


def make_schtasks_args(hours: str, days: str, command: list) -> list:
    """Return a list of schtasks /Create argument lists (one task, or one per hour)."""
    hrs = parse_field(hours, 0, 23)
    day_names = []
    for d in parse_field(days, 0, 7):
        name = WIN_DAYS[d]
        if name not in day_names:
            day_names.append(name)
    tr = subprocess.list2cmdline(command)
    base = ["/Create", "/F", "/SC", "WEEKLY", "/D", ",".join(day_names)]
    steps = {b - a for a, b in zip(hrs, hrs[1:])}
    if len(hrs) == 1 or len(steps) == 1:
        step = steps.pop() if steps else 1
        args = base + ["/TN", WIN_TASK, "/TR", tr, "/ST", f"{hrs[0]:02d}:00"]
        if len(hrs) > 1:
            span = (hrs[-1] - hrs[0]) * 60 + 1
            args += ["/RI", str(step * 60), "/DU", f"{span // 60:04d}:{span % 60:02d}"]
        return [args]
    return [base + ["/TN", f"{WIN_TASK}-{h:02d}", "/TR", tr, "/ST", f"{h:02d}:00"] for h in hrs]


def detect_os() -> str:
    return platform.system()


def launchd_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"


def cron_edit(current: str, line=None) -> str:
    """Drop our marked line(s) from crontab text; append `line` when given."""
    kept = [l for l in current.splitlines() if CRON_MARKER not in l]
    if line:
        kept.append(line)
    return "\n".join(kept) + "\n" if kept else ""


def read_crontab() -> str:
    proc = run_cmd(["crontab", "-l"])
    return proc.stdout if proc.returncode == 0 else ""


def schedule_log_path(cfg) -> str:
    return (data_dir(cfg) / "state" / "schedule.out.log").as_posix()


def parse_win_tasks(csv_text: str) -> list:
    """Task names of ours from `schtasks /Query /FO CSV /NH` output (any hours, exact prefix match)."""
    import csv
    names = []
    for row in csv.reader(io.StringIO(csv_text or "")):
        if not row:
            continue
        name = row[0].lstrip("\\")
        if (name == WIN_TASK or name.startswith(WIN_TASK + "-")) and name not in names:
            names.append(name)
    return names


def win_existing_tasks() -> list:
    proc = run_cmd(["schtasks", "/Query", "/FO", "CSV", "/NH"])
    return parse_win_tasks(proc.stdout) if proc.returncode == 0 else []


def schedule_install(cfg, hours, days) -> int:
    system = detect_os()
    command = scheduler_command(cfg)
    parse_field(hours, 0, 23)
    parse_field(days, 0, 7)
    if system == "Darwin":
        plist_path = launchd_path()
        domain = f"gui/{os.getuid()}"
        plist_path.parent.mkdir(parents=True, exist_ok=True)
        with plist_path.open("wb") as fh:
            plistlib.dump(make_launchd_plist(hours, days, command, schedule_log_path(cfg)), fh)
        run_cmd(["launchctl", "bootout", f"{domain}/{LAUNCHD_LABEL}"])
        rc = run_cmd(["launchctl", "bootstrap", domain, str(plist_path)]).returncode
        out(f"installed {LAUNCHD_LABEL} ({plist_path})")
        return rc
    if system == "Windows":
        for name in win_existing_tasks():  # no stray tasks when the hours pattern changes
            run_cmd(["schtasks", "/Delete", "/TN", name, "/F"])
        for task in make_schtasks_args(hours, days, command):
            rc = run_cmd(["schtasks", *task]).returncode
            if rc:
                return rc
        out(f"installed {WIN_TASK}")
        return 0
    new = cron_edit(read_crontab(), make_cron_line(hours, days, command))
    proc = run_cmd(["crontab", "-"], input=new)
    out("installed crontab entry" if proc.returncode == 0 else f"crontab failed: {proc.stderr}")
    return proc.returncode


def schedule_remove() -> int:
    system = detect_os()
    if system == "Darwin":
        run_cmd(["launchctl", "bootout", f"gui/{os.getuid()}/{LAUNCHD_LABEL}"])
        if launchd_path().is_file():
            launchd_path().unlink()  # our own plist only
        out(f"removed {LAUNCHD_LABEL}")
        return 0
    if system == "Windows":
        for name in win_existing_tasks():
            run_cmd(["schtasks", "/Delete", "/TN", name, "/F"])
        out(f"removed {WIN_TASK}")
        return 0
    current = read_crontab()
    new = cron_edit(current)
    proc = run_cmd(["crontab", "-"], input=new) if new != current else None
    out("removed crontab entry")
    return proc.returncode if proc else 0


def schedule_state():
    """None when not installed, else {'hours': str|None, 'days': str|None} read back from the entry."""
    system = detect_os()
    if system == "Darwin":
        path = launchd_path()
        if not path.is_file():
            return None
        try:
            ivs = plistlib.loads(path.read_bytes()).get("StartCalendarInterval", [])
            hours = ",".join(str(h) for h in sorted({i["Hour"] for i in ivs}))
            days = ",".join(str(d) for d in sorted({i["Weekday"] for i in ivs}))
            return {"hours": hours or None, "days": days or None}
        except (OSError, ValueError, KeyError, plistlib.InvalidFileException):
            return {"hours": None, "days": None}
    if system == "Windows":
        return {"hours": None, "days": None} if win_existing_tasks() else None
    for line in read_crontab().splitlines():
        if CRON_MARKER in line:
            fields = line.split()
            return {"hours": fields[1], "days": fields[4]} if len(fields) > 5 else {"hours": None, "days": None}
    return None


def reinstall_schedule(cfg) -> None:
    """After the toolkit dir moved: re-register an existing entry so it points at the new checkout."""
    state = schedule_state()
    if state is None:
        return
    schedule_install(cfg, state["hours"] or DEFAULT_HOURS, state["days"] or DEFAULT_DAYS)
    out("scheduler entry re-installed for the new toolkit directory")


def cmd_schedule(args) -> int:
    cfg = load_config()
    if args.action == "install":
        return schedule_install(cfg, args.hours, args.days)
    if args.action == "remove":
        return schedule_remove()
    state = schedule_state()
    out(f"scheduler entry: {'installed' if state is not None else 'not installed'}")
    return 0 if state is not None else 1


# --------------------------------------------------------------------------- surfaces refresh

def surfaces_command(corpus, windows: bool, apply: bool = True) -> list:
    """Pure: installer command from the corpus checkout itself. Never contains the force option."""
    if windows:
        from pathlib import PureWindowsPath
        root = PureWindowsPath(str(corpus))
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
               str(root / "scripts" / "install-global-surfaces.ps1")]
        if apply:
            cmd.append("-Apply")
        return cmd + ["-ToolkitRoot", str(root)]
    root = Path(str(corpus))
    cmd = ["bash", (root / "scripts" / "install-global-surfaces.sh").as_posix()]
    if apply:
        cmd.append("--apply")
    return cmd + ["--toolkit-root", root.as_posix()]


def surfaces_blocked_rows(output: str) -> int:
    """Count `blocked` rows in the installer's table (TOOL  SURFACE  ACTION  DETAIL, two-space separated)."""
    count = 0
    for line in (output or "").splitlines():
        cols = re.split(r"\s{2,}", line.strip())
        if len(cols) >= 3 and cols[2] == "blocked":
            count += 1
    return count


def classify_surfaces(returncode: int, output: str):
    """('refreshed'|'partial'|'failed', blocked_count)."""
    if returncode == 0:
        return "refreshed", 0
    blocked = surfaces_blocked_rows(output)
    m = re.search(r"Done with (\d+) blocked path", output or "")
    if returncode not in (124, 127) and blocked >= 1 and m and int(m.group(1)) == blocked:
        return "partial", blocked
    return "failed", blocked


def corpus_head(corpus):
    proc = git_run(corpus, "rev-parse", "HEAD")
    head = proc.stdout.strip() if proc.returncode == 0 else ""
    return head or None


def surfaces_head_file(cfg) -> Path:
    return data_dir(cfg) / "state" / "surfaces-head"


def read_surfaces_head(cfg):
    try:
        return surfaces_head_file(cfg).read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def surfaces_due(cfg):
    """(due, recorded, current). Not due when the corpus has no readable HEAD."""
    current = corpus_head(cfg["LLM_KB_CORPUS_DIR"])
    recorded = read_surfaces_head(cfg)
    return (current is not None and current != recorded), recorded, current


def do_surfaces_refresh(cfg, apply=True):
    """Run the corpus checkout's installer. Returns (outcome, blocked, output); raises KBError (exit 2)."""
    if not (data_dir(cfg) / "state").is_dir():
        raise KBError("data folder missing, run init")
    corpus = Path(cfg["LLM_KB_CORPUS_DIR"])
    windows = detect_os() == "Windows"
    script = corpus / "scripts" / ("install-global-surfaces.ps1" if windows else "install-global-surfaces.sh")
    if not script.is_file():
        raise KBError(f"installer not found: {script.as_posix()}")
    proc = run_cmd(surfaces_command(corpus, windows, apply), timeout=TIMEOUT_SURFACES)
    output = (proc.stdout or "") + (proc.stderr or "")
    outcome, blocked = classify_surfaces(proc.returncode, output)
    if apply and outcome in ("refreshed", "partial"):
        head = corpus_head(corpus)
        if head:
            surfaces_head_file(cfg).write_text(head + "\n", encoding="utf-8")
    return outcome, blocked, output


def cmd_surfaces(args) -> int:
    cfg = load_config()
    if args.action == "status":
        due, recorded, current = surfaces_due(cfg)
        out(f"recorded HEAD: {recorded or 'none'}")
        out(f"corpus HEAD: {current or 'unknown'}")
        out("refresh: due" if due else "refresh: up to date")
        return 0
    outcome, blocked, output = do_surfaces_refresh(cfg, apply=not args.dry_run)
    if args.dry_run:
        out(output.rstrip())
        out("dry run: no state written")
        return 0 if outcome == "refreshed" else 1
    if outcome == "refreshed":
        out("surfaces refreshed")
        return 0
    if outcome == "partial":
        out(f"surfaces partial ({blocked} blocked): blocked paths are left as they are; the HEAD is recorded")
        return 0
    err(output.rstrip()[-2000:])
    out("surfaces refresh failed")
    return 1


# --------------------------------------------------------------------------- scheduled-run

def git_run(corpus, *args):
    return run_cmd(["git", "-C", str(corpus), *args], timeout=TIMEOUT_GIT)


def default_branch(corpus: Path):
    proc = git_run(corpus, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if proc.returncode == 0 and proc.stdout.strip():
        return proc.stdout.strip().split("/", 1)[-1]
    return None


def can_fast_forward(corpus: Path):
    """(ok, reason): only on the default branch with no modified tracked files.

    Untracked paths (for example a linked worktree) are ignored: `git pull --ff-only`
    itself refuses if an incoming commit would overwrite one.
    """
    if git_run(corpus, "rev-parse", "--is-inside-work-tree").returncode != 0:
        return False, "not a git checkout"
    branch = git_run(corpus, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    default = default_branch(corpus)
    allowed = {default} if default else {"main", "master"}
    if branch not in allowed:
        return False, f"on branch {branch}, not the default branch"
    if git_run(corpus, "status", "--porcelain", "--untracked-files=no").stdout.strip():
        return False, "working tree not clean"
    return True, "ok"


def docker_app_present() -> bool:
    return any(Path(p).expanduser().exists() for p in ("/Applications/Docker.app", "~/Applications/Docker.app"))


def docker_ready():
    """(ok, note). Starts the desktop app on macOS when the daemon is down; waits up to 180 s."""
    if run_cmd(["docker", "info"], timeout=30).returncode == 0:
        return True, "docker ready"
    if detect_os() == "Darwin" and docker_app_present():
        run_cmd(["open", "-ga", "Docker"], timeout=30)
        for _ in range(DOCKER_WAIT_SECONDS // WAIT_INTERVAL):
            sleep(WAIT_INTERVAL)
            if run_cmd(["docker", "info"], timeout=30).returncode == 0:
                return True, "docker started"
        return False, f"docker did not start within {DOCKER_WAIT_SECONDS}s"
    return False, "docker not running"


def append_schedule_log(cfg, line: str) -> None:
    state = data_dir(cfg) / "state"
    if state.is_dir():
        with (state / "schedule.log").open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")


def cmd_scheduled_run(args) -> int:
    cfg = load_config()
    try:
        ensure_ready(cfg)
    except KBError as exc:
        append_schedule_log(cfg, f"{iso(utcnow())} refused {exc}")
        raise
    notes = []
    status = "ok"
    try:
        ready, note = docker_ready()
        if not ready:
            raise RuntimeError(note)
        notes.append(note)
        up = run_compose(cfg, "up", "-d", timeout=TIMEOUT_COMPOSE_UP)
        if up.returncode:
            raise RuntimeError("stack start failed")
        notes.append("stack up")
        ok, reason = can_fast_forward(Path(cfg["LLM_KB_CORPUS_DIR"]))
        if ok:
            pull = git_run(cfg["LLM_KB_CORPUS_DIR"], "pull", "--ff-only")
            notes.append("pull ok" if pull.returncode == 0 else "pull failed")
        else:
            notes.append(f"pull skipped ({reason})")
        if truthy(cfg["LLM_KB_REFRESH_SURFACES"]):
            try:
                due, _, _ = surfaces_due(cfg)
                if due:
                    outcome, blocked, _ = do_surfaces_refresh(cfg)
                    notes.append({"refreshed": "surfaces refreshed",
                                  "partial": f"surfaces partial ({blocked} blocked)"}.get(outcome, "surfaces refresh failed"))
            except (KBError, OSError):
                notes.append("surfaces refresh failed")
        idx = run_compose(cfg, "--profile", "tools", "run", "--rm", "-T", "ingest", timeout=TIMEOUT_INGEST)
        if idx.returncode:
            raise RuntimeError("index failed")
        notes.append("index ok")
    except (RuntimeError, OSError) as exc:
        status = "error"
        notes.append(str(exc))
    line = f"{iso(utcnow())} {status} {'; '.join(notes)}"
    append_schedule_log(cfg, line)
    out(line)
    return 0 if status == "ok" else 1


# --------------------------------------------------------------------------- hook

def hook_command(port) -> str:
    return f"{HOOK_PREFIX}{port}{HOOK_SUFFIX}"


def is_own_hook(entry) -> bool:
    """Recognises the current command and the earlier form without -f / Content-Type."""
    cmd = entry.get("command", "") if isinstance(entry, dict) else ""
    return (isinstance(cmd, str) and cmd.endswith(HOOK_SUFFIX)
            and (cmd.startswith(HOOK_PREFIX) or cmd.startswith(HOOK_PREFIX_OLD)))


def settings_path(args) -> Path:
    if args.settings:
        return Path(os.path.expanduser(args.settings))
    return Path.home() / ".claude" / "settings.json"


def load_settings(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise KBError(f"settings file is not valid JSON, refusing to edit: {path} ({exc})")
    if not isinstance(data, dict):
        raise KBError(f"settings file is not a JSON object: {path}")
    return data


def backup_file(path: Path) -> Path:
    stamp = utcnow().strftime("%Y%m%dT%H%M%S%fZ")
    target = path.with_name(f"{path.name}.bak-{stamp}")
    shutil.copy2(path, target)
    return target


def hook_install(settings: dict, command: str) -> dict:
    hooks = settings.setdefault("hooks", {})
    groups = hooks.setdefault("UserPromptSubmit", [])
    for group in groups:
        for entry in group.get("hooks", []) if isinstance(group, dict) else []:
            if is_own_hook(entry):
                entry["command"] = command
                return settings
    groups.append({"hooks": [{"type": "command", "command": command}]})
    return settings


def hook_remove(settings: dict) -> bool:
    groups = settings.get("hooks", {}).get("UserPromptSubmit") if isinstance(settings.get("hooks"), dict) else None
    if not isinstance(groups, list):
        return False
    changed = False
    for group in list(groups):
        if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
            continue
        kept = [e for e in group["hooks"] if not is_own_hook(e)]
        if len(kept) != len(group["hooks"]):
            changed = True
            group["hooks"] = kept
            if not kept and set(group.keys()) <= {"hooks", "matcher"}:
                groups.remove(group)
    if changed and not groups:
        del settings["hooks"]["UserPromptSubmit"]
        if not settings["hooks"]:
            del settings["hooks"]
    return changed


def cmd_hook(args) -> int:
    cfg = load_config()
    path = settings_path(args)
    settings = load_settings(path)
    if args.action == "status":
        groups = (settings.get("hooks") or {}).get("UserPromptSubmit") or []
        present = any(is_own_hook(e) for g in groups if isinstance(g, dict) for e in g.get("hooks", []))
        out(f"hook: {'installed' if present else 'not installed'} ({path})")
        return 0 if present else 1
    if args.action == "install":
        if path.exists():
            out(f"backup: {backup_file(path)}")
        hook_install(settings, hook_command(cfg["LLM_KB_PORT"]))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        out(f"hook installed in {path}")
        return 0
    if not path.exists():
        out("nothing to remove")
        return 0
    backup = backup_file(path)
    if hook_remove(settings):
        path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        out(f"hook removed from {path} (backup: {backup})")
    else:
        backup.unlink()
        out("hook was not installed")
    return 0


# --------------------------------------------------------------------------- doctor

def wait_for_health(cfg) -> bool:
    for _ in range(HEALTH_WAIT_SECONDS // WAIT_INTERVAL):
        try:
            http_json(cfg, "GET", "/health", timeout=3)
            return True
        except ServiceUnavailable:
            sleep(WAIT_INTERVAL)
    return False


def doctor_deep(cfg, report) -> None:
    """Restart chroma and the service, wait for health, read stored vectors back, run one search."""
    try:
        ensure_ready(cfg)
    except KBError as exc:
        report("deep: preconditions", False, str(exc))
        return
    proc = run_compose(cfg, "restart", "chroma", "service", timeout=TIMEOUT_COMPOSE_UP)
    report("deep: restart chroma and service", proc.returncode == 0, (proc.stderr or "").strip()[:80])
    if proc.returncode != 0:
        return
    healthy = wait_for_health(cfg)
    report("deep: service healthy after restart", healthy)
    if not healthy:
        return
    try:
        res = http_json(cfg, "POST", "/verify", {}, timeout=120)
        report("deep: stored vectors read back", bool(res.get("ok")),
               f"checked={res.get('checked')} chunks={res.get('chunks')} {res.get('detail', '')}"[:100])
    except ServiceUnavailable as exc:
        report("deep: stored vectors read back", False, str(exc))
    try:
        hits = http_json(cfg, "POST", "/search", {"q": "knowledge base", "k": 1,
                                                  "max_distance": 2.0}, timeout=60).get("hits", [])
        report("deep: search answers", bool(hits), f"{len(hits)} hit(s)")
    except ServiceUnavailable as exc:
        report("deep: search answers", False, str(exc))


def cmd_doctor(args) -> int:
    cfg = load_config()
    problems = 0

    def report(label, ok, detail=""):
        nonlocal problems
        problems += 0 if ok else 1
        out(f"{'ok  ' if ok else 'FAIL'} {label}{(' - ' + detail) if detail else ''}")

    report("docker on PATH", shutil.which("docker") is not None)
    if shutil.which("docker"):
        proc = run_cmd(["docker", "compose", "version"])
        report("docker compose", proc.returncode == 0, (proc.stdout or proc.stderr).strip()[:80])
    base = data_dir(cfg)
    report("data folder", all((base / s).is_dir() for s in DATA_SUBDIRS), base.as_posix())
    report("compose file", (Path(cfg["LLM_KB_TOOLKIT_DIR"]) / "kb" / "docker-compose.yml").is_file())
    try:
        health = http_json(cfg, "GET", "/health", timeout=3)
        report("service health", True, f"{health.get('chunks')} chunks")
    except ServiceUnavailable as exc:
        report("service health", False, str(exc))
    if args.deep:
        doctor_deep(cfg, report)
    return 0 if problems == 0 else 1


# --------------------------------------------------------------------------- argparse

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="kb.py", description="Toolkit knowledge base command-line tool.")
    sub = p.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    s = sub.add_parser("init", help="create the data folder and kb.env (idempotent)")
    s.add_argument("--data-dir")
    s.add_argument("--corpus")
    s.add_argument("--port", type=int)
    s.add_argument("--toolkit-dir", help="re-point the toolkit checkout (re-installs an existing scheduler entry)")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("up", help="start the stack")
    s.add_argument("--build", action="store_true")
    s.set_defaults(func=cmd_up)

    s = sub.add_parser("down", help="stop the stack")
    s.set_defaults(func=cmd_down)

    s = sub.add_parser("status", help="service status")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("index", help="full re-index")
    s.add_argument("--allow-mass-delete", action="store_true",
                   help="lift the 50%% deletion guard for this one run (never the zero-files rule)")
    s.set_defaults(func=cmd_index)

    s = sub.add_parser("search", help="semantic search (plain-text fallback exits 3)")
    s.add_argument("query")
    s.add_argument("-k", type=int, default=5)
    s.add_argument("--kind")
    s.add_argument("--source", choices=SEARCH_SOURCES,
                   help="default: knowledge sources (repo and inbox); plugins = capability cards; all = everything")
    s.add_argument("--max-distance", type=float)
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_search)

    s = sub.add_parser("check", help="intake gate: secrets, security scan, dedupe")
    s.add_argument("file", help="file path or - for stdin")
    s.add_argument("--source", choices=KNOWLEDGE_SOURCES,
                   help="only compare against this source (default: repo and inbox; plugin cards never count)")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_check)

    s = sub.add_parser("add", help="gate, then write a pending inbox item")
    s.add_argument("file", help="file path or - for stdin")
    s.add_argument("--title", required=True)
    s.add_argument("--kind")
    s.add_argument("--origin")
    s.add_argument("--allow-near", action="store_true")
    s.set_defaults(func=cmd_add)

    s = sub.add_parser("inbox", help="list pending items; 'inbox archive <name>...' moves items to archive/")
    s.add_argument("args", nargs="*")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_inbox)

    s = sub.add_parser("sync-status", help="one-call summary for the scheduled sync")
    s.add_argument("--json", action="store_true")
    s.add_argument("--mark", nargs="?", const="", default=None, metavar="ISO",
                   help="store the watermark (default: the time this run started)")
    s.add_argument("--no-fetch", action="store_true", help="skip git fetch")
    s.set_defaults(func=cmd_sync_status)

    s = sub.add_parser("sessions", help="opt-in digest of local session transcripts (stdout only)")
    s.add_argument("--since", required=True)
    s.add_argument("--root")
    s.add_argument("--json", action="store_true")
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_sessions)

    s = sub.add_parser("schedule", help="install, remove or show the OS scheduler entry")
    s.add_argument("action", choices=["install", "remove", "status"])
    s.add_argument("--hours", default=DEFAULT_HOURS)
    s.add_argument("--days", default=DEFAULT_DAYS)
    s.set_defaults(func=cmd_schedule)

    s = sub.add_parser("scheduled-run", help="what the scheduler runs")
    s.set_defaults(func=cmd_scheduled_run)

    s = sub.add_parser("hook", help="opt-in prompt hook in agent-CLI settings")
    s.add_argument("action", choices=["install", "remove", "status"])
    s.add_argument("--settings")
    s.set_defaults(func=cmd_hook)

    s = sub.add_parser("surfaces", help="refresh the toolkit's global tool surfaces (skills, agents, instruction block)")
    s.add_argument("action", choices=["refresh", "status"])
    s.add_argument("--dry-run", action="store_true", help="refresh: show the installer plan, change and record nothing")
    s.set_defaults(func=cmd_surfaces)

    s = sub.add_parser("doctor", help="check docker, data folder, service")
    s.add_argument("--deep", action="store_true",
                   help="restart chroma and service, wait for health, verify stored vectors, run a search")
    s.set_defaults(func=cmd_doctor)
    return p


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args) or 0)
    except KBError as exc:
        err(f"error: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
