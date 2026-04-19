#!/usr/bin/env bash
# Shared functions for LLM toolkit setup scripts.
# Source this file: source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

set -euo pipefail

_IS_WINDOWS=""
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) _IS_WINDOWS=1 ;;
esac

to_windows_path() {
  local path="$1"
  python3 -c "import os, sys; print(os.path.abspath(sys.argv[1]))" "$path" 2>/dev/null && return 0
  # Already a Windows-style path
  if [[ "$path" =~ ^[A-Za-z]: ]]; then
    echo "$path"
    return 0
  fi
  # Pure-bash fallback: /c/Users/... -> C:\Users\...
  if [[ "$path" =~ ^/([a-zA-Z])(/.*) ]]; then
    echo "${BASH_REMATCH[1]^^}:${BASH_REMATCH[2]}" | sed 's|/|\\|g'
    return 0
  fi
  echo "$path"
}

create_link() {
  local target="$1" link_name="$2" actual_src="$3"

  if [[ -n "$_IS_WINDOWS" ]]; then
    local win_target win_link
    win_target="$(to_windows_path "$actual_src")"
    win_link="$(to_windows_path "$link_name")"

    if [[ -d "$actual_src" ]]; then
      # Try junction first (no admin needed) then symlink (requires admin/Dev Mode)
      cmd //c "mklink /J \"$win_link\" \"$win_target\"" > /dev/null 2>&1 && return 0
      cmd //c "mklink /D \"$win_link\" \"$win_target\"" > /dev/null 2>&1 && return 0
    else
      cmd //c "mklink \"$win_link\" \"$win_target\"" > /dev/null 2>&1 && return 0
    fi
  fi

  if ln -s "$target" "$link_name" 2>/dev/null; then
    return 0
  fi

  echo "Error: could not create a live link for $link_name -> $actual_src." >&2
  echo "Enable Developer Mode or run as administrator on Windows; use a local filesystem that supports symlinks." >&2
  return 1
}

compute_relative_path() {
  local from_dir="$1" to_dir="$2"
  python3 -c "
import os, sys
c = os.path.abspath(sys.argv[1])
d = os.path.abspath(sys.argv[2])
os.chdir(c)
print(os.path.relpath(d))
" "$from_dir" "$to_dir" 2>/dev/null && return 0

  realpath --relative-to="$from_dir" "$to_dir" 2>/dev/null && return 0
  echo "Error: could not compute relative path (need python3 or GNU realpath)" >&2
  return 1
}

safe_remove_path() {
  local target="$1"
  if [[ -z "$target" || "$target" == "/" || "$target" == "." || "$target" == ".." || "$target" == "~" || "$target" =~ ^[A-Za-z]:[\\/]*$ ]]; then
    echo "Error: refusing to remove unsafe path: '$target'" >&2
    return 1
  fi
  rm -rf -- "$target"
}

ensure_dir_link() {
  local link_path="$1"
  local actual_src="$2"
  local allow_repair="${3:-}"
  local link_parent rel_target resolved expected

  if [[ ! -d "$actual_src" ]]; then
    echo "Error: toolkit directory missing: $actual_src" >&2
    return 1
  fi

  expected="$(cd "$actual_src" && pwd -P)" || return 1

  if [[ -e "$link_path" ]]; then
    resolved="$(cd "$link_path" 2>/dev/null && pwd -P)" || resolved=""
    if [[ -n "$resolved" && "$resolved" == "$expected" ]]; then
      return 0
    fi
    if [[ -z "$allow_repair" ]]; then
      echo "Error: blocking path exists at $link_path and does not point at the expected toolkit directory." >&2
      echo "Remove it manually, or rerun with --force if you want the toolkit to repair it." >&2
      return 1
    fi
    echo "Warning: removing blocking path (not a symlink to expected target): $link_path" >&2
    safe_remove_path "$link_path" || return 1
  fi

  link_parent="$(dirname "$link_path")"
  mkdir -p "$link_parent"
  rel_target="$(compute_relative_path "$link_parent" "$actual_src")" || return 1
  create_link "$rel_target" "$link_path" "$actual_src" || return 1

  resolved="$(cd "$link_path" && pwd -P)" || true
  if [[ -z "$resolved" || "$resolved" != "$expected" ]]; then
    echo "Error: $link_path did not become a symlink to $actual_src (check link permissions)." >&2
    safe_remove_path "$link_path" 2>/dev/null || true
    return 1
  fi
  return 0
}

ensure_toolkit_windsurf_layout() {
  local root="$1"
  local allow_repair="${2:-}"
  [[ -d "$root/rules" ]] || { echo "Error: toolkit rules/ missing at $root" >&2; return 1; }
  [[ -d "$root/workflows" ]] || { echo "Error: toolkit workflows/ missing at $root" >&2; return 1; }
  mkdir -p "$root/.windsurf"
  ensure_dir_link "$root/.windsurf/rules" "$root/rules" "$allow_repair" || return 1
  ensure_dir_link "$root/.windsurf/workflows" "$root/workflows" "$allow_repair" || return 1
}

ensure_toolkit_setup_layout() {
  local root="$1"
  local allow_repair="${2:-}"
  mkdir -p "$root/.setup"
  if [[ -d "$root/integrations" ]]; then
    ensure_dir_link "$root/.setup/integrations" "$root/integrations" "$allow_repair" || return 1
  fi
  if [[ -d "$root/rules/examples" ]]; then
    ensure_dir_link "$root/.setup/examples" "$root/rules/examples" "$allow_repair" || return 1
  fi
}

resolve_absolute_path() {
  local path="$1"
  if [[ "$path" != /* ]] && [[ ! "$path" =~ ^[A-Za-z]: ]]; then
    (cd "$path" && pwd)
  else
    echo "$path"
  fi
}

is_windows() {
  [[ -n "$_IS_WINDOWS" ]]
}

is_macos() {
  [ "$(uname -s)" = "Darwin" ]
}

# Portable sed -i: GNU (Linux/Git Bash) needs sed -i; BSD (macOS) needs sed -i ''
sed_inplace() {
    if is_macos; then
        sed -i '' "$@"
    else
        sed -i "$@"
    fi
}

# Convert a Windows-style path to Unix style if running under Git Bash
to_unix_path() {
    local p="$1"
    if is_windows && command -v cygpath &>/dev/null; then
        cygpath -u "$p"
    else
        echo "$p"
    fi
}
