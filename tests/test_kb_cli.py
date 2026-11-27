"""Tests for scripts/kb.py (no Docker, no outside network)."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import plistlib
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("kb_cli_under_test", REPO / "scripts" / "kb.py")
kb = importlib.util.module_from_spec(SPEC)
sys.modules["kb_cli_under_test"] = kb
SPEC.loader.exec_module(kb)

AWS_KEY = "AKIA" + "ABCDEFGHIJKLMNOP"  # assembled so the test file itself holds no literal key


class StubCore:
    """Minimal stand-in for kb/service/kb_core.py (the contract subset kb.py uses)."""

    INDEXED_EXTENSIONS = {".md", ".txt"}
    _RULES = [("aws-access-key-id", re.compile(r"AKIA[0-9A-Z]{16}")),
              ("secret-assignment", re.compile(r"(?i)password\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"))]

    @classmethod
    def find_secrets(cls, text):
        return [name for name, rx in cls._RULES if rx.search(text)]

    @classmethod
    def mask_secrets(cls, text):
        for name, rx in cls._RULES:
            text = rx.sub(f"[REDACTED:{name}]", text)
        return text

    @staticmethod
    def parse_front_matter(text):
        m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
        if not m:
            return {}, text
        meta = {}
        for line in m.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip().strip('"')
        return meta, m.group(2)

    @staticmethod
    def iter_corpus_files(root):
        for p in sorted(Path(root).rglob("*.md")):
            yield p.relative_to(root).as_posix(), str(p)


class FakeService:
    """Local HTTP server on an ephemeral 127.0.0.1 port."""

    def __init__(self, dedupe_verdict="novel", hits=None, verify_ok=True):
        self.dedupe_verdict = dedupe_verdict
        self.verify_ok = verify_ok
        self.hits = hits
        self.requests = []
        self.headers = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, payload):
                body = json.dumps(payload).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                outer.headers.append(("GET", self.path, dict(self.headers)))
                outer.requests.append(("GET", self.path, None))
                self._send({"collection": "t", "chunks": 7, "files": 2, "last_scan": "x", "quarantined": {}})

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(length) or b"{}")
                outer.requests.append(("POST", self.path, payload))
                outer.headers.append(("POST", self.path, dict(self.headers)))
                if self.path == "/verify":
                    self._send({"ok": outer.verify_ok, "chunks": 7, "checked": 3, "detail": "x"})
                elif self.path == "/search" and outer.hits is not None:
                    self._send({"hits": outer.hits})
                elif self.path == "/search":
                    self._send({"hits": [{"source": "repo", "path": "rules/a.md", "kind": "rule", "title": "A",
                                          "heading": "Intro", "chunk": 0, "chunks": 1, "distance": 0.2,
                                          "text": "alpha text"}]})
                elif self.path == "/dedupe":
                    self._send({"verdict": outer.dedupe_verdict,
                                "nearest": [{"source": "repo", "path": "rules/a.md", "heading": "Intro", "distance": 0.1}]})
                else:
                    self._send({"indexed": []})

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


def free_port():
    import socket
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class KBTestCase(unittest.TestCase):
    LAYOUT = True  # create the data-folder layout like `init` would (only init creates folders)

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name).resolve()
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.data = self.tmp / "data"
        self.corpus = self.tmp / "corpus"
        self.corpus.mkdir()
        env = {k: v for k, v in os.environ.items() if not k.startswith("LLM_KB_") and k != "LLM_RUN_LOG"}
        env.update({"HOME": str(self.home), "USERPROFILE": str(self.home),
                    "LLM_KB_ENV_FILE": str(self.tmp / "kb.env"),
                    "LLM_KB_DATA_DIR": str(self.data), "LLM_KB_CORPUS_DIR": str(self.corpus),
                    "LLM_RUN_LOG": str(self.tmp / "run-log.jsonl")})
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._tmp.cleanup)
        kb.set_core(StubCore)
        self.addCleanup(kb.set_core, None)
        # No test may really wait or depend on what is installed on the machine running it:
        # on a machine with the container desktop app present, the start-and-wait loop would
        # otherwise sleep for real. Tests that exercise the loop patch these two again.
        for name, replacement in (("sleep", lambda seconds: None), ("docker_app_present", lambda: False)):
            default = mock.patch.object(kb, name, replacement)
            default.start()
            self.addCleanup(default.stop)
        if self.LAYOUT:
            for sub in kb.DATA_SUBDIRS:
                (self.data / sub).mkdir(parents=True)

    def make_corpus(self):
        (self.corpus / "AGENTS.md").write_text("# agents\n")

    def run_main(self, *argv, stdin=None):
        buf, ebuf = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(ebuf):
            if stdin is not None:
                with mock.patch.object(sys, "stdin", io.StringIO(stdin)):
                    rc = kb.main(list(argv))
            else:
                rc = kb.main(list(argv))
        return rc, buf.getvalue(), ebuf.getvalue()

    def use_service(self, svc):
        os.environ["LLM_KB_PORT"] = str(svc.port)


class HelpTests(unittest.TestCase):
    COMMANDS = ["init", "up", "down", "status", "index", "search", "check", "add", "inbox", "sync-status",
                "sessions", "schedule", "scheduled-run", "hook", "doctor"]

    def test_help_exits_zero_for_all(self):
        for argv in [["--help"]] + [[c, "--help"] for c in self.COMMANDS]:
            with self.subTest(argv=argv), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as cm:
                    kb.main(argv)
                self.assertEqual(cm.exception.code, 0)

    def test_cli_process_help(self):
        proc = subprocess.run([sys.executable, str(REPO / "scripts" / "kb.py"), "--help"],
                              capture_output=True, text=True, cwd=tempfile.gettempdir())
        self.assertEqual(proc.returncode, 0)


class EnvFileTests(KBTestCase):
    def test_parse(self):
        got = kb.parse_env_text("# c\n\nA=1\nexport B = two \nC=\"q x\"\nbad line\n")
        self.assertEqual(got, {"A": "1", "B": "two", "C": "q x"})

    def test_merge_precedence_process_over_file_over_default(self):
        (self.tmp / "kb.env").write_text("LLM_KB_PORT=9001\nLLM_KB_COLLECTION=fromfile\n")
        cfg = kb.load_config()
        self.assertEqual(cfg["LLM_KB_PORT"], "9001")
        self.assertEqual(cfg["LLM_KB_SCAN_SECONDS"], "30")  # default
        os.environ["LLM_KB_PORT"] = "9100"
        cfg = kb.load_config()
        self.assertEqual(cfg["LLM_KB_PORT"], "9100")  # process wins
        self.assertEqual(cfg["LLM_KB_COLLECTION"], "fromfile")

    def test_env_file_relocation(self):
        other = self.tmp / "elsewhere.env"
        other.write_text("LLM_KB_COLLECTION=moved\n")
        os.environ["LLM_KB_ENV_FILE"] = str(other)
        self.assertEqual(kb.load_config()["LLM_KB_COLLECTION"], "moved")

    def test_default_env_path_uses_home(self):
        del os.environ["LLM_KB_ENV_FILE"]
        self.assertEqual(kb.env_file_path(), self.home / ".llm-toolkit" / "kb.env")

    def test_toolkit_default_is_repo_and_corpus_follows(self):
        del os.environ["LLM_KB_CORPUS_DIR"]
        cfg = kb.load_config()
        self.assertEqual(cfg["LLM_KB_TOOLKIT_DIR"], REPO.resolve().as_posix())
        self.assertEqual(cfg["LLM_KB_CORPUS_DIR"], cfg["LLM_KB_TOOLKIT_DIR"])


class InitTests(KBTestCase):
    LAYOUT = False

    def setUp(self):
        super().setUp()
        # init must read its own env file, not the process-level data dir override
        for key in ("LLM_KB_DATA_DIR", "LLM_KB_CORPUS_DIR"):
            os.environ.pop(key)

    def test_init_creates_layout_and_is_idempotent_and_preserves_keys(self):
        envf = self.tmp / "kb.env"
        envf.write_text("# keep me\nLLM_KB_COLLECTION=custom\nUNRELATED=1\n")
        rc, _, _ = self.run_main("init", "--data-dir", str(self.data), "--corpus", str(self.corpus), "--port", "9011")
        self.assertEqual(rc, 0)
        for sub in kb.DATA_SUBDIRS:
            self.assertTrue((self.data / sub).is_dir())
        first = envf.read_text()
        self.assertIn("# keep me", first)
        self.assertIn("LLM_KB_COLLECTION=custom", first)
        self.assertIn("UNRELATED=1", first)
        self.assertIn("LLM_KB_PORT=9011", first)
        rc, _, _ = self.run_main("init")  # no flags: nothing may change
        self.assertEqual(rc, 0)
        self.assertEqual(envf.read_text(), first)
        rc, _, _ = self.run_main("init", "--port", "9022")
        self.assertIn("LLM_KB_PORT=9022", envf.read_text())
        self.assertIn("LLM_KB_COLLECTION=custom", envf.read_text())
        self.assertEqual(envf.read_text().count("LLM_KB_PORT="), 1)

    def test_compose_env_rendering(self):
        self.run_main("init", "--data-dir", str(self.data), "--corpus", str(self.corpus), "--port", "9011")
        text = (self.data / "state" / "compose.env").read_text()
        keys = [l.split("=", 1)[0] for l in text.splitlines() if l and not l.startswith("#")]
        self.assertEqual(keys, ["KB_DATA_DIR", "KB_CORPUS_DIR", "KB_PORT", "KB_COLLECTION",
                                "KB_MAX_DISTANCE", "KB_DUP_DISTANCE", "KB_NEAR_DISTANCE", "KB_SCAN_SECONDS",
                                "KB_SYNC_SAFE_INDEX"])
        vals = dict(l.split("=", 1) for l in text.splitlines() if l and not l.startswith("#"))
        self.assertEqual(vals["KB_DATA_DIR"], self.data.as_posix())
        self.assertEqual(vals["KB_CORPUS_DIR"], self.corpus.as_posix())
        self.assertEqual(vals["KB_PORT"], "9011")
        self.assertNotIn("\\", text)
        self.assertTrue(Path(vals["KB_DATA_DIR"]).is_absolute())


class ComposeCommandTests(KBTestCase):
    def test_command_shape(self):
        cfg = kb.load_config()
        cmd = kb.compose_command(cfg, "up", "-d")
        toolkit = Path(cfg["LLM_KB_TOOLKIT_DIR"])
        self.assertEqual(cmd[:7], ["docker", "compose", "-p", "llm-toolkit-kb", "-f",
                                   (toolkit / "kb" / "docker-compose.yml").as_posix(), "--env-file"])
        self.assertEqual(cmd[7], (self.data / "state" / "compose.env").as_posix())
        self.assertEqual(cmd[8:], ["up", "-d"])

    def test_up_down_index_go_through_builder(self):
        calls = []

        def fake(cmd, **kw):
            calls.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 0, "", "")

        self.make_corpus()
        with mock.patch.object(kb, "run_cmd", fake):
            self.run_main("up", "--build")
            self.run_main("down")
            self.run_main("index")
        self.assertEqual(calls[0][-3:], ["up", "-d", "--build"])
        self.assertEqual(calls[1][-1], "down")
        self.assertEqual(calls[2][-6:], ["--profile", "tools", "run", "--rm", "-T", "ingest"][-6:])
        self.assertTrue(all(c[:4] == ["docker", "compose", "-p", "llm-toolkit-kb"] for c in calls))


class SearchTests(KBTestCase):
    def test_search_via_service(self):
        with FakeService() as svc:
            self.use_service(svc)
            rc, text, _ = self.run_main("search", "alpha", "-k", "3", "--kind", "rule")
            payload = [r for r in svc.requests if r[1] == "/search"][0][2]
        self.assertEqual(rc, 0)
        self.assertEqual(payload["k"], 3)
        self.assertEqual(payload["kind"], "rule")
        self.assertEqual(payload["max_distance"], 0.55)
        self.assertIn("0.200  rule  repo:rules/a.md › Intro", text)
        self.assertIn("alpha text", text)

    def test_fallback_exit_3_when_service_down(self):
        (self.corpus / "a.md").write_text("The quick brown fox\njumps over\n")
        (self.corpus / "b.md").write_text("nothing relevant\n")
        os.environ["LLM_KB_PORT"] = str(free_port())
        rc, text, err = self.run_main("search", "quick fox")
        self.assertEqual(rc, 3)
        self.assertIn("a.md", text)
        self.assertNotIn("b.md", text)
        self.assertIn("unreachable", err)

    def test_fallback_without_core_module(self):
        kb.set_core(None)
        (self.corpus / "x.txt").write_text("needle here\n")
        (self.corpus / ".hidden").mkdir()
        (self.corpus / ".hidden" / "y.md").write_text("needle\n")
        os.environ["LLM_KB_TOOLKIT_DIR"] = str(self.tmp / "no-toolkit")
        os.environ["LLM_KB_PORT"] = str(free_port())
        rc, text, _ = self.run_main("search", "needle")
        self.assertEqual(rc, 3)
        self.assertIn("x.txt", text)
        self.assertNotIn("y.md", text)


class CheckTests(KBTestCase):
    def check(self, text, verdict="novel", up=True):
        if not up:
            os.environ["LLM_KB_PORT"] = str(free_port())
            return self.run_main("check", "-", stdin=text)
        with FakeService(verdict) as svc:
            self.use_service(svc)
            return self.run_main("check", "-", stdin=text)

    def test_exit_codes(self):
        self.assertEqual(self.check("A harmless note.\n", "novel")[0], 0)
        self.assertEqual(self.check("A harmless note.\n", "duplicate")[0], 3)
        self.assertEqual(self.check("A harmless note.\n", "near")[0], 5)
        self.assertEqual(self.check("A harmless note.\n", up=False)[0], 6)

    def test_security_hit_exit_4_rule_names_only(self):
        rc, text, err = self.check(f"key {AWS_KEY} here\n")
        self.assertEqual(rc, 4)
        self.assertIn("aws-access-key-id", text)
        self.assertNotIn(AWS_KEY, text + err)

    def test_security_checked_before_service(self):
        rc, _, _ = self.check(f"key {AWS_KEY}\n", up=False)
        self.assertEqual(rc, 4)

    def test_json_output(self):
        with FakeService("near") as svc:
            self.use_service(svc)
            rc, text, _ = self.run_main("check", "-", "--json", stdin="note\n")
        self.assertEqual(rc, 5)
        data = json.loads(text)
        self.assertEqual(data["verdict"], "near")
        self.assertEqual(data["exit_code"], 5)

    def test_surface_scanner_findings_block(self):
        fake_toolkit = self.tmp / "tk"
        (fake_toolkit / "scripts").mkdir(parents=True)
        (fake_toolkit / "scripts" / "scan-llm-surface-security.py").write_text(
            "import sys\nprint('docs/candidate.md:3: ignore-instructions: msg: SECRET LINE', file=sys.stderr)\nsys.exit(1)\n")
        os.environ["LLM_KB_TOOLKIT_DIR"] = str(fake_toolkit)
        rc, text, err = self.check("anything\n")
        self.assertEqual(rc, 4)
        self.assertIn("ignore-instructions", text)
        self.assertNotIn("SECRET LINE", text + err)


class AddTests(KBTestCase):
    def add(self, text, verdict="novel", *extra):
        with FakeService(verdict) as svc:
            self.use_service(svc)
            return self.run_main("add", "-", "--title", "My Great: Note!", *extra, stdin=text)

    def test_add_writes_front_matter_and_slug(self):
        rc, text, _ = self.add("Body text.\n")
        self.assertEqual(rc, 0, text)
        files = list((self.data / "inbox").glob("*.md"))
        self.assertEqual(len(files), 1)
        self.assertRegex(files[0].name, r"^\d{4}-\d{2}-\d{2}-my-great-note\.md$")
        content = files[0].read_text()
        meta, body = StubCore.parse_front_matter(content)
        self.assertEqual(meta["title"], "My Great: Note!")
        self.assertEqual(meta["kind"], "learning")
        self.assertEqual(meta["status"], "pending")
        self.assertEqual(meta["origin"], "manual")
        self.assertRegex(meta["created"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        self.assertIn("Body text.", body)

    def test_add_kind_origin_and_same_slug_gets_suffix(self):
        self.add("One.\n", "novel", "--kind", "rule", "--origin", "session")
        self.add("Two.\n")
        names = sorted(p.name for p in (self.data / "inbox").glob("*.md"))
        self.assertEqual(len(names), 2)
        first = [n for n in names if not n.endswith("-2.md")]
        self.assertEqual(len(first), 1)
        meta, _ = StubCore.parse_front_matter((self.data / "inbox" / first[0]).read_text())
        self.assertEqual(meta["kind"], "rule")
        self.assertEqual(meta["origin"], "session")

    def test_refusals(self):
        self.assertEqual(self.add("x\n", "duplicate")[0], 3)
        self.assertEqual(self.add("x\n", "near")[0], 5)
        self.assertEqual(self.add(f"{AWS_KEY}\n")[0], 4)
        self.assertFalse(list((self.data / "inbox").glob("*.md")))
        rc, _, _ = self.add("x\n", "near", "--allow-near")
        self.assertEqual(rc, 0)
        self.assertEqual(len(list((self.data / "inbox").glob("*.md"))), 1)

    def test_secret_text_never_printed_or_written(self):
        rc, text, err = self.add(f"leak {AWS_KEY}\n")
        self.assertNotIn(AWS_KEY, text + err)
        self.assertFalse((self.data / "inbox").exists() and list((self.data / "inbox").iterdir()))

    def test_slugify(self):
        self.assertEqual(kb.slugify("  Ação -- Test_Case 1 "), "acao-test-case-1")
        self.assertEqual(kb.slugify("!!!"), "note")
        self.assertLessEqual(len(kb.slugify("a" * 200)), 60)


class InboxTests(KBTestCase):
    def test_list_and_archive_moves_not_deletes(self):
        inbox = self.data / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        (inbox / "2026-01-01-a.md").write_text('---\ntitle: "A"\nkind: rule\n---\nbody\n')
        (inbox / "2026-01-01-b.md").write_text("---\ntitle: B\n---\nbody\n")
        rc, text, _ = self.run_main("inbox", "--json")
        self.assertEqual([i["name"] for i in json.loads(text)], ["2026-01-01-a.md", "2026-01-01-b.md"])
        rc, _, _ = self.run_main("inbox", "archive", "2026-01-01-a.md")
        self.assertEqual(rc, 0)
        self.assertFalse((inbox / "2026-01-01-a.md").exists())
        self.assertTrue((self.data / "archive" / "2026-01-01-a.md").is_file())
        self.assertTrue((inbox / "2026-01-01-b.md").is_file())

    def test_archive_collision_keeps_both(self):
        inbox, archive = self.data / "inbox", self.data / "archive"
        inbox.mkdir(parents=True, exist_ok=True)
        archive.mkdir(parents=True, exist_ok=True)
        (archive / "n.md").write_text("old")
        (inbox / "n.md").write_text("new")
        self.run_main("inbox", "archive", "n.md")
        self.assertEqual((archive / "n.md").read_text(), "old")
        self.assertEqual((archive / "n-2.md").read_text(), "new")

    def test_archive_rejects_paths(self):
        (self.data / "inbox").mkdir(parents=True, exist_ok=True)
        outside = self.data / "keep.md"
        outside.write_text("x")
        rc, _, err = self.run_main("inbox", "archive", "../keep.md")
        self.assertEqual(rc, 2)
        self.assertTrue(outside.exists())


class SyncStatusTests(KBTestCase):
    def write_log(self, rows):
        Path(os.environ["LLM_RUN_LOG"]).write_text("\n".join(json.dumps(r) if isinstance(r, dict) else r for r in rows) + "\n")

    def test_run_log_watermark_logic(self):
        self.write_log([{"ts": "2026-01-01T10:00:00Z", "n": 1}, {"ts": "2026-01-02T10:00:00Z", "n": 2},
                        {"n": 3}, "not json", {"ts": "2026-01-03T10:00:00Z", "n": 4}])
        recs, undated = kb.run_log_since(Path(os.environ["LLM_RUN_LOG"]), None)
        self.assertEqual([r["n"] for r in recs], [1, 2, 4])
        self.assertEqual(undated, 1)
        recs, _ = kb.run_log_since(Path(os.environ["LLM_RUN_LOG"]), kb.parse_iso("2026-01-02T10:00:00Z"))
        self.assertEqual([r["n"] for r in recs], [4])  # strictly newer
        self.assertEqual(kb.run_log_since(self.tmp / "missing.jsonl", None), ([], 0))

    def test_sync_status_mark_persists_watermark(self):
        self.write_log([{"ts": "2026-01-01T10:00:00Z"}])
        with FakeService() as svc:
            self.use_service(svc)
            rc, text, _ = self.run_main("sync-status", "--json", "--no-fetch", "--mark")
            data = json.loads(text)
            self.assertEqual(rc, 0)
            self.assertTrue(data["service"]["up"])
            self.assertEqual(data["run_log"]["new"], 1)
            self.assertIsNone(data["watermark"])
            state = json.loads((self.data / "state" / "sync-state.json").read_text())
            self.assertRegex(state["watermark"], r"^\d{4}-")
            rc, text, _ = self.run_main("sync-status", "--json", "--no-fetch")
            data = json.loads(text)
        self.assertEqual(data["run_log"]["new"], 0)
        self.assertEqual(data["watermark"], state["watermark"])
        self.assertFalse(data["corpus"]["git"])

    def test_service_down_reported(self):
        os.environ["LLM_KB_PORT"] = str(free_port())
        rc, text, _ = self.run_main("sync-status", "--json", "--no-fetch")
        self.assertEqual(rc, 0)
        self.assertFalse(json.loads(text)["service"]["up"])


class SessionsTests(KBTestCase):
    def make_root(self):
        root = self.tmp / "projects"
        proj = root / "-some-project"
        proj.mkdir(parents=True)
        rows = [
            {"type": "user", "message": {"role": "user", "content": f"Please fix this. key {AWS_KEY}"}},
            {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "working"}]}},
            {"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "text", "text": "Done. password=" + "Abcdefgh12345678XYZ"}, {"type": "tool_use", "name": "x"}]}},
        ]
        (proj / "sess-1.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        return root

    def test_refuses_without_opt_in(self):
        root = self.make_root()
        rc, text, err = self.run_main("sessions", "--since", "2000-01-01", "--root", str(root))
        self.assertEqual(rc, 2)
        self.assertEqual(text, "")
        self.assertIn("opt-in", err)

    def test_digest_redacts_and_writes_nothing(self):
        root = self.make_root()
        before = sorted(p.as_posix() for p in self.tmp.rglob("*"))
        rc, text, err = self.run_main("sessions", "--since", "2000-01-01", "--root", str(root), "--force", "--json")
        self.assertEqual(rc, 0, err)
        self.assertNotIn(AWS_KEY, text)
        self.assertNotIn("Abcdefgh12345678XYZ", text)
        data = json.loads(text)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["project"], "-some-project")
        self.assertEqual(data[0]["session"], "sess-1")
        self.assertIn("[REDACTED:aws-access-key-id]", data[0]["first_prompt"])
        self.assertTrue(data[0]["last_assistant"].startswith("Done."))
        self.assertEqual(before, sorted(p.as_posix() for p in self.tmp.rglob("*")))

    def test_env_opt_in_and_length_limits_and_since_filter(self):
        root = self.make_root()
        long_file = root / "-p2" / "long.jsonl"
        long_file.parent.mkdir()
        rows = [{"type": "user", "message": {"role": "user", "content": "q" * 500}},
                {"type": "assistant", "message": {"role": "assistant", "content": "a" * 900}}]
        long_file.write_text("\n".join(json.dumps(r) for r in rows))
        os.environ["LLM_KB_HARVEST_SESSIONS"] = "1"
        rc, text, _ = self.run_main("sessions", "--since", "2000-01-01", "--root", str(root), "--json")
        self.assertEqual(rc, 0)
        longd = [d for d in json.loads(text) if d["session"] == "long"][0]
        self.assertEqual(len(longd["first_prompt"]), 200)
        self.assertEqual(len(longd["last_assistant"]), 600)
        rc, text, _ = self.run_main("sessions", "--since", "2999-01-01", "--root", str(root), "--json")
        self.assertEqual(json.loads(text), [])


class SchedulerTests(KBTestCase):
    CMD = ["/usr/bin/python3", "/opt/kb/scripts/kb.py", "scheduled-run"]

    def test_parse_field(self):
        self.assertEqual(kb.parse_field("8-20/2", 0, 23), [8, 10, 12, 14, 16, 18, 20])
        self.assertEqual(kb.parse_field("1-5", 0, 7), [1, 2, 3, 4, 5])
        self.assertEqual(kb.parse_field("9,17", 0, 23), [9, 17])
        for bad in ("25", "5-2", "a"):
            with self.assertRaises((kb.KBError, ValueError)):
                kb.parse_field(bad, 0, 23)

    def test_launchd_plist(self):
        plist = kb.make_launchd_plist("8-20/2", "1-5", self.CMD, "/x/log")
        self.assertEqual(plist["Label"], "dev.llm-toolkit.kb-sync")
        ivs = plist["StartCalendarInterval"]
        self.assertEqual(len(ivs), 35)
        self.assertEqual({i["Weekday"] for i in ivs}, {1, 2, 3, 4, 5})
        self.assertEqual({i["Hour"] for i in ivs}, {8, 10, 12, 14, 16, 18, 20})
        self.assertTrue(all(i["Minute"] == 0 for i in ivs))
        self.assertEqual(plist["ProgramArguments"], self.CMD)
        self.assertEqual(plistlib.loads(plistlib.dumps(plist))["Label"], plist["Label"])

    def test_cron_line(self):
        line = kb.make_cron_line("8-20/2", "1-5", self.CMD)
        self.assertTrue(line.startswith("0 8-20/2 * * 1-5 "))
        self.assertTrue(line.endswith(kb.CRON_MARKER))
        self.assertIn("scheduled-run", line)

    def test_cron_edit_only_touches_own_line(self):
        other = "5 4 * * * /bin/backup"
        line = kb.make_cron_line("8-20/2", "1-5", self.CMD)
        installed = kb.cron_edit(other + "\n", line)
        self.assertEqual(installed.splitlines()[0], other)
        self.assertEqual(kb.cron_edit(installed, line).count(kb.CRON_MARKER), 1)  # idempotent
        self.assertEqual(kb.cron_edit(installed), other + "\n")
        self.assertEqual(kb.cron_edit(line + "\n"), "")

    def test_schtasks_uniform_hours(self):
        tasks = kb.make_schtasks_args("8-20/2", "1-5", self.CMD)
        self.assertEqual(len(tasks), 1)
        a = tasks[0]
        self.assertEqual(a[a.index("/TN") + 1], "llm-toolkit-kb-sync")
        self.assertEqual(a[a.index("/SC") + 1], "WEEKLY")
        self.assertEqual(a[a.index("/D") + 1], "MON,TUE,WED,THU,FRI")
        self.assertEqual(a[a.index("/ST") + 1], "08:00")
        self.assertEqual(a[a.index("/RI") + 1], "120")
        self.assertEqual(a[a.index("/DU") + 1], "0012:01")  # 08:00 .. 20:00 inclusive
        self.assertIn("scheduled-run", a[a.index("/TR") + 1])

    def test_schtasks_irregular_hours_one_task_per_hour(self):
        tasks = kb.make_schtasks_args("9,13,20", "1-5", self.CMD)
        self.assertEqual([t[t.index("/ST") + 1] for t in tasks], ["09:00", "13:00", "20:00"])
        self.assertEqual([t[t.index("/TN") + 1] for t in tasks],
                         ["llm-toolkit-kb-sync-09", "llm-toolkit-kb-sync-13", "llm-toolkit-kb-sync-20"])

    def test_generators_are_pure(self):
        with mock.patch.object(kb, "run_cmd", side_effect=AssertionError("must not execute")):
            kb.make_launchd_plist("8-20/2", "1-5", self.CMD, "/l")
            kb.make_cron_line("8-20/2", "1-5", self.CMD)
            kb.make_schtasks_args("8-20/2", "1-5", self.CMD)

    def test_install_remove_linux_uses_crontab_with_fake_runner(self):
        store = {"tab": "0 1 * * * /bin/other\n"}

        def fake(cmd, **kw):
            if cmd[:2] == ["crontab", "-l"]:
                return subprocess.CompletedProcess(cmd, 0, store["tab"], "")
            if cmd[:2] == ["crontab", "-"]:
                store["tab"] = kw["input"]
                return subprocess.CompletedProcess(cmd, 0, "", "")
            raise AssertionError(cmd)

        with mock.patch.object(kb, "run_cmd", fake), mock.patch.object(kb, "detect_os", return_value="Linux"):
            self.assertEqual(self.run_main("schedule", "install")[0], 0)
            self.assertIn("0 8-20/2 * * 1-5 ", store["tab"])
            self.assertIn("/bin/other", store["tab"])
            self.assertEqual(self.run_main("schedule", "status")[0], 0)
            self.assertEqual(self.run_main("schedule", "remove")[0], 0)
            self.assertEqual(store["tab"], "0 1 * * * /bin/other\n")


NEW_HOOK = 'curl -sf --max-time 2 -H "Content-Type: application/json" http://localhost:%s/hook -d @-'
OLD_HOOK = "curl -s --max-time 2 http://localhost:%s/hook -d @-"


class HookTests(KBTestCase):
    def settings(self):
        path = self.tmp / "claude" / "settings.json"
        path.parent.mkdir()
        original = {"model": "x", "permissions": {"allow": ["Bash(ls)"]},
                    "hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": "echo mine"}]}],
                              "Stop": [{"hooks": [{"type": "command", "command": "echo stop"}]}]}}
        path.write_text(json.dumps(original, indent=4))
        return path, original

    def test_install_backup_and_other_entries_untouched(self):
        path, original = self.settings()
        os.environ["LLM_KB_PORT"] = "9011"
        rc, _, _ = self.run_main("hook", "install", "--settings", str(path))
        self.assertEqual(rc, 0)
        backups = list(path.parent.glob("settings.json.bak-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(json.loads(backups[0].read_text()), original)
        data = json.loads(path.read_text())
        cmds = [h["command"] for g in data["hooks"]["UserPromptSubmit"] for h in g["hooks"]]
        self.assertEqual(cmds, ["echo mine", NEW_HOOK % 9011])
        self.assertEqual(data["hooks"]["Stop"], original["hooks"]["Stop"])
        self.assertEqual(data["permissions"], original["permissions"])
        self.assertEqual(self.run_main("hook", "status", "--settings", str(path))[0], 0)

    def test_install_twice_keeps_one_entry_and_updates_port(self):
        path, _ = self.settings()
        os.environ["LLM_KB_PORT"] = "9011"
        self.run_main("hook", "install", "--settings", str(path))
        os.environ["LLM_KB_PORT"] = "9012"
        self.run_main("hook", "install", "--settings", str(path))
        text = path.read_text()
        self.assertEqual(text.count("/hook -d @-"), 1)
        self.assertIn("localhost:9012", text)

    def test_remove_restores_equivalent_settings(self):
        path, original = self.settings()
        self.run_main("hook", "install", "--settings", str(path))
        rc, _, _ = self.run_main("hook", "remove", "--settings", str(path))
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(path.read_text()), original)
        self.assertEqual(self.run_main("hook", "status", "--settings", str(path))[0], 1)

    def test_install_creates_missing_settings_and_remove_prunes_empty(self):
        path = self.tmp / "new" / "settings.json"
        self.assertEqual(self.run_main("hook", "install", "--settings", str(path))[0], 0)
        self.assertFalse(list(path.parent.glob("*.bak-*")))  # nothing to back up
        self.run_main("hook", "remove", "--settings", str(path))
        self.assertEqual(json.loads(path.read_text()), {})

    def test_invalid_json_refused_and_untouched(self):
        path = self.tmp / "bad.json"
        path.write_text("{not json")
        rc, _, err = self.run_main("hook", "install", "--settings", str(path))
        self.assertEqual(rc, 2)
        self.assertEqual(path.read_text(), "{not json")

    def test_remove_when_absent_leaves_no_stray_backup(self):
        path, original = self.settings()
        self.run_main("hook", "remove", "--settings", str(path))
        self.assertEqual(json.loads(path.read_text()), original)
        self.assertFalse(list(path.parent.glob("*.bak-*")))


def git(repo, *args):
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
           "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env, check=True)


@unittest.skipUnless(subprocess.run(["git", "--version"], capture_output=True).returncode == 0, "git missing")
class ScheduledRunTests(KBTestCase):
    def make_repo(self):
        git(self.tmp, "init", "-q", "-b", "main", str(self.corpus))
        (self.corpus / "a.md").write_text("a\n")
        git(self.corpus, "add", "a.md")
        git(self.corpus, "commit", "-q", "-m", "init")

    def run_scheduled(self):
        calls = []

        def fake(cmd, **kw):
            calls.append(list(cmd))
            if cmd[0] == "git":
                real = subprocess.run(cmd, capture_output=True, text=True, **{k: v for k, v in kw.items()
                                                                              if k in ("timeout",)})
                if "pull" in cmd:
                    return subprocess.CompletedProcess(cmd, 0, "", "")  # never really pull in tests
                return real
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with mock.patch.object(kb, "run_cmd", fake):
            rc, text, _ = self.run_main("scheduled-run")
        return rc, text, calls

    def pulls(self, calls):
        return [c for c in calls if c[0] == "git" and "pull" in c]

    def test_pulls_on_default_branch_clean(self):
        self.make_repo()
        rc, text, calls = self.run_scheduled()
        self.assertEqual(rc, 0)
        self.assertEqual(len(self.pulls(calls)), 1)
        self.assertIn("--ff-only", self.pulls(calls)[0])
        self.assertIn("pull ok", text)
        log = (self.data / "state" / "schedule.log").read_text()
        self.assertIn("ok", log)

    def test_no_pull_on_feature_branch(self):
        self.make_repo()
        git(self.corpus, "checkout", "-q", "-b", "feat/x")
        rc, text, calls = self.run_scheduled()
        self.assertEqual(self.pulls(calls), [])
        self.assertIn("pull skipped", text)

    def test_no_pull_on_dirty_tree(self):
        self.make_repo()
        (self.corpus / "a.md").write_text("changed\n")
        rc, text, calls = self.run_scheduled()
        self.assertEqual(self.pulls(calls), [])
        self.assertIn("not clean", text)

    def test_no_pull_outside_git_and_no_other_git_writes(self):
        (self.corpus / "a.md").write_text("a\n")
        rc, text, calls = self.run_scheduled()
        self.assertEqual(self.pulls(calls), [])
        git(self.corpus, "init", "-q", "-b", "main")
        git(self.corpus, "add", "-A")
        git(self.corpus, "commit", "-q", "-m", "init")
        _, _, calls = self.run_scheduled()
        allowed = {"rev-parse", "symbolic-ref", "status", "pull"}
        for c in calls:
            if c[0] == "git":
                self.assertIn(c[3], allowed, c)

    def test_stack_failure_logged_and_nonzero(self):
        self.make_corpus()

        def fail(cmd, **kw):
            return subprocess.CompletedProcess(cmd, 1, "", "boom")

        with mock.patch.object(kb, "run_cmd", fail):
            rc, text, _ = self.run_main("scheduled-run")
        self.assertEqual(rc, 1)
        self.assertIn("error", (self.data / "state" / "schedule.log").read_text())


class DoctorTests(KBTestCase):
    def test_doctor_runs_without_docker(self):
        with mock.patch.object(kb.shutil, "which", return_value=None):
            os.environ["LLM_KB_PORT"] = str(free_port())
            rc, text, _ = self.run_main("doctor")
        self.assertEqual(rc, 1)
        self.assertIn("docker on PATH", text)


@unittest.skipUnless((REPO / "kb" / "service" / "kb_core.py").is_file(), "kb_core.py not present yet")
class RealCoreContractTests(KBTestCase):
    """Run the key flows against the real shared module."""

    def setUp(self):
        super().setUp()
        kb.set_core(None)
        os.environ["LLM_KB_TOOLKIT_DIR"] = str(REPO)

    def test_loads_by_path_and_has_contract(self):
        core = kb.get_core(kb.load_config())
        for name in ("find_secrets", "mask_secrets", "parse_front_matter", "iter_corpus_files"):
            self.assertTrue(hasattr(core, name), name)

    def test_check_blocks_secret_and_add_front_matter(self):
        rc, text, err = self.run_main("check", "-", stdin=f"aws {AWS_KEY}\n")
        self.assertEqual(rc, 4)
        self.assertNotIn(AWS_KEY, text + err)
        with FakeService() as svc:
            self.use_service(svc)
            rc, _, _ = self.run_main("add", "-", "--title", "Real core note", stdin="Plain note body.\n")
        self.assertEqual(rc, 0)
        item = next((self.data / "inbox").glob("*real-core-note.md"))
        meta, _ = kb.get_core().parse_front_matter(item.read_text())
        self.assertEqual(meta.get("status"), "pending")

    def test_sessions_masking_with_real_core(self):
        root = self.tmp / "proj" / "p"
        root.mkdir(parents=True)
        (root / "s.jsonl").write_text(json.dumps({"type": "user", "message": {"role": "user", "content": f"k {AWS_KEY}"}}) + "\n")
        rc, text, _ = self.run_main("sessions", "--since", "2000-01-01", "--root", str(self.tmp / "proj"), "--force", "--json")
        self.assertEqual(rc, 0)
        self.assertNotIn(AWS_KEY, text)


# ---------------------------------------------------------------- iteration 2 (review + refinement contract)

def ok_proc(cmd, **kw):
    return subprocess.CompletedProcess(cmd, 0, "", "")


class NoChromaPortTests(KBTestCase):  # S-M5
    def test_variable_and_flag_are_gone(self):
        self.assertNotIn("CHROMA_PORT", (REPO / "scripts" / "kb.py").read_text())
        self.assertNotIn("LLM_KB_CHROMA_PORT", kb.DEFAULTS)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
            kb.main(["init", "--chroma-port", "1"])
        self.assertEqual(cm.exception.code, 2)
        kb.write_compose_env(kb.load_config())
        self.assertNotIn("CHROMA", (self.data / "state" / "compose.env").read_text())


class ReadinessTests(KBTestCase):  # S-M3, S-M2 (CLI side)
    def calls_for(self, *argv):
        calls = []

        def fake(cmd, **kw):
            calls.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with mock.patch.object(kb, "run_cmd", fake):
            rc, text, err = self.run_main(*argv)
        return rc, err, calls

    def test_missing_data_folder_exit_2_and_nothing_created(self):
        self.make_corpus()
        import shutil
        shutil.rmtree(self.data)
        for argv in (("up",), ("index",), ("scheduled-run",)):
            with self.subTest(argv=argv):
                rc, err, calls = self.calls_for(*argv)
                self.assertEqual(rc, 2)
                self.assertEqual(err.strip(), "error: data folder missing, run init")
                self.assertEqual(calls, [])
                self.assertFalse(self.data.exists())

    def test_missing_chroma_folder_only(self):
        self.make_corpus()
        (self.data / "chroma").rmdir()
        rc, err, _ = self.calls_for("up")
        self.assertEqual(rc, 2)
        self.assertFalse((self.data / "chroma").exists())  # up does not repair it

    def test_corpus_missing_or_empty_exit_2(self):
        import shutil
        for argv in (("up",), ("index",), ("scheduled-run",)):
            with self.subTest(argv=argv, case="empty"):
                rc, err, calls = self.calls_for(*argv)
                self.assertEqual(rc, 2)
                self.assertIn("corpus folder missing or empty", err)
                self.assertEqual(len(err.strip().splitlines()), 1)
                self.assertEqual(calls, [])
        shutil.rmtree(self.corpus)
        rc, err, _ = self.calls_for("index")
        self.assertEqual(rc, 2)
        self.assertIn("corpus folder missing or empty", err)

    def test_indexable_file_is_enough_and_refusal_is_logged(self):
        (self.corpus / "notes.md").write_text("x\n")
        rc, err, calls = self.calls_for("up")
        self.assertEqual(rc, 0)
        self.assertTrue(calls)
        (self.corpus / "notes.md").unlink()
        self.calls_for("scheduled-run")
        self.assertIn("refused", (self.data / "state" / "schedule.log").read_text())

    def test_add_and_archive_do_not_create_folders(self):
        import shutil
        shutil.rmtree(self.data)
        with FakeService() as svc:
            self.use_service(svc)
            rc, _, err = self.run_main("add", "-", "--title", "t", stdin="body\n")
        self.assertEqual(rc, 2)
        self.assertEqual(self.run_main("inbox", "archive", "x.md")[0], 2)
        self.assertFalse(self.data.exists())


class AddRenderedGateTests(KBTestCase):  # S-M1
    def add(self, *argv, text="Harmless body.\n"):
        with FakeService() as svc:
            self.use_service(svc)
            return self.run_main("add", "-", *argv, stdin=text)

    def inbox_files(self):
        return list((self.data / "inbox").iterdir())

    def test_secret_shaped_title_refused_nothing_written(self):
        rc, text, err = self.add("--title", f"key {AWS_KEY}")
        self.assertEqual(rc, 4)
        self.assertNotIn(AWS_KEY, text + err)
        self.assertEqual(self.inbox_files(), [])

    def test_secret_shaped_origin_refused_nothing_written(self):
        rc, text, err = self.add("--title", "ok", "--origin", f"session {AWS_KEY}")
        self.assertEqual(rc, 4)
        self.assertNotIn(AWS_KEY, text + err)
        self.assertEqual(self.inbox_files(), [])

    def test_kind_with_newline_or_unknown_kind_refused(self):
        for kind in ("learning\nstatus: merged", "bogus"):
            with self.subTest(kind=kind):
                rc, _, err = self.add("--title", "ok", "--kind", kind)
                self.assertEqual(rc, 2)
                self.assertEqual(self.inbox_files(), [])
        rc, _, _ = self.add("--title", "ok", "--kind", "workflow")
        self.assertEqual(rc, 0)

    def test_front_matter_kind_is_validated_too(self):
        rc, _, _ = self.add("--title", "ok", text="---\nkind: nonsense\n---\nbody\n")
        self.assertEqual(rc, 2)
        self.assertEqual(self.inbox_files(), [])

    def test_newlines_in_title_and_origin_are_neutralised(self):
        rc, _, _ = self.add("--title", "a\nstatus: merged", "--origin", "x\nkind: rule")
        self.assertEqual(rc, 0)
        content = self.inbox_files()[0].read_text()
        head = content.split("---\n")[1]
        self.assertEqual(sum(1 for l in head.splitlines() if l.startswith("status:")), 1)
        self.assertIn("status: pending", head)
        self.assertEqual(sum(1 for l in head.splitlines() if l.startswith("kind:")), 1)


class HookFormTests(KBTestCase):  # S-L3
    def test_exact_command(self):
        self.assertEqual(kb.hook_command(8011),
                         'curl -sf --max-time 2 -H "Content-Type: application/json" http://localhost:8011/hook -d @-')

    def test_old_form_recognised_by_status_remove_and_upgraded_by_install(self):
        path = self.tmp / "s.json"
        data = {"hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": OLD_HOOK % 8011}]}]}}
        path.write_text(json.dumps(data))
        self.assertEqual(self.run_main("hook", "status", "--settings", str(path))[0], 0)
        self.run_main("hook", "install", "--settings", str(path))
        cmds = [h["command"] for g in json.loads(path.read_text())["hooks"]["UserPromptSubmit"] for h in g["hooks"]]
        self.assertEqual(cmds, [NEW_HOOK % 8011])
        path.write_text(json.dumps(data))
        self.run_main("hook", "remove", "--settings", str(path))
        self.assertEqual(json.loads(path.read_text()), {})


class HttpHeaderTests(KBTestCase):
    def test_post_sends_json_content_type_and_no_origin(self):
        self.make_corpus()
        with FakeService() as svc:
            self.use_service(svc)
            self.run_main("search", "q")
            self.run_main("check", "-", stdin="note\n")
            self.run_main("status")
            posts = [h for h in svc.headers if h[0] == "POST"]
            self.assertTrue(posts)
            for _, _, headers in svc.headers:
                self.assertNotIn("Origin", headers)
            for _, _, headers in posts:
                self.assertEqual(headers.get("Content-Type"), "application/json")


class SchedulerPathTests(KBTestCase):  # D1
    CMD = ["/usr/bin/python3", "/opt/kb/scripts/kb.py", "scheduled-run"]

    def test_build_path_adds_existing_dirs_and_dedupes(self):
        home_docker = os.path.expanduser("~/.docker/bin")
        present = {home_docker, "/usr/local/bin", "/usr/bin", "/bin"}
        # Isolate from the host: some CI runners make /usr/local/bin world-writable.
        with mock.patch.object(kb, "world_writable", return_value=False):
            got = kb.build_path("/usr/bin:/usr/local/bin:/bin", exists=lambda p: p in present)
        self.assertEqual(got.split(os.pathsep), ["/usr/bin", "/usr/local/bin", "/bin", home_docker])
        self.assertNotIn("/opt/homebrew/bin", got)

    def test_build_path_drops_world_writable_dirs(self):
        present = {"/usr/bin", "/shared/bin"}
        with mock.patch.object(kb, "world_writable", side_effect=lambda p: p == "/shared/bin"):
            got = kb.build_path("/usr/bin:/shared/bin", exists=lambda p: p in present)
        self.assertEqual(got.split(os.pathsep), ["/usr/bin"])

    def test_plist_has_environment_path_and_out_log(self):
        env = {"PATH": "/usr/bin:/opt/homebrew/bin"}
        plist = kb.make_launchd_plist("8-20/2", "1-5", self.CMD, kb.schedule_log_path(kb.load_config()), env)
        self.assertEqual(plist["EnvironmentVariables"]["PATH"], "/usr/bin:/opt/homebrew/bin")
        self.assertTrue(plist["StandardOutPath"].endswith("/state/schedule.out.log"))
        self.assertEqual(plist["StandardErrorPath"], plist["StandardOutPath"])

    def test_cron_line_sets_path_inline(self):
        line = kb.make_cron_line("8-20/2", "1-5", self.CMD, {"PATH": "/usr/bin:/opt/homebrew/bin"})
        self.assertTrue(line.startswith("0 8-20/2 * * 1-5 PATH=/usr/bin:/opt/homebrew/bin /usr/bin/python3 "))
        self.assertTrue(line.endswith(kb.CRON_MARKER))

    def test_env_file_override_travels_with_the_entry(self):
        env = kb.scheduler_env("/usr/bin")
        self.assertEqual(env["LLM_KB_ENV_FILE"], str(self.tmp / "kb.env"))

    def test_command_uses_configured_toolkit(self):
        os.environ["LLM_KB_TOOLKIT_DIR"] = str(self.tmp / "other-checkout")
        cmd = kb.scheduler_command(kb.load_config())
        self.assertEqual(cmd[1], (self.tmp / "other-checkout" / "scripts" / "kb.py").as_posix().replace("/", os.sep)
                         if os.sep != "/" else (self.tmp / "other-checkout" / "scripts" / "kb.py").as_posix())


class DockerStartTests(KBTestCase):  # D2
    def runner(self, info_ok_after):
        state = {"info": 0, "calls": []}

        def fake(cmd, **kw):
            state["calls"].append(list(cmd))
            if cmd[:2] == ["docker", "info"]:
                state["info"] += 1
                return subprocess.CompletedProcess(cmd, 0 if state["info"] > info_ok_after else 1, "", "")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        return fake, state

    def test_already_running(self):
        fake, state = self.runner(0)
        with mock.patch.object(kb, "run_cmd", fake):
            self.assertEqual(kb.docker_ready(), (True, "docker ready"))

    def test_macos_starts_desktop_app_and_waits_without_sleeping(self):
        fake, state = self.runner(3)
        slept = []
        with mock.patch.object(kb, "run_cmd", fake), mock.patch.object(kb, "sleep", slept.append), \
                mock.patch.object(kb, "detect_os", return_value="Darwin"), \
                mock.patch.object(kb, "docker_app_present", return_value=True):
            ok, note = kb.docker_ready()
        self.assertTrue(ok)
        self.assertIn(["open", "-ga", "Docker"], state["calls"])
        self.assertEqual(len(slept), 3)

    def test_macos_gives_up_after_180_seconds(self):
        fake, _ = self.runner(10 ** 6)
        slept = []
        with mock.patch.object(kb, "run_cmd", fake), mock.patch.object(kb, "sleep", slept.append), \
                mock.patch.object(kb, "detect_os", return_value="Darwin"), \
                mock.patch.object(kb, "docker_app_present", return_value=True):
            ok, note = kb.docker_ready()
        self.assertFalse(ok)
        self.assertEqual(sum(slept), 180)

    def test_other_systems_log_docker_not_running_and_exit_1(self):
        self.make_corpus()
        fake, state = self.runner(10 ** 6)
        with mock.patch.object(kb, "run_cmd", fake), mock.patch.object(kb, "detect_os", return_value="Linux"):
            rc, text, _ = self.run_main("scheduled-run")
        self.assertEqual(rc, 1)
        self.assertIn("docker not running", text)
        self.assertIn("docker not running", (self.data / "state" / "schedule.log").read_text())
        self.assertNotIn(["open", "-ga", "Docker"], state["calls"])
        self.assertFalse([c for c in state["calls"] if c[:2] == ["docker", "compose"]])


class TimeoutTests(KBTestCase):  # D3
    def test_run_cmd_sets_timeout_and_git_no_prompt(self):
        seen = []

        def fake_run(cmd, **kw):
            seen.append((list(cmd), kw))
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with mock.patch.object(kb.subprocess, "run", fake_run):
            kb.run_cmd(["git", "status"])
            kb.run_cmd(["docker", "info"])
        (gcmd, gkw), (dcmd, dkw) = seen
        self.assertEqual(gkw["env"]["GIT_TERMINAL_PROMPT"], "0")
        self.assertEqual(gkw["timeout"], kb.TIMEOUT_DEFAULT)
        self.assertNotIn("env", dkw)
        self.assertEqual(dkw["timeout"], kb.TIMEOUT_DEFAULT)

    def test_timeout_expiry_becomes_return_code_124(self):
        def boom(cmd, **kw):
            raise subprocess.TimeoutExpired(cmd, kw["timeout"])

        with mock.patch.object(kb.subprocess, "run", boom):
            proc = kb.run_cmd(["sleep", "99"], timeout=1)
        self.assertEqual(proc.returncode, 124)
        self.assertIn("timed out", proc.stderr)

    def test_missing_binary_is_return_code_127(self):
        self.assertEqual(kb.run_cmd(["definitely-not-a-real-binary-xyz"]).returncode, 127)

    @unittest.skipUnless(subprocess.run(["git", "--version"], capture_output=True).returncode == 0, "git missing")
    def test_scheduled_run_passes_per_command_timeouts(self):
        git(self.tmp, "init", "-q", "-b", "main", str(self.corpus))
        (self.corpus / "a.md").write_text("a\n")
        git(self.corpus, "add", "-A")
        git(self.corpus, "commit", "-q", "-m", "i")
        seen = []

        def fake(cmd, **kw):
            seen.append((list(cmd), kw.get("timeout")))
            if cmd[0] == "git":
                if "pull" in cmd:
                    return subprocess.CompletedProcess(cmd, 0, "", "")
                return subprocess.run(cmd, capture_output=True, text=True)
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with mock.patch.object(kb, "run_cmd", fake):
            self.assertEqual(self.run_main("scheduled-run")[0], 0)
        by = lambda pred: [t for c, t in seen if pred(c)]
        self.assertEqual(by(lambda c: "up" in c and c[0] == "docker"), [600])
        self.assertEqual(by(lambda c: "ingest" in c), [1800])
        self.assertEqual(by(lambda c: c[0] == "git" and "pull" in c), [120])


class InitToolkitDirTests(KBTestCase):  # D4
    LAYOUT = False

    def setUp(self):
        super().setUp()
        for key in ("LLM_KB_DATA_DIR", "LLM_KB_CORPUS_DIR"):
            os.environ.pop(key)
        self.other = self.tmp / "other-checkout"
        (self.other / "scripts").mkdir(parents=True)
        (self.other / "kb").mkdir()
        (self.other / "scripts" / "kb.py").write_text("")
        (self.other / "kb" / "docker-compose.yml").write_text("")

    def _no_host_schedule(self):
        # Without this, init --toolkit-dir reads and rewrites the real crontab or
        # Windows scheduled task of whoever runs the tests.
        return mock.patch.object(kb, "schedule_state", lambda: None)

    def test_toolkit_dir_is_repointed_and_others_kept(self):
        (self.tmp / "kb.env").write_text("LLM_KB_COLLECTION=keep\n")
        self.run_main("init", "--data-dir", str(self.data))
        with self._no_host_schedule():
            self.run_main("init", "--toolkit-dir", str(self.other))
        values = kb.read_env_file(self.tmp / "kb.env")
        self.assertEqual(values["LLM_KB_TOOLKIT_DIR"], self.other.as_posix())
        self.assertEqual(values["LLM_KB_COLLECTION"], "keep")
        compose = (self.data / "state" / "compose.env").read_text()
        self.assertNotIn("KB_TOOLKIT", compose)  # the toolkit dir is not a compose variable
        self.assertIn(f"KB_CORPUS_DIR={self.other.as_posix()}", compose)  # corpus defaults to the toolkit checkout

    def test_first_init_honours_toolkit_dir(self):
        with self._no_host_schedule():
            self.run_main("init", "--data-dir", str(self.data), "--toolkit-dir", str(self.other))
        self.assertEqual(kb.read_env_file(self.tmp / "kb.env")["LLM_KB_TOOLKIT_DIR"], self.other.as_posix())

    def test_installed_schedule_is_reinstalled_with_same_times_and_new_path(self):
        old_line = kb.make_cron_line("9,13", "1-3", ["/py", "/old/scripts/kb.py", "scheduled-run"], {"PATH": "/usr/bin"})
        store = {"tab": "0 1 * * * /bin/other\n" + old_line + "\n"}

        def fake(cmd, **kw):
            if cmd[:2] == ["crontab", "-l"]:
                return subprocess.CompletedProcess(cmd, 0, store["tab"], "")
            if cmd[:2] == ["crontab", "-"]:
                store["tab"] = kw["input"]
                return ok_proc(cmd)
            raise AssertionError(cmd)

        with mock.patch.object(kb, "run_cmd", fake), mock.patch.object(kb, "detect_os", return_value="Linux"):
            self.run_main("init", "--data-dir", str(self.data), "--toolkit-dir", str(self.other))
        lines = [l for l in store["tab"].splitlines() if kb.CRON_MARKER in l]
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("0 9,13 * * 1-3 "))
        self.assertIn(self.other.as_posix(), lines[0])
        self.assertNotIn("/old/", lines[0])
        self.assertIn("/bin/other", store["tab"])

    def test_no_scheduler_entry_means_nothing_is_installed(self):
        calls = []

        def fake(cmd, **kw):
            calls.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 1 if cmd[:2] == ["crontab", "-l"] else 0, "", "")

        with mock.patch.object(kb, "run_cmd", fake), mock.patch.object(kb, "detect_os", return_value="Linux"):
            self.run_main("init", "--data-dir", str(self.data), "--toolkit-dir", str(self.other))
        self.assertNotIn(["crontab", "-"], calls)


class DoctorDeepTests(KBTestCase):  # D5
    def run_deep(self, svc=None, compose_rc=0):
        self.make_corpus()
        calls = []
        slept = []

        def fake(cmd, **kw):
            calls.append(list(cmd))
            return subprocess.CompletedProcess(cmd, compose_rc, "", "")

        with mock.patch.object(kb, "run_cmd", fake), mock.patch.object(kb, "sleep", slept.append), \
                mock.patch.object(kb.shutil, "which", return_value="/x/docker"):
            if svc:
                self.use_service(svc)
            else:
                os.environ["LLM_KB_PORT"] = str(free_port())
            rc, text, _ = self.run_main("doctor", "--deep")
        return rc, text, calls, slept

    def test_deep_success_restarts_verifies_and_searches(self):
        with FakeService() as svc:
            rc, text, calls, _ = self.run_deep(svc)
            paths = [r[1] for r in svc.requests]
        self.assertEqual(rc, 0, text)
        self.assertTrue(any(c[-3:] == ["restart", "chroma", "service"] for c in calls))
        self.assertIn("/verify", paths)
        self.assertIn("/search", paths)
        self.assertIn("stored vectors read back", text)

    def test_deep_verify_failure_exit_1(self):
        with FakeService(verify_ok=False) as svc:
            rc, text, _, _ = self.run_deep(svc)
        self.assertEqual(rc, 1)
        self.assertIn("FAIL deep: stored vectors read back", text)

    def test_deep_health_never_returns_exit_1_without_real_sleeping(self):
        rc, text, _, slept = self.run_deep(None)
        self.assertEqual(rc, 1)
        self.assertEqual(sum(slept), 120)
        self.assertIn("FAIL deep: service healthy after restart", text)

    def test_deep_restart_failure_stops_early(self):
        with FakeService() as svc:
            rc, text, _, _ = self.run_deep(svc, compose_rc=1)
            paths = [r[1] for r in svc.requests]
        self.assertEqual(rc, 1)
        self.assertNotIn("/verify", paths)

    def test_plain_doctor_does_not_restart(self):
        calls = []
        with mock.patch.object(kb, "run_cmd", lambda c, **kw: calls.append(list(c)) or ok_proc(c)):
            self.run_main("doctor")
        self.assertFalse([c for c in calls if "restart" in c])


class CheckSourceTests(KBTestCase):
    def test_source_is_passed_to_dedupe(self):
        with FakeService() as svc:
            self.use_service(svc)
            self.run_main("check", "-", "--source", "repo", stdin="note\n")
            self.run_main("check", "-", stdin="note\n")
            payloads = [r[2] for r in svc.requests if r[1] == "/dedupe"]
        self.assertEqual(payloads[0]["source"], "repo")
        self.assertNotIn("source", payloads[1])


class PluginSourceCliTests(KBTestCase):
    """KB changes for plugin capability cards: init folders, --source values, catalog fallback."""

    def test_init_creates_plugin_folders(self):
        rc, _, _ = self.run_main("init")
        self.assertEqual(rc, 0)
        for sub in kb.PLUGIN_SUBDIRS:
            self.assertTrue((self.data / sub).is_dir(), sub)

    def test_ensure_ready_creates_missing_plugin_catalog(self):
        self.make_corpus()
        self.assertFalse((self.data / "plugins" / "catalog").exists())
        kb.ensure_ready(kb.load_config())
        self.assertTrue((self.data / "plugins" / "catalog").is_dir())
        self.assertTrue((self.data / "plugins" / "quarantine").is_dir())

    def test_search_source_values(self):
        with FakeService() as svc:
            self.use_service(svc)
            for value in ("plugins", "all", "repo", "inbox"):
                self.assertEqual(self.run_main("search", "q", "--source", value)[0], 0)
            self.run_main("search", "q")
            payloads = [r[2] for r in svc.requests if r[1] == "/search"]
        self.assertEqual([p.get("source") for p in payloads], ["plugins", "all", "repo", "inbox", None])
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
            kb.main(["search", "q", "--source", "archive"])
        self.assertEqual(cm.exception.code, 2)

    def test_check_never_compares_against_plugin_cards(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
            kb.main(["check", "-", "--source", "plugins"])
        self.assertEqual(cm.exception.code, 2)

    def test_plugins_fallback_reads_the_catalog(self):
        (self.corpus / "AGENTS.md").write_text("needle in the corpus\n")
        card = self.data / "plugins" / "catalog" / "claude-code" / "demo.md"
        card.parent.mkdir(parents=True)
        card.write_text("---\nkind: plugin-capability\n---\n## skill demo:needle\n")
        os.environ["LLM_KB_PORT"] = str(free_port())
        rc, text, _ = self.run_main("search", "needle", "--source", "plugins")
        self.assertEqual(rc, 3)
        self.assertIn("claude-code/demo.md", text)
        self.assertNotIn("AGENTS.md", text)


class SearchPendingTests(KBTestCase):  # S-M4 CLI side
    def test_inbox_hits_marked_pending_with_source(self):
        hits = [{"source": "inbox", "path": "n.md", "kind": "learning", "heading": "H", "distance": 0.3, "text": "t"},
                {"source": "repo", "path": "rules/a.md", "kind": "rule", "heading": "", "distance": 0.1, "text": "t"}]
        with FakeService(hits=hits) as svc:
            self.use_service(svc)
            rc, text, _ = self.run_main("search", "q")
        lines = text.splitlines()
        self.assertIn("inbox:n.md", lines[0])
        self.assertTrue(lines[0].endswith("[pending]"))
        repo_line = [l for l in lines if "repo:rules/a.md" in l][0]
        self.assertNotIn("[pending]", repo_line)


class FallbackSecretTests(KBTestCase):  # S-L1
    def test_files_with_secrets_are_skipped_with_core(self):
        (self.corpus / "clean.md").write_text("needle in a clean file\n")
        (self.corpus / "dirty.md").write_text(f"needle {AWS_KEY}\n")
        os.environ["LLM_KB_PORT"] = str(free_port())
        rc, text, _ = self.run_main("search", "needle")
        self.assertEqual(rc, 3)
        self.assertIn("clean.md", text)
        self.assertNotIn("dirty.md", text)
        self.assertNotIn(AWS_KEY, text)

    def test_files_with_secrets_are_skipped_without_core(self):
        kb.set_core(None)
        os.environ["LLM_KB_TOOLKIT_DIR"] = str(self.tmp / "no-toolkit")
        (self.corpus / "clean.md").write_text("needle clean\n")
        (self.corpus / "dirty.md").write_text(f"needle {AWS_KEY}\n")
        (self.corpus / "pem.txt").write_text("needle\n-----BEGIN RSA PRIVATE KEY-----\n")
        os.environ["LLM_KB_PORT"] = str(free_port())
        rc, text, _ = self.run_main("search", "needle")
        self.assertIn("clean.md", text)
        self.assertNotIn("dirty.md", text)
        self.assertNotIn("pem.txt", text)


class MarkWatermarkTests(KBTestCase):  # S-L4
    def test_now_is_printed_and_mark_uses_run_start_or_given_time(self):
        rc, text, _ = self.run_main("sync-status", "--json", "--no-fetch", "--mark")
        data = json.loads(text)
        self.assertRegex(data["now"], r"^\d{4}-\d{2}-\d{2}T")
        state = json.loads((self.data / "state" / "sync-state.json").read_text())
        self.assertEqual(state["watermark"], data["now"])  # the run start, not the end of the run
        self.assertEqual(data["marked"], data["now"])
        rc, text, _ = self.run_main("sync-status", "--json", "--no-fetch", "--mark", "2026-01-02T03:04:05Z")
        state = json.loads((self.data / "state" / "sync-state.json").read_text())
        self.assertEqual(state["watermark"], "2026-01-02T03:04:05Z")

    def test_no_mark_flag_writes_nothing(self):
        self.run_main("sync-status", "--json", "--no-fetch")
        self.assertFalse((self.data / "state" / "sync-state.json").exists())

    def test_start_time_is_taken_before_reading(self):
        times = iter([kb.parse_iso("2026-05-05T05:05:05Z"), kb.parse_iso("2030-01-01T00:00:00Z")])
        with mock.patch.object(kb, "utcnow", lambda: next(times)):
            rc, text, _ = self.run_main("sync-status", "--json", "--no-fetch", "--mark")
        self.assertEqual(json.loads((self.data / "state" / "sync-state.json").read_text())["watermark"],
                         "2026-05-05T05:05:05Z")


class WindowsTaskTests(KBTestCase):  # S-L5
    CSV = ('"\\llm-toolkit-kb-sync","N/A","Ready"\n"\\llm-toolkit-kb-sync-09","N/A","Ready"\n'
           '"\\llm-toolkit-kb-synced-other","N/A","Ready"\n"\\Other Task","N/A","Ready"\n')

    def test_parse_prefix_match_only(self):
        self.assertEqual(kb.parse_win_tasks(self.CSV), ["llm-toolkit-kb-sync", "llm-toolkit-kb-sync-09"])
        self.assertEqual(kb.parse_win_tasks(""), [])

    def test_remove_and_status_use_existing_tasks_not_hours(self):
        calls = []

        def fake(cmd, **kw):
            calls.append(list(cmd))
            if cmd[:2] == ["schtasks", "/Query"] and "/TN" not in cmd:
                return subprocess.CompletedProcess(cmd, 0, self.CSV, "")
            return ok_proc(cmd)

        with mock.patch.object(kb, "run_cmd", fake), mock.patch.object(kb, "detect_os", return_value="Windows"):
            self.assertEqual(self.run_main("schedule", "status", "--hours", "1-2")[0], 0)
            self.assertEqual(self.run_main("schedule", "remove", "--hours", "1-2")[0], 0)
        deleted = sorted(c[c.index("/TN") + 1] for c in calls if c[:2] == ["schtasks", "/Delete"])
        self.assertEqual(deleted, ["llm-toolkit-kb-sync", "llm-toolkit-kb-sync-09"])

    def test_install_clears_stale_tasks_first(self):
        calls = []

        def fake(cmd, **kw):
            calls.append(list(cmd))
            if cmd[:2] == ["schtasks", "/Query"]:
                return subprocess.CompletedProcess(cmd, 0, self.CSV, "")
            return ok_proc(cmd)

        with mock.patch.object(kb, "run_cmd", fake), mock.patch.object(kb, "detect_os", return_value="Windows"):
            self.run_main("schedule", "install")
        kinds = [c[1] for c in calls if c[0] == "schtasks"]
        self.assertLess(kinds.index("/Delete"), kinds.index("/Create"))


class WrapperTests(unittest.TestCase):  # S-L6 and shellcheck SC1007
    def test_ps1_tries_py_launcher_before_python_before_python3(self):
        text = (REPO / "scripts" / "kb.ps1").read_text()
        order = [text.index("py -3"), text.index("& python $script"), text.index("& python3 $script")]
        self.assertEqual(order, sorted(order))

    def test_sh_has_no_empty_assignment_before_cd(self):
        text = (REPO / "scripts" / "kb.sh").read_text()
        self.assertNotIn("CDPATH= cd", text)
        self.assertIn("CDPATH='' cd", text)
        proc = subprocess.run(["sh", "-n", str(REPO / "scripts" / "kb.sh")], capture_output=True)
        self.assertEqual(proc.returncode, 0)

    def test_sh_runs_from_other_directory(self):
        proc = subprocess.run(["sh", str(REPO / "scripts" / "kb.sh"), "--help"], capture_output=True,
                              cwd=tempfile.gettempdir())
        self.assertEqual(proc.returncode, 0)


class IterationThreeTests(KBTestCase):  # N3, N4, N5, N6
    def test_n3_init_refuses_non_toolkit_dir_and_changes_nothing(self):
        bogus = self.tmp / "not-a-toolkit"
        bogus.mkdir()
        (bogus / "scripts").mkdir()
        (bogus / "scripts" / "kb.py").write_text("")  # compose file missing
        envf = self.tmp / "kb.env"
        envf.write_text("LLM_KB_COLLECTION=keep\n")
        before = envf.read_text()
        calls = []
        with mock.patch.object(kb, "run_cmd", lambda c, **kw: calls.append(list(c)) or ok_proc(c)):
            rc, _, err = self.run_main("init", "--toolkit-dir", str(bogus))
        self.assertEqual(rc, 2)
        self.assertEqual(len(err.strip().splitlines()), 1)
        self.assertEqual(envf.read_text(), before)
        self.assertEqual(calls, [])
        self.assertEqual(self.run_main("init", "--toolkit-dir", str(self.tmp / "missing"))[0], 2)

    def test_n4_path_keeps_only_safe_absolute_existing_unique_dirs(self):
        good, good2, writable = self.tmp / "g1", self.tmp / "g2", self.tmp / "ww"
        for d in (good, good2, writable):
            d.mkdir()
        os.chmod(good, 0o755)
        os.chmod(good2, 0o755)
        os.chmod(writable, 0o777)
        raw = os.pathsep.join([str(good), "relative/bin", str(self.tmp / "gone"), str(writable), str(good2), str(good)])
        got = kb.build_path(raw).split(os.pathsep)
        self.assertEqual([p for p in got if p.startswith(str(self.tmp))], [str(good), str(good2)])
        self.assertNotIn("relative/bin", got)
        self.assertEqual(len(got), len(set(got)))
        env = kb.scheduler_env(kb.build_path(raw))
        self.assertNotIn(str(writable), env["PATH"])

    def test_n5_bad_mark_exits_2_one_line_no_traceback(self):
        rc, text, err = self.run_main("sync-status", "--no-fetch", "--mark", "not-a-date")
        self.assertEqual(rc, 2)
        self.assertEqual(len(err.strip().splitlines()), 1)
        self.assertNotIn("Traceback", err)
        self.assertFalse((self.data / "state" / "sync-state.json").exists())

    def ingest_calls(self, *argv):
        self.make_corpus()
        calls = []
        with mock.patch.object(kb, "run_cmd", lambda c, **kw: calls.append(list(c)) or ok_proc(c)):
            self.run_main(*argv)
        return [c for c in calls if "ingest" in c]

    def test_n6_allow_mass_delete_adds_env_to_one_shot_run_only(self):
        (call,) = self.ingest_calls("index", "--allow-mass-delete")
        self.assertEqual(call[-8:], ["--profile", "tools", "run", "--rm", "-T", "-e", "KB_ALLOW_MASS_DELETE=1",
                                     "ingest"])
        self.assertLess(call.index("-e"), call.index("ingest"))
        (plain,) = self.ingest_calls("index")
        self.assertNotIn("KB_ALLOW_MASS_DELETE=1", plain)
        self.assertNotIn("-e", plain)

    def test_n6_scheduled_run_never_passes_it(self):
        with mock.patch.object(kb, "docker_ready", return_value=(True, "ready")):
            calls = self.ingest_calls("scheduled-run")
        self.assertTrue(calls)
        self.assertFalse([c for c in calls if any("MASS_DELETE" in a for a in c)])

    def test_n6_help_describes_flag_in_one_line(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), self.assertRaises(SystemExit):
            kb.main(["index", "--help"])
        text = buf.getvalue()
        self.assertIn("--allow-mass-delete", text)
        self.assertIn("deletion guard", text)


TABLE_OK = """TOOL    SURFACE   ACTION     DETAIL
----    -------   ------     ------
claude  skills    unchanged  /h/.claude/skills -> /t/skills
gemini  skills    updated    /h/.gemini/skills -> /t/skills

Done. Global surfaces installed for: claude gemini
"""
TABLE_PARTIAL = """TOOL    SURFACE   ACTION     DETAIL
----    -------   ------     ------
claude  skills    unchanged  /h/.claude/skills -> /t/skills
gemini  skills    blocked    existing non-link path at /h/.gemini/skills; rerun with --force

Done with 1 blocked path(s). Re-run with --force after checking the backups it would take.
"""
TABLE_BLOCKED_PLUS_ERROR = TABLE_PARTIAL + "line 99: unexpected failure\n"


class SurfacesCommandTests(KBTestCase):  # row 22
    def test_posix_command_is_pure_uses_corpus_and_never_forces(self):
        cmd = kb.surfaces_command("/data/corpus", windows=False)
        self.assertEqual(cmd, ["bash", "/data/corpus/scripts/install-global-surfaces.sh", "--apply",
                               "--toolkit-root", "/data/corpus"])
        self.assertEqual(kb.surfaces_command("/data/corpus", windows=False, apply=False),
                         ["bash", "/data/corpus/scripts/install-global-surfaces.sh", "--toolkit-root", "/data/corpus"])

    def test_windows_command(self):
        cmd = kb.surfaces_command("C:/code/corpus", windows=True)
        self.assertEqual(cmd[:6], ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                                   "C:\\code\\corpus\\scripts\\install-global-surfaces.ps1"])
        self.assertEqual(cmd[6:], ["-Apply", "-ToolkitRoot", "C:\\code\\corpus"])
        self.assertNotIn("-Apply", kb.surfaces_command("C:/code/corpus", windows=True, apply=False))

    def test_never_force_and_corpus_not_running_checkout(self):
        for windows in (False, True):
            joined = " ".join(kb.surfaces_command("/elsewhere/corpus", windows)).lower()
            self.assertNotIn("force", joined)
            self.assertNotIn(REPO.as_posix().lower(), joined)

    def test_installer_must_exist_in_corpus_checkout(self):
        rc, _, err = self.run_main("surfaces", "refresh")
        self.assertEqual(rc, 2)
        self.assertIn("installer not found", err)

    def test_missing_data_folder_exit_2(self):
        import shutil
        shutil.rmtree(self.data)
        self.assertEqual(self.run_main("surfaces", "refresh")[0], 2)

    def test_classification_from_installer_output(self):
        self.assertEqual(kb.classify_surfaces(0, TABLE_OK), ("refreshed", 0))
        self.assertEqual(kb.classify_surfaces(1, TABLE_PARTIAL), ("partial", 1))
        self.assertEqual(kb.classify_surfaces(1, TABLE_BLOCKED_PLUS_ERROR)[0], "partial")  # count matches the footer
        self.assertEqual(kb.classify_surfaces(1, "boom: no table at all\n"), ("failed", 0))
        self.assertEqual(kb.classify_surfaces(124, TABLE_PARTIAL)[0], "failed")  # timeout
        self.assertEqual(kb.classify_surfaces(1, TABLE_PARTIAL.replace("Done with 1", "Done with 2"))[0], "failed")
        self.assertEqual(kb.surfaces_blocked_rows(TABLE_PARTIAL), 1)


@unittest.skipUnless(subprocess.run(["git", "--version"], capture_output=True).returncode == 0, "git missing")
class SurfacesRefreshFlowTests(KBTestCase):
    def setUp(self):
        super().setUp()
        git(self.tmp, "init", "-q", "-b", "main", str(self.corpus))
        (self.corpus / "scripts").mkdir()
        (self.corpus / "scripts" / "install-global-surfaces.sh").write_text("#!/bin/sh\n")
        (self.corpus / "AGENTS.md").write_text("x\n")
        git(self.corpus, "add", "-A")
        git(self.corpus, "commit", "-q", "-m", "i")
        self.head = git(self.corpus, "rev-parse", "HEAD").stdout.strip()
        self.calls = []
        self.installer = (0, TABLE_OK)

    def fake(self, cmd, **kw):
        self.calls.append(list(cmd))
        if cmd[0] == "git":
            if "pull" in cmd:
                return subprocess.CompletedProcess(cmd, 0, "", "")
            return subprocess.run(cmd, capture_output=True, text=True)
        if cmd[0] == "bash":
            return subprocess.CompletedProcess(cmd, self.installer[0], self.installer[1], "")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    def go(self, *argv):
        with mock.patch.object(kb, "run_cmd", self.fake), mock.patch.object(kb, "detect_os", return_value="Linux"), \
                mock.patch.object(kb, "docker_ready", return_value=(True, "docker ready")):
            return self.run_main(*argv)

    def installer_calls(self):
        return [c for c in self.calls if c[0] == "bash"]

    def head_file(self):
        return self.data / "state" / "surfaces-head"

    def test_refresh_refreshed_records_head_exit_0(self):
        rc, text, _ = self.go("surfaces", "refresh")
        self.assertEqual(rc, 0)
        self.assertIn("surfaces refreshed", text)
        self.assertEqual(self.head_file().read_text().strip(), self.head)
        self.assertIn("--apply", self.installer_calls()[0])
        self.assertIn(self.corpus.as_posix(), self.installer_calls()[0])

    def test_refresh_partial_records_head_exit_0_with_note(self):
        self.installer = (1, TABLE_PARTIAL)
        rc, text, _ = self.go("surfaces", "refresh")
        self.assertEqual(rc, 0)
        self.assertIn("partial (1 blocked)", text)
        self.assertEqual(self.head_file().read_text().strip(), self.head)

    def test_refresh_failed_exit_1_no_head(self):
        self.installer = (1, "Traceback: nope\n")
        rc, text, _ = self.go("surfaces", "refresh")
        self.assertEqual(rc, 1)
        self.assertFalse(self.head_file().exists())

    def test_dry_run_writes_nothing_and_passes_no_apply(self):
        rc, text, _ = self.go("surfaces", "refresh", "--dry-run")
        self.assertEqual(rc, 0)
        self.assertFalse(self.head_file().exists())
        self.assertNotIn("--apply", self.installer_calls()[0])
        self.assertEqual(len(self.installer_calls()), 1)

    def test_status_due_then_up_to_date(self):
        rc, text, _ = self.go("surfaces", "status")
        self.assertEqual(rc, 0)
        self.assertIn(f"corpus HEAD: {self.head}", text)
        self.assertIn("recorded HEAD: none", text)
        self.assertIn("refresh: due", text)
        self.go("surfaces", "refresh")
        text = self.go("surfaces", "status")[1]
        self.assertIn(f"recorded HEAD: {self.head}", text)
        self.assertIn("up to date", text)

    def test_scheduled_run_default_calls_nothing(self):
        rc, text, _ = self.go("scheduled-run")
        self.assertEqual(rc, 0)
        self.assertEqual(self.installer_calls(), [])
        self.assertNotIn("surfaces", text)

    def test_scheduled_run_key_on_refreshes_between_pull_and_index(self):
        os.environ["LLM_KB_REFRESH_SURFACES"] = "1"
        rc, text, _ = self.go("scheduled-run")
        self.assertEqual(rc, 0)
        self.assertIn("surfaces refreshed", text)
        pos = lambda pred: next(i for i, c in enumerate(self.calls) if pred(c))
        pull, inst, idx = (pos(lambda c: c[0] == "git" and "pull" in c), pos(lambda c: c[0] == "bash"),
                           pos(lambda c: "ingest" in c))
        self.assertLess(pull, inst)
        self.assertLess(inst, idx)
        self.go("scheduled-run")  # HEAD unchanged: not due again
        self.assertEqual(len(self.installer_calls()), 1)
        (self.corpus / "new.md").write_text("n\n")
        git(self.corpus, "add", "-A")
        git(self.corpus, "commit", "-q", "-m", "more")
        self.go("scheduled-run")
        self.assertEqual(len(self.installer_calls()), 2)

    def test_partial_in_status_line(self):
        os.environ["LLM_KB_REFRESH_SURFACES"] = "1"
        self.installer = (1, TABLE_PARTIAL)
        rc, text, _ = self.go("scheduled-run")
        self.assertEqual(rc, 0)
        self.assertIn("surfaces partial (1 blocked)", text)

    def test_failure_does_not_skip_index_or_change_exit_code(self):
        os.environ["LLM_KB_REFRESH_SURFACES"] = "1"
        self.installer = (1, "Traceback\n")
        rc, text, _ = self.go("scheduled-run")
        self.assertEqual(rc, 0)
        self.assertIn("surfaces refresh failed", text)
        self.assertIn("index ok", text)
        self.assertTrue([c for c in self.calls if "ingest" in c])
        self.assertFalse(self.head_file().exists())  # retried next run

    def test_missing_installer_in_corpus_counts_as_failed_not_fatal(self):
        os.environ["LLM_KB_REFRESH_SURFACES"] = "1"
        (self.corpus / "scripts" / "install-global-surfaces.sh").unlink()
        git(self.corpus, "add", "-A")
        git(self.corpus, "commit", "-q", "-m", "rm")
        rc, text, _ = self.go("scheduled-run")
        self.assertEqual(rc, 0)
        self.assertIn("surfaces refresh failed", text)
        self.assertIn("index ok", text)



class NoRealWaitTests(KBTestCase):
    """Guard: a failing stack start must not wait for a desktop app that happens to be installed."""

    def test_scheduled_run_does_not_sleep_when_app_is_installed_on_this_machine(self):
        self.make_corpus()
        real_sleeps = []

        def fail(cmd, **kw):
            return subprocess.CompletedProcess(cmd, 1, "", "boom")

        with mock.patch.object(kb, "run_cmd", fail), \
                mock.patch.object(kb.time, "sleep", real_sleeps.append), \
                mock.patch.object(kb, "detect_os", return_value="Darwin"):
            rc, _text, _ = self.run_main("scheduled-run")
        self.assertEqual(rc, 1)
        self.assertEqual(real_sleeps, [])


if __name__ == "__main__":
    unittest.main()
