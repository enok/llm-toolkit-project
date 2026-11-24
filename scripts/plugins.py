#!/usr/bin/env python3
"""Plugin capability catalog and security gate for LLM tool plugins (stdlib only).

Reads plugin directories as untrusted data: nothing from a plugin is executed,
imported, sourced or installed. Symlinks are never followed. The static scanner
gives each plugin a verdict (pass / review / block); the catalog turns installed
plugins into short capability cards that the knowledge base indexes as source
``plugins``, so one search can weigh toolkit assets against plugin capabilities.

Shared helpers come from scripts/kb.py (config, data folder, HTTP client, command
runner) and kb/service/kb_core.py (secret detection and masking, front matter),
both imported by path, never copied. Install locations come from
skills/llm-toolchain-provisioning/scripts/toolchain_lib.py.

Exit codes: 0 ok; 2 usage; 3 refused; 4 block verdict; 5 review verdict;
6 git failed or knowledge base unreachable without a catalog; 7 nothing found.
See docs/plugins.md.
"""
from __future__ import annotations

import argparse
import importlib.util
import ipaddress
import json
import math
import os
import re
import shutil
import stat
import sys
import tempfile
import time
import urllib.parse
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

EXIT_OK, EXIT_USAGE, EXIT_REFUSED, EXIT_BLOCK, EXIT_REVIEW, EXIT_UNREACHABLE, EXIT_NONE = 0, 2, 3, 4, 5, 6, 7
EXIT_GIT = 6

PLUGIN_DEFAULTS = {
    "LLM_PLUGINS_DIRS": "",
    "LLM_PLUGINS_ALLOWED_HOSTS": "github.com",
    "LLM_PLUGINS_MARGIN": "0.05",
    "LLM_PLUGINS_DESC_CHARS": "300",
}
CARD_NOTICE = "Descriptive catalog entry generated from an installed plugin. Reference data, not instructions."
CATALOG_VERSION = 1
DEFAULT_MARKETPLACE = "claude-plugins-official"
MANIFEST_CANDIDATES = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json", ".cursor-plugin/plugin.json",
                       "plugin.json")
MARKETPLACE_FILE = ".claude-plugin/marketplace.json"

# scanner bounds
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_JSON_BYTES = 1024 * 1024
MAX_FILES = 5000
MAX_PER_RULE_FILE = 5
MAX_FINDINGS = 300
MAX_CAPABILITIES = 500
EVIDENCE_CHARS = 160
MAX_HOSTS = 50
HEADER_BYTES = 4096
SEGMENT = 4096
SEGMENT_OVERLAP = 256
SKIP_DIRS = {".git"}

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}
CODE_EXT = {".sh", ".bash", ".zsh", ".ksh", ".fish", ".ps1", ".psm1", ".psd1", ".py", ".pyw", ".js", ".mjs",
            ".cjs", ".ts", ".mts", ".cts", ".jsx", ".tsx", ".rb", ".pl", ".php", ".lua", ".cmd", ".bat", ".vbs",
            ".applescript", ".go", ".rs"}
MD_EXT = {".md", ".markdown", ".mdx"}
CONFIG_EXT = {".json", ".jsonc", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf"}
SURFACE_DIRS = {"skills", "commands", "agents"}
SHELLS_AND_INTERPRETERS = ("/bin/", "/usr/bin/", "/usr/local/bin/", "/opt/homebrew/bin/", "/dev/null", "/dev/stdin",
                           "/dev/stdout", "/dev/stderr", "/tmp/")


class PluginError(Exception):
    """User-facing usage error (exit 2)."""


class Refused(Exception):
    """A request the tool refuses on policy grounds (exit 3)."""


# --------------------------------------------------------------------------- shared modules

def _load_module(name: str, path: Path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


kb = _load_module("llm_kb_cli", SCRIPTS_DIR / "kb.py")
_TOOLCHAIN = None


def toolchain():
    """skills/llm-toolchain-provisioning/scripts/toolchain_lib.py (install-location discovery)."""
    global _TOOLCHAIN
    if _TOOLCHAIN is None:
        path = SCRIPTS_DIR.parent / "skills" / "llm-toolchain-provisioning" / "scripts" / "toolchain_lib.py"
        _TOOLCHAIN = _load_module("llm_toolchain_lib", path)
    return _TOOLCHAIN


_CORE = None


def core():
    """kb/service/kb_core.py (find_secrets, mask_secrets, parse_front_matter), loaded once."""
    global _CORE
    if _CORE is None:
        _CORE = kb.get_core(load_config())
    return _CORE


def run_cmd(cmd, **kwargs):
    """Every external command goes through kb.run_cmd (timeouts, no git prompts); patched in tests."""
    return kb.run_cmd(cmd, **kwargs)


def out(text: str = "") -> None:
    print(text)


def err(text: str) -> None:
    print(text, file=sys.stderr)


# --------------------------------------------------------------------------- config and data

def load_config(environ=None) -> dict:
    """kb.py config plus the LLM_PLUGINS_* keys (defaults < env file < process env)."""
    environ = os.environ if environ is None else environ
    cfg = kb.load_config(environ)
    cfg.update(PLUGIN_DEFAULTS)
    file_values = kb.read_env_file(kb.env_file_path(environ))
    cfg.update({k: v for k, v in file_values.items() if k in PLUGIN_DEFAULTS})
    cfg.update({k: v for k, v in environ.items() if k in PLUGIN_DEFAULTS})
    return cfg


def cfg_float(cfg, key) -> float:
    try:
        return float(cfg[key])
    except (TypeError, ValueError):
        return float(PLUGIN_DEFAULTS[key])


def cfg_int(cfg, key) -> int:
    try:
        return max(40, int(cfg[key]))
    except (TypeError, ValueError):
        return int(PLUGIN_DEFAULTS[key])


def plugins_dir(cfg) -> Path:
    return kb.data_dir(cfg) / "plugins"


def catalog_path(base: Path) -> Path:
    return base / "catalog.json"


def decisions_path(cfg) -> Path:
    return plugins_dir(cfg) / "decisions.json"


def read_json_capped(path: Path, cap: int = MAX_JSON_BYTES):
    """(data, error). Never follows a symlink; refuses files above the cap."""
    try:
        if path.is_symlink():
            return None, "is a symlink"
        with open(path, "rb") as fh:
            raw = fh.read(cap + 1)
    except FileNotFoundError:
        return None, "missing"
    except OSError as exc:
        return None, type(exc).__name__
    if len(raw) > cap:
        return None, "too large"
    try:
        return json.loads(raw.decode("utf-8-sig")), None
    except (UnicodeDecodeError, ValueError):
        return None, "not valid JSON"


def write_json_atomic(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


# --------------------------------------------------------------------------- text helpers

HIDDEN_CHARS = ("\u200b\u200c\u200d\u200e\u200f\u2060\u2061\u2062\u2063\u2064\ufeff\u180e\u061c"
                "\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069\ufe00-\ufe0f"
                "\u2800\u3164\u115f\u1160\uffa0")  # last five render blank (Braille blank, Hangul fillers)
TAG_CHARS = "\U000e0000-\U000e007f"
HIDDEN_RX = re.compile("[" + HIDDEN_CHARS + TAG_CHARS + "\U000e0100-\U000e01ef]")
TAG_RX = re.compile("[" + TAG_CHARS + "]")
# characters that must never appear in a file or folder name: controls (newline included), bidi, invisible
BAD_NAME_RX = re.compile("[\x00-\x1f\x7f-\x9f" + HIDDEN_CHARS + TAG_CHARS + "\u2028\u2029]")
WINDOWS_DEVICES = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)}
CTRL_RX = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")
MARKUP_RX = re.compile(r"[<>`*#\[\]{}|\\]")
SAFE_NAME_RX = re.compile(r"[^A-Za-z0-9._-]+")
NAME_ARG_RX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")


def safe_name(value, fallback="plugin") -> str:
    """Letters, digits, dot, dash, underscore; never empty, never a Windows device name."""
    name = SAFE_NAME_RX.sub("-", str(value or "")).strip(".-_")[:80].strip(".-_")
    stem, dot, rest = name.partition(".")
    if stem.upper() in WINDOWS_DEVICES:  # CON, NUL, COM1... are devices on Windows, with or without extension
        name = f"{stem}-x{dot}{rest}"
    return name or fallback


def clean_path(value: str) -> str:
    """A local path for catalog.json: controls and hidden characters removed (separators kept)."""
    return BAD_NAME_RX.sub("", str(value or ""))[:4096]


def clean_text(value, cap: int) -> str:
    """One line, secrets masked, hidden/control/markup characters stripped, length-capped."""
    if isinstance(value, list):
        value = ", ".join(str(v) for v in value[:50])
    if not isinstance(value, str):
        return ""
    text = value[:20000]
    text = HIDDEN_RX.sub("", text)
    text = CTRL_RX.sub(" ", text)
    text = core().mask_secrets(text)
    text = MARKUP_RX.sub(" ", text)
    text = " ".join(text.split())
    if len(text) > cap:
        text = text[: max(1, cap - 1)].rstrip() + "…"
    return text


def escape_hidden(text: str) -> str:
    return HIDDEN_RX.sub(lambda m: f"<U+{ord(m.group(0)):04X}>", CTRL_RX.sub(" ", text))


def make_evidence(segment: str, needle: str = "", pos: int = 0) -> str:
    """Evidence window: secrets masked on the whole segment first, then cut to 160 chars."""
    masked = core().mask_secrets(segment)
    idx = masked.find(needle) if needle and needle in masked else int(pos * len(masked) / max(1, len(segment)))
    start = max(0, idx - 40)
    piece = masked[start:start + EVIDENCE_CHARS]
    piece = " ".join(escape_hidden(piece).split())
    return piece[:EVIDENCE_CHARS]


def iter_segments(text: str):
    """(line number, segment): lines capped at 4 KB, longer lines cut into overlapping windows."""
    for lineno, line in enumerate(text.split("\n"), 1):
        if len(line) <= SEGMENT:
            yield lineno, line
            continue
        step = SEGMENT - SEGMENT_OVERLAP
        start = 0
        while True:
            yield lineno, line[start:start + SEGMENT]
            if start + SEGMENT >= len(line):
                break
            start += step


def is_link(path) -> bool:
    try:
        if os.path.islink(path):
            return True
        check = getattr(os.path, "isjunction", None)
        return bool(check(path)) if check else False
    except OSError:
        return True


def within(root: str, candidate: str) -> bool:
    root = os.path.normcase(os.path.normpath(root))
    candidate = os.path.normcase(os.path.normpath(candidate))
    return candidate == root or candidate.startswith(root.rstrip(os.sep) + os.sep)


def path_escapes(value: str) -> bool:
    """Declared component path: absolute, drive-qualified, or with a '..' segment."""
    text = str(value).strip()
    for prefix in ("${CLAUDE_PLUGIN_ROOT}", "$CLAUDE_PLUGIN_ROOT"):
        if text.startswith(prefix):
            text = "." + text[len(prefix):]
    if text.startswith(("/", "\\", "~")) or re.match(r"^[A-Za-z]:", text):
        return True
    return ".." in re.split(r"[\\/]+", text)


# --------------------------------------------------------------------------- scanner rules

class Rule:
    __slots__ = ("rid", "severity", "keys", "rx", "check")

    def __init__(self, rid, severity, keys, pattern, flags=0, check=None):
        self.rid, self.severity, self.keys = rid, severity, tuple(keys)
        self.rx = re.compile(pattern, flags)
        self.check = check


_SH_SEP = r"(?:\s|$|;|&|\)|\"|')"

DOWNLOAD_EXEC = Rule(
    "download-exec", "high", ("curl", "wget", "iex", "invoke-expression", "downloadstring", "irm", "iwr"),
    r"\b(?:curl|wget)\b[^\n|;&]{0,400}\|\s{0,4}(?:sudo\s+(?:-\S+\s+){0,3})?(?:ba|z|k|da|fi)?sh\b"
    r"|\b(?:curl|wget)\b[^\n|;&]{0,400}\|\s{0,4}(?:sudo\s+)?(?:python[23]?|node|perl|ruby|php)\s{0,4}-?\s{0,4}(?:$|[;&|)])"
    r"|\b(?:ba|z)?sh\s+(?:-c\s+)?[\"']?\$\(\s*(?:curl|wget)\b"
    r"|(?:\b(?:ba|z)?sh|\bsource|(?:^|\s)\.)\s+<\(\s*(?:curl|wget)\b"
    r"|\beval\s+[\"']?\$\(\s*(?:curl|wget)\b"
    r"|(?i:\b(?:iex|invoke-expression)\b\s{0,4}\(?\s{0,4}\(?\s{0,4}(?:irm|iwr|invoke-restmethod|invoke-webrequest"
    r"|new-object\s+(?:system\.)?net\.webclient)\b)"
    r"|(?i:\b(?:irm|iwr|invoke-restmethod|invoke-webrequest)\b[^\n|]{0,300}\|\s{0,4}(?:iex|invoke-expression)\b)"
    r"|(?i:downloadstring\s*\([^\n]{0,300}\)\s*\)?\s*\|\s*(?:iex|invoke-expression)\b)",
)

DYNAMIC_EXEC_PY = Rule(
    "dynamic-exec-remote", "high", ("exec", "eval"),
    r"\b(?:exec|eval)\s*\([^\n]{0,300}(?:urlopen|urllib\.request|requests\.(?:get|post)|httpx\.(?:get|post)"
    r"|https?://)",
)
DYNAMIC_EXEC_JS = Rule(
    "dynamic-exec-remote", "high", ("eval", "function", "runin", "import"),
    r"(?:\beval\s*\(|\bnew\s+Function\s*\(|\bvm\.runIn\w{0,20}Context\s*\()[^\n]{0,300}"
    r"(?:\bfetch\s*\(|axios|https?\.get\s*\(|XMLHttpRequest|https?://)"
    r"|\bimport\s*\(\s*[\"'`]https?://",
)

# a credential file name only counts next to a home-folder reference (a list of risky names is detection, not access)
_HOME_ANCHOR = re.compile(r"~[/\\]|\$HOME\b|\$\{HOME\}|%USERPROFILE%|%APPDATA%|\$env:(?:USERPROFILE|APPDATA|HOME)\b"
                          r"|expanduser\s*\(|Path\.home\s*\(|os\.homedir\s*\(|homedir\s*\(|getenv\s*\(\s*[\"']HOME"
                          r"|environ\[\s*[\"']HOME|Library[/\\]Application Support|AppData[/\\]", re.IGNORECASE)
_KEYCHAIN_CMD = re.compile(r"(?i)\bsecurity\s|\bsecret-tool\b|\bCred(?:Read|Enumerate)|login\.keychain")

CREDENTIAL_STORE = Rule(
    "credential-store-access", "high",
    (".ssh", ".aws", "gcloud", ".azure", ".kube", ".docker", ".netrc", "git-credentials", "keychain", "secret-tool",
     "login data", "cookies", "logins.json", "key3.db", "key4.db", "chat.db", "credread", "credenumerate",
     "-password"),
    r"(?i:\.ssh[/\\]+id_[a-z0-9_]{2,20}\b|\.aws[/\\]+credentials\b"
    r"|\.config[/\\]+gcloud[/\\]+(?:credentials|application_default_credentials|access_tokens|legacy_credentials)"
    r"|\.azure[/\\]+(?:accessTokens|msal_token_cache)|\.kube[/\\]+config\b|\.docker[/\\]+config\.json"
    r"|(?<![\w.])\.netrc\b|\.git-credentials\b"
    r"|\bsecurity\s+(?:find|dump)-(?:generic-password|internet-password|keychain)\b|\blogin\.keychain"
    r"|\bsecret-tool\s+lookup\b|\bCred(?:Read|Enumerate)W?\b"
    r"|(?:Chrome|Chromium|Edge|Brave|BraveSoftware|Opera)[^\n]{0,80}[/\\](?:Login Data|Cookies)\b"
    r"|\bcookies\.sqlite\b|\blogins\.json\b|\bkey[34]\.db\b|Messages[/\\]+chat\.db)",
    check=lambda seg, m: bool(_KEYCHAIN_CMD.search(m.group(0)) or _HOME_ANCHOR.search(seg)),
)

PERSISTENCE = Rule(
    "persistence", "high",
    ("launchagents", "launchdaemons", "launchctl", "crontab", "/etc/cron", "systemctl", "schtasks",
     "register-scheduledtask", "currentversion", "bashrc", "zshrc", "profile", "config.fish"),
    r"(?i:Library[/\\]+Launch(?:Agents|Daemons)\b|\blaunchctl\s+(?:load|bootstrap|submit)\b"
    r"|\|\s*crontab\b|\bcrontab\s+(?:-u\s+\S+\s+)?(?:-|-e|\S+\.cron)(?=\s|$)|/etc/cron"
    r"|\bsystemctl\s+(?:--user\s+)?enable\b|\bschtasks(?:\.exe)?\s+/create\b|\bRegister-ScheduledTask\b"
    r"|CurrentVersion\\{1,2}Run(?:Once)?\b"
    r"|(?:>>|\btee\s+-a|Add-Content|Out-File[^\n]{0,40}-Append|appendFile(?:Sync)?\s*\()[^\n]{0,120}"
    r"(?:\.bashrc|\.zshrc|\.bash_profile|\.zprofile|\.profile\b|\$PROFILE|config\.fish)"
    r"|(?:\.bashrc|\.zshrc|\.bash_profile|\.zprofile)[\"']\s*\)?\s*,\s*[\"']a\+?[\"'])",
)

DESTRUCTIVE_FS = Rule(
    "destructive-fs", "high", ("rm ", "mkfs", "dd ", "remove-item", "rmtree", "format ", ":(){"),
    r"\brm\s+(?:-{1,2}[A-Za-z-]+\s+){0,4}(?:-[A-Za-z]*[rR][A-Za-z]*|--recursive)(?:\s+-{1,2}[A-Za-z-]+){0,4}\s+"
    r"[\"']?(?:/|~/?|\$HOME/?|\$\{HOME\}/?|/\*|\*|\.\.?/?|--no-preserve-root)[\"']?" + _SH_SEP +
    r"|\bmkfs(?:\.\w+)?\s|\bdd\s+[^\n]{0,80}\bof=/dev/(?:sd|nvme|disk|hd|mmcblk)"
    r"|(?i:\bRemove-Item\b[^\n]{0,200}-Recurse[^\n]{0,200}\s[\"']?(?:[A-Z]:\\?|\$env:(?:USERPROFILE|HOMEDRIVE|SystemRoot)"
    r"|\$HOME|~)[\"']?(?:\s|$))"
    r"|\bshutil\.rmtree\(\s*(?:[\"']/[\"']|[\"']~/?[\"']|os\.path\.expanduser\(\s*[\"']~/?[\"']\s*\)"
    r"|Path\.home\(\)\s*\)|os\.environ\[[\"']HOME[\"']\]\s*\))"
    r"|(?i:\bformat\s+[A-Z]:\s*(?:/|$))|:\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:",
)

PRIV_ESC = Rule(
    "privilege-escalation", "medium", ("sudo", "doas", "runas", "pkexec"),
    r"(?:^|[\s;&|(`\"'])(?:sudo|doas)\s+[^\s#]|\brunas\s+/user:|(?i:-Verb\s+RunAs\b)|\bpkexec\s+\S",
)

_OBF_DECODE = re.compile(
    r"base64\s+(?:-d|--decode|-D)\b|b64decode\s*\(|\batob\s*\(|FromBase64String\s*\(|bytes\.fromhex\s*\("
    r"|unhexlify\s*\(|Buffer\.from\([^\n)]{0,4000},\s*[\"'](?:base64|hex)[\"']\)"
    r"|codecs\.decode\s*\([^\n)]{0,4000}[\"'](?:hex|rot13|rot_13|base64)[\"']")
_OBF_BLOB = re.compile(r"[A-Za-z0-9+/]{200,}={0,2}|(?:\\x[0-9a-fA-F]{2}){60,}|\b[0-9a-fA-F]{200,}\b")
_OBF_EXEC = re.compile(
    r"\|\s*(?:ba|z)?sh\b|\beval\s*\(|\bexec\s*\(|\bnew\s+Function\b|(?i:\bInvoke-Expression\b|\biex\b)"
    r"|\bos\.system\s*\(|\bsubprocess\.\w+\s*\(|\bexecSync\s*\(|\bspawnSync?\s*\(")


def _obfuscation_check(segment, _m):
    return bool(_OBF_EXEC.search(segment)) and bool(_OBF_DECODE.search(segment) or _OBF_BLOB.search(segment))


OBFUSCATION = Rule(
    "obfuscation", "medium", ("base64", "b64decode", "atob", "frombase64", "fromhex", "unhexlify", "buffer.from",
                              "codecs.decode", "\\x"),
    r"base64|b64decode|atob|FromBase64String|fromhex|unhexlify|Buffer\.from|codecs\.decode|(?:\\x[0-9a-fA-F]{2}){60}"
    r"|[A-Za-z0-9+/]{200}",
    check=_obfuscation_check,
)
BOT_EVASION = Rule(
    "bot-evasion", "medium",
    ("captcha", "chromedriver", "stealth", "bot", "cloudflare", "webdriver"),
    r"(?i:\b(?:solve|solving|solver|bypass(?:es|ing)?|defeat(?:ing)?|evad(?:e|es|ing)|circumvent(?:ing)?|crack(?:ing)?)"
    r"\b[^\n.]{0,40}\b(?:re)?captchas?\b"
    r"|\b(?:re)?captchas?\b[^\n.]{0,40}\b(?:solv(?:e|er|ers|ing)|bypass(?:es|ing)?)\b"
    r"|\b(?:2captcha|anti-captcha|anticaptcha|capsolver|capmonster|deathbycaptcha)\b"
    r"|\bundetected[-_]chromedriver\b|puppeteer-extra-plugin-stealth|playwright[-_]stealth|\bselenium[-_]stealth\b"
    r"|\b(?:bypass(?:es|ing)?|evad(?:e|es|ing)|circumvent(?:ing)?)\s+(?:the\s+)?(?:anti-bot|bot|cloudflare)"
    r"(?:[\s-]+(?:detection|protection|checks?|challenges?))?\b"
    r"|navigator\.webdriver\s*=)",
    check=lambda seg, m: _not_described(seg, m),
)

_NEGATED = re.compile(r"(?i)\b(?:no|never|not|don't|do not|must not|cannot|can't|won't|without|refuse|avoid|detect\w*|flag\w*|"
                      r"watch for|such as|e\.g\.|example|attack\w*|inject\w*|malicious|adversar\w*|untrusted|"
                      r"phrases? like|patterns? like)\b")


def _not_described(segment, m):
    """Skip a match that a nearby word marks as described or forbidden rather than instructed."""
    before = segment[max(0, m.start() - 60):m.start()]
    after = segment[m.end():m.end() + 40]
    return not (_NEGATED.search(before) or re.search(r"(?i)\b(?:attack|injection|example)\b", after)
                or before.rstrip().endswith(("\"", "'", "“", "`")))


INSTRUCTION_OVERRIDE = Rule(
    "instruction-override", "high",
    ("ignore", "disregard", "forget", "override", "tell", "inform", "show", "reveal", "mention", "disclose", "hide",
     "conceal", "without", "disable", "bypass", "turn off", "circumvent", "skip", "dangerously"),
    r"(?i:\b(?:ignore|disregard|forget|override)\s+(?:all\s+|any\s+)?(?:(?:of\s+)?(?:the|your)\s+)?"
    r"(?:previous|prior|above|earlier|preceding|system|original)\s+(?:instructions|prompts?|rules|guidelines|directions"
    r"|messages)"
    r"|\b(?:do\s+not|don't|never)\s+(?:tell|inform|show|reveal\s+to|mention\s+(?:this|it)\s+to|disclose\s+(?:this|it)\s+to)"
    r"\s+the\s+user\s*(?:about\s+(?:this|it|these|that)\b|what\s+you\b|that\s+you\b|[.;:!)]|$)"
    r"|\b(?:hide|conceal)\s+(?:this|it|these|that|your\s+\w+)\s+from\s+the\s+user\b"
    r"|\b(?:disable|bypass|turn\s+off|circumvent)\s+(?:all\s+|any\s+)?(?:the\s+|your\s+)?(?:safety|security"
    r"|guardrails?|sandbox(?:ing)?|permission\s+(?:checks?|prompts?))\b"
    r"|--dangerously-skip-permissions)",
    check=_not_described,
)
MANDATE = Rule(
    "mandate-language", "medium",
    ("before", "extremely", "absolutely", "choice", "any", "every", "all"),
    r"(?i:\b(?:must|always|shall)\b[^\n.]{0,30}\b(?:invoke|use|call|load|check\s+for)\s+(?:this|these|the|a|any|relevant)?"
    r"\s*(?:skills?|plugins?|this)\b[^\n.]{0,40}\bbefore\s+(?:any|every|each|responding|answering|replying|doing)\b"
    r"|\b(?:always|must)\s+use\s+[^\n.]{1,40}\bfor\s+(?:any|every|all)\b)"
    r"|\b(?:EXTREMELY|ABSOLUTELY)[\s-]+(?:IMPORTANT|CRITICAL|REQUIRED|MANDATORY)\b"
    r"|(?i:\byou\s+(?:do\s+not|don't)\s+have\s+a\s+choice\b"
    r"|\buse\s+(?:this(?:\s+skill)?\s+|it\s+)?(?:for|on|with|in)\s+(?:any|every|all)\s+(?:tasks?|requests?|prompts?"
    r"|questions?|conversations?|messages?)\b"
    r"|\b(?:any|every)\s+(?:task|request|prompt|conversation|message)\s*,?\s+(?:no\s+matter|regardless)\b)",
)
NETWORK_IN_SCRIPT = Rule(
    "hook-script-network", "medium",
    ("urlopen", "urllib", "requests.", "http", "fetch", "axios", "curl", "wget", "invoke-webrequest",
     "invoke-restmethod", "socket"),
    r"\burlopen\s*\(|\burllib\.request\b|\brequests\.(?:get|post|put|patch|request)\s*\(|\bhttp\.client\b"
    r"|\bhttpx\.\w+\s*\(|\bfetch\s*\(\s*[\"'`]?https?:|\baxios\b|\bcurl\s|\bwget\s|(?i:\binvoke-(?:webrequest|restmethod)\b)"
    r"|\bsocket\.(?:create_connection|connect)\b",
)
AUTO_APPROVE = Rule(
    "hook-auto-approve", "high", ("permissiondecision", "decision", "approve"),
    r"(?i:[\"']?permissionDecision[\"']?\s*[:=]\s*[\\]?[\"'](?:allow|approve)[\\]?[\"']"
    r"|[\"']decision[\"']\s*:\s*[\\]?[\"']approve[\\]?[\"']|[\"']behavior[\"']\s*:\s*[\\]?[\"']allow[\\]?[\"'])",
)
CONTEXT_MARKER = re.compile(r"additionalContext|hookSpecificOutput|systemMessage")
HOOK_NET_RX = re.compile(r"(?i)\b(?:curl|wget|nc|ncat|telnet|invoke-webrequest|invoke-restmethod|iwr|irm)\b|https?://")
INLINE_SHELL_RX = re.compile(r"(?:^|\s)!`[^`\n]{1,300}`")
HOST_RX = re.compile(r"\bhttps?://(\[[0-9A-Fa-f:]{2,45}\]|[A-Za-z0-9.-]{1,253})")
UNRESTRICTED_SHELL = {"bash", "bash(*)", "bash(*:*)", "bash(:*)", "*", "powershell", "powershell(*)", "shell"}

_WARNED = re.compile(r"(?i)\b(?:never|avoid|don't|do not|can't|cannot|untrusted|dangerous|unsafe|risky|instead of)\b")
DOWNLOAD_EXEC_DOC = Rule("download-exec", "medium", DOWNLOAD_EXEC.keys, DOWNLOAD_EXEC.rx.pattern,
                         check=lambda seg, _m: not _WARNED.search(seg))

SHELL_EXT = {".sh", ".bash", ".zsh", ".ksh", ".fish", ".ps1", ".psm1", ".cmd", ".bat"}
# in a shell script the pipe-to-shell line runs unless it is only printed or commented
_PRINTED_LINE = re.compile(r"^\s*(?:#|::|rem\s|echo\b|printf\b|write-(?:host|output)\b|cat\s*<<)", re.IGNORECASE)
# in a program the command only runs when the line hands it to a process or shell
_EXEC_SINK = re.compile(r"\bsubprocess\.|\bos\.(?:system|popen|exec\w*)\s*\(|\bPopen\s*\(|shell\s*=\s*True"
                        r"|\bchild_process\b|\b(?:execSync|execFileSync|spawnSync|spawn|exec|execFile)\s*\("
                        r"|\bsystem\s*\(|\bBun\.\$|\$`|\bRuntime\.getRuntime\(\)\.exec|\bProcess\.Start\b"
                        r"|\bStart-Process\b|\bInvoke-Expression\b|\biex\b|`[^`\n]*\|\s*(?:ba)?sh[^`\n]*`")
_CHAINED = re.compile(r";|&&|\|\||\||`|\$\(")


def _shell_download_severity(seg, m):
    """Medium only when the text before the match prints or comments it and chains no other command."""
    before = seg[:m.start()]
    return "medium" if _PRINTED_LINE.match(before) and not _CHAINED.search(before) else True


DOWNLOAD_EXEC_SHELL = Rule("download-exec", "high", DOWNLOAD_EXEC.keys, DOWNLOAD_EXEC.rx.pattern,
                           check=_shell_download_severity)
DOWNLOAD_EXEC_PROGRAM = Rule("download-exec", "high", DOWNLOAD_EXEC.keys, DOWNLOAD_EXEC.rx.pattern,
                             check=lambda seg, _m: True if _EXEC_SINK.search(seg) else "medium")
# the fenced-sample downgrade applies only to material kept in these folders, never to an arbitrary skill file
FIXTURE_DIRS = {"tests", "test", "fixtures", "examples", "evals", "prompts"}
_ASSIGNED_NAME = re.compile(r"^\s*(?:(?:const|let|var|my|local|export)\s+)?\$?([A-Za-z_]\w{0,80})\s*(?::[^=\n]{0,80})?=(?!=)")
_ALIAS = re.compile(r"^\s*(?:(?:const|let|var|my|local)\s+)?\$?([A-Za-z_]\w{0,80})\s*=\s*\$?([A-Za-z_]\w{0,80})\s*;?\s*$")
_IDENT = re.compile(r"[A-Za-z_]\w{0,80}")


def program_download_rule(text: str) -> Rule:
    """download-exec for a program file: high when the matched line has an execution sink, or when the line
    assigns the command to a name that a sink in the same file uses (directly, inside an f-string, format or
    concatenation, or through simple `b = a` aliases); otherwise medium (a printed suggestion)."""
    used, aliases = set(), {}
    for _line, seg in iter_segments(text):
        m = _EXEC_SINK.search(seg)
        if m:
            used.update(_IDENT.findall(seg[m.start():]))
        a = _ALIAS.match(seg)
        if a:
            aliases.setdefault(a.group(1), set()).add(a.group(2))
    frontier = list(used)
    while frontier:  # a name used by a sink makes every name it was copied from used too
        for source in aliases.get(frontier.pop(), ()):
            if source not in used:
                used.add(source)
                frontier.append(source)

    def severity(seg, _m):
        if _EXEC_SINK.search(seg):
            return True
        name = _ASSIGNED_NAME.match(seg)
        return True if name and name.group(1) in used else "medium"

    return Rule("download-exec", "high", DOWNLOAD_EXEC.keys, DOWNLOAD_EXEC.rx.pattern, check=severity)


_FIXTURE_HEADING = re.compile(r"(?i)adversar|injection|fixture|attack|malicious|red[- ]team|hostile|jailbreak")


def fixture_fence_lines(text: str) -> set:
    """Line numbers inside fenced code blocks whose heading trail names adversarial or fixture material."""
    lines, trail, fence = set(), ["", "", "", "", "", ""], ""
    for lineno, line in enumerate(text.split("\n"), 1):
        stripped = line.lstrip()
        if fence:
            if stripped.startswith(fence):
                fence = ""
            elif any(_FIXTURE_HEADING.search(t) for t in trail if t):
                lines.add(lineno)
            continue
        if stripped.startswith(("```", "~~~")):
            fence = stripped[:3]
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            trail[level - 1] = m.group(2)
            for j in range(level, 6):
                trail[j] = ""
    return lines


CODE_RULES = (CREDENTIAL_STORE, PERSISTENCE, DESTRUCTIVE_FS, PRIV_ESC, OBFUSCATION, BOT_EVASION)
# an install instruction in prose is reviewed (medium); the same command in bundled code blocks (high)
SURFACE_RULES = (INSTRUCTION_OVERRIDE, MANDATE, DOWNLOAD_EXEC_DOC, BOT_EVASION)


# --------------------------------------------------------------------------- scanner

class PluginScan:
    """Static, read-only scan of one plugin directory."""

    def __init__(self, path, desc_chars: int = 300):
        self.given = str(path)
        self.root = os.path.realpath(os.path.abspath(str(path)))
        self.desc_chars = desc_chars
        self.findings = []
        self.suppressed = 0
        self._per_file_rule = {}
        self._seen = set()
        self.hosts = []
        self.manifest = {}
        self.manifest_file = None
        self.hook_events = []
        self.hooks = []  # (event, command)
        self.hook_files = set()
        self.context_files = {}
        self.mcp = []
        self.skills, self.commands, self.agents = [], [], []
        self.scripts = 0
        self.binaries = 0
        self.files = 0
        self.hook_description = ""

    # ------------------------------------------------------------ findings

    def add(self, rid, severity, rel, line, evidence):
        key = (rid, rel, line, "" if line else str(evidence)[:80])
        if key in self._seen:
            return
        count = self._per_file_rule.get((rid, rel), 0)
        if count >= MAX_PER_RULE_FILE and rid not in ("mcp-server", "mcp-unpinned-package", "mcp-literal-secret"):
            return
        if len(self.findings) >= MAX_FINDINGS:
            self.suppressed += 1
            if SEVERITY_ORDER[severity] < min(SEVERITY_ORDER[f["severity"]] for f in self.findings):
                self.findings.append(self._finding(rid, severity, rel, line, evidence))
            return
        self._seen.add(key)
        self._per_file_rule[(rid, rel)] = count + 1
        self.findings.append(self._finding(rid, severity, rel, line, evidence))

    @staticmethod
    def _finding(rid, severity, rel, line, evidence):
        return {"rule": rid, "severity": severity, "file": " ".join(escape_hidden(str(rel)).split())[:300], "line": line,
                "evidence": " ".join(escape_hidden(str(evidence)).split())[:EVIDENCE_CHARS]}

    def add_host(self, host):
        host = str(host or "").strip("[]").lower().rstrip(".")
        if not re.fullmatch(r"[a-z0-9.:-]{1,253}", host):
            return
        if not host or host in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            return
        if host.endswith((".example", ".test", ".invalid", ".local")) or host.split(".")[-2:-1] == ["example"]:
            return
        if host not in self.hosts and len(self.hosts) < MAX_HOSTS:
            self.hosts.append(host)

    # ------------------------------------------------------------ entry point

    def run(self) -> dict:
        started = time.monotonic()
        if not os.path.isdir(self.root):
            raise PluginError(f"not a directory: {self.given}")
        self._manifest()
        self._hooks()
        self._mcp()
        self._walk()
        self._hook_context()
        self._inventory()
        if self.hosts:
            self.add("network-hosts", "info", "", 0, ", ".join(self.hosts))
        elapsed = time.monotonic() - started
        return self.result(elapsed)

    def result(self, elapsed) -> dict:
        counts = {s: 0 for s in SEVERITY_ORDER}
        for f in self.findings:
            counts[f["severity"]] += 1
        verdict = "block" if counts["high"] else "review" if counts["medium"] else "pass"
        self.findings.sort(key=lambda f: (SEVERITY_ORDER[f["severity"]], f["rule"], f["file"], f["line"]))
        name = self.plugin_name()
        listing = sum(len(c["handle"]) + len(c.get("_full", "")) + 2 for c in self.skills + self.commands + self.agents)
        protective = self._protective()
        return {
            "plugin": name,
            "dir": clean_text(os.path.basename(self.root), 200),
            "path": clean_path(self.root),
            "verdict": verdict,
            "counts": counts,
            "suppressed": self.suppressed,
            "findings": self.findings,
            "manifest": {
                "name": name,
                "version": clean_text(self.manifest.get("version", ""), 40),
                "description": clean_text(self.manifest.get("description", ""), self.desc_chars),
                "author": clean_text((self.manifest.get("author") or {}).get("name", "")
                                     if isinstance(self.manifest.get("author"), dict)
                                     else self.manifest.get("author", ""), 80),
                "homepage": clean_text(self.manifest.get("homepage", "") or self.manifest.get("repository", ""), 200),
                "file": self.manifest_file,
            },
            "inventory": {
                "skills": [self._public(c) for c in self.skills],
                "commands": [self._public(c) for c in self.commands],
                "agents": [self._public(c) for c in self.agents],
                "mcp": self.mcp,
                "hook_events": self.hook_events,
                "scripts": self.scripts,
                "binaries": self.binaries,
                "files": self.files,
                "hosts": self.hosts,
                "listing_chars": listing,
                "protective": protective,
            },
            "elapsed": round(elapsed, 4),
        }

    @staticmethod
    def _public(cap):
        return {k: v for k, v in cap.items() if not k.startswith("_")}

    def plugin_name(self) -> str:
        name = self.manifest.get("name") if isinstance(self.manifest, dict) else None
        return safe_name(name if isinstance(name, str) and name.strip() else os.path.basename(self.root))

    # ------------------------------------------------------------ manifest

    def _manifest(self):
        for rel in MANIFEST_CANDIDATES:
            full = os.path.join(self.root, *rel.split("/"))
            if os.path.lexists(full):
                self.manifest_file = rel
                data, problem = read_json_capped(Path(full))
                if problem:
                    self.add("manifest-invalid", "medium", rel, 0, f"manifest {problem}")
                elif not isinstance(data, dict):
                    self.add("manifest-invalid", "medium", rel, 0, "manifest is not a JSON object")
                else:
                    self.manifest = data
                    if not isinstance(data.get("name"), str) or not data.get("name").strip():
                        self.add("manifest-invalid", "medium", rel, 0, "manifest has no name")
                    self._manifest_paths(rel, data)
                    description = data.get("description")
                    if isinstance(description, str):
                        # it becomes the body of the card's "## plugin" section: same checks as skill prose
                        text = description[:20000]
                        self.apply((INSTRUCTION_OVERRIDE, MANDATE), rel, text, text.lower())
                        self._hidden(rel, text)
                return
        self.add("manifest-missing", "info", "", 0, "no plugin manifest; components found by folder convention")

    def _manifest_paths(self, rel, data):
        for key in ("commands", "agents", "skills", "hooks", "mcpServers", "outputStyles", "lspServers"):
            value = data.get(key)
            values = [value] if isinstance(value, str) else value if isinstance(value, list) else []
            for item in values:
                if isinstance(item, str) and path_escapes(item):
                    self.add("manifest-path-escape", "high", rel, 0, f"{key}: {make_evidence(item)}")

    def declared(self, key):
        value = self.manifest.get(key) if isinstance(self.manifest, dict) else None
        values = [value] if isinstance(value, str) else value if isinstance(value, list) else []
        result = []
        for item in values:
            if isinstance(item, str) and not path_escapes(item):
                text = item.replace("${CLAUDE_PLUGIN_ROOT}", ".").replace("$CLAUDE_PLUGIN_ROOT", ".")
                full = os.path.normpath(os.path.join(self.root, text))
                if within(self.root, full):
                    result.append(full)
        return result

    def _safe_json(self, full):
        if not within(self.root, full) or is_link(full):
            return None
        data, problem = read_json_capped(Path(full))
        return None if problem else data

    # ------------------------------------------------------------ hooks

    def _hooks(self):
        sources = []
        default = os.path.join(self.root, "hooks", "hooks.json")
        if os.path.isfile(default) and not is_link(default):
            sources.append(("hooks/hooks.json", self._safe_json(default)))
        inline = self.manifest.get("hooks") if isinstance(self.manifest, dict) else None
        if isinstance(inline, dict):
            sources.append((self.manifest_file, inline))
        for full in self.declared("hooks"):
            if os.path.normcase(full) != os.path.normcase(default) and full.endswith(".json"):
                sources.append((self.rel(full), self._safe_json(full)))
        for rel, data in sources:
            if not isinstance(data, dict):
                continue
            if isinstance(data.get("description"), str):
                self.hook_description += " " + data["description"][:500]
            events = data.get("hooks", data) if isinstance(data.get("hooks"), dict) else {}
            for event, groups in events.items():
                if not isinstance(groups, list):
                    continue
                found = False
                for group in groups:
                    for hook in (group.get("hooks") if isinstance(group, dict) else None) or []:
                        if not isinstance(hook, dict):
                            continue
                        found = True
                        command = hook.get("command") if isinstance(hook.get("command"), str) else ""
                        self.hooks.append((str(event), command, rel))
                        if command:
                            self._hook_command(str(event), command, rel)
                if found and str(event) not in self.hook_events:
                    self.hook_events.append(safe_name(event, "event"))
        if self.hook_events:
            self.add("hook-present", "info", "hooks/hooks.json", 0, "events: " + ", ".join(self.hook_events))

    def _hook_command(self, event, command, rel):
        text = command[:4000]
        if HOOK_NET_RX.search(text):
            self.add("hook-network", "high", rel, 0, f"{event}: {make_evidence(text)}")
        m = AUTO_APPROVE.rx.search(text)
        if m:
            self.add("hook-auto-approve", "high", rel, 0, f"{event}: {make_evidence(text, m.group(0))}")
        for token in re.findall(r"[^\s\"';|&()<>]+", text):
            if "CLAUDE_PLUGIN_ROOT" in token:
                tail = re.sub(r"^.*?\$\{?CLAUDE_PLUGIN_ROOT\}?", "", token).lstrip("/\\")
                if ".." in re.split(r"[\\/]+", tail):
                    self.add("hook-outside-root", "high", rel, 0, f"{event}: {make_evidence(text, token)}")
                elif tail:
                    full = os.path.normpath(os.path.join(self.root, tail))
                    if within(self.root, full):
                        self.hook_files.add(self.rel(full))
                continue
            outside = (token.startswith(("~", "$HOME", "${HOME}", "%USERPROFILE%", "$env:USERPROFILE"))
                       or (token.startswith("/") and not token.startswith(SHELLS_AND_INTERPRETERS))
                       or re.match(r"^[A-Za-z]:[\\/]", token) is not None
                       or ".." in re.split(r"[\\/]+", token))
            if outside:
                self.add("hook-outside-root", "high", rel, 0, f"{event}: {make_evidence(text, token)}")

    def _hook_context(self):
        for event, command, rel in self.hooks:
            if event not in ("SessionStart", "UserPromptSubmit"):
                continue
            stripped = command.strip()
            direct = re.match(r"^(?:echo|printf|cat)\b", stripped) is not None or CONTEXT_MARKER.search(stripped)
            refs = sorted(f for f in self.context_files
                          if f in self.hook_files or f.split("/")[0] == "hooks")
            if direct or refs:
                where = f"{refs[0]}:{self.context_files[refs[0]]}" if refs else "inline command"
                self.add("hook-context-injection", "medium", rel, 0,
                         f"{event} hook emits context ({where}): {make_evidence(stripped)}")

    # ------------------------------------------------------------ MCP

    def _mcp(self):
        sources = []
        default = os.path.join(self.root, ".mcp.json")
        if os.path.isfile(default) and not is_link(default):
            sources.append((".mcp.json", self._safe_json(default)))
        inline = self.manifest.get("mcpServers") if isinstance(self.manifest, dict) else None
        if isinstance(inline, dict):
            sources.append((self.manifest_file, {"mcpServers": inline}))
        for full in self.declared("mcpServers"):
            if os.path.normcase(full) != os.path.normcase(default):
                sources.append((self.rel(full), self._safe_json(full)))
        for rel, data in sources:
            if not isinstance(data, dict):
                continue
            servers = data.get("mcpServers") if isinstance(data.get("mcpServers"), dict) else data
            for name, conf in servers.items():
                if isinstance(conf, dict):
                    self._mcp_server(rel, safe_name(name, "server"), conf)

    def _mcp_server(self, rel, name, conf):
        command = conf.get("command") if isinstance(conf.get("command"), str) else ""
        url = conf.get("url") if isinstance(conf.get("url"), str) else ""
        args = [a for a in conf.get("args", []) if isinstance(a, str)] if isinstance(conf.get("args"), list) else []
        transport = str(conf.get("type") or ("stdio" if command else "http" if url else "unknown"))[:20]
        target = ""
        if url:
            parsed = urllib.parse.urlsplit(url)
            host = parsed.hostname or ""
            target = host
            self.add_host(host)
            self._mcp_url(rel, name, parsed, host)
        elif command:
            target = " ".join([os.path.basename(command)] + [a for a in args if not a.startswith("-")][:1])
        entry = {"name": name, "transport": safe_name(transport, "unknown"), "target": clean_text(target, 120)}
        if entry not in self.mcp and self._room():
            self.mcp.append(entry)
        self.add("mcp-server", "info", rel, 0, f"{name}: {entry['transport']} {entry['target']}")
        if command:
            self._mcp_pin(rel, name, command, args, conf)
        self._mcp_secrets(rel, name, conf, args, url)

    def _mcp_url(self, rel, name, parsed, host):
        loopback = host in ("localhost", "127.0.0.1", "::1")
        raw_ip = False
        try:
            raw_ip = not ipaddress.ip_address(host).is_loopback
        except ValueError:
            pass
        if (parsed.scheme == "http" and not loopback) or raw_ip:
            self.add("mcp-insecure-url", "medium", rel, 0, f"{name}: {parsed.scheme}://{host}")

    def _mcp_pin(self, rel, name, command, args, conf=None):
        tool = os.path.basename(command).lower()
        for suffix in (".cmd", ".exe"):
            if tool.endswith(suffix):
                tool = tool[: -len(suffix)]
        rest = list(args)
        if tool in ("npm", "pnpm", "yarn", "bun") and rest and rest[0] in ("exec", "dlx", "x"):
            tool, rest = "npx", rest[1:]
        if tool in ("npm", "pnpm", "yarn", "bun"):
            self._mcp_package_script(rel, name, tool, rest, conf or {})
            return
        if tool not in ("npx", "bunx", "pnpx", "uvx", "pipx"):
            return
        if tool == "pipx" and rest and rest[0] == "run":
            rest = rest[1:]
        spec = None
        if "--from" in rest and rest.index("--from") + 1 < len(rest):
            spec = rest[rest.index("--from") + 1]
        else:
            skip_next = False
            for arg in rest:
                if skip_next:
                    skip_next = False
                    continue
                if arg in ("-p", "--package", "--python", "--with", "--index-url"):
                    skip_next = arg not in ("-p", "--package")
                    continue
                if arg.startswith("-"):
                    continue
                spec = arg
                break
        if not spec or spec.startswith((".", "/", "$", "~")):
            return
        if tool in ("uvx", "pipx"):
            pinned = re.search(r"==\s*\d[\w.+-]*$", spec) is not None or re.search(r"@[0-9a-f]{40}$", spec) is not None
        else:
            pinned = re.search(r"^(?:@[^/@\s]+/)?[^@\s]+@v?\d+\.\d+\.\d+(?:[-+][\w.]+)?$", spec) is not None
        if not pinned:
            self.add("mcp-unpinned-package", "medium", rel, 0, f"{name}: {tool} {clean_text(spec, 100)}")

    def _mcp_package_script(self, rel, name, tool, args, conf):
        """`bun run start` and the like: read package.json scripts as data; an install step resolves
        version ranges at start-up, and an npx-style call can fetch an unpinned package."""
        script, cwd, skip = None, None, False
        for i, arg in enumerate(args):
            if skip:
                skip = False
                continue
            if arg in ("--cwd", "--prefix", "-C", "--dir"):
                cwd, skip = (args[i + 1] if i + 1 < len(args) else None), True
            elif arg.startswith(("--cwd=", "--prefix=", "--dir=")):
                cwd = arg.split("=", 1)[1]
            elif arg in ("start", "test") and script is None:
                script = arg
            elif arg in ("run", "run-script"):
                continue
            elif not arg.startswith("-") and script is None:
                script = arg
        if not script:
            return
        cwd = cwd or (conf.get("cwd") if isinstance(conf.get("cwd"), str) else None) or "."
        text = cwd.replace("${CLAUDE_PLUGIN_ROOT}", ".").replace("$CLAUDE_PLUGIN_ROOT", ".")
        if path_escapes(text):
            return
        pkg_path = os.path.normpath(os.path.join(self.root, text, "package.json"))
        pkg = self._safe_json(pkg_path) if within(self.root, pkg_path) else None
        if not isinstance(pkg, dict) or not isinstance(pkg.get("scripts"), dict):
            return
        body = pkg["scripts"].get(script)
        if not isinstance(body, str):
            return
        prel = self.rel(pkg_path)
        body = body[:2000]
        if re.search(r"\b(?:npm|pnpm|yarn|bun)\s+(?:install|i|add|ci)\b", body) and not re.search(
                r"--frozen-lockfile|--immutable|\bnpm\s+ci\b", body):
            ranges = []
            for field in ("dependencies", "optionalDependencies"):
                deps = pkg.get(field)
                if isinstance(deps, dict):
                    ranges += [f"{safe_name(k)}@{clean_text(str(v), 30)}" for k, v in deps.items()
                               if not re.fullmatch(r"v?\d+\.\d+\.\d+(?:[-+][\w.]+)?", str(v).strip())]
            if ranges:
                self.add("mcp-unpinned-package", "medium", prel, 0,
                         f"{name}: {tool} {script} runs an install with version ranges ({', '.join(ranges[:4])})")
        for m in re.finditer(r"\b(?:npx|bunx|pnpx|uvx|pipx\s+run|(?:npm|pnpm|yarn|bun)\s+(?:exec|dlx|x))\s+"
                             r"((?:-{1,2}[\w-]+\s+){0,4})([^\s;&|]+)", body):
            spec = m.group(2)
            pinned = (re.search(r"@v?\d+\.\d+\.\d+(?:[-+][\w.]+)?$", spec) or re.search(r"==\s*\d", spec)
                      or spec.startswith((".", "/", "$")))
            if not pinned:
                self.add("mcp-unpinned-package", "medium", prel, 0,
                         f"{name}: {tool} {script} calls {clean_text(m.group(0), 80)}")

    def _mcp_secrets(self, rel, name, conf, args, url):
        find = core().find_secrets
        pairs = []
        for field in ("env", "headers"):
            value = conf.get(field)
            if isinstance(value, dict):
                pairs.extend((str(k), v) for k, v in value.items() if isinstance(v, str))
        secretish = re.compile(r"(?i)token|secret|password|passwd|api[_-]?key|authorization|credential")
        for key, value in pairs:
            literal = value.strip()
            placeholder = (not literal or "${" in literal or literal.startswith(("$", "<", "{{"))
                           or literal.lower() in ("true", "false"))
            if find(f"{key}={value}") or find(value) or (secretish.search(key) and not placeholder and len(literal) >= 12
                                                         and not re.fullmatch(r"(?i)bearer\s+\$\{?\w+\}?", literal)):
                self.add("mcp-literal-secret", "high", rel, 0, f"{name}: {key}=[REDACTED]")
        joined = " ".join(args + [url])
        if joined.strip() and find(joined):
            self.add("mcp-literal-secret", "high", rel, 0, f"{name}: {make_evidence(joined)}")

    # ------------------------------------------------------------ walk

    def rel(self, full) -> str:
        return os.path.relpath(full, self.root).replace(os.sep, "/")

    def _walk(self):
        stop = False
        for dirpath, dirnames, filenames in os.walk(self.root, followlinks=False):
            keep = []
            for d in sorted(dirnames):
                full = os.path.join(dirpath, d)
                self._check_name(full, d)
                if is_link(full):
                    self._link(full)
                elif d not in SKIP_DIRS:
                    keep.append(d)
            dirnames[:] = keep
            for name in sorted(filenames):
                full = os.path.join(dirpath, name)
                self._check_name(full, name)
                if is_link(full):
                    self._link(full)
                    continue
                self.files += 1
                if self.files > MAX_FILES:
                    self.add("file-limit-reached", "medium", self.rel(dirpath), 0,
                             f"more than {MAX_FILES} files; the rest was not scanned")
                    stop = True
                    break
                try:
                    self._file(full)
                except OSError as exc:
                    self.add("unreadable-file", "info", self.rel(full), 0, type(exc).__name__)
            if stop:
                break

    def _check_name(self, full, name):
        """A newline, control, bidi or invisible character in a file or folder name can forge card text."""
        m = BAD_NAME_RX.search(name)
        if m:
            self.add("hidden-unicode", "high", self.rel(full), 0,
                     f"U+{ord(m.group(0)):04X} in a file or folder name: {make_evidence(name[:200])}")

    def _link(self, full):
        rel = self.rel(full)
        try:
            target = os.readlink(full)
        except OSError:
            self.add("symlink-escape", "high", rel, 0, "link target unreadable")
            return
        resolved = target if os.path.isabs(target) else os.path.join(os.path.dirname(full), target)
        if re.match(r"^[A-Za-z]:", target) or not within(self.root, os.path.normpath(resolved)):
            self.add("symlink-escape", "high", rel, 0, f"-> {make_evidence(target[:120])}")

    def _file(self, full):
        rel = self.rel(full)
        size = os.lstat(full).st_size
        with open(full, "rb") as fh:
            head = fh.read(HEADER_BYTES)
            kind = binary_kind(head)
            if kind:
                self.binaries += 1
                self.add("opaque-binary", "high", rel, 0, f"{kind} executable ({size} bytes)")
                return
            if size > MAX_FILE_BYTES:
                self.add("large-file-skipped", "info", rel, 0, f"{size} bytes, above the 2 MB scan cap")
                return
            data = head + fh.read(MAX_FILE_BYTES + 1 - len(head))
        if b"\x00" in data[:8192]:
            return  # images, fonts, archives: no text rules
        text = data.decode("utf-8", errors="replace")
        name = os.path.basename(full)
        ext = os.path.splitext(name)[1].lower()
        parts = rel.split("/")
        is_code = ext in CODE_EXT or text.startswith("#!")
        is_md = ext in MD_EXT
        surface = is_md and (any(p in SURFACE_DIRS for p in parts[:-1]) or name.lower() == "skill.md")
        low = text.lower()
        if is_code:
            self.scripts += 1
        self._secrets(rel, text, is_md)
        self._hidden(rel, text, is_code)
        if is_code:
            shell = ext in SHELL_EXT or (not ext and re.match(r"#![^\n]*\b(?:ba|z|k|da)?sh\b", text) is not None)
            if shell:
                download = DOWNLOAD_EXEC_SHELL
            else:
                download = program_download_rule(text)
            self.apply(CODE_RULES + (download,), rel, text, low)
            self.apply((DYNAMIC_EXEC_PY,) if ext in (".py", ".pyw") else
                       (DYNAMIC_EXEC_JS,) if ext in (".js", ".mjs", ".cjs", ".ts", ".mts", ".cts", ".jsx", ".tsx")
                       else (), rel, text, low)
        if surface:
            self.apply(SURFACE_RULES, rel, text, low,
                       downgrade={"instruction-override": fixture_fence_lines(text)
                                  if FIXTURE_DIRS.intersection(p.lower() for p in parts[:-1]) else set()})
            self._front_matter_tools(rel, text)
            if "commands" in parts[:-1]:
                m = INLINE_SHELL_RX.search(text)
                if m:
                    line = text.count("\n", 0, m.start()) + 1
                    self.add("inline-shell", "info", rel, line, make_evidence(m.group(0).strip()))
        hook_file = rel in self.hook_files or parts[0] == "hooks"
        if hook_file:
            self.apply((AUTO_APPROVE, NETWORK_IN_SCRIPT), rel, text, low)
            m = CONTEXT_MARKER.search(text)
            if m:
                self.context_files[rel] = text.count("\n", 0, m.start()) + 1
        if is_code or ext in CONFIG_EXT:
            for m in HOST_RX.finditer(text[:MAX_FILE_BYTES]):
                self.add_host(m.group(1))
                if len(self.hosts) >= MAX_HOSTS:
                    break

    def apply(self, rules, rel, text, low, downgrade=None):
        """Run line rules. A check may return a severity string instead of True; `downgrade` maps a rule id
        to line numbers where a high finding is reported as medium."""
        active = [r for r in rules if any(k in low for k in r.keys)]
        if not active:
            return
        for lineno, seg in iter_segments(text):
            seg_low = seg.lower()
            for rule in active:
                if not any(k in seg_low for k in rule.keys):
                    continue
                m = rule.rx.search(seg)
                if not m:
                    continue
                verdict = True if rule.check is None else rule.check(seg, m)
                if not verdict:
                    continue
                severity = verdict if isinstance(verdict, str) else rule.severity
                if severity == "high" and lineno in (downgrade or {}).get(rule.rid, ()):
                    severity = "medium"
                self.add(rule.rid, severity, rel, lineno, make_evidence(seg, m.group(0), m.start()))

    def _secrets(self, rel, text, is_md=False):
        """Format-specific tokens are high anywhere; keyword assignments are high in shipped code and
        config, medium in tests, and info (secret-example) when the value is an obvious stand-in."""
        kb_core = core()
        if not kb_core.find_secrets(text):
            return
        in_tests = is_test_path(rel)
        found = 0
        for lineno, seg in iter_segments(text):
            spans = kb_core.find_secret_spans(seg)
            if not spans:
                continue
            real = [(n, a, b) for n, a, b in spans
                    if n in STRONG_SECRET_RULES or not example_value(seg[a:b], seg[max(0, a - 60):a])]
            names = ", ".join(dict.fromkeys(n for n, _a, _b in (real or spans)))
            if not real:
                self.add("secret-example", "info", rel, lineno, f"{names}: {make_evidence(seg)}")
            elif in_tests:  # fixtures of a plugin's own tests: reviewed, not blocked
                self.add("secret", "medium", rel, lineno, f"{names} (test or example file): {make_evidence(seg)}")
            elif is_md and all(n not in STRONG_SECRET_RULES for n, _a, _b in real):
                # a keyword assignment in documentation is usually a sample; a token format still blocks
                self.add("secret", "medium", rel, lineno, f"{names} (documentation): {make_evidence(seg)}")
            else:
                self.add("secret", "high", rel, lineno, f"{names}: {make_evidence(seg)}")
            found += 1
            if found >= 2 * MAX_PER_RULE_FILE:
                break

    def _hidden(self, rel, text, is_code=False):
        reported = 0
        exempted = {}  # line start -> selectors exempted on that line
        for m in HIDDEN_RX.finditer(text):
            pos, ch = m.start(), m.group(0)
            if ch == "\ufeff" and pos == 0:
                continue
            prev = text[pos - 1] if pos else ""
            nxt = text[pos + 1] if pos + 1 < len(text) else ""
            if ch == "\ufeff" and is_code and (prev in "\"'" or nxt in "\"'"):
                continue  # a byte-order mark written as test data inside a string literal
            if (ch in "\ufe0e\ufe0f" and prev and not _selector(prev) and not _selector(nxt)
                    and not HIDDEN_RX.match(prev) and (ord(prev) >= 0x2000 or nxt == "\u20e3")):
                # one presentation selector right after a visible symbol or emoji, or in a keycap. Emoji
                # presentation (FE0F) is ordinary and unlimited; text presentation (FE0E) is rare, so more than
                # three on one line could carry a FE0E/FE0F bit pattern and is reported
                if ch == "\ufe0f":
                    continue
                start = text.rfind("\n", 0, pos) + 1
                exempted[start] = exempted.get(start, 0) + 1
                if exempted[start] <= MAX_EXEMPT_SELECTORS:
                    continue
            if ch == "\u200d" and (_emoji(prev) or _emoji(nxt)):
                continue  # emoji sequence joiner
            if ch in "\u200c\u200d\u200e\u200f" and (_script_letter(prev) or _script_letter(nxt)):
                continue  # joiners and direction marks inside non-Latin script text
            line = text.count("\n", 0, pos) + 1
            start = text.rfind("\n", 0, pos) + 1
            end = text.find("\n", pos)
            segment = text[max(start, pos - 2000):(end if end != -1 else len(text))][:4096]
            # a plugin's own tests often carry hostile characters as fixtures: reviewed, not blocked;
            # tag characters (invisible text) stay high everywhere
            severity = "medium" if is_test_path(rel) and not TAG_RX.match(ch) else "high"
            self.add("hidden-unicode", severity, rel, line, f"U+{ord(ch):04X}: " + make_evidence(segment, ch))
            reported += 1
            if reported >= MAX_PER_RULE_FILE:
                break

    def _front_matter_tools(self, rel, text):
        front, _body = core().parse_front_matter(text[:65536])
        value = (front or {}).get("allowed-tools")
        if not value:
            return
        items = value if isinstance(value, list) else re.split(r",\s*|\s+(?=[A-Z*])", str(value))
        for item in items:
            token = str(item).strip().strip("\"'").replace(" ", "").lower()
            if token in UNRESTRICTED_SHELL:
                lines = text.split("\n", 80)
                line = next((i + 1 for i, ln in enumerate(lines[:80]) if ln.startswith("allowed-tools")), 0)
                self.add("broad-tools", "medium", rel, line, f"allowed-tools: {clean_text(str(item), 60)}")
                return

    # ------------------------------------------------------------ inventory

    def _inventory(self):
        plugin = self.plugin_name()
        skill_dirs = []
        for base in self.declared("skills") + [os.path.join(self.root, "skills")]:
            if not os.path.isdir(base) or is_link(base):
                continue
            if os.path.isfile(os.path.join(base, "SKILL.md")):
                skill_dirs.append(base)
                continue
            for child in sorted(os.listdir(base)):
                full = os.path.join(base, child)
                if not is_link(full) and os.path.isfile(os.path.join(full, "SKILL.md")):
                    skill_dirs.append(full)
                if len(skill_dirs) > MAX_CAPABILITIES:
                    break
        seen = set()
        for d in skill_dirs:
            key = os.path.normcase(d)
            if key in seen:
                continue
            seen.add(key)
            if not self._room():
                return
            md = os.path.join(d, "SKILL.md")
            front = self._front(md)
            name = safe_name(front.get("name") or os.path.basename(d), "skill")
            self.skills.append(self._cap("skill", plugin, name, front, md))
        for kind, folder, target in (("command", "commands", self.commands), ("agent", "agents", self.agents)):
            names = set()
            for base in self.declared(folder) + [os.path.join(self.root, folder)]:
                for md in self._md_files(base):
                    front = self._front(md)
                    stem = os.path.splitext(os.path.basename(md))[0]
                    name = safe_name(front.get("name") if kind == "agent" and front.get("name") else stem, kind)
                    if name in names:
                        continue
                    if not self._room():
                        return
                    names.add(name)
                    target.append(self._cap(kind, plugin, name, front, md))

    def _room(self) -> bool:
        """Capability inventory cap (skills + commands + agents + MCP servers) with one finding when hit."""
        if len(self.skills) + len(self.commands) + len(self.agents) + len(self.mcp) < MAX_CAPABILITIES:
            return True
        self.add("capability-limit-reached", "medium", "", 0,
                 f"more than {MAX_CAPABILITIES} capabilities; the rest is not catalogued")
        return False

    def _md_files(self, base):
        if os.path.isfile(base) and base.lower().endswith(".md") and not is_link(base):
            return [base]
        if not os.path.isdir(base) or is_link(base):
            return []
        found = []
        for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
            dirnames[:] = sorted(d for d in dirnames if not is_link(os.path.join(dirpath, d)) and not d.startswith("."))
            for name in sorted(filenames):
                full = os.path.join(dirpath, name)
                if name.lower().endswith(".md") and not is_link(full) and name.lower() != "readme.md":
                    found.append(full)
                if len(found) >= 500:
                    return found
        return found

    def _front(self, md) -> dict:
        try:
            if is_link(md):
                return {}
            with open(md, "rb") as fh:
                text = fh.read(65536).decode("utf-8", errors="replace")
        except OSError:
            return {}
        front, _body = core().parse_front_matter(text)
        return front if isinstance(front, dict) else {}

    def _cap(self, kind, plugin, name, front, md) -> dict:
        raw = front.get("description", "")
        full = clean_text(raw, 5000)
        handle = f"/{plugin}:{name}" if kind == "command" else f"{plugin}:{name}"
        return {"type": kind, "name": name, "handle": handle, "description": clean_text(raw, self.desc_chars),
                "path": clean_text(self.rel(md), 200), "_full": full}

    def _protective(self) -> bool:
        guard_events = {"PreToolUse", "Stop", "SubagentStop", "PermissionRequest"}
        if not guard_events.intersection(self.hook_events):
            return False
        words = f"{self.manifest.get('description', '') if isinstance(self.manifest, dict) else ''} {self.hook_description}"
        return re.search(r"(?i)\b(?:secur\w*|safety|safe|protect\w*|guard\w*|block\w*|vulnerab\w*|secrets?|danger\w*)",
                         str(words)[:4000]) is not None


STRONG_SECRET_RULES = {"aws-access-key-id", "private-key", "github-token", "slack-token", "stripe-key", "google-api-key",
                       "openai-key", "jwt"}
_WORDY_VALUE = re.compile(r"[A-Za-z]{1,40}\d{0,6}(?:[-_:./](?:[A-Za-z]{1,40}\d{0,6}|\d{1,6})){0,10}")


def _low_entropy(value: str) -> bool:
    counts = {}
    for ch in value:
        counts[ch] = counts.get(ch, 0) + 1
    entropy = -sum(n / len(value) * math.log2(n / len(value)) for n in counts.values()) if value else 0.0
    return len(counts) < 10 or entropy < 3.0


def example_value(value: str, context: str = "") -> bool:
    """A keyword-assignment value that is a stand-in, not a credential: elided, templated, plain words, or
    named fake, dummy, example, sample or placeholder (the key name just before it counts only for a
    low-entropy value)."""
    value = value.rstrip(";,")
    marker = re.compile(r"(?i)fake|dummy|example|sample|placeholder")
    if marker.search(value):
        return True
    if marker.search(context[-40:]) and _low_entropy(value):
        return True  # the key name counts only for a value that does not look random
    if any(mark in value for mark in ("...", "…", "{", "}", "$", "%", "<", ">", "*")):
        return True
    return _WORDY_VALUE.fullmatch(value) is not None or len(set(value.lower())) < 8


def is_test_path(rel: str) -> bool:
    parts = rel.lower().split("/")
    name = parts[-1]
    return (any(p in ("test", "tests", "__tests__", "fixtures", "testdata", "spec", "examples", "example")
                for p in parts[:-1])
            or name.startswith("test_") or ".test." in name or ".spec." in name or name.endswith("_test.py"))


MAX_EXEMPT_SELECTORS = 3


def _selector(ch: str) -> bool:
    return bool(ch) and ("\ufe00" <= ch <= "\ufe0f" or "\U000e0100" <= ch <= "\U000e01ef")


def _emoji(ch: str) -> bool:
    return bool(ch) and (ord(ch) >= 0x1F000 or 0x2600 <= ord(ch) <= 0x27BF or ch in "\ufe0f\u2640\u2642\u2695")


def _script_letter(ch: str) -> bool:
    return bool(ch) and ord(ch) >= 0x0590 and ch.isalpha()


def binary_kind(head: bytes):
    """Executable format from the first bytes (never executes or loads the file)."""
    if head.startswith(b"\x7fELF"):
        return "ELF"
    if head[:4] in (b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf", b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe"):
        return "Mach-O"
    if head[:4] == b"\xca\xfe\xba\xbe" and len(head) >= 8 and int.from_bytes(head[4:8], "big") < 30:
        return "Mach-O"
    if head[:2] == b"MZ" and len(head) >= 0x40:
        offset = int.from_bytes(head[0x3C:0x40], "little")
        if 0 < offset <= len(head) - 4 and head[offset:offset + 4] == b"PE\x00\x00":
            return "PE"
    return None


def scan_plugin(path, desc_chars=300) -> dict:
    return PluginScan(path, desc_chars).run()


def is_plugin_dir(path: Path) -> bool:
    if not path.is_dir() or is_link(path):
        return False
    if any((path / rel).is_file() for rel in MANIFEST_CANDIDATES):
        return True
    return any((path / d).is_dir() for d in ("skills", "commands", "agents", "hooks")) or (path / ".mcp.json").is_file()


def verdict_exit(results, strict=False) -> int:
    verdicts = {r["verdict"] for r in results}
    if "block" in verdicts or (strict and "review" in verdicts):
        return EXIT_BLOCK
    return EXIT_REVIEW if "review" in verdicts else EXIT_OK


def print_scan(result: dict, limit: int = 40) -> None:
    c = result["counts"]
    out(f"{result['verdict'].upper():6} {result['plugin']} ({result['dir']})  high={c['high']} medium={c['medium']} "
        f"info={c['info']} files={result['inventory']['files']} time={result['elapsed']:.2f}s")
    shown = [f for f in result["findings"] if f["severity"] != "info"] + \
            [f for f in result["findings"] if f["severity"] == "info"]
    for f in shown[:limit]:
        where = f"{f['file']}:{f['line']}" if f["line"] else (f["file"] or "-")
        out(f"  [{f['severity']}] {f['rule']}  {where}  {f['evidence']}")
    if len(shown) > limit:
        out(f"  ... {len(shown) - limit} more (use --json)")


def cmd_scan(args) -> int:
    cfg = load_config()
    results = []
    for path in args.paths:
        if not os.path.isdir(path):
            raise PluginError(f"not a directory: {path}")
        results.append(scan_plugin(path, cfg_int(cfg, "LLM_PLUGINS_DESC_CHARS")))
    code = verdict_exit(results, args.strict)
    if args.json:
        summary = {v: sum(1 for r in results if r["verdict"] == v) for v in ("pass", "review", "block")}
        out(json.dumps({"summary": summary, "strict": args.strict, "plugins": results}, indent=2, ensure_ascii=False))
    else:
        for result in results:
            print_scan(result)
    return code


# --------------------------------------------------------------------------- discovery

def sibling_meta(plugin_dir: Path) -> dict:
    """Hosted-app copies keep `<dir>.meta.json` beside the plugin: read its marketplace name as data."""
    data, problem = read_json_capped(plugin_dir.parent / f"{plugin_dir.name}.meta.json", 65536)
    if problem or not isinstance(data, dict):
        return {}
    market = data.get("marketplace_name")
    return {"origin": safe_name(market, "unknown")} if isinstance(market, str) else {}


def plugins_under(root: Path) -> list:
    root = Path(os.path.expanduser(str(root)))
    if is_plugin_dir(root) and any((root / rel).is_file() for rel in MANIFEST_CANDIDATES):
        return [root]
    if not root.is_dir():
        return []
    found = []
    for child in sorted(root.iterdir(), key=lambda p: p.name):
        if not child.name.startswith(".") and is_plugin_dir(child):
            found.append(child)
    return found


def discover_auto(cfg) -> dict:
    """{tool label: [(plugin dir, meta)]} for every install location found (labels with no plugins included)."""
    tl = toolchain()
    base = tl.home()
    found = {}
    claude = base / ".claude"
    if claude.is_dir():
        found["claude-code"] = []
        result = tl.discover_claude(claude)
        enabled = {e["id"]: e.get("enabled") for e in result.extensions}
        installed = tl.read_json(claude / "plugins" / "installed_plugins.json") or {}
        plugins_home = os.path.realpath(claude / "plugins")
        for key, entries in sorted((installed.get("plugins") or {}).items()):
            if not isinstance(entries, list) or not entries or not isinstance(entries[0], dict):
                continue
            path = entries[0].get("installPath")
            if not isinstance(path, str) or not path:
                continue
            p = Path(path)
            if not within(plugins_home, os.path.realpath(p)) or not is_plugin_dir(p):
                continue  # a recorded path outside the tool's plugin folder is not read
            market = key.partition("@")[2]
            found["claude-code"].append((p, {"origin": safe_name(market, "unknown") if market else "unknown",
                                             "enabled": enabled.get(key)}))
        synced = claude / "plugins" / "synced"
        if synced.is_dir() and not is_link(synced):
            found["claude-app"] = []
            for group in sorted(synced.iterdir(), key=lambda p: p.name):
                if group.is_dir() and not is_link(group):
                    for child in plugins_under(group):
                        found["claude-app"].append((child, sibling_meta(child)))
    for label, subdir, _discover in tl.PROVIDERS:
        if label == "claude-code":
            continue
        root = base / subdir / "plugins"
        if root.is_dir() and not is_link(root):
            found[label] = [(p, {"origin": "local"}) for p in plugins_under(root)]
    for entry in [e for e in str(cfg.get("LLM_PLUGINS_DIRS") or "").split(os.pathsep) if e.strip()]:
        label, sep, path = entry.partition("=")
        if not sep or re.match(r"^[A-Za-z]$", label):  # no label, or a drive letter
            label, path = "extra", entry
        label = safe_name(label, "extra")
        found.setdefault(label, []).extend((p, {"origin": "local"}) for p in plugins_under(Path(path.strip())))
    return found


# --------------------------------------------------------------------------- catalog

def card_text(entry: dict, generated: str) -> str:
    """Capability card: front matter, notice line, one section per capability. Never a skill body."""
    plugin = entry["plugin"]
    lines = [
        "---",
        "kind: plugin-capability",
        "title: " + json.dumps(f"Plugin {plugin} ({entry['tool']})"),
        f"plugin: {plugin}",
        f"tool: {entry['tool']}",
        f"origin: {entry['origin']}",
        f"version: {json.dumps(entry['version'] or 'unknown')}",
        f"verdict: {entry['verdict']}",
        f"protective: {'true' if entry['protective'] else 'false'}",
        f"generated: {generated}",
        "---",
        "",
        CARD_NOTICE,
        "",
        f"## plugin {plugin}",
        "",
        entry["description"] or "(no description)",
        "",
        f"- Tool: {entry['tool']}; origin: {entry['origin']}; verdict: {entry['verdict']}"
        + ("; protective hooks" if entry["protective"] else ""),
        f"- Components: {len([c for c in entry['capabilities'] if c['type'] == 'skill'])} skills, "
        f"{len([c for c in entry['capabilities'] if c['type'] == 'command'])} commands, "
        f"{len([c for c in entry['capabilities'] if c['type'] == 'agent'])} agents, "
        f"{len(entry['mcp'])} MCP servers; hook events: {', '.join(entry['hook_events']) or 'none'}",
        "",
    ]
    for cap in entry["capabilities"]:
        lines += [f"## {cap['type']} {cap['handle'].lstrip('/') if cap['type'] != 'command' else cap['handle']}", "",
                  cap["description"] or "(no description)", ""]
        if cap["type"] == "mcp":
            lines.append(f"- Invoke: MCP server `{cap['name']}` of plugin `{plugin}` ({cap['transport']}, "
                         f"{cap['target'] or 'no target'}); its tools are listed by the tool that runs the plugin")
        else:
            how = {"skill": "skill", "command": "slash command", "agent": "subagent"}[cap["type"]]
            lines.append(f"- Invoke: `{cap['handle']}` ({how})")
        lines += [f"- Path: {cap['path']}", ""]
    return "\n".join(lines).rstrip("\n") + "\n"


def catalog_entry(result: dict, tool: str, meta: dict, generated: str, scanned: bool) -> dict:
    plugin = result["plugin"]
    inv = result["inventory"]
    caps = [dict(c) for c in inv["skills"] + inv["commands"] + inv["agents"]]
    for server in inv["mcp"]:
        caps.append({"type": "mcp", "name": server["name"], "handle": f"{plugin}:{server['name']}",
                     "description": f"MCP server ({server['transport']}) {server['target']}".strip(),
                     "path": ".mcp.json", "transport": server["transport"], "target": server["target"]})
    return {
        "tool": tool,
        "plugin": plugin,
        "dir": result["dir"],
        "path": result["path"],
        "origin": meta.get("origin") or "local",
        "enabled": meta.get("enabled"),
        "version": result["manifest"]["version"],
        "description": result["manifest"]["description"],
        "verdict": result["verdict"] if scanned else "unscanned",
        "counts": result["counts"] if scanned else {},
        "rules": sorted({f["rule"] for f in result["findings"] if f["severity"] in ("high", "medium")}) if scanned else [],
        "protective": inv["protective"],
        "listing_chars": inv["listing_chars"],
        "hook_events": inv["hook_events"],
        "mcp": inv["mcp"],
        "hosts": inv["hosts"],
        "scripts": inv["scripts"],
        "binaries": inv["binaries"],
        "capabilities": caps,
        "generated": generated,
    }


def is_generated_card(path: Path) -> bool:
    try:
        if is_link(path):
            return False
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            head = fh.read(400)
    except OSError:
        return False
    return head.startswith("---\n") and "\nkind: plugin-capability\n" in head


def load_catalog(base: Path) -> dict:
    data, problem = read_json_capped(catalog_path(base), 64 * 1024 * 1024)
    if problem or not isinstance(data, dict) or not isinstance(data.get("plugins"), list):
        return {"version": CATALOG_VERSION, "generated": None, "tools": {}, "plugins": []}
    data.setdefault("tools", {})
    return data


class InventoryOnly(PluginScan):
    """Inventory without the security rules (catalog --no-scan)."""

    def _walk(self):
        return

    def _hook_context(self):
        return


def build_catalog(groups: dict, out_dir: Path, cfg, scan=True, progress=None) -> dict:
    generated = kb.iso(kb.utcnow())
    desc_chars = cfg_int(cfg, "LLM_PLUGINS_DESC_CHARS")
    catalog = load_catalog(out_dir)
    labels = set(groups)
    plugins = [p for p in catalog["plugins"] if isinstance(p, dict) and p.get("tool") not in labels]
    written = []
    for label, items in sorted(groups.items()):
        tool = safe_name(label, "tool")
        folder = out_dir / "catalog" / tool
        folder.mkdir(parents=True, exist_ok=True)
        used = set()
        for path, meta in items:
            result = (PluginScan if scan else InventoryOnly)(path, desc_chars).run()
            entry = catalog_entry(result, tool, meta, generated, scan)
            stem = entry["plugin"]
            n = 2
            while stem.lower() in used:  # file systems may ignore case: Demo.md and demo.md are one file
                stem = f"{entry['plugin']}-{n}"
                n += 1
            used.add(stem.lower())
            card = folder / f"{stem}.md"
            card.write_text(card_text(entry, generated), encoding="utf-8")
            entry["card"] = f"catalog/{tool}/{stem}.md"
            entry["scan_seconds"] = result["elapsed"]
            plugins.append(entry)
            written.append(entry)
            if progress:
                progress(entry)
        for old in sorted(folder.glob("*.md")):
            if old.stem.lower() not in used and is_generated_card(old):
                old.unlink()
        catalog["tools"][tool] = generated
    catalog.update({"version": CATALOG_VERSION, "generated": generated, "plugins": plugins})
    write_json_atomic(catalog_path(out_dir), catalog)
    return {"catalog": catalog, "written": written}


def cmd_catalog(args) -> int:
    cfg = load_config()
    if not args.auto and not args.from_roots:
        raise PluginError("catalog needs --auto or at least one --from <root>")
    groups = {}
    if args.auto:
        groups.update({k: list(v) for k, v in discover_auto(cfg).items()})
    for root in args.from_roots or []:
        if not os.path.isdir(os.path.expanduser(root)):
            raise PluginError(f"not a directory: {root}")
        label = safe_name(args.tool or "claude-code", "tool")
        for p in plugins_under(Path(root)):
            groups.setdefault(label, []).append((p, sibling_meta(p) or {"origin": "local"}))
    total = sum(len(v) for v in groups.values())
    if total == 0:
        err("no plugin found in the given roots")
        return EXIT_NONE
    out_dir = Path(os.path.expanduser(args.out)) if args.out else plugins_dir(cfg)
    result = build_catalog(groups, out_dir, cfg, scan=not args.no_scan,
                           progress=None if args.json else
                           lambda e: out(f"{e['verdict']:9} {e['tool']}/{e['plugin']}  "
                                         f"{len(e['capabilities'])} capabilities  {e['scan_seconds']:.2f}s"))
    written = result["written"]
    summary = {v: sum(1 for e in written if e["verdict"] == v) for v in ("pass", "review", "block", "unscanned")}
    reindex = "requested"
    try:
        kb.http_json(cfg, "POST", "/reindex", {}, timeout=30)
    except kb.ServiceUnavailable:
        reindex = "service unreachable; cards are indexed on its next scan"
    if args.json:
        out(json.dumps({"out": out_dir.as_posix(), "summary": summary, "plugins": len(written),
                        "reindex": reindex}, indent=2))
    else:
        out(f"catalog: {out_dir.as_posix()}  plugins={len(written)}  " +
            "  ".join(f"{k}={v}" for k, v in summary.items() if v))
        out(f"knowledge base reindex: {reindex}")
    return EXIT_OK


# --------------------------------------------------------------------------- marketplace

def load_marketplace(mdir: Path) -> dict:
    data, problem = read_json_capped(mdir / ".claude-plugin" / "marketplace.json", 8 * 1024 * 1024)
    if problem:
        raise PluginError(f"marketplace file {problem}: {(mdir / MARKETPLACE_FILE).as_posix()}")
    if not isinstance(data, dict) or not isinstance(data.get("plugins"), list):
        raise PluginError("marketplace file has no plugins list")
    return data


def source_info(source) -> dict:
    if isinstance(source, str):
        return {"type": "in-repo", "path": source, "pinned": True}
    if not isinstance(source, dict):
        return {"type": "unknown", "pinned": False}
    kind = str(source.get("source") or "unknown")
    url = source.get("url") if isinstance(source.get("url"), str) else ""
    if kind == "github" and isinstance(source.get("repo"), str):
        url = f"https://github.com/{source['repo']}.git"
    sha = source.get("sha") if isinstance(source.get("sha"), str) else ""
    return {"type": kind, "url": url, "sha": sha, "ref": source.get("ref") if isinstance(source.get("ref"), str) else "",
            "path": source.get("path") if isinstance(source.get("path"), str) else "",
            "pinned": bool(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", sha or ""))}


def market_entries(data: dict, desc_chars: int) -> list:
    entries = []
    for item in data["plugins"]:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            continue
        info = source_info(item.get("source"))
        author = item.get("author")
        author = author.get("name", "") if isinstance(author, dict) else author if isinstance(author, str) else ""
        where = ("in-repo" if info["type"] == "in-repo" else
                 f"outside repo, pinned sha" if info["pinned"] else "outside repo, no pinned sha")
        entries.append({"name": safe_name(item["name"]), "category": clean_text(item.get("category", ""), 40),
                        "author": clean_text(author, 80), "description": clean_text(item.get("description", ""),
                                                                                    desc_chars),
                        "source_type": info["type"], "source": where, "pinned": info["pinned"]})
    return entries


def cmd_marketplace(args) -> int:
    cfg = load_config()
    mdir = Path(os.path.expanduser(args.marketplace_dir))
    data = load_marketplace(mdir)
    entries = market_entries(data, cfg_int(cfg, "LLM_PLUGINS_DESC_CHARS"))
    installed = {p.get("plugin") for p in load_catalog(plugins_dir(cfg))["plugins"] if isinstance(p, dict)}
    if not args.all:
        entries = [e for e in entries if e["name"] not in installed]
    if args.query:
        terms = query_terms(args.query)
        entries = [e for e in entries if all(t in f"{e['name']} {e['category']} {e['description']}".lower()
                                             for t in terms)]
    if args.json:
        out(json.dumps({"marketplace": safe_name(data.get("name"), "marketplace"), "entries": entries}, indent=2,
                       ensure_ascii=False))
    else:
        for e in entries:
            mark = " [installed]" if e["name"] in installed else ""
            out(f"{e['name']}{mark}  [{e['category'] or '-'}]  {e['author'] or '-'}  ({e['source']})")
            if e["description"]:
                out(f"    {e['description']}")
        out(f"{len(entries)} entries")
    return EXIT_OK if entries else EXIT_NONE


# --------------------------------------------------------------------------- fetch

def _rmtree(path: Path) -> None:
    def onerror(func, target, _exc):
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except OSError:
            pass
    if path.is_symlink():
        path.unlink()
    elif path.exists():
        if sys.version_info >= (3, 12):
            shutil.rmtree(path, onexc=onerror)
        else:
            shutil.rmtree(path, onerror=onerror)


def _copy_plugin(src: Path, dest: Path) -> None:
    shutil.copytree(src, dest, symlinks=True, ignore=shutil.ignore_patterns(".git"))


def no_link_between(base: Path, target: Path) -> bool:
    """True when no component from `base` down to `target` is a symlink or junction and the real path of
    `target` stays inside the real path of `base`."""
    probe = Path(target)
    while within(str(base), str(probe)) and os.path.normcase(str(probe)) != os.path.normcase(str(base)):
        if is_link(probe):
            return False
        probe = probe.parent
    return within(os.path.realpath(base), os.path.realpath(target))


def check_url(url: str, allowed) -> str:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https":
        raise Refused(f"only https sources are fetched: {url[:120]}")
    if parsed.username or parsed.password:
        raise Refused("source URL carries credentials")
    host = (parsed.hostname or "").lower()
    if host not in allowed:
        raise Refused(f"host {host or '?'} is not in LLM_PLUGINS_ALLOWED_HOSTS ({', '.join(sorted(allowed))})")
    if parsed.port not in (None, 443):
        raise Refused("non-default port refused")
    return url


def safe_subpath(value: str) -> str:
    if not value:
        return ""
    if path_escapes(value):
        raise Refused(f"source path escapes the repository: {value[:120]}")
    return value.strip("/\\")


def git_fetch(url, sha, ref, tmp: Path) -> None:
    """init + shallow fetch of one commit + detached checkout; hooks, submodules and LFS smudge disabled."""
    with tempfile.TemporaryDirectory(prefix="plugin-fetch-") as scratch:
        empty = Path(scratch) / "empty"
        empty.mkdir()
        base = ["git", "-c", f"core.hooksPath={empty.as_posix()}", "-c", "protocol.allow=never",
                "-c", "protocol.https.allow=always", "-c", "submodule.recurse=false", "-c", "filter.lfs.smudge=",
                "-c", "filter.lfs.process=", "-c", "filter.lfs.required=false", "-c", "core.fsmonitor=false",
                "-c", "advice.detachedHead=false", "-c", "http.followRedirects=false"]
        env = dict(os.environ, GIT_LFS_SKIP_SMUDGE="1", GIT_TERMINAL_PROMPT="0")
        steps = [
            base + ["init", "--quiet", f"--template={empty.as_posix()}", tmp.as_posix()],
            base + ["-C", tmp.as_posix(), "fetch", "--quiet", "--depth", "1", "--no-tags", "--no-recurse-submodules",
                    url, sha or ref or "HEAD"],
            base + ["-C", tmp.as_posix(), "checkout", "--quiet", "--detach", "FETCH_HEAD"],
        ]
        for cmd in steps:
            proc = run_cmd(cmd, env=env)
            if proc.returncode != 0:
                raise RuntimeError(f"git {cmd[len(base)] if cmd[len(base)] != '-C' else cmd[len(base) + 2]} failed: "
                                   + " ".join((proc.stderr or "").split())[:200])
        if sha:
            proc = run_cmd(base + ["-C", tmp.as_posix(), "rev-parse", "HEAD"], env=env)
            if proc.returncode != 0 or proc.stdout.strip() != sha:
                raise RuntimeError("checked-out commit does not match the pinned sha")


def cmd_fetch(args) -> int:
    cfg = load_config()
    name = args.name
    if not NAME_ARG_RX.match(name):
        raise PluginError(f"invalid plugin name: {name[:60]!r}")
    mdir = Path(os.path.expanduser(args.marketplace_dir)).resolve()
    data = load_marketplace(mdir)
    renames = data.get("renames") if isinstance(data.get("renames"), dict) else {}
    wanted = renames.get(name, name) if isinstance(renames.get(name, name), str) else name
    item = next((p for p in data["plugins"] if isinstance(p, dict) and p.get("name") == wanted), None)
    if item is None:
        err(f"not in the marketplace: {name}")
        return EXIT_NONE
    quarantine = plugins_dir(cfg) / "quarantine"
    dest = Path(os.path.expanduser(args.dest)) if args.dest else quarantine / safe_name(wanted)
    allowed = {h.strip().lower() for h in str(cfg["LLM_PLUGINS_ALLOWED_HOSTS"]).split(",") if h.strip()}
    info = source_info(item.get("source"))
    try:
        if dest.exists() or dest.is_symlink():
            if args.dest is None and within(str(quarantine), os.path.abspath(dest)):
                _rmtree(dest)  # an earlier quarantine copy of the same plugin
            elif dest.is_dir() and not any(dest.iterdir()):
                dest.rmdir()
            else:
                raise Refused(f"destination exists and is not empty: {dest.as_posix()}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        if info["type"] == "in-repo":
            rel = safe_subpath(info["path"])
            src = Path(os.path.normpath(mdir / rel))
            if not within(str(mdir), str(src)) or not src.is_dir():
                raise Refused(f"in-repo source missing or outside the marketplace: {info['path'][:120]}")
            if not no_link_between(mdir, src):
                raise Refused("in-repo source path goes through a symlink")
            _copy_plugin(src, dest)
        elif info["type"] in ("url", "github", "git-subdir"):
            check_url(info["url"], allowed)
            sub = safe_subpath(info["path"]) if info["type"] == "git-subdir" else ""
            if not info["pinned"]:
                if info["sha"]:
                    raise Refused("pinned sha is not a full commit id")
                if not args.allow_unpinned:
                    raise Refused("entry has no pinned sha (use --allow-unpinned to fetch its ref anyway)")
            ref = info["ref"] or ""
            if ref and not re.fullmatch(r"[A-Za-z0-9._/][A-Za-z0-9._/-]{0,199}", ref):
                raise Refused("ref has unexpected characters")
            tmp = dest.parent / f".fetch-{safe_name(wanted)}-{os.getpid()}"
            _rmtree(tmp)
            try:
                try:
                    git_fetch(info["url"], info["sha"] if info["pinned"] else "", ref, tmp)
                except RuntimeError as exc:
                    err(f"git failed: {exc}")
                    return EXIT_GIT
                src = Path(os.path.normpath(tmp / sub)) if sub else tmp
                if not within(str(tmp), str(src)) or not no_link_between(tmp, src) or not src.is_dir():
                    raise Refused(f"subdirectory missing or reached through a symlink in the fetched commit: {sub}")
                _copy_plugin(src, dest)
            finally:
                _rmtree(tmp)
        else:
            raise Refused(f"source type {clean_text(info['type'], 30)!r} is not fetched (only in-repo, url, github, "
                          "git-subdir)")
    except Refused as exc:
        err(f"refused: {exc}")
        return EXIT_REFUSED
    out(f"fetched {wanted} into {dest.as_posix()} (not installed)")
    result = scan_plugin(dest, cfg_int(cfg, "LLM_PLUGINS_DESC_CHARS"))
    print_scan(result)
    return verdict_exit([result])


# --------------------------------------------------------------------------- plan

def detected_tools(cfg) -> list:
    tools = []
    try:
        base = toolchain().home()
        if (base / ".claude").is_dir():
            tools.append("claude-code")
        if (base / ".claude" / "plugins" / "synced").is_dir():
            tools.append("claude-app")
        for label, subdir, _d in toolchain().PROVIDERS:
            if label != "claude-code" and (base / subdir).is_dir():
                tools.append(label)
    except (OSError, AttributeError):
        pass
    for p in load_catalog(plugins_dir(cfg))["plugins"]:
        if isinstance(p, dict) and p.get("tool") and p["tool"] not in tools:
            tools.append(p["tool"])
    return tools or ["claude-code"]


def plan_lines(action, tool, name, market) -> list:
    ref = f"{name}@{market}"
    if tool == "claude-code":
        verb = "install" if action == "add" else "uninstall"
        lines = [f"claude plugin {verb} {ref}", f"  (inside a session: /plugin {verb} {ref})"]
        if action == "add":
            lines.insert(0, f"claude plugin marketplace add <marketplace source>   # only if {market} is not added yet")
        return lines
    if tool == "claude-app":
        return [f"hosted Claude app: {'add' if action == 'add' else 'remove'} '{name}' from the app's plugin "
                "settings or an install card; plugins provided by an organization are an account setting "
                "an administrator changes"]
    return [f"manual step: {'install' if action == 'add' else 'remove'} '{name}' with {tool}'s own plugin or "
            "extension manager, if it supports this plugin format"]


def cmd_plan(args) -> int:
    cfg = load_config()
    name, _, market = args.name.partition("@")
    if not NAME_ARG_RX.match(name) or (market and not NAME_ARG_RX.match(market)):
        raise PluginError(f"invalid plugin reference: {args.name[:80]!r}")
    entries = [p for p in load_catalog(plugins_dir(cfg))["plugins"] if isinstance(p, dict) and p.get("plugin") == name]
    if args.action == "remove":
        if not entries:
            err(f"unknown plugin (not in the catalog): {name}")
            return EXIT_NONE
        if any(p.get("protective") for p in entries) and not args.i_understand:
            err(f"refused: {name} carries protective hooks (security or safety guard); removing it weakens a guard. "
                "Confirm with the owner, then pass --i-understand")
            return EXIT_REFUSED
    if args.marketplace_dir and args.action == "add":
        data = load_marketplace(Path(os.path.expanduser(args.marketplace_dir)))
        if not any(isinstance(p, dict) and p.get("name") == name for p in data["plugins"]):
            err(f"unknown plugin (not in the marketplace): {name}")
            return EXIT_NONE
        market = market or safe_name(data.get("name"), DEFAULT_MARKETPLACE)
    if not market:  # add never consults the catalog; remove uses the marketplace the plugin came from
        origins = [p.get("origin") for p in entries if p.get("origin") not in (None, "local", "unknown")]
        market = origins[0] if origins and args.action == "remove" else DEFAULT_MARKETPLACE
    tools = sorted({p["tool"] for p in entries}) if args.action == "remove" else detected_tools(cfg)
    out(f"plan: {args.action} {name}@{market} (printed only; nothing is run)")
    for tool in tools:
        for line in plan_lines(args.action, tool, name, market):
            out(f"[{tool}] {line}")
    out("after the change: python3 scripts/plugins.py catalog --auto")
    return EXIT_OK


# --------------------------------------------------------------------------- recommend

STOPWORDS = {"the", "and", "for", "with", "from", "that", "this", "into", "onto", "how", "what", "which", "use", "using",
             "best", "task", "want", "need", "should", "can", "make", "some", "about", "are", "our", "your"}


def query_terms(text: str) -> list:
    return [t for t in dict.fromkeys(re.split(r"[^a-z0-9]+", text.lower())) if len(t) >= 3 and t not in STOPWORDS]


CAP_HEADING_RX = re.compile(r"^(skill|command|agent|mcp|plugin)\s+(\S+)$")


def recommend_kb(cfg, task, k):
    max_distance = float(cfg["LLM_KB_MAX_DISTANCE"])
    assets = kb.http_json(cfg, "POST", "/search", {"q": task, "k": k, "max_distance": max_distance}).get("hits", [])
    caps = kb.http_json(cfg, "POST", "/search", {"q": task, "k": k, "max_distance": max_distance,
                                                 "source": "plugins"}).get("hits", [])
    return assets, caps


def merge_ranked(assets, caps, catalog, margin, k) -> list:
    by_card = {}
    for p in catalog.get("plugins", []):
        if isinstance(p, dict) and p.get("card"):
            by_card[p["card"][len("catalog/"):]] = p
    rows, seen = [], set()
    for hit in assets:
        key = ("asset", hit.get("source"), hit.get("path"))
        if key in seen:
            continue
        seen.add(key)
        rows.append({"type": "asset", "distance": float(hit.get("distance") or 0), "kind": hit.get("kind", ""),
                     "source": hit.get("source", ""), "path": hit.get("path", ""), "heading": hit.get("heading", "")})
    for hit in caps:
        entry = by_card.get(str(hit.get("path", "")), {})
        verdict = entry.get("verdict", "unknown")
        if verdict == "block":
            continue
        m = CAP_HEADING_RX.match(str(hit.get("heading", "")).strip())
        cap_type, handle = (m.group(1), m.group(2)) if m else ("plugin", entry.get("plugin") or hit.get("path", ""))
        key = ("plugin", handle, entry.get("tool"))
        if key in seen:
            continue
        seen.add(key)
        rows.append({"type": "plugin", "distance": float(hit.get("distance") or 0), "capability": cap_type,
                     "handle": handle, "plugin": entry.get("plugin", ""), "tool": entry.get("tool", ""),
                     "verdict": verdict, "card": entry.get("card", "")})
    rows.sort(key=lambda r: (r["distance"] + (margin if r["type"] == "plugin" else 0.0), r["type"] != "asset"))
    return rows[:k]


def recommend_lexical(task, catalog, k) -> list:
    """Capabilities from catalog.json ranked by distinct query terms matched (no toolkit assets: those need the KB
    or `kb.py search`, whose plain-text fallback covers the corpus)."""
    terms = query_terms(task)
    rows = []
    if not terms:
        return rows
    for p in catalog.get("plugins", []):
        if not isinstance(p, dict) or p.get("verdict") == "block":
            continue
        for cap in p.get("capabilities", []):
            text = f"{cap.get('handle', '')} {cap.get('description', '')} {p.get('description', '')}".lower()
            score = sum(1 for t in terms if t in text)
            if score:
                rows.append({"type": "plugin", "score": score, "capability": cap.get("type"),
                             "handle": cap.get("handle", "").lstrip("/") if cap.get("type") != "command"
                             else cap.get("handle"), "plugin": p.get("plugin"), "tool": p.get("tool"),
                             "verdict": p.get("verdict"), "card": p.get("card", "")})
    rows.sort(key=lambda r: (-r["score"], r["type"] != "asset"))
    return rows[:k]


def cmd_recommend(args) -> int:
    cfg = load_config()
    base = plugins_dir(cfg)
    catalog = load_catalog(base)
    has_catalog = catalog_path(base).is_file()
    k = max(1, min(20, args.k))
    mode = "kb"
    try:
        assets, caps = recommend_kb(cfg, args.task, k)
        rows = merge_ranked(assets, caps, catalog, cfg_float(cfg, "LLM_PLUGINS_MARGIN"), k)
    except kb.ServiceUnavailable as exc:
        if not has_catalog:
            err(f"knowledge base unreachable ({exc}) and no plugin catalog; run: plugins.py catalog --auto")
            return EXIT_UNREACHABLE
        err(f"knowledge base unreachable ({exc}); lexical fallback over catalog.json")
        mode = "lexical"
        rows = recommend_lexical(args.task, catalog, k)
    if args.json:
        out(json.dumps({"mode": mode, "margin": cfg_float(cfg, "LLM_PLUGINS_MARGIN"), "results": rows}, indent=2))
    else:
        if mode == "lexical":
            out("mode: lexical fallback over the plugin catalog (knowledge base unreachable); "
                "toolkit assets are not ranked here: run kb.py search for them")
        for n, r in enumerate(rows, 1):
            score = f"{r['distance']:.3f}" if mode == "kb" else f"{r['score']} terms"
            if r["type"] == "asset":
                where = f"{r['source']}:{r['path']}" + (f" › {r['heading']}" if r.get("heading") else "")
                out(f"{n}. [asset]  {score}  {r.get('kind') or ''} {where}".rstrip())
            else:
                mark = "" if r["verdict"] == "pass" else f"  [{r['verdict']}]"
                out(f"{n}. [plugin] {score}  {r['capability']} {r['handle']} ({r['tool']}){mark}")
    return EXIT_OK if rows else EXIT_NONE


# --------------------------------------------------------------------------- decisions and status

def load_decisions(cfg) -> list:
    path = decisions_path(cfg)
    if not path.exists():
        return []
    data, problem = read_json_capped(path, 16 * 1024 * 1024)
    if problem or not isinstance(data, dict) or not isinstance(data.get("decisions"), list):
        raise PluginError(f"decision register unreadable ({problem or 'unexpected shape'}); not overwriting: "
                          f"{path.as_posix()}")
    return data["decisions"]


def cmd_decide(args) -> int:
    cfg = load_config()
    if not NAME_ARG_RX.match(args.plugin):
        raise PluginError(f"invalid plugin name: {args.plugin[:60]!r}")
    reason = clean_text(args.reason, 500)
    if not reason:
        raise PluginError("--reason must not be empty")
    entries = [p for p in load_catalog(plugins_dir(cfg))["plugins"]
               if isinstance(p, dict) and p.get("plugin") == args.plugin]
    tool = safe_name(args.tool, "tool") if args.tool else (entries[0]["tool"] if len(entries) == 1 else "any")
    match = [p for p in entries if tool == "any" or p.get("tool") == tool]
    verdict = match[0].get("verdict", "unknown") if match else "unknown"
    decisions = load_decisions(cfg)
    record = {"date": kb.iso(kb.utcnow()), "tool": tool, "plugin": args.plugin, "decision": args.decision,
              "reason": reason, "verdict": verdict}
    decisions.append(record)
    write_json_atomic(decisions_path(cfg), {"version": 1, "decisions": decisions})
    out(f"recorded: {args.decision} {args.plugin} ({tool}, verdict {verdict})")
    return EXIT_OK


def cmd_decisions(args) -> int:
    decisions = load_decisions(load_config())
    if args.json:
        out(json.dumps({"decisions": decisions}, indent=2, ensure_ascii=False))
        return EXIT_OK
    for d in decisions:
        out(f"{d.get('date')}  {d.get('decision'):6}  {d.get('tool')}/{d.get('plugin')}  verdict={d.get('verdict')}  "
            f"{d.get('reason')}")
    if not decisions:
        out("no decisions recorded")
    return EXIT_OK


def cmd_status(args) -> int:
    cfg = load_config()
    base = plugins_dir(cfg)
    catalog = load_catalog(base)
    plugins = [p for p in catalog["plugins"] if isinstance(p, dict)]
    try:
        decided = {(d.get("tool"), d.get("plugin")) for d in load_decisions(cfg)}
    except PluginError as exc:
        err(str(exc))
        decided = set()
    age = None
    if catalog.get("generated"):
        try:
            age = round((kb.utcnow() - kb.parse_iso(catalog["generated"])).total_seconds() / 3600, 1)
        except (TypeError, ValueError):
            age = None
    tools = {}
    for p in plugins:
        t = tools.setdefault(p.get("tool"), {"plugins": 0, "capabilities": 0, "listing_chars": 0,
                                             "verdicts": {}})
        t["plugins"] += 1
        t["capabilities"] += len(p.get("capabilities", []))
        t["listing_chars"] += int(p.get("listing_chars") or 0)
        t["verdicts"][p.get("verdict")] = t["verdicts"].get(p.get("verdict"), 0) + 1
    undecided = sorted(f"{p.get('tool')}/{p.get('plugin')}" for p in plugins
                       if (p.get("tool"), p.get("plugin")) not in decided and ("any", p.get("plugin")) not in decided)
    report = {"catalog": catalog_path(base).as_posix(), "generated": catalog.get("generated"), "age_hours": age,
              "tools": tools,
              "plugins": [{"tool": p.get("tool"), "plugin": p.get("plugin"), "verdict": p.get("verdict"),
                           "protective": p.get("protective"), "capabilities": len(p.get("capabilities", [])),
                           "listing_chars": p.get("listing_chars")} for p in plugins],
              "undecided": undecided}
    if args.json:
        out(json.dumps(report, indent=2))
        return EXIT_OK
    if not plugins:
        out("no catalog yet: run plugins.py catalog --auto")
        return EXIT_OK
    out(f"catalog: generated {catalog.get('generated')} ({age} h ago)")
    for name, t in sorted(tools.items()):
        verdicts = " ".join(f"{k}={v}" for k, v in sorted(t["verdicts"].items()))
        out(f"{name}: plugins={t['plugins']} capabilities={t['capabilities']} listing_chars={t['listing_chars']} "
            f"{verdicts}")
    for p in sorted(report["plugins"], key=lambda x: -(x["listing_chars"] or 0))[:15]:
        out(f"  {p['listing_chars']:>7}  {p['tool']}/{p['plugin']}  {p['verdict']}"
            + ("  protective" if p["protective"] else ""))
    out(f"undecided: {len(undecided)}" + (f" ({', '.join(undecided[:10])}{' ...' if len(undecided) > 10 else ''})"
                                          if undecided else ""))
    return EXIT_OK


# --------------------------------------------------------------------------- argparse

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="plugins.py", description="Plugin capability catalog and security gate.")
    sub = p.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    s = sub.add_parser("scan", help="static security scan of plugin directories (0 pass, 5 review, 4 block)")
    s.add_argument("paths", nargs="+", metavar="plugin-dir")
    s.add_argument("--json", action="store_true")
    s.add_argument("--strict", action="store_true", help="treat a review verdict as block for the exit code")
    s.set_defaults(func=cmd_scan)

    s = sub.add_parser("catalog", help="build capability cards and catalog.json (7 when no plugin is found)")
    s.add_argument("--auto", action="store_true", help="discover every tool's plugin folders")
    s.add_argument("--from", dest="from_roots", action="append", metavar="root",
                   help="a folder of plugin directories, or one plugin directory (repeatable)")
    s.add_argument("--tool", help="tool label for --from roots (default claude-code)")
    s.add_argument("--out", help="output folder (default <data>/plugins)")
    s.add_argument("--no-scan", action="store_true", help="inventory only; verdict 'unscanned'")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_catalog)

    s = sub.add_parser("marketplace", help="list marketplace entries not in the catalog (or --all)")
    s.add_argument("marketplace_dir", metavar="marketplace-dir")
    s.add_argument("--query")
    s.add_argument("--all", action="store_true")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_marketplace)

    s = sub.add_parser("fetch", help="copy or clone one marketplace plugin into quarantine and scan it (never installs)")
    s.add_argument("marketplace_dir", metavar="marketplace-dir")
    s.add_argument("name")
    s.add_argument("--dest")
    s.add_argument("--allow-unpinned", action="store_true")
    s.set_defaults(func=cmd_fetch)

    s = sub.add_parser("plan", help="print (never run) the per-tool steps to add or remove a plugin")
    s.add_argument("action", choices=["add", "remove"])
    s.add_argument("name", metavar="name[@marketplace]")
    s.add_argument("--marketplace-dir", help="check the name against a local marketplace clone (add)")
    s.add_argument("--i-understand", action="store_true", help="allow a removal plan for a protective plugin")
    s.set_defaults(func=cmd_plan)

    s = sub.add_parser("recommend", help="rank toolkit assets and plugin capabilities for a task")
    s.add_argument("task")
    s.add_argument("-k", type=int, default=8)
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_recommend)

    s = sub.add_parser("decide", help="append a decision to the register")
    s.add_argument("plugin")
    s.add_argument("--decision", required=True, choices=["keep", "remove", "add", "reject"])
    s.add_argument("--reason", required=True)
    s.add_argument("--tool")
    s.set_defaults(func=cmd_decide)

    s = sub.add_parser("decisions", help="list the decision register")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_decisions)

    s = sub.add_parser("status", help="catalog age, counts, verdicts, context cost, undecided plugins")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_status)
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
    except (PluginError, kb.KBError) as exc:
        err(f"error: {exc}")
        return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
