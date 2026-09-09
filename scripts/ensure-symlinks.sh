#!/usr/bin/env bash
# Ensure a consumer repo has symlinks for all current skills, provider compatibility paths, rules, and workflows.
# Links shared toolkit content by subpath so repo-specific skills can coexist.
#
# Windows (PowerShell): scripts/ensure-symlinks.ps1 - same behavior.
#
# Usage: ./scripts/ensure-symlinks.sh [path-to-consumer-repo] [--pull] [--force]
#   Run from toolkit root: ./scripts/ensure-symlinks.sh /path/to/consumer
#   Or from consumer: ../llm-toolkit-project/scripts/ensure-symlinks.sh .
#   --pull:  run 'git pull' in the toolkit before creating symlinks (so you get latest).
#   --force: replace blocking paths with the expected toolkit links.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLKIT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

CONSUMER="."
DO_PULL=""
FORCE=""
for arg in "$@"; do
  if [[ "$arg" == "--pull" ]]; then
    DO_PULL=1
  elif [[ "$arg" == "--force" ]]; then
    FORCE=1
  elif [[ -n "$arg" ]]; then
    CONSUMER="$arg"
  fi
done

if [[ ! -d "$TOOLKIT_ROOT/skills" && ! -d "$TOOLKIT_ROOT/.agents/skills" ]]; then
  echo "Error: toolkit root not found (expected skills/ at $TOOLKIT_ROOT)" >&2
  exit 1
fi

if [[ ! -d "$CONSUMER" ]]; then
  echo "Error: consumer path is not a directory: $CONSUMER" >&2
  exit 1
fi

CONSUMER="$(resolve_absolute_path "$CONSUMER")"
TOOLKIT_ROOT="$(resolve_absolute_path "$TOOLKIT_ROOT")"

IS_TOOLKIT_REPO=0
if [[ "$CONSUMER" == "$TOOLKIT_ROOT" ]]; then
  IS_TOOLKIT_REPO=1
fi

if [[ -n "$DO_PULL" ]]; then
  if ! (cd "$TOOLKIT_ROOT" && git pull --ff-only); then
    echo "Warning: git pull --ff-only failed in $TOOLKIT_ROOT; continuing with local copy." >&2
  fi
fi

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

# Toolkit repo uses catalog junctions (.cursor/skills -> .agents/skills -> skills/)
# repaired by sync-tool-configs.sh. Consumer repos use per-skill links so local skills can coexist.
ensure_toolkit_windsurf_layout "$TOOLKIT_ROOT" "$FORCE" || exit 1

if [[ "$IS_TOOLKIT_REPO" -eq 1 ]]; then
  echo "Toolkit repo: skipping per-skill provider links; sync-tool-configs.sh repairs catalog junctions."
else
  # 1. Shared skills and provider roots, linked by subpath.
  ensure_plain_dir "$CONSUMER/.agents" "$FORCE" || exit 1
  link_shared_skill_catalog "$CONSUMER/.agents/skills" "Skills: .agents/skills/<name> -> toolkit/skills/<name>" || exit 1

  ensure_plain_dir "$CONSUMER/.agent" "$FORCE" || exit 1
  link_shared_skill_catalog "$CONSUMER/.agent/skills" "Antigravity: .agent/skills/<name> -> toolkit/skills/<name>" || exit 1

  ensure_plain_dir "$CONSUMER/.claude" "$FORCE" || exit 1
  link_shared_skill_catalog "$CONSUMER/.claude/skills" "Claude Code: .claude/skills/<name> -> toolkit/skills/<name>" || exit 1
  if [[ -d "$TOOLKIT_ROOT/tool-subagents" ]]; then
    ensure_dir_link "$CONSUMER/.claude/agents" "$TOOLKIT_ROOT/tool-subagents" "$FORCE" || exit 1
  fi

  ensure_plain_dir "$CONSUMER/.codex" "$FORCE" || exit 1
  link_shared_skill_catalog "$CONSUMER/.codex/skills" "Codex: .codex/skills/<name> -> toolkit/skills/<name>" || exit 1
  if [[ -d "$TOOLKIT_ROOT/tool-subagents" ]]; then
    ensure_dir_link "$CONSUMER/.codex/agents" "$TOOLKIT_ROOT/tool-subagents" "$FORCE" || exit 1
  fi

  ensure_plain_dir "$CONSUMER/.windsurf" "$FORCE" || exit 1
  ensure_dir_link "$CONSUMER/.windsurf/rules" "$TOOLKIT_ROOT/rules" "$FORCE" || exit 1
  ensure_dir_link "$CONSUMER/.windsurf/workflows" "$TOOLKIT_ROOT/workflows" "$FORCE" || exit 1
  link_shared_skill_catalog "$CONSUMER/.windsurf/skills" "Windsurf: .windsurf/skills/<name> -> toolkit/skills/<name>" || exit 1

  ensure_plain_dir "$CONSUMER/.cursor" "$FORCE" || exit 1
  link_shared_skill_catalog "$CONSUMER/.cursor/skills" "Cursor: .cursor/skills/<name> -> toolkit/skills/<name>" || exit 1
  if [[ -d "$TOOLKIT_ROOT/tool-subagents" ]]; then
    ensure_dir_link "$CONSUMER/.cursor/agents" "$TOOLKIT_ROOT/tool-subagents" "$FORCE" || exit 1
  fi
  echo "Cursor: .cursor root ready; shared rules/workflows refresh during sync"

  ensure_plain_dir "$CONSUMER/.gemini" "$FORCE" || exit 1
  link_shared_skill_catalog "$CONSUMER/.gemini/skills" "Gemini CLI: .gemini/skills/<name> -> toolkit/skills/<name>" || exit 1

  ensure_plain_dir "$CONSUMER/.opencode" "$FORCE" || exit 1
  link_shared_skill_catalog "$CONSUMER/.opencode/skills" "OpenCode: .opencode/skills/<name> -> toolkit/skills/<name>" || exit 1

  if [[ -d "$TOOLKIT_ROOT/learnings" ]]; then
    ensure_dir_link "$CONSUMER/learnings" "$TOOLKIT_ROOT/learnings" "$FORCE" || exit 1
    echo "learnings verified or linked"
  else
    echo "Warning: toolkit learnings/ not found; skipped consumer learnings link." >&2
  fi
fi

if [[ -f "$SCRIPT_DIR/sync-tool-configs.sh" ]]; then
  SYNC_ARGS=("$CONSUMER")
  if [[ -n "$FORCE" ]]; then
    SYNC_ARGS+=("--force")
  fi
  if [[ "$IS_TOOLKIT_REPO" -eq 1 ]]; then
    SYNC_ARGS+=("--skip-agents-md")
  fi
  if bash "$SCRIPT_DIR/sync-tool-configs.sh" "${SYNC_ARGS[@]}"; then
    echo "Shared tool surfaces repaired and local exports refreshed via sync-tool-configs.sh"
  else
    echo "Error: sync-tool-configs.sh failed. Shared tool symlinks or local exports may be stale." >&2
    echo "Fix the issue and re-run, or run manually: bash $SCRIPT_DIR/sync-tool-configs.sh $CONSUMER" >&2
    exit 1
  fi
fi

# Mark link-surface directories skip-worktree to prevent git checkout conflicts
if [[ "$IS_TOOLKIT_REPO" -eq 0 ]]; then
  (
    cd "$CONSUMER" || exit 1
    link_paths=(
      ".agents/skills"
      ".claude/agents"
      ".claude/skills"
      ".codex/skills"
      ".cursor/agents"
      ".cursor/rules"
      ".cursor/workflows"
      ".windsurf/rules"
      ".windsurf/skills"
      ".windsurf/workflows"
    )
    # Only mark paths that exist in the index
    existing_paths=()
    for p in "${link_paths[@]}"; do
      if git ls-files "$p" 2>/dev/null | grep -q .; then
        existing_paths+=("$p")
      fi
    done
    if [[ ${#existing_paths[@]} -gt 0 ]]; then
      echo "Marking link surfaces skip-worktree: ${existing_paths[*]}"
      if ! git update-index --skip-worktree "${existing_paths[@]}" 2>/dev/null; then
        echo "Warning: git update-index --skip-worktree failed; continuing." >&2
      fi
    fi
  )
fi

echo "Integration refresh complete."
