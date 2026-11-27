#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly SCRIPT_DIR
readonly REPO_ROOT
readonly SKILLS_ROOT="$REPO_ROOT/skills"
readonly AGENTS_SKILLS="$REPO_ROOT/.agents/skills"
readonly CLAUDE_SKILLS="$REPO_ROOT/.claude/skills"
readonly CODEX_SKILLS="$SCRIPT_DIR/skills"
readonly WINDSURF_SKILLS="$REPO_ROOT/.windsurf/skills"
readonly GLOBAL_CODEX_SKILLS="${CODEX_HOME:-$HOME/.codex}/skills"

usage() {
  cat <<'USAGE'
Usage: ./.codex/sync-shared-skills.sh [--no-global]

Repairs the repo-local shared skill catalog links (toolkit root only):
  skills/                 canonical source of truth
  .agents/skills          -> ../skills
  .claude/skills          -> ../.agents/skills

It no longer creates .codex/skills or .windsurf/skills (Codex, Cursor and
Windsurf read .agents/skills) and no longer mirrors into ~/.codex/skills (the
global installer links ~/.agents/skills). Existing old links are never deleted;
one line is printed for each one found, saying it can be removed.
Existing real directories are preserved; only symlink-style paths are replaced.

Options:
  --no-global  Accepted for compatibility; has no effect (nothing global is written)
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-global)
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s\n\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [[ ! -d "$SKILLS_ROOT" ]]; then
  printf 'Missing canonical skills directory: %s\n' "$SKILLS_ROOT" >&2
  exit 1
fi

mkdir -p "$REPO_ROOT/.agents" "$REPO_ROOT/.claude"

link_catalog() {
  local link_path="$1"
  local target="$2"

  if [[ -L "$link_path" ]]; then
    rm -f "$link_path"
  elif [[ -e "$link_path" ]]; then
    printf 'Refusing to replace non-symlink path: %s\n' "$link_path" >&2
    printf 'Use scripts/sync-tool-configs.sh --force only after confirming the path is toolkit-managed.\n' >&2
    return 1
  fi

  ln -s "$target" "$link_path"
}

link_catalog "$AGENTS_SKILLS" "../skills"
link_catalog "$CLAUDE_SKILLS" "../.agents/skills"

# Old skill roots are no longer created or mirrored; existing links are never removed here.
note_legacy() {
  local path="$1" entry found=0
  if [[ -L "$path" ]]; then
    found=1
  elif [[ -d "$path" ]]; then
    for entry in "$path"/*; do
      [[ -L "$entry" ]] && { found=1; break; }
    done
  fi
  if (( found )); then
    printf 'Note: %s holds links that are no longer created; it can be removed (.agents/skills is used).\n' "$path"
  fi
}
note_legacy "$CODEX_SKILLS"
note_legacy "$WINDSURF_SKILLS"
note_legacy "$GLOBAL_CODEX_SKILLS"

echo "Repaired shared skill catalog symlinks"
