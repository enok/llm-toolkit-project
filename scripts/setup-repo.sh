#!/usr/bin/env bash
# Setup a consumer repo to use LLM toolkit.
# Symlinks skills, rules, workflows, and optional Codex mirror paths.
#
# Windows (PowerShell): scripts/setup-repo.ps1 - same behavior using directory links.
#
# Usage: ./scripts/setup-repo.sh [path-to-consumer-repo] [--force]
#   Run from toolkit root: ./scripts/setup-repo.sh /path/to/consumer
#   Or from consumer repo: ../llm-toolkit/scripts/setup-repo.sh .

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLKIT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FORCE=""

# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

POSITIONAL=()
for arg in "$@"; do
  if [[ "$arg" == "--force" ]]; then
    FORCE=1
  else
    POSITIONAL+=("$arg")
  fi
done

CONSUMER="${POSITIONAL[0]:-.}"

if [[ ! -d "$TOOLKIT_ROOT/.agents" ]]; then
  echo "Error: toolkit root not found (expected .agents/ at $TOOLKIT_ROOT)" >&2
  exit 1
fi

if [[ ! -d "$CONSUMER" ]]; then
  echo "Error: consumer path is not a directory: $CONSUMER" >&2
  exit 1
fi

CONSUMER="$(resolve_absolute_path "$CONSUMER")"

ensure_text_file() {
  local path="$1"
  local label="$2"
  local content="$3"
  local parent
  parent="$(dirname "$path")"
  mkdir -p "$parent"
  if [[ -f "$path" ]]; then
    echo "$label: already exists, unchanged."
    return 0
  fi
  printf "%s\n" "$content" > "$path"
  echo "$label: created."
}

# Detect fresh install vs upgrade
FRESH_INSTALL=1
if [[ -d "$CONSUMER/.agents" || -d "$CONSUMER/.windsurf" || -d "$CONSUMER/skills" || -f "$CONSUMER/docs/llm/toolkit-selection.txt" ]]; then
  FRESH_INSTALL=0
fi

if [[ $FRESH_INSTALL -eq 1 ]]; then
  echo ""
  echo "Fresh install — setting up LLM toolkit for: $CONSUMER"
else
  echo ""
  echo "Existing configuration detected — upgrading LLM toolkit for: $CONSUMER"
  echo "  Junctions will be repaired if needed; existing files will be preserved."
  echo "  Use --force to repair broken junctions. AGENTS.md toolkit block will be updated."
fi

# Interactive tool selection
USE_WINDSURF=0; USE_CURSOR=0; USE_CLAUDE=0; USE_CODEX=0

echo ""
echo "Which LLM tools does this project use? (enter numbers separated by spaces)"
echo "  1) Windsurf"
echo "  2) Cursor"
echo "  3) Claude Code"
echo "  4) Codex"
echo "  a) All of the above"
echo ""
read -rp "Selection [default: a]: " TOOL_SELECTION
TOOL_SELECTION="${TOOL_SELECTION:-a}"

if [[ "$TOOL_SELECTION" == "a" || "$TOOL_SELECTION" == "A" ]]; then
  USE_WINDSURF=1; USE_CURSOR=1; USE_CLAUDE=1; USE_CODEX=1
else
  for choice in $TOOL_SELECTION; do
    case "$choice" in
      1) USE_WINDSURF=1 ;;
      2) USE_CURSOR=1 ;;
      3) USE_CLAUDE=1 ;;
      4) USE_CODEX=1 ;;
      *) echo "Warning: unknown selection '$choice', ignored." >&2 ;;
    esac
  done
fi

echo ""
echo "Setting up: $(
  parts=()
  [[ $USE_WINDSURF -eq 1 ]] && parts+=("Windsurf")
  [[ $USE_CURSOR -eq 1 ]]   && parts+=("Cursor")
  [[ $USE_CLAUDE -eq 1 ]]   && parts+=("Claude Code")
  [[ $USE_CODEX -eq 1 ]]    && parts+=("Codex")
  (IFS=,; echo "${parts[*]}") | sed 's/,/, /g'
)"
echo ""

# 1. Canonical skills/ and workflows/ - always linked to toolkit's canonical source
ensure_dir_link "$CONSUMER/skills" "$TOOLKIT_ROOT/skills" "$FORCE" || exit 1
echo "Skills: skills -> toolkit/skills (canonical)"

ensure_dir_link "$CONSUMER/workflows" "$TOOLKIT_ROOT/workflows" "$FORCE" || exit 1
echo "Workflows: workflows -> toolkit/workflows (canonical)"

# 2. .setup/ (examples, integrations)
if [[ -d "$TOOLKIT_ROOT/.setup" ]]; then
  ensure_dir_link "$CONSUMER/.setup" "$TOOLKIT_ROOT/.setup" "$FORCE" || exit 1
  echo ".setup -> toolkit/.setup"
fi

# 3. Tool-specific: each agent dir gets a skills/ junction to canonical

# Windsurf: workflows junction (windsurf has native workflows support)
if [[ $USE_WINDSURF -eq 1 ]]; then
  mkdir -p "$CONSUMER/.windsurf"
  ensure_dir_link "$CONSUMER/.windsurf/workflows" "$TOOLKIT_ROOT/workflows" "$FORCE" || exit 1
  echo "Windsurf: .windsurf/workflows -> toolkit/workflows"
fi

# Cursor: skills and agents
if [[ $USE_CURSOR -eq 1 ]]; then
  mkdir -p "$CONSUMER/.cursor"
  ensure_dir_link "$CONSUMER/.cursor/skills" "$TOOLKIT_ROOT/skills" "$FORCE" || exit 1
  echo "Cursor: .cursor/skills -> toolkit/skills"
  if [[ -d "$TOOLKIT_ROOT/.cursor/agents" ]]; then
    ensure_dir_link "$CONSUMER/.cursor/agents" "$TOOLKIT_ROOT/.cursor/agents" "$FORCE" || exit 1
    echo "Cursor: .cursor/agents -> toolkit/.cursor/agents"
  fi
fi

# Claude Code: skills junction
if [[ $USE_CLAUDE -eq 1 ]]; then
  mkdir -p "$CONSUMER/.claude"
  ensure_dir_link "$CONSUMER/.claude/skills" "$TOOLKIT_ROOT/skills" "$FORCE" || exit 1
  echo "Claude Code: .claude/skills -> toolkit/skills"
fi

# Codex: skills junction
if [[ $USE_CODEX -eq 1 ]]; then
  mkdir -p "$CONSUMER/.codex"
  ensure_dir_link "$CONSUMER/.codex/skills" "$TOOLKIT_ROOT/skills" "$FORCE" || exit 1
  echo "Codex: .codex/skills -> toolkit/skills"
fi

# Agents (generic): skills junction
mkdir -p "$CONSUMER/.agents"
ensure_dir_link "$CONSUMER/.agents/skills" "$TOOLKIT_ROOT/skills" "$FORCE" || exit 1
echo "Agents: .agents/skills -> toolkit/skills"

# 3. Scaffold repo-local LLM configuration
mkdir -p "$CONSUMER/docs/llm"

ensure_text_file "$CONSUMER/docs/llm/README.md" "docs/llm/README.md" "$(cat "$SCRIPT_DIR/templates/docs-llm-README.md")"

ensure_text_file "$CONSUMER/docs/llm/toolkit-selection.txt" "docs/llm/toolkit-selection.txt" "$(cat "$SCRIPT_DIR/templates/toolkit-selection.txt")"

if [[ $USE_CURSOR -eq 1 ]]; then
  ensure_text_file "$CONSUMER/.cursorignore" ".cursorignore" "# Repo-local Cursor visibility overrides.
# ".setup/examples/
# ".setup/integrations/"

ensure_text_file "$CONSUMER/.cursorindexingignore" ".cursorindexingignore" "# Repo-local Cursor indexing overrides.
# ".setup/examples/
# ".setup/integrations/"
fi

ensure_text_file "$CONSUMER/scripts/sync-llm-configs.ps1" "scripts/sync-llm-configs.ps1" "$(cat "$SCRIPT_DIR/templates/sync-llm-configs.ps1")"

ensure_text_file "$CONSUMER/scripts/sync-llm-configs.sh" "scripts/sync-llm-configs.sh" "$(cat "$SCRIPT_DIR/templates/sync-llm-configs.sh")"
chmod +x "$CONSUMER/scripts/sync-llm-configs.sh" 2>/dev/null || true

# 4. Repair shared tool symlinks and refresh repo-local exports
if [[ -f "$SCRIPT_DIR/sync-tool-configs.sh" ]]; then
  if bash "$SCRIPT_DIR/sync-tool-configs.sh" "$CONSUMER"; then
    echo "Shared tool surfaces repaired and local exports refreshed via sync-tool-configs.sh"
  else
    echo "Error: sync-tool-configs.sh failed. Shared tool symlinks or local exports may be stale." >&2
    exit 1
  fi
else
  echo "Warning: sync-tool-configs.sh not found; skipping tool surface repair." >&2
fi

# 5. Update AGENTS.md
# Strategy:
#   - Fresh file: write the full template.
#   - Existing file with sentinel block: replace the block in-place (upgrade).
#   - Existing file without sentinel: append the template block.
#   - --force on an existing sentinel block: same replace-in-place (idempotent).
TOOLKIT_BLOCK="$(cat "$SCRIPT_DIR/templates/consumer-AGENTS.md")"
CONSUMER_AGENTS="$CONSUMER/AGENTS.md"

if [[ ! -f "$CONSUMER_AGENTS" ]]; then
  printf "%s\n" "$TOOLKIT_BLOCK" > "$CONSUMER_AGENTS"
  echo "AGENTS.md: created."
elif grep -q "<!-- BEGIN LLM TOOLKIT -->" "$CONSUMER_AGENTS" 2>/dev/null; then
  # Replace only the sentinel block, preserving everything outside it.
  # Pass the replacement block via a temp file; export path for awk via ENVIRON.
  BLOCK_TMP="$(mktemp)"
  printf "%s\n" "$TOOLKIT_BLOCK" > "$BLOCK_TMP"
  export BLOCK_TMP
  awk '
    /<!-- BEGIN LLM TOOLKIT -->/ {
      found=1
      while ((getline line < ENVIRON["BLOCK_TMP"]) > 0) print line
      close(ENVIRON["BLOCK_TMP"])
      next
    }
    found && /<!-- END LLM TOOLKIT -->/ { found=0; next }
    found { next }
    { print }
  ' "$CONSUMER_AGENTS" > "${CONSUMER_AGENTS}.tmp" \
    && mv "${CONSUMER_AGENTS}.tmp" "$CONSUMER_AGENTS"
  rm -f "$BLOCK_TMP"
  unset BLOCK_TMP
  echo "AGENTS.md: toolkit block updated in-place."
else
  # Legacy file (no sentinel) — append the block so existing content is preserved.
  printf "\n---\n%s\n" "$TOOLKIT_BLOCK" >> "$CONSUMER_AGENTS"
  echo "AGENTS.md: toolkit block appended (no existing sentinel found)."
fi

# 6. .gitignore - only add entries for selected tools
CONSUMER_GITIGNORE="$CONSUMER/.gitignore"

if [[ -f "$CONSUMER_GITIGNORE" ]] && grep -q "LLM integration\|LLM toolkit\|\.agents/" "$CONSUMER_GITIGNORE" 2>/dev/null; then
  echo ".gitignore: already configured, unchanged."
else
  {
    echo ""
    echo "# LLM integration - symlinked/generated content (do not commit)"
    echo ".agents/"
    echo ".setup/"
    [[ $USE_WINDSURF -eq 1 ]] && echo ".windsurf/"
    [[ $USE_CURSOR -eq 1 ]]   && echo ".cursor/"
    [[ $USE_CLAUDE -eq 1 ]]   && echo ".claude/"
    [[ $USE_CODEX -eq 1 ]]    && echo ".codex/"
  } >> "$CONSUMER_GITIGNORE"
  echo ".gitignore: appended LLM tool entries."
fi

if [[ $USE_CURSOR -eq 1 ]] && ! grep -qx '!\.cursorignore' "$CONSUMER_GITIGNORE" 2>/dev/null; then
  cat >> "$CONSUMER_GITIGNORE" <<'EOF'

# Keep repo-local Cursor visibility filters committed.
!.cursorignore
!.cursorindexingignore
EOF
  echo ".gitignore: ensured repo-local Cursor visibility filters stay committed."
fi

echo ""
echo "Done. Consumer repo configured at: $CONSUMER"
echo ""
echo "  Always:"
echo "    .agents/                   - skills -> toolkit .agents/"
echo "    .setup/                    - templates -> toolkit .setup/"
echo "    docs/llm/                  - repo-local LLM guidance"
echo "    scripts/sync-llm-configs.* - consumer-local LLM sync wrapper"
echo "    AGENTS.md                  - repo-level instructions and context"
[[ $USE_WINDSURF -eq 1 ]] && echo "  Windsurf:"  && echo "    .windsurf/                 - -> toolkit .windsurf/ (symlink)"
[[ $USE_CURSOR -eq 1 ]]   && echo "  Cursor:"    && echo "    .cursor/                   - -> toolkit/.cursor (symlink)"
[[ $USE_CLAUDE -eq 1 ]]   && echo "  Claude Code:" && echo "    .claude/                   - -> toolkit .claude/ (symlink)"
[[ $USE_CODEX -eq 1 ]]    && echo "  Codex:"     && echo "    .codex/                    - -> toolkit .codex/ (symlink)"
echo ""
echo "Note: linked/generated toolkit directories are gitignored; repo-local files stay committed."
echo "Next: review docs/llm/toolkit-selection.txt and ask the LLM to add repo-specific context in docs/llm/."
