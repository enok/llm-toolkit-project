#!/usr/bin/env bash
# First-time developer bootstrap for the LLM toolkit toolkit.
# Installs required binaries/CLIs, optional tooling, and an agent CLI of choice,
# then wires the toolkit so any LLM agent (Claude Code, Cursor, Windsurf, Codex,
# Gemini CLI, Copilot) can use it. npm-based tools are exact-version pinned and
# installed without lifecycle scripts.
#
# Windows (PowerShell): scripts/bootstrap-dev.ps1 - same behavior via winget.
#
# Usage: ./scripts/bootstrap-dev.sh [options]
#   --minimal            Core tools only (git, node, python, jq, ripgrep, gh)
#   --full               Core + recommended + docs/diagram extras
#   --agent <name>       Also install an agent CLI: claude | codex | gemini | all
#   --consumer <path>    Link a consumer repo to this toolkit after installs
#   --no-kb              Skip the knowledge-base step (on by default except with --minimal)
#   --kb-data-dir <path> Data folder for the knowledge base (passed to kb.py init)
#   --security-tools     Opt-in (off by default): install the security-check toolchain.
#                        brew formulas of the same names on macOS (shellcheck, actionlint,
#                        hadolint, syft, grype, trivy, gitleaks, osv-scanner, semgrep,
#                        yamllint, pip-audit, checkov, trufflehog); winget ids under Git Bash;
#                        on Linux the tools without a package are listed under manual
#                        actions. PSScriptAnalyzer needs PowerShell and is listed as manual. pip tools install in user
#                        scope (semgrep, yamllint, pip-audit, checkov, skillspector==2.13.7).
#   --rtk                Opt-in (off by default): install only the reviewed RTK 1.2.1
#                        (winget --exact plus pin under Git Bash; brew on macOS, and the
#                        script stops unless `rtk --version` reports 1.2.1). See
#                        skills/token-efficiency/references/rtk-reviewed-deployment.md.
#   --dry-run            Print what would be installed without changing anything
#
# The knowledge-base step (scripts/kb.py init, up --build, index, schedule install)
# runs after the tool installs and needs Docker with compose; without it the step
# prints the command to run later and the bootstrap still succeeds. The prompt
# hook is never installed here (opt-in: kb.py hook install).
#
# Idempotent: existing tools are detected and skipped. Interactive auth steps
# (gh auth login, acli auth, aws configure) are printed, never run silently.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PROFILE="default"   # default = core + recommended; minimal = core; full = everything
AGENT=""
CONSUMER=""
DRY_RUN=""
NO_KB=""
SECURITY_TOOLS=""
RTK_INSTALL=""
RTK_REVIEWED_VERSION="1.2.1"
KB_DATA_DIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --minimal) PROFILE="minimal"; shift ;;
    --full) PROFILE="full"; shift ;;
    --agent) AGENT="${2:-}"; shift 2 ;;
    --consumer) CONSUMER="${2:-}"; shift 2 ;;
    --no-kb) NO_KB=1; shift ;;
    --kb-data-dir) KB_DATA_DIR="${2:-}"; [[ -n "$KB_DATA_DIR" ]] || { echo "--kb-data-dir requires a path" >&2; exit 2; }; shift 2 ;;
    --security-tools) SECURITY_TOOLS=1; shift ;;
    --rtk) RTK_INSTALL=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

# ---------- platform + package manager detection ----------

OS="unknown"
PKG=""
case "$(uname -s)" in
  Darwin) OS="macos" ;;
  Linux) OS="linux" ;;
  MINGW*|MSYS*|CYGWIN*) OS="windows-gitbash" ;;
esac

if [[ "$OS" == "macos" ]]; then
  command -v brew >/dev/null 2>&1 && PKG="brew"
elif [[ "$OS" == "linux" ]]; then
  if command -v apt-get >/dev/null 2>&1; then PKG="apt"
  elif command -v dnf >/dev/null 2>&1; then PKG="dnf"
  fi
elif [[ "$OS" == "windows-gitbash" ]]; then
  command -v winget.exe >/dev/null 2>&1 && PKG="winget"
fi

if [[ -z "$PKG" ]]; then
  echo "No supported package manager found (brew/apt/dnf/winget)." >&2
  echo "Install one first, or install the tools listed by --dry-run manually." >&2
  [[ -n "$DRY_RUN" ]] || exit 1
fi

MISSING_SUMMARY=()
INSTALLED_SUMMARY=()
SKIPPED_SUMMARY=()

run() {
  if [[ -n "$DRY_RUN" ]]; then
    echo "[dry-run] $*"
  else
    echo "+ $*"
    "$@"
  fi
}

# install <check-command> <label> <brew-pkg> <apt-pkg> <dnf-pkg> <winget-id>
install_tool() {
  local check="$1" label="$2" brew_pkg="$3" apt_pkg="$4" dnf_pkg="$5" winget_id="$6"
  if command -v "$check" >/dev/null 2>&1; then
    SKIPPED_SUMMARY+=("$label (already installed)")
    return 0
  fi
  local pkg_name=""
  case "$PKG" in
    brew) pkg_name="$brew_pkg"; [[ -z "$pkg_name" ]] || run brew install "$pkg_name" ;;
    apt) pkg_name="$apt_pkg"; [[ -z "$pkg_name" ]] || run sudo apt-get install -y "$pkg_name" ;;
    dnf) pkg_name="$dnf_pkg"; [[ -z "$pkg_name" ]] || run sudo dnf install -y "$pkg_name" ;;
    winget) pkg_name="$winget_id"; [[ -z "$pkg_name" ]] || run winget.exe install --id "$winget_id" -e --silent --accept-package-agreements --accept-source-agreements ;;
  esac
  if [[ -z "$pkg_name" ]]; then
    MISSING_SUMMARY+=("$label")
  elif [[ -n "$DRY_RUN" ]]; then
    MISSING_SUMMARY+=("$label (would install)")
  elif command -v "$check" >/dev/null 2>&1; then
    INSTALLED_SUMMARY+=("$label")
  else
    MISSING_SUMMARY+=("$label (install attempted; open a new shell or install manually)")
  fi
}

npm_install_global() {
  local check="$1" label="$2" pkg="$3"
  if command -v "$check" >/dev/null 2>&1; then
    SKIPPED_SUMMARY+=("$label (already installed)")
    return 0
  fi
  if ! command -v npm >/dev/null 2>&1; then
    MISSING_SUMMARY+=("$label (needs npm first)")
    return 0
  fi
  # Packages are exact-version pinned and lifecycle scripts are disabled. This
  # keeps the new-client bootstrap deterministic and prevents package hooks
  # from reading inherited credentials.
  run npm install -g --ignore-scripts --no-audit --no-fund "$pkg"
  command -v "$check" >/dev/null 2>&1 && INSTALLED_SUMMARY+=("$label") || MISSING_SUMMARY+=("$label (npm install attempted; open a new shell)")
}

# pip_install_user <check-command> <label> <spec>
pip_install_user() {
  local check="$1" label="$2" spec="$3" pip_cmd=""
  if command -v "$check" >/dev/null 2>&1; then
    SKIPPED_SUMMARY+=("$label (already installed)")
    return 0
  fi
  if command -v pip3 >/dev/null 2>&1; then pip_cmd="pip3"
  elif command -v pip >/dev/null 2>&1; then pip_cmd="pip"
  fi
  if [[ -z "$pip_cmd" ]]; then
    if [[ -n "$DRY_RUN" ]]; then run pip3 install --user "$spec"; return 0; fi
    MISSING_SUMMARY+=("$label (needs pip first: pip install --user $spec)")
    return 0
  fi
  if run "$pip_cmd" install --user "$spec"; then
    if [[ -n "$DRY_RUN" ]]; then MISSING_SUMMARY+=("$label (would install)"); else INSTALLED_SUMMARY+=("$label"); fi
  else
    MISSING_SUMMARY+=("$label (pip install failed)")
  fi
}

echo "== LLM toolkit bootstrap (profile: $PROFILE, os: $OS, pkg: ${PKG:-none}) =="

# ---------- core tools (every profile) ----------

install_tool git "git" git git git Git.Git
install_tool node "Node.js" node nodejs nodejs OpenJS.NodeJS.LTS
install_tool python3 "Python 3" python@3.12 python3 python3 Python.Python.3.12
install_tool jq "jq" jq jq jq jqlang.jq
install_tool rg "ripgrep" ripgrep ripgrep ripgrep BurntSushi.ripgrep.MSVC
install_tool gh "GitHub CLI" gh gh gh GitHub.cli

# ---------- recommended tools (default + full) ----------

if [[ "$PROFILE" != "minimal" ]]; then
  install_tool aws "AWS CLI v2" awscli awscli awscli Amazon.AWSCLI
  if command -v mvn >/dev/null 2>&1; then
    SKIPPED_SUMMARY+=("Maven (already installed)")
  else
    MISSING_SUMMARY+=("Maven — no winget package (brew install maven / apt install maven elsewhere); or download from https://maven.apache.org/download.cgi")
  fi
  # Token-efficiency tools (see skills/token-efficiency/SKILL.md)
  install_tool sg "ast-grep" ast-grep "" "" ast-grep.ast-grep
  npm_install_global repomix "repomix" repomix@1.18.0
  # Atlassian CLI (acli): no universal package; official installer docs:
  if ! command -v acli >/dev/null 2>&1; then
    MISSING_SUMMARY+=("Atlassian CLI (acli) — install per https://developer.atlassian.com/cloud/acli/guides/install-acli/")
  else
    SKIPPED_SUMMARY+=("Atlassian CLI (already installed)")
  fi
  if ! command -v slack >/dev/null 2>&1; then
    MISSING_SUMMARY+=("Slack CLI — install manually if your workflow needs it (authentication remains interactive)")
  else
    SKIPPED_SUMMARY+=("Slack CLI (already installed)")
  fi
  # RTK: token-saving command-output proxy. Only the security-reviewed deployment
  # is approved (see rules/command-safety.md); do not auto-install from public
  # registries and never run 'rtk init' or enable hooks/telemetry/tee.
  if ! command -v rtk >/dev/null 2>&1; then
    MISSING_SUMMARY+=("rtk — optional token optimizer; run with --rtk or follow skills/token-efficiency/references/rtk-reviewed-deployment.md")
  else
    SKIPPED_SUMMARY+=("rtk (already installed)")
  fi
fi

# ---------- docs/diagram extras (full only) ----------

if [[ "$PROFILE" == "full" ]]; then
  npm_install_global mmdc "Mermaid CLI" @mermaid-js/mermaid-cli@11.17.0
  install_tool plantuml "PlantUML" plantuml plantuml plantuml ""
  install_tool pandoc "Pandoc" pandoc pandoc pandoc JohnMacFarlane.Pandoc
  install_tool typst "Typst" typst "" typst Typst.Typst
fi

# ---------- agent CLI (opt-in) ----------

case "$AGENT" in
  "") : ;;
  claude) npm_install_global claude "Claude Code" @anthropic-ai/claude-code@2.1.261 ;;
  codex) npm_install_global codex "Codex CLI" @openai/codex@0.153.4 ;;
  gemini) npm_install_global gemini "Gemini CLI" @google/gemini-cli@0.58.0 ;;
  all)
    npm_install_global claude "Claude Code" @anthropic-ai/claude-code@2.1.261
    npm_install_global codex "Codex CLI" @openai/codex@0.153.4
    npm_install_global gemini "Gemini CLI" @google/gemini-cli@0.58.0
    ;;
  *) echo "Unknown --agent '$AGENT' (expected claude|codex|gemini|all)" >&2 ;;
esac

# ---------- security-check toolchain (opt-in: --security-tools) ----------

if [[ -n "$SECURITY_TOOLS" ]]; then
  echo "== Security tools =="
  # install_tool <check> <label> <brew> <apt> <dnf> <winget-id>; "" = no package for that manager
  install_tool shellcheck "shellcheck" shellcheck shellcheck ShellCheck koalaman.shellcheck
  install_tool actionlint "actionlint" actionlint "" "" rhysd.actionlint
  install_tool hadolint "hadolint" hadolint "" "" hadolint.hadolint
  install_tool syft "Syft" syft "" "" Anchore.Syft
  install_tool grype "Grype" grype "" "" Anchore.Grype
  install_tool trivy "Trivy" trivy "" "" AquaSecurity.Trivy
  install_tool gitleaks "Gitleaks" gitleaks "" "" Gitleaks.Gitleaks
  install_tool osv-scanner "OSV-Scanner" osv-scanner "" "" Google.OSVScanner
  if [[ "$PKG" == "brew" ]]; then
    install_tool trufflehog "trufflehog" trufflehog "" "" ""
  else
    command -v trufflehog >/dev/null 2>&1 || MISSING_SUMMARY+=("trufflehog — no package for this platform; install from its GitHub release if needed")
  fi
  pip_install_user semgrep "semgrep" semgrep
  pip_install_user yamllint "yamllint" yamllint
  pip_install_user pip-audit "pip-audit" pip-audit
  pip_install_user checkov "checkov" checkov
  pip_install_user skillspector "skillspector" "skillspector==2.13.7"
  command -v pwsh >/dev/null 2>&1 || MISSING_SUMMARY+=("PSScriptAnalyzer — needs PowerShell: Install-Module PSScriptAnalyzer -Scope CurrentUser")
fi

# ---------- reviewed RTK (opt-in: --rtk) ----------

if [[ -n "$RTK_INSTALL" ]]; then
  echo "== RTK (reviewed version only) =="
  rtk_version_ok() { command -v rtk >/dev/null 2>&1 && [[ "$(rtk --version 2>&1)" == *"$RTK_REVIEWED_VERSION"* ]]; }
  if command -v rtk >/dev/null 2>&1; then
    if rtk_version_ok; then
      SKIPPED_SUMMARY+=("rtk $RTK_REVIEWED_VERSION (already installed)")
    else
      echo "rtk is installed but is not the reviewed $RTK_REVIEWED_VERSION: $(rtk --version 2>&1). Replace it, then rerun." >&2
      exit 3
    fi
  elif [[ "$PKG" == "winget" ]]; then
    run winget.exe install --id rtk-ai.rtk --version "$RTK_REVIEWED_VERSION" --exact --silent --accept-package-agreements --accept-source-agreements
    run winget.exe pin add --id rtk-ai.rtk --version "$RTK_REVIEWED_VERSION"
    [[ -n "$DRY_RUN" ]] || MISSING_SUMMARY+=("rtk: open a new shell, verify the installer SHA-256 against the release checksums.txt, then run the smoke test in skills/token-efficiency/references/rtk-reviewed-deployment.md")
  elif [[ "$PKG" == "brew" ]]; then
    # macOS: the Homebrew build of the reviewed version passed the smoke test. Refuse any other version.
    run brew install rtk
    if [[ -z "$DRY_RUN" ]] && ! rtk_version_ok; then
      echo "rtk --version does not report the reviewed $RTK_REVIEWED_VERSION; uninstall it (brew uninstall rtk) and install the reviewed version manually. Stopping." >&2
      exit 3
    fi
    [[ -n "$DRY_RUN" ]] || INSTALLED_SUMMARY+=("rtk $RTK_REVIEWED_VERSION (run the smoke test in skills/token-efficiency/references/rtk-reviewed-deployment.md)")
  else
    MISSING_SUMMARY+=("rtk $RTK_REVIEWED_VERSION — reviewed on Windows only; no supported install route on this platform without a new review")
  fi
fi

# ---------- RTK privacy environment (POSIX equivalent of approved Windows controls) ----------

if command -v rtk >/dev/null 2>&1 && [[ -z "$DRY_RUN" ]]; then
  PROFILE_FILE="$HOME/.bashrc"
  [[ "$OS" == "macos" && -f "$HOME/.zshrc" ]] && PROFILE_FILE="$HOME/.zshrc"
  if ! grep -q "RTK_SUPPRESS_HOOK_WARNING" "$PROFILE_FILE" 2>/dev/null; then
    {
      echo ""
      echo "# RTK privacy controls (LLM toolkit bootstrap): no DB, no telemetry, no tee"
      if [[ "$OS" == "macos" ]]; then
        # A plain file as the parent: the DB paths below can never be created.
        : > "$HOME/.rtk-off"
        echo "export RTK_DB_PATH=\"\$HOME/.rtk-off/history.db\""
        echo "export RTK_RECALL_DB=\"\$HOME/.rtk-off/recall.db\""
      else
        echo "export RTK_DB_PATH=/dev/null"
      fi
      echo "export RTK_TELEMETRY_DISABLED=1"
      echo "export RTK_TEE=0"
      echo "export RTK_RECALL=0"
      echo "export RTK_SUPPRESS_HOOK_WARNING=1"
    } >> "$PROFILE_FILE"
    INSTALLED_SUMMARY+=("RTK privacy env vars in $PROFILE_FILE")
  fi
fi

# ---------- knowledge base (default + full; skipped by --minimal or --no-kb) ----------

if [[ "$PROFILE" != "minimal" && -z "$NO_KB" ]]; then
  echo "== Knowledge base =="
  KB_PY="$SCRIPT_DIR/kb.py"
  KB_INIT=(python3 "$KB_PY" init)
  [[ -n "$KB_DATA_DIR" ]] && KB_INIT+=(--data-dir "$KB_DATA_DIR")
  KB_LATER="$(printf '%q ' "${KB_INIT[@]}")"
  for kb_step in "up --build" "index" "schedule install"; do
    # shellcheck disable=SC2086  # kb_step is a fixed word list
    KB_LATER+="; $(printf '%q ' python3 "$KB_PY" $kb_step)"
  done
  if [[ -n "$DRY_RUN" ]]; then
    run "${KB_INIT[@]}"
    run python3 "$KB_PY" up --build
    run python3 "$KB_PY" index
    run python3 "$KB_PY" schedule install
  elif ! command -v python3 >/dev/null 2>&1; then
    echo "Knowledge base skipped: python3 is missing. Run later: $KB_LATER"
    MISSING_SUMMARY+=("Knowledge base (needs python3 first)")
  elif ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
    echo "Knowledge base skipped: Docker with compose is missing or its daemon is not running. Run later: $KB_LATER"
    MISSING_SUMMARY+=("Knowledge base (start Docker, then run the command printed above)")
  elif run "${KB_INIT[@]}" && run python3 "$KB_PY" up --build && run python3 "$KB_PY" index && run python3 "$KB_PY" schedule install; then
    INSTALLED_SUMMARY+=("Knowledge base (indexed; scheduled sync installed)")
  else
    echo "Knowledge base step failed. Run later: $KB_LATER"
    MISSING_SUMMARY+=("Knowledge base (a kb.py step failed; see output above)")
  fi
fi

# ---------- toolkit wiring ----------

if [[ -n "$CONSUMER" ]]; then
  echo "== Linking consumer repo: $CONSUMER =="
  if [[ -n "$DRY_RUN" ]]; then
    echo "[dry-run] $SCRIPT_DIR/setup-repo.sh $CONSUMER"
  else
    "$SCRIPT_DIR/setup-repo.sh" "$CONSUMER"
  fi
fi

# ---------- report ----------

echo ""
echo "== Bootstrap summary =="
((${#INSTALLED_SUMMARY[@]})) && printf 'Installed:\n' && printf '  - %s\n' "${INSTALLED_SUMMARY[@]}"
((${#SKIPPED_SUMMARY[@]})) && printf 'Already present:\n' && printf '  - %s\n' "${SKIPPED_SUMMARY[@]}"
((${#MISSING_SUMMARY[@]})) && printf 'Needs manual action:\n' && printf '  - %s\n' "${MISSING_SUMMARY[@]}"

cat <<'EOF'

Next steps (interactive, run yourself):
  1. gh auth login                      # GitHub CLI authentication
  2. acli jira auth login               # Atlassian CLI auth (if installed)
  3. aws configure sso                  # AWS auth (if your team uses AWS)
  4. slack login                        # Slack CLI auth (if installed and needed)
  5. Pick your agent surface:
     - Claude Code:  run 'claude' in any linked repo (CLAUDE.md -> AGENTS.md)
     - Cursor/Windsurf: open the repo; rules/workflows load from .cursor/.windsurf
     - Codex CLI:    run 'codex' (AGENTS.md is the primary surface)
     - Gemini CLI:   run 'gemini' (.gemini/skills compatibility link)
     - VS Code Copilot: .github/copilot-instructions.md is generated on sync
  6. Link your project repo (if not done): ./scripts/setup-repo.sh /path/to/repo
  7. Validate the toolkit:               npm run validate && ./scripts/security-check-toolkit.sh
  8. Knowledge base status:              python3 scripts/kb.py status
     Optional prompt hook (explicit opt-in, never installed by this script):
                                         python3 scripts/kb.py hook install

Never run 'rtk init' or enable RTK hooks/telemetry/tee/audit logging; RTK stays
an explicit per-command proxy (see rules/command-safety.md and
skills/token-efficiency/SKILL.md).
EOF
