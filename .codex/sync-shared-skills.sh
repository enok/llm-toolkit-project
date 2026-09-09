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
readonly CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
readonly GLOBAL_CODEX_SKILLS="$CODEX_HOME/skills"

sync_global=true

usage() {
  cat <<'USAGE'
Usage: ./.codex/sync-shared-skills.sh [--no-global]

Repairs the shared skill catalog layout:
  skills/                 canonical source of truth
  .agents/skills          -> ../skills
  .claude/skills          -> ../.agents/skills
  .codex/skills           -> ../.agents/skills
  .windsurf/skills        -> ../.agents/skills

By default, also mirrors shared skills into ~/.codex/skills/.
Existing real directories are preserved; only symlink-style paths are replaced.

Options:
  --no-global  Skip mirroring into ~/.codex/skills/
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-global)
      sync_global=false
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

mkdir -p "$REPO_ROOT/.agents" "$REPO_ROOT/.claude" "$REPO_ROOT/.windsurf"
if $sync_global; then
  mkdir -p "$GLOBAL_CODEX_SKILLS"
fi

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

sync_global_codex_mirror() {
  local skill_dir
  local skill_name
  local target
  local resolved

  for skill_dir in "$AGENTS_SKILLS"/*; do
    [[ -f "$skill_dir/SKILL.md" ]] || continue
    skill_name="$(basename "$skill_dir")"
    target="$GLOBAL_CODEX_SKILLS/$skill_name"
    if [[ -e "$target" && ! -L "$target" ]]; then
      printf 'Preserving non-symlink global Codex skill path: %s\n' "$target" >&2
      continue
    fi
    ln -sfn "$AGENTS_SKILLS/$skill_name" "$target"
  done

  for target in "$GLOBAL_CODEX_SKILLS"/*; do
    [[ -L "$target" ]] || continue
    skill_name="$(basename "$target")"
    [[ "$skill_name" == .* ]] && continue

    resolved="$(readlink "$target" || true)"
    case "$resolved" in
      "$AGENTS_SKILLS/"*|*/.agents/skills/*|"$CODEX_SKILLS/"*|*/.codex/skills/*)
        [[ -e "$AGENTS_SKILLS/$skill_name" || -L "$AGENTS_SKILLS/$skill_name" ]] || rm -f "$target"
        ;;
      *)
        continue
        ;;
    esac
  done
}

link_catalog "$AGENTS_SKILLS" "../skills"
link_catalog "$CLAUDE_SKILLS" "../.agents/skills"
link_catalog "$CODEX_SKILLS" "../.agents/skills"
link_catalog "$WINDSURF_SKILLS" "../.agents/skills"

if $sync_global; then
  sync_global_codex_mirror
fi

if $sync_global; then
  echo "Repaired shared skill catalog symlinks and refreshed ~/.codex/skills"
else
  echo "Repaired shared skill catalog symlinks"
fi
