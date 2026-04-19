#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly SCRIPT_DIR
readonly REPO_ROOT
readonly AGENTS_SKILLS="$REPO_ROOT/.agents/skills"
readonly CODEX_SKILLS="$SCRIPT_DIR/skills"
readonly CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
readonly GLOBAL_CODEX_SKILLS="$CODEX_HOME/skills"

sync_global=true
mirror_mode="auto"

usage() {
  cat <<'USAGE'
Usage: ./.codex/sync-shared-skills.sh [--no-global] [--copy|--symlink]

Mirrors portable skills from .agents/skills/ into .codex/skills/.
By default, also mirrors .codex/skills/ into ~/.codex/skills/.

Options:
  --no-global  Skip mirroring into ~/.codex/skills/
  --copy       Force copy mode (for filesystems without symlink support)
  --symlink    Force symlink mode
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-global)
      sync_global=false
      ;;
    --copy)
      mirror_mode="copy"
      ;;
    --symlink)
      mirror_mode="symlink"
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

if [[ ! -d "$AGENTS_SKILLS" ]]; then
  printf 'Missing portable skills directory: %s\n' "$AGENTS_SKILLS" >&2
  exit 1
fi

mkdir -p "$CODEX_SKILLS"
if $sync_global; then
  mkdir -p "$GLOBAL_CODEX_SKILLS"
fi

link_supported() {
  local probe_base probe_dir probe_target
  probe_base="$CODEX_SKILLS"
  mkdir -p "$probe_base"
  probe_dir="$(mktemp -d "$probe_base/.link-check.XXXXXX")"
  probe_target="$probe_dir/target"
  mkdir -p "$probe_target"

  if ln -s "$probe_target" "$probe_dir/link" 2>/dev/null; then
    rm -f "$probe_dir/link"
    rmdir "$probe_target" "$probe_dir" 2>/dev/null || true
    return 0
  fi

  rmdir "$probe_target" "$probe_dir" 2>/dev/null || true
  return 1
}

copy_tree() {
  local src="$1"
  local dst="$2"
  mkdir -p "$dst"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete "$src/" "$dst/"
  else
    rm -rf "$dst"
    mkdir -p "$dst"
    cp -a "$src/." "$dst/"
  fi
}

sync_codex_symlink_mirror() {
  local skill_dir
  local skill_name
  local target

  for skill_dir in "$AGENTS_SKILLS"/*; do
    [[ -f "$skill_dir/SKILL.md" ]] || continue
    skill_name="$(basename "$skill_dir")"
    target="$CODEX_SKILLS/$skill_name"
    if [[ -e "$target" && ! -L "$target" ]]; then
      printf 'Preserving non-symlink Codex skill path: %s\n' "$target" >&2
      continue
    fi
    ln -sfn "$skill_dir" "$target"
  done

  for target in "$CODEX_SKILLS"/*; do
    [[ -L "$target" ]] || continue
    skill_name="$(basename "$target")"
    [[ "$skill_name" == .* ]] && continue
    [[ -f "$AGENTS_SKILLS/$skill_name/SKILL.md" ]] || rm -f "$target"
  done
}

sync_codex_copy_mirror() {
  local skill_dir
  local skill_name
  local target
  declare -A expected=()

  for skill_dir in "$AGENTS_SKILLS"/*; do
    [[ -f "$skill_dir/SKILL.md" ]] || continue
    skill_name="$(basename "$skill_dir")"
    expected["$skill_name"]=1
    target="$CODEX_SKILLS/$skill_name"
    [[ -L "$target" ]] && rm -f "$target"
    copy_tree "$skill_dir" "$target"
  done

  for target in "$CODEX_SKILLS"/*; do
    [[ -e "$target" || -L "$target" ]] || continue
    skill_name="$(basename "$target")"
    [[ "$skill_name" == .* || "$skill_name" == "README.md" ]] && continue
    [[ -n "${expected[$skill_name]:-}" ]] || rm -rf "$target"
  done
}

sync_global_codex_symlink_mirror() {
  local skill_dir
  local skill_name
  local target
  local resolved

  for skill_dir in "$CODEX_SKILLS"/*; do
    [[ -f "$skill_dir/SKILL.md" ]] || continue
    skill_name="$(basename "$skill_dir")"
    target="$GLOBAL_CODEX_SKILLS/$skill_name"
    if [[ -e "$target" && ! -L "$target" ]]; then
      printf 'Preserving non-symlink global Codex skill path: %s\n' "$target" >&2
      continue
    fi
    ln -sfn "$skill_dir" "$target"
  done

  for target in "$GLOBAL_CODEX_SKILLS"/*; do
    [[ -L "$target" ]] || continue
    skill_name="$(basename "$target")"
    [[ "$skill_name" == .* ]] && continue

    resolved="$(readlink "$target" || true)"
    case "$resolved" in
      "$CODEX_SKILLS/"*|*/.codex/skills/*)
        [[ -e "$CODEX_SKILLS/$skill_name" || -L "$CODEX_SKILLS/$skill_name" ]] || rm -f "$target"
        ;;
      *)
        continue
        ;;
    esac
  done
}

sync_global_codex_copy_mirror() {
  local skill_dir
  local skill_name
  local target

  for skill_dir in "$CODEX_SKILLS"/*; do
    [[ -f "$skill_dir/SKILL.md" ]] || continue
    skill_name="$(basename "$skill_dir")"
    target="$GLOBAL_CODEX_SKILLS/$skill_name"
    [[ -L "$target" ]] && rm -f "$target"
    copy_tree "$skill_dir" "$target"
  done
}

if [[ "$mirror_mode" == "auto" ]]; then
  if link_supported; then
    mirror_mode="symlink"
  else
    mirror_mode="copy"
    echo "Symlinks are not supported in this environment; using copy mode." >&2
  fi
fi

if [[ "$mirror_mode" == "symlink" ]]; then
  sync_codex_symlink_mirror
else
  sync_codex_copy_mirror
fi

if $sync_global; then
  if [[ "$mirror_mode" == "symlink" ]]; then
    sync_global_codex_symlink_mirror
  else
    sync_global_codex_copy_mirror
  fi
fi

if $sync_global; then
  echo "Synced .codex/skills and ~/.codex/skills from .agents/skills (mode: $mirror_mode)"
else
  echo "Synced .codex/skills from .agents/skills (mode: $mirror_mode)"
fi
