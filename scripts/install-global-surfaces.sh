#!/usr/bin/env bash
# Install the shared LLM toolkit as the global (home-directory) skills,
# agents, and instruction surface for every LLM tool on this machine.
#
# Canonical sources stay in this repository (skills/, tool-subagents/);
# this script only links user-level tool directories back to them and
# writes a managed instruction block into each tool's global instruction
# file. It never copies shared content and never edits files outside the
# managed block markers.
#
# Usage:
#   ./scripts/install-global-surfaces.sh [--apply] [--tools <list>]
#       [--force] [--toolkit-root <path>] [--home <path>]
#
# Default mode is a dry-run: it prints the plan and changes nothing on
# disk. Pass --apply to create/update the links and managed blocks.
#
#   --tools <list>   Comma-separated: claude,codex,cursor,windsurf,gemini,
#                     opencode,antigravity,all. Default "auto": only tools
#                     whose home directory already exists.
#   --force          Replace a blocking non-link path after backing it up
#                     to <path>.bak-<yyyyMMddHHmmss>.
#   --toolkit-root   Toolkit repository root (default: the repo root that
#                     contains this script).
#   --home           Home directory to install into (default: $HOME).
#                     Use this to test against a scratch directory.
#
# Exit status: non-zero only when --apply hits at least one blocked path
# (an existing non-link path with --force not given). A dry-run always
# exits 0 so it is safe to run for inspection.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_TOOLKIT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

BEGIN_MARK="<!-- BEGIN LLM-TOOLKIT GLOBAL -->"
END_MARK="<!-- END LLM-TOOLKIT GLOBAL -->"
TOOLS_ALL_LIST="claude codex cursor windsurf gemini opencode antigravity"

APPLY=0
FORCE=0
TOOLS_ARG="auto"
TOOLKIT_ROOT=""
HOME_DIR="${HOME:-}"
BACKUP_TS="$(date +%Y%m%d%H%M%S)"

usage() {
  cat <<'USAGE'
Usage: ./scripts/install-global-surfaces.sh [--apply] [--tools <list>] [--force] [--toolkit-root <path>] [--home <path>]

  --apply            Apply changes (default: print the plan only).
  --tools <list>     claude,codex,cursor,windsurf,gemini,opencode,antigravity,all
                      Default: auto (only tools whose home dir already exists).
  --force            Replace a blocking non-link path (backed up first).
  --toolkit-root     Toolkit repository root (default: this script's repo root).
  --home             Home directory to install into (default: $HOME).
  -h, --help         Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    --tools) TOOLS_ARG="${2:?--tools requires a value}"; shift 2 ;;
    --tools=*) TOOLS_ARG="${1#*=}"; shift ;;
    --force) FORCE=1; shift ;;
    --toolkit-root) TOOLKIT_ROOT="${2:?--toolkit-root requires a value}"; shift 2 ;;
    --toolkit-root=*) TOOLKIT_ROOT="${1#*=}"; shift ;;
    --home) HOME_DIR="${2:?--home requires a value}"; shift 2 ;;
    --home=*) HOME_DIR="${1#*=}"; shift ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Error: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$TOOLKIT_ROOT" ]]; then
  TOOLKIT_ROOT="$DEFAULT_TOOLKIT_ROOT"
fi
if [[ ! -d "$TOOLKIT_ROOT" ]]; then
  echo "Error: toolkit root not found: $TOOLKIT_ROOT" >&2
  exit 1
fi
TOOLKIT_ROOT="$(cd "$TOOLKIT_ROOT" && pwd)"

if [[ -z "$HOME_DIR" ]]; then
  echo "Error: could not determine a home directory; pass --home <path>" >&2
  exit 1
fi
if [[ ! -d "$HOME_DIR" ]]; then
  echo "Error: --home path not found: $HOME_DIR" >&2
  exit 1
fi
HOME_DIR="$(cd "$HOME_DIR" && pwd)"

TEMPLATE_FILE="$TOOLKIT_ROOT/scripts/templates/global-agent-directive.md"
if [[ ! -f "$TEMPLATE_FILE" ]]; then
  echo "Error: missing directive template: $TEMPLATE_FILE" >&2
  exit 1
fi

is_valid_tool() {
  local needle="$1" candidate
  for candidate in $TOOLS_ALL_LIST; do
    [[ "$candidate" == "$needle" ]] && return 0
  done
  return 1
}

result_contains_tool() {
  local haystack="$1" needle="$2" candidate
  for candidate in $haystack; do
    [[ "$candidate" == "$needle" ]] && return 0
  done
  return 1
}

compute_selected_tools() {
  local arg="$1"
  local result=""

  case "$arg" in
    all)
      result="$TOOLS_ALL_LIST"
      ;;
    auto)
      [[ -d "$HOME_DIR/.claude" ]] && result="$result claude"
      [[ -d "$HOME_DIR/.codex" ]] && result="$result codex"
      [[ -d "$HOME_DIR/.cursor" ]] && result="$result cursor"
      [[ -d "$HOME_DIR/.codeium/windsurf" ]] && result="$result windsurf"
      [[ -d "$HOME_DIR/.gemini" ]] && result="$result gemini"
      [[ -d "$HOME_DIR/.config/opencode" ]] && result="$result opencode"
      [[ -d "$HOME_DIR/.gemini/antigravity" ]] && result="$result antigravity"
      ;;
    *)
      local normalized tool
      normalized="$(printf '%s' "$arg" | tr ',' ' ')"
      for tool in $normalized; do
        tool="$(printf '%s' "$tool" | tr -d '[:space:]')"
        [[ -z "$tool" ]] && continue
        if ! is_valid_tool "$tool"; then
          echo "Error: unknown tool '$tool' (expected one of: $TOOLS_ALL_LIST, or auto/all)" >&2
          exit 2
        fi
        if ! result_contains_tool "$result" "$tool"; then
          result="$result $tool"
        fi
      done
      ;;
  esac

  result="${result# }"
  printf '%s\n' "$result"
}

SELECTED_TOOLS="$(compute_selected_tools "$TOOLS_ARG")"

# ---------------------------------------------------------------------------
# Result tracking / summary table
# ---------------------------------------------------------------------------

RESULT_ROWS=()
BLOCKED_COUNT=0

add_row() {
  local tool="$1" surface="$2" action="$3" detail="${4:-}"
  RESULT_ROWS+=("$tool"$'\t'"$surface"$'\t'"$action"$'\t'"$detail")
  if [[ "$action" == "blocked" ]]; then
    BLOCKED_COUNT=$((BLOCKED_COUNT + 1))
  fi
}

print_table() {
  if [[ "${#RESULT_ROWS[@]}" -eq 0 ]]; then
    echo "(no surfaces processed)"
    return 0
  fi

  local w_tool=4 w_surface=7 w_action=6 w_detail=6
  local row tool surface action detail
  for row in "${RESULT_ROWS[@]}"; do
    IFS=$'\t' read -r tool surface action detail <<<"$row"
    [[ ${#tool} -gt $w_tool ]] && w_tool=${#tool}
    [[ ${#surface} -gt $w_surface ]] && w_surface=${#surface}
    [[ ${#action} -gt $w_action ]] && w_action=${#action}
    [[ ${#detail} -gt $w_detail ]] && w_detail=${#detail}
  done

  printf '%-*s  %-*s  %-*s  %-*s\n' "$w_tool" "TOOL" "$w_surface" "SURFACE" "$w_action" "ACTION" "$w_detail" "DETAIL"
  printf '%-*s  %-*s  %-*s  %-*s\n' "$w_tool" "----" "$w_surface" "-------" "$w_action" "------" "$w_detail" "------"
  for row in "${RESULT_ROWS[@]}"; do
    IFS=$'\t' read -r tool surface action detail <<<"$row"
    printf '%-*s  %-*s  %-*s  %-*s\n' "$w_tool" "$tool" "$w_surface" "$surface" "$w_action" "$action" "$w_detail" "$detail"
  done
}

# ---------------------------------------------------------------------------
# Link surfaces (directory junction/symlink equivalents)
# ---------------------------------------------------------------------------

link_points_to() {
  local link="$1" target="$2"
  [[ -L "$link" ]] || return 1

  local link_dir raw resolved resolved_canon target_canon
  link_dir="$(cd "$(dirname "$link")" && pwd -P)" || return 1
  raw="$(readlink "$link")"
  case "$raw" in
    /*) resolved="$raw" ;;
    *) resolved="$link_dir/$raw" ;;
  esac

  if [[ -d "$resolved" ]]; then
    resolved_canon="$(cd "$resolved" && pwd -P)"
  else
    resolved_canon="$resolved"
  fi
  target_canon="$(cd "$target" && pwd -P)"
  [[ "$resolved_canon" == "$target_canon" ]]
}

plan_link_surface() {
  local tool="$1" surface_label="$2" link_path="$3" target_path="$4"
  local parent
  parent="$(dirname "$link_path")"

  if [[ -L "$link_path" ]]; then
    if link_points_to "$link_path" "$target_path"; then
      add_row "$tool" "$surface_label" "unchanged" "$link_path -> $target_path"
      return 0
    fi
    if (( APPLY )); then
      mkdir -p "$parent"
      ln -sfn "$target_path" "$link_path"
    fi
    add_row "$tool" "$surface_label" "updated" "$link_path -> $target_path"
    return 0
  fi

  if [[ -e "$link_path" ]]; then
    if (( FORCE )); then
      local backup="${link_path}.bak-${BACKUP_TS}"
      if (( APPLY )); then
        mv "$link_path" "$backup"
        mkdir -p "$parent"
        ln -sfn "$target_path" "$link_path"
      fi
      add_row "$tool" "$surface_label" "updated" "backed up to $backup, then linked"
    else
      add_row "$tool" "$surface_label" "blocked" "existing non-link path at $link_path; rerun with --force"
    fi
    return 0
  fi

  if (( APPLY )); then
    mkdir -p "$parent"
    ln -sfn "$target_path" "$link_path"
  fi
  add_row "$tool" "$surface_label" "created" "$link_path -> $target_path"
}

# ---------------------------------------------------------------------------
# Managed-block instruction files
# ---------------------------------------------------------------------------

render_template() {
  sed "s|{{TOOLKIT_ROOT}}|$TOOLKIT_ROOT|g" "$TEMPLATE_FILE"
}

extract_block() {
  local file="$1"
  awk -v start="$BEGIN_MARK" -v end="$END_MARK" '
    { sub(/\r$/, "") }
    $0 == start { inb=1; next }
    $0 == end { inb=0; next }
    inb { print }
  ' "$file"
}

replace_block_in_place() {
  local file="$1" block="$2"
  local tmp="$file.tmp-install-global-surfaces.$$"
  _BLOCK="$block" awk -v start="$BEGIN_MARK" -v end="$END_MARK" '
    BEGIN { blk = ENVIRON["_BLOCK"] }
    { sub(/\r$/, "") }
    $0 == start { print blk; skip=1; next }
    $0 == end { skip=0; next }
    !skip { print }
  ' "$file" > "$tmp"
  mv "$tmp" "$file"
}

file_is_effectively_empty() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  [[ -z "$(tr -d '[:space:]' < "$file" 2>/dev/null)" ]]
}

managed_block_apply() {
  local tool="$1" surface_label="$2" file="$3"
  local rendered block parent
  rendered="$(render_template)"
  block="$(printf '%s\n%s\n%s' "$BEGIN_MARK" "$rendered" "$END_MARK")"
  parent="$(dirname "$file")"

  if [[ -f "$file" ]] && grep -qF "$BEGIN_MARK" "$file" 2>/dev/null && grep -qF "$END_MARK" "$file" 2>/dev/null; then
    local current current_norm rendered_norm
    current="$(extract_block "$file")"
    current_norm="$(printf '%s' "$current" | sed 's/\r$//')"
    rendered_norm="$(printf '%s' "$rendered" | sed 's/\r$//')"
    if [[ "$current_norm" == "$rendered_norm" ]]; then
      add_row "$tool" "$surface_label" "unchanged" "$file"
    else
      (( APPLY )) && replace_block_in_place "$file" "$block"
      add_row "$tool" "$surface_label" "updated" "$file"
    fi
    return 0
  fi

  if file_is_effectively_empty "$file"; then
    if (( APPLY )); then
      mkdir -p "$parent"
      printf '%s\n' "$block" > "$file"
    fi
    add_row "$tool" "$surface_label" "created" "$file"
    return 0
  fi

  # Existing non-empty file without our markers: append, preserving content.
  if (( APPLY )); then
    mkdir -p "$parent"
    printf '\n%s\n' "$block" >> "$file"
  fi
  add_row "$tool" "$surface_label" "created" "$file (appended)"
}

# ---------------------------------------------------------------------------
# Per-tool installers
# ---------------------------------------------------------------------------

CURSOR_SELECTED=0
CURSOR_RULES_TEXT=""

install_claude() {
  local base="$HOME_DIR/.claude"
  plan_link_surface "claude" "skills" "$base/skills" "$TOOLKIT_ROOT/skills"
  plan_link_surface "claude" "agents" "$base/agents" "$TOOLKIT_ROOT/tool-subagents"
  managed_block_apply "claude" "CLAUDE.md" "$base/CLAUDE.md"
}

install_codex() {
  local base="$HOME_DIR/.codex"

  if [[ -d "$TOOLKIT_ROOT/skills" ]]; then
    local skill_dir name
    for skill_dir in "$TOOLKIT_ROOT/skills"/*/; do
      [[ -f "${skill_dir}SKILL.md" ]] || continue
      name="$(basename "$skill_dir")"
      plan_link_surface "codex" "skills/$name" "$base/skills/$name" "$TOOLKIT_ROOT/skills/$name"
    done
  fi

  plan_link_surface "codex" "agents" "$base/agents" "$TOOLKIT_ROOT/tool-subagents"
  managed_block_apply "codex" "AGENTS.md" "$base/AGENTS.md"
}

install_cursor() {
  local base="$HOME_DIR/.cursor"
  plan_link_surface "cursor" "skills" "$base/skills" "$TOOLKIT_ROOT/skills"
  plan_link_surface "cursor" "agents" "$base/agents" "$TOOLKIT_ROOT/tool-subagents"
  add_row "cursor" "user-rules (manual)" "skipped" "no global rules file; paste text below into Cursor Settings > Rules"
  CURSOR_SELECTED=1
  CURSOR_RULES_TEXT="$(render_template)"
}

install_windsurf() {
  local base="$HOME_DIR/.codeium/windsurf"
  plan_link_surface "windsurf" "skills" "$base/skills" "$TOOLKIT_ROOT/skills"
  managed_block_apply "windsurf" "memories/global_rules.md" "$base/memories/global_rules.md"
}

install_gemini() {
  local base="$HOME_DIR/.gemini"
  plan_link_surface "gemini" "skills" "$base/skills" "$TOOLKIT_ROOT/skills"
  managed_block_apply "gemini" "GEMINI.md" "$base/GEMINI.md"
}

install_opencode() {
  local base="$HOME_DIR/.config/opencode"
  plan_link_surface "opencode" "skills" "$base/skills" "$TOOLKIT_ROOT/skills"
}

install_antigravity() {
  local base="$HOME_DIR/.gemini/antigravity"
  plan_link_surface "antigravity" "skills" "$base/skills" "$TOOLKIT_ROOT/skills"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

echo "LLM toolkit global install"
echo "  Mode:         $([[ $APPLY -eq 1 ]] && echo APPLY || echo "PLAN (dry-run, no changes)")"
echo "  Toolkit root: $TOOLKIT_ROOT"
echo "  Home:         $HOME_DIR"
echo "  Tools:        ${SELECTED_TOOLS:-(none)}"
echo

if [[ -z "$SELECTED_TOOLS" ]]; then
  echo "No tool home directories were found under $HOME_DIR."
  echo "Pass --tools all (or a specific list) to install anyway."
  exit 0
fi

for tool in $SELECTED_TOOLS; do
  case "$tool" in
    claude) install_claude ;;
    codex) install_codex ;;
    cursor) install_cursor ;;
    windsurf) install_windsurf ;;
    gemini) install_gemini ;;
    opencode) install_opencode ;;
    antigravity) install_antigravity ;;
  esac
done

print_table

if [[ "$CURSOR_SELECTED" -eq 1 ]]; then
  echo
  echo "Cursor has no global rules file; paste the following into Cursor Settings > Rules (User Rules):"
  echo "--------------------------------------------------------------------------------"
  printf '%s\n' "$CURSOR_RULES_TEXT"
  echo "--------------------------------------------------------------------------------"
fi

echo
if (( APPLY )); then
  if (( BLOCKED_COUNT > 0 )); then
    echo "Done with $BLOCKED_COUNT blocked path(s). Re-run with --force after checking the backups it would take."
    exit 1
  fi
  echo "Done. Global surfaces installed for: $SELECTED_TOOLS"
else
  echo "This was a plan only; nothing was changed. Re-run with --apply to make these changes."
fi
