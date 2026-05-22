#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

status=0

fail() {
  echo "FAIL: $*" >&2
  status=1
}

info() {
  echo "OK: $*"
}

path_exists_or_allowed_placeholder() {
  local path="$1"

  [[ -n "$path" ]] || return 0
  path="${path//\\//}"
  [[ "$path" == *"<"* || "$path" == *">"* ]] && return 0
  [[ "$path" == *"*"* ]] && return 0
  [[ "$path" == http://* || "$path" == https://* ]] && return 0
  [[ "$path" == ./* ]] && path="${path#./}"
  [[ "$path" == scripts/sync-llm-configs.sh || "$path" == scripts/sync-llm-configs.ps1 ]] && return 0
  [[ "$path" == docs/jira || "$path" == docs/jira/ ]] && return 0

  if [[ -e "$path" ]]; then
    return 0
  fi

  return 1
}

extract_backtick_paths() {
  local file="$1"
  grep -Eo '`(\./)?(AGENTS\.md|CLAUDE\.md|INTENTS\.md|README\.md|rules|workflows|skills|tool-subagents|integrations|docs|rubrics|scripts|learnings)/?[^`[:space:]]*`|`(AGENTS\.md|CLAUDE\.md|INTENTS\.md|README\.md)`' "$file" 2>/dev/null |
    tr -d '`' || true
}

check_referenced_paths_exist() {
  local file="$1"
  [[ -f "$file" ]] || return 0

  local path
  while IFS= read -r path; do
    [[ -n "$path" ]] || continue
    path="${path%:}"
    path="${path%,}"
    if ! path_exists_or_allowed_placeholder "$path"; then
      fail "$file references missing path: $path"
    fi
  done < <(extract_backtick_paths "$file")
}

check_skill_names() {
  local skill_file skill_dir folder_name skill_name
  while IFS= read -r -d '' skill_file; do
    skill_dir="$(dirname "$skill_file")"
    folder_name="$(basename "$skill_dir")"
    skill_name="$(awk -F': *' '/^name:/ {gsub(/["'\''\r]/, "", $2); print $2; exit}' "$skill_file")"
    if [[ -z "$skill_name" ]]; then
      fail "$skill_file missing frontmatter name"
    elif [[ "$skill_name" != "$folder_name" ]]; then
      fail "$skill_file name '$skill_name' does not match folder '$folder_name'"
    fi
  done < <(find skills -mindepth 2 -maxdepth 2 -name SKILL.md -print0 | LC_ALL=C sort -z)
}

check_workflow_names() {
  local workflow
  while IFS= read -r -d '' workflow; do
    case "$(basename "$workflow")" in
      README.md) continue ;;
      *" ("*").md") fail "cloud-sync duplicate workflow filename: $workflow" ;;
    esac
  done < <(find workflows -maxdepth 1 -type f -name '*.md' -print0 | LC_ALL=C sort -z)
}

check_cloud_sync_duplicates() {
  local tracked all_files
  tracked="$(git ls-files 2>/dev/null | grep -E ' \([0-9]+\)\.' || true)"
  if [[ -n "$tracked" ]]; then
    fail "tracked cloud-sync duplicate files detected: $tracked"
  fi

  all_files="$(find . -path ./.git -prune -o -type f -name '* ([0-9]).*' -print || true)"
  if [[ -n "$all_files" ]]; then
    fail "cloud-sync duplicate files detected in working tree: $all_files"
  fi
}

check_project_specific_leaks() {
  local pattern="${FORBIDDEN_PROJECT_PATTERNS:-}"
  [[ -n "$pattern" ]] || return 0

  local file
  while IFS= read -r -d '' file; do
    case "$file" in
      ./learnings/*) continue ;;
    esac
    if grep -Eq "$pattern" "$file"; then
      fail "project-specific reference matched forbidden pattern in: ${file#./}"
    fi
  done < <(find . -path ./.git -prune -o -type f \( -name '*.md' -o -name '*.toml' -o -name '*.ps1' -o -name '*.sh' -o -name '*.py' \) -print0)
}

check_scripts_have_shebang_permissions() {
  local script
  while IFS= read -r -d '' script; do
    if head -n1 "$script" | grep -q '^#!' && [[ ! -x "$script" ]]; then
      fail "script has shebang but is not executable: ${script#./}"
    fi
  done < <(find scripts -maxdepth 1 -type f -name '*.sh' -print0)
}

for file in AGENTS.md README.md INTENTS.md workflows/README.md docs/repo-setup-prompt.md; do
  check_referenced_paths_exist "$file"
done

check_skill_names
check_workflow_names
check_cloud_sync_duplicates
check_project_specific_leaks
check_scripts_have_shebang_permissions

if [[ "$status" -ne 0 ]]; then
  exit "$status"
fi

info "toolkit indexes, skill frontmatter, references, and genericity checks passed"
