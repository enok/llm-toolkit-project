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
#   --dry-run            Print what would be installed without changing anything
#
# Idempotent: existing tools are detected and skipped. Interactive auth steps
# (gh auth login, acli auth, aws configure) are printed, never run silently.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PROFILE="default"   # default = core + recommended; minimal = core; full = everything
AGENT=""
CONSUMER=""
DRY_RUN=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --minimal) PROFILE="minimal"; shift ;;
    --full) PROFILE="full"; shift ;;
    --agent) AGENT="${2:-}"; shift 2 ;;
    --consumer) CONSUMER="${2:-}"; shift 2 ;;
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
  case "$PKG" in
    brew) [[ -n "$brew_pkg" ]] && run brew install "$brew_pkg" || MISSING_SUMMARY+=("$label") ;;
    apt) [[ -n "$apt_pkg" ]] && run sudo apt-get install -y "$apt_pkg" || MISSING_SUMMARY+=("$label") ;;
    dnf) [[ -n "$dnf_pkg" ]] && run sudo dnf install -y "$dnf_pkg" || MISSING_SUMMARY+=("$label") ;;
    winget) [[ -n "$winget_id" ]] && run winget.exe install --id "$winget_id" -e --silent --accept-package-agreements --accept-source-agreements || MISSING_SUMMARY+=("$label") ;;
    *) MISSING_SUMMARY+=("$label") ; return 0 ;;
  esac
  if [[ -n "$DRY_RUN" ]]; then
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
  install_tool mvn "Maven" maven maven maven Apache.Maven
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
    MISSING_SUMMARY+=("rtk — optional token optimizer; use your team's security-reviewed RTK deployment per rules/command-safety.md and skills/token-efficiency/SKILL.md")
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

# ---------- RTK privacy environment (POSIX equivalent of approved Windows controls) ----------

if command -v rtk >/dev/null 2>&1 && [[ -z "$DRY_RUN" ]]; then
  PROFILE_FILE="$HOME/.bashrc"
  [[ "$OS" == "macos" && -f "$HOME/.zshrc" ]] && PROFILE_FILE="$HOME/.zshrc"
  if ! grep -q "RTK_TELEMETRY_DISABLED" "$PROFILE_FILE" 2>/dev/null; then
    {
      echo ""
      echo "# RTK privacy controls (LLM toolkit bootstrap): no DB, no telemetry, no tee"
      echo "export RTK_DB_PATH=/dev/null"
      echo "export RTK_TELEMETRY_DISABLED=1"
      echo "export RTK_TEE=0"
    } >> "$PROFILE_FILE"
    INSTALLED_SUMMARY+=("RTK privacy env vars in $PROFILE_FILE")
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

Never run 'rtk init' or enable RTK hooks/telemetry/tee/audit logging; RTK stays
an explicit per-command proxy (see rules/command-safety.md and
skills/token-efficiency/SKILL.md).
EOF
