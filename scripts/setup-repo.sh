#!/usr/bin/env bash
# Setup a consumer repo to use LLM toolkit.
# Symlinks skills, rules, workflows, and provider compatibility paths.
#
# Windows (PowerShell): scripts/setup-repo.ps1 - same behavior using directory links.
#
# Usage: ./scripts/setup-repo.sh [path-to-consumer-repo] [--force]
#   Run from toolkit root: ./scripts/setup-repo.sh /path/to/consumer
#   Or from consumer repo: ../llm-toolkit-project/scripts/setup-repo.sh .

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

if [[ ! -d "$TOOLKIT_ROOT/skills" && ! -d "$TOOLKIT_ROOT/.agents/skills" ]]; then
  echo "Error: toolkit root not found (expected skills/ at $TOOLKIT_ROOT)" >&2
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

append_shared_skill_ignores() {
  local prefix="$1"
  local skill_dir
  if [[ -d "$TOOLKIT_ROOT/skills" ]]; then
    find "$TOOLKIT_ROOT/skills" -mindepth 1 -maxdepth 1 -type d -print | LC_ALL=C sort | while IFS= read -r skill_dir; do
      echo "$prefix/skills/$(basename "$skill_dir")"
    done
  fi
}

ensure_plain_dir() {
  local path="$1"
  local allow_repair="${2:-}"

  if [[ -e "$path" || -L "$path" ]]; then
    if [[ -d "$path" && ! -L "$path" ]]; then
      return 0
    fi
    if [[ -z "$allow_repair" ]]; then
      echo "Error: blocking link/file exists at $path." >&2
      echo "Remove it manually, or rerun with --force to replace it with a directory for per-path toolkit links." >&2
      return 1
    fi
    safe_remove_path "$path" || return 1
  fi
  mkdir -p "$path"
}

link_shared_skill_catalog() {
  local skills_root="$1"
  local label="$2"
  local skill_dir skill_name

  ensure_plain_dir "$skills_root" "$FORCE" || return 1
  # Keep the loop in the current shell so ensure_dir_link failures propagate;
  # a pipeline subshell would swallow the return status.
  while IFS= read -r skill_dir; do
    skill_name="${skill_dir##*/}"
    if [[ -z "$skill_name" ]]; then
      echo "Error: empty skill name resolved from '$skill_dir'; aborting catalog link pass." >&2
      return 1
    fi
    ensure_dir_link "$skills_root/$skill_name" "$skill_dir" "$FORCE" || return 1
  done < <(find "$TOOLKIT_ROOT/skills" -mindepth 1 -maxdepth 1 -type d -print | LC_ALL=C sort)
  echo "$label"
}

# ── Interactive tool selection ────────────────────────────────────────────────
# Ask which LLM agents/tools the project uses. Only set up selected ones.
# Re-running setup is safe — existing links are preserved.

USE_WINDSURF=0; USE_CURSOR=0; USE_CLAUDE=0; USE_CODEX=0; USE_ANTIGRAVITY=0; USE_GEMINI=0; USE_OPENCODE=0

echo ""
echo "Which LLM tools does this project use? (enter numbers separated by spaces)"
echo "  1) Windsurf"
echo "  2) Cursor"
echo "  3) Claude Code"
echo "  4) Codex compatibility surface"
echo "  5) Antigravity"
echo "  6) Gemini CLI"
echo "  7) OpenCode"
echo "  a) All of the above"
echo ""
read -rp "Selection [default: a]: " TOOL_SELECTION
TOOL_SELECTION="${TOOL_SELECTION:-a}"

if [[ "$TOOL_SELECTION" == "a" || "$TOOL_SELECTION" == "A" ]]; then
  USE_WINDSURF=1; USE_CURSOR=1; USE_CLAUDE=1; USE_CODEX=1; USE_ANTIGRAVITY=1; USE_GEMINI=1; USE_OPENCODE=1
else
  for choice in $TOOL_SELECTION; do
    case "$choice" in
      1) USE_WINDSURF=1 ;;
      2) USE_CURSOR=1 ;;
      3) USE_CLAUDE=1 ;;
      4) USE_CODEX=1 ;;
      5) USE_ANTIGRAVITY=1 ;;
      6) USE_GEMINI=1 ;;
      7) USE_OPENCODE=1 ;;
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
  [[ $USE_CODEX -eq 1 ]]    && parts+=("Codex compatibility surface")
  [[ $USE_ANTIGRAVITY -eq 1 ]] && parts+=("Antigravity")
  [[ $USE_GEMINI -eq 1 ]] && parts+=("Gemini CLI")
  [[ $USE_OPENCODE -eq 1 ]] && parts+=("OpenCode")
  joined=""
  for part in "${parts[@]}"; do
    if [ -n "$joined" ]; then
      joined="${joined}, "
    fi
    joined="${joined}${part}"
  done
  echo "$joined"
)"
echo ""

# ── 1. Shared skills (.agents/skills/*) — always linked ─────────────────────
ensure_plain_dir "$CONSUMER/.agents" "$FORCE" || exit 1
link_shared_skill_catalog "$CONSUMER/.agents/skills" "Skills: .agents/skills/<name> -> toolkit/skills/<name>" || exit 1

if [[ $USE_ANTIGRAVITY -eq 1 ]]; then
  ensure_plain_dir "$CONSUMER/.agent" "$FORCE" || exit 1
  link_shared_skill_catalog "$CONSUMER/.agent/skills" "Antigravity: .agent/skills/<name> -> toolkit/skills/<name>" || exit 1
fi

# ── 2. Ensure toolkit layouts ────────────────────────────────────────────────
ensure_toolkit_windsurf_layout "$TOOLKIT_ROOT" "$FORCE" || exit 1

# ── 3. Tool-specific setup ───────────────────────────────────────────────────

# Shared rules/workflows are linked by path so provider roots can hold
# repo-specific files alongside toolkit-managed compatibility links.
ensure_plain_dir "$CONSUMER/.windsurf" "$FORCE" || exit 1
ensure_dir_link "$CONSUMER/.windsurf/rules" "$TOOLKIT_ROOT/rules" "$FORCE" || exit 1
ensure_dir_link "$CONSUMER/.windsurf/workflows" "$TOOLKIT_ROOT/workflows" "$FORCE" || exit 1
if [[ $USE_WINDSURF -eq 1 ]]; then
  link_shared_skill_catalog "$CONSUMER/.windsurf/skills" "Windsurf: .windsurf/skills/<name> -> toolkit/skills/<name>" || exit 1
  echo "Windsurf: .windsurf/rules and .windsurf/workflows linked to toolkit"
fi

# Cursor: create the provider root; sync-tool-configs links shared subpaths.
if [[ $USE_CURSOR -eq 1 ]]; then
  ensure_plain_dir "$CONSUMER/.cursor" "$FORCE" || exit 1
  link_shared_skill_catalog "$CONSUMER/.cursor/skills" "Cursor: .cursor/skills/<name> -> toolkit/skills/<name>" || exit 1
  if [[ -d "$TOOLKIT_ROOT/tool-subagents" ]]; then
    ensure_dir_link "$CONSUMER/.cursor/agents" "$TOOLKIT_ROOT/tool-subagents" "$FORCE" || exit 1
  fi
  echo "Cursor: .cursor root ready; shared rules/workflows refresh during sync"
fi

if [[ $USE_GEMINI -eq 1 ]]; then
  ensure_plain_dir "$CONSUMER/.gemini" "$FORCE" || exit 1
  link_shared_skill_catalog "$CONSUMER/.gemini/skills" "Gemini CLI: .gemini/skills/<name> -> toolkit/skills/<name>" || exit 1
fi

if [[ $USE_OPENCODE -eq 1 ]]; then
  ensure_plain_dir "$CONSUMER/.opencode" "$FORCE" || exit 1
  link_shared_skill_catalog "$CONSUMER/.opencode/skills" "OpenCode: .opencode/skills/<name> -> toolkit/skills/<name>" || exit 1
fi

# Claude Code: link only shared subpaths so repo-specific skills can coexist.
if [[ $USE_CLAUDE -eq 1 ]]; then
  ensure_plain_dir "$CONSUMER/.claude" "$FORCE" || exit 1
  link_shared_skill_catalog "$CONSUMER/.claude/skills" "Claude Code: .claude/skills/<name> -> toolkit/skills/<name>" || exit 1
  if [[ -d "$TOOLKIT_ROOT/tool-subagents" ]]; then
    ensure_dir_link "$CONSUMER/.claude/agents" "$TOOLKIT_ROOT/tool-subagents" "$FORCE" || exit 1
  fi
fi

# Codex: link only shared subpaths; AGENTS.md remains primary.
if [[ $USE_CODEX -eq 1 ]]; then
  ensure_plain_dir "$CONSUMER/.codex" "$FORCE" || exit 1
  link_shared_skill_catalog "$CONSUMER/.codex/skills" "Codex: .codex/skills/<name> -> toolkit/skills/<name>" || exit 1
  if [[ -d "$TOOLKIT_ROOT/tool-subagents" ]]; then
    ensure_dir_link "$CONSUMER/.codex/agents" "$TOOLKIT_ROOT/tool-subagents" "$FORCE" || exit 1
  fi
fi

# 3. Scaffold repo-local LLM configuration outside linked toolkit directories.
mkdir -p "$CONSUMER/docs/llm/rules" "$CONSUMER/docs/llm/workflows"

ensure_text_file "$CONSUMER/docs/llm/README.md" "docs/llm/README.md" "$(cat "$SCRIPT_DIR/templates/docs-llm-README.md")"

ensure_text_file "$CONSUMER/docs/llm/rules/README.md" "docs/llm/rules/README.md" "$(cat <<'EOF'
# Repo-Local Rules

Add repository-only rules here. Keep reusable generic rules in the shared toolkit.
EOF
)"

ensure_text_file "$CONSUMER/docs/llm/workflows/README.md" "docs/llm/workflows/README.md" "$(cat <<'EOF'
# Repo-Local Workflows

Add repository-only workflows here. Keep reusable generic workflows in the shared toolkit.
EOF
)"

ensure_text_file "$CONSUMER/docs/llm/toolkit-selection.txt" "docs/llm/toolkit-selection.txt" "$(cat "$SCRIPT_DIR/templates/toolkit-selection.txt")"

if [[ $USE_CURSOR -eq 1 ]]; then
  ensure_text_file "$CONSUMER/.cursorignore" ".cursorignore" "$(cat <<'EOF'
# Repo-local Cursor visibility overrides.
# `sync-tool-configs.sh` manages a selection block here when `docs/llm/toolkit-selection.txt` contains entries.
# Common local hides after initial setup:
# rules/examples/
# integrations/jira.md
# integrations/confluence.md
EOF
)"

  ensure_text_file "$CONSUMER/.cursorindexingignore" ".cursorindexingignore" "$(cat <<'EOF'
# Repo-local Cursor indexing overrides.
# `sync-tool-configs.sh` manages a selection block here when `docs/llm/toolkit-selection.txt` contains entries.
# Common local hides after initial setup:
# rules/examples/
# integrations/jira.md
# integrations/confluence.md
EOF
)"
fi

ensure_text_file "$CONSUMER/scripts/sync-llm-configs.ps1" "scripts/sync-llm-configs.ps1" "$(cat "$SCRIPT_DIR/templates/sync-llm-configs.ps1")"

ensure_text_file "$CONSUMER/scripts/sync-llm-configs.sh" "scripts/sync-llm-configs.sh" "$(cat "$SCRIPT_DIR/templates/sync-llm-configs.sh")"
chmod +x "$CONSUMER/scripts/sync-llm-configs.sh" 2>/dev/null || true

# 4. Repair shared tool symlinks and refresh repo-local exports after the local scaffold exists.
if [[ -f "$SCRIPT_DIR/sync-tool-configs.sh" ]]; then
  SYNC_ARGS=("$CONSUMER")
  if [[ -n "$FORCE" ]]; then
    SYNC_ARGS+=("--force")
  fi
  if [[ $USE_CURSOR -ne 1 ]]; then
    SYNC_ARGS+=("--skip-cursor-rules")
  fi
  if bash "$SCRIPT_DIR/sync-tool-configs.sh" "${SYNC_ARGS[@]}"; then
    echo "Shared tool surfaces repaired and local exports refreshed via sync-tool-configs.sh"
  else
    echo "Error: sync-tool-configs.sh failed. Shared tool symlinks or local exports may be stale." >&2
    echo "Fix the issue and re-run, or run manually: bash $SCRIPT_DIR/sync-tool-configs.sh $CONSUMER" >&2
    exit 1
  fi
else
  echo "Error: sync-tool-configs.sh not found at $SCRIPT_DIR; cannot repair tool surfaces or refresh exports." >&2
  exit 1
fi

# 5. Generate AGENTS.md.
REFERENCE_AGENTS="$(cat "$SCRIPT_DIR/templates/consumer-AGENTS.md")"

ORCHESTRATION_HEADING="## Mandatory agent orchestration (all LLM assistants)"
# Single source of truth: the section lives at the end of the template
# (from the heading line to end-of-template); extract it instead of
# duplicating the text here.
ORCHESTRATION_SECTION="$(awk -v h="$ORCHESTRATION_HEADING" '
  $0 == h { found=1 }
  found { print }
' "$SCRIPT_DIR/templates/consumer-AGENTS.md")"

CONSUMER_AGENTS="$CONSUMER/AGENTS.md"
if [[ -f "$CONSUMER_AGENTS" ]]; then
  if grep -q "LLM Dev Tools\|LLM-assisted development" "$CONSUMER_AGENTS" 2>/dev/null; then
    echo "AGENTS.md: already configured, unchanged."
  else
    {
      echo ""
      echo "---"
      echo "$REFERENCE_AGENTS"
    } >> "$CONSUMER_AGENTS"
    echo "AGENTS.md: appended LLM tools reference."
  fi
else
  echo "$REFERENCE_AGENTS" > "$CONSUMER_AGENTS"
  echo "AGENTS.md: created."
fi

# 5b. Idempotently ensure the mandatory agent-orchestration section is present.
# The template-append/create paths above already carry it as part of
# REFERENCE_AGENTS; this only fires when an already-configured AGENTS.md
# (marker present) predates the section being added to the template.
if grep -qF "$ORCHESTRATION_HEADING" "$CONSUMER_AGENTS" 2>/dev/null; then
  echo "AGENTS.md: agent-orchestration section already present, unchanged."
else
  {
    echo ""
    echo "$ORCHESTRATION_SECTION"
  } >> "$CONSUMER_AGENTS"
  echo "AGENTS.md: appended mandatory agent-orchestration section."
fi

# 6. .gitignore — only add entries for selected tools.
CONSUMER_GITIGNORE="$CONSUMER/.gitignore"

if [[ -f "$CONSUMER_GITIGNORE" ]] && grep -q "LLM integration\|LLM toolkit\|\docs/jira/" "$CONSUMER_GITIGNORE" 2>/dev/null; then
  echo ".gitignore: already configured, unchanged."
else
  {
    echo ""
    echo "# LLM integration — local output and symlinked/generated toolkit paths"
    echo "docs/jira/"
    echo "node_modules/"
    echo ".DS_Store"
    append_shared_skill_ignores ".agents"
    echo ".agents/skills/AGENTS.md"
    echo ".windsurf/rules/"
    echo ".windsurf/workflows/"
    [[ $USE_WINDSURF -eq 1 ]] && append_shared_skill_ignores ".windsurf"
    [[ $USE_ANTIGRAVITY -eq 1 ]] && append_shared_skill_ignores ".agent" && echo ".agent/skills/AGENTS.md"
    [[ $USE_CURSOR -eq 1 ]]   && append_shared_skill_ignores ".cursor" && echo ".cursor/skills/AGENTS.md" && echo ".cursor/rules/" && echo ".cursor/workflows/" && echo ".cursor/agents/"
    [[ $USE_CLAUDE -eq 1 ]]   && append_shared_skill_ignores ".claude" && echo ".claude/skills/AGENTS.md"
    [[ $USE_CODEX -eq 1 ]]    && append_shared_skill_ignores ".codex" && echo ".codex/skills/AGENTS.md" && echo ".codex/agents/"
    [[ $USE_GEMINI -eq 1 ]]   && append_shared_skill_ignores ".gemini" && echo ".gemini/skills/AGENTS.md"
    [[ $USE_OPENCODE -eq 1 ]] && append_shared_skill_ignores ".opencode" && echo ".opencode/skills/AGENTS.md"
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
echo "    .agents/skills/<name>      - shared skills -> toolkit skills/<name>"
echo "    .windsurf/rules/           - shared rules -> toolkit rules/"
echo "    .windsurf/workflows/       - shared workflows -> toolkit workflows/"
echo "    docs/llm/                  - repo-local LLM guidance"
echo "    scripts/sync-llm-configs.* - consumer-local LLM sync wrapper"
echo "    AGENTS.md                  - repo-level instructions and context"
[[ $USE_WINDSURF -eq 1 ]] && echo "  Windsurf:"  && echo "    .windsurf/skills/<name>    - shared skills -> toolkit skills/<name>"
[[ $USE_ANTIGRAVITY -eq 1 ]] && echo "  Antigravity:" && echo "    .agent/skills/<name>       - shared skills -> toolkit skills/<name>"
[[ $USE_CURSOR -eq 1 ]]   && echo "  Cursor:"    && echo "    .cursor/skills/<name>      - shared skills -> toolkit skills/<name>" && echo "    .cursor/                   - provider root with shared subpath links"
[[ $USE_CLAUDE -eq 1 ]]   && echo "  Claude Code:" && echo "    .claude/skills/<name>      - shared skills -> toolkit skills/<name>"
[[ $USE_CODEX -eq 1 ]]    && echo "  Codex:"     && echo "    .codex/skills/<name>       - shared skills -> toolkit skills/<name>"
[[ $USE_GEMINI -eq 1 ]]   && echo "  Gemini CLI:" && echo "    .gemini/skills/<name>      - shared skills -> toolkit skills/<name>"
[[ $USE_OPENCODE -eq 1 ]] && echo "  OpenCode:" && echo "    .opencode/skills/<name>    - shared skills -> toolkit skills/<name>"
echo ""
echo "Note: linked/generated toolkit directories are gitignored; repo-local files stay committed."
echo "Next: review docs/llm/toolkit-selection.txt and ask the LLM to add repo-specific context in docs/llm/."
