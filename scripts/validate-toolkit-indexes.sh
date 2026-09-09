#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

status=0

fail() {
  echo "FAIL: $*" >&2
  status=1
}

# Membership test against a newline-delimited list without forking a `grep`
# per lookup. The previous `grep -qxF "$x" <<< "$list"` call spawned a
# subprocess per invocation; repeated in a loop over dozens of items this
# became slow enough to look like a hang on Windows Git Bash, where process
# spawn is comparatively expensive. This in-process loop avoids the fork
# cost entirely.
list_contains() {
  local needle="$1" list="$2" line
  while IFS= read -r line; do
    [ "$line" = "$needle" ] && return 0
  done <<< "$list"
  return 1
}

find_python_cmd() {
  local candidate found
  for candidate in python3 python python.exe py; do
    found="$(command -v "$candidate" 2>/dev/null || true)"
    [ -n "$found" ] || continue
    case "$found" in
      */WindowsApps/*|*\\WindowsApps\\*) continue ;;
    esac
    if [ "$candidate" = "py" ]; then
      if py -3 -c 'import sys' >/dev/null 2>&1; then
        printf '%s\n' "py -3"
        return 0
      fi
    elif "$candidate" -c 'import sys' >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

trim_metadata_value() {
  local value="$1"
  value="${value//$'\r'/}"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  value="${value%\"}"
  value="${value#\"}"
  value="${value%\'}"
  value="${value#\'}"
  printf '%s\n' "$value"
}

read_metadata_value() {
  local file="$1" key="$2" line
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      "$key":*)
        trim_metadata_value "${line#*:}"
        return 0
        ;;
    esac
  done < "$file"
  return 0
}

check_referenced_paths_exist() {
  local line file path
  while IFS= read -r line; do
    file="${line%%:*}"
    path="${line#*:}"
    path="${path#\`}"
    [[ "$path" == *'<'* || "$path" == *'>'* ]] && continue
    if [ ! -e "$path" ]; then
      fail "$file references missing path: $path"
    fi
  done < <(grep -HEo '`(rules|workflows|skills|learnings)/[^`[:space:]]+\.md' "$@" 2>/dev/null || true)
}

iter_scoped_markdown_files() {
  local file
  while IFS= read -r -d '' file; do
    printf './%s\0' "$file"
  done < <(git ls-files --cached -z -- '*.md')
  while IFS= read -r -d '' file; do
    printf './%s\0' "$file"
  done < <(git ls-files --others --exclude-standard -z -- '*.md' \
    ':(exclude).agents/skills/**' ':(exclude).agents/worktrees/**' \
    ':(exclude).claude/agents/**' ':(exclude).claude/skills/**' ':(exclude).claude/worktrees/**' \
    ':(exclude).codex/agents/**' ':(exclude).codex/skills/**' ':(exclude).codex/worktrees/**' \
    ':(exclude).cursor/agents/**' ':(exclude).cursor/rules/**' ':(exclude).cursor/skills/**' \
    ':(exclude).cursor/workflows/**' ':(exclude).cursor/worktrees/**' \
    ':(exclude).windsurf/rules/**' ':(exclude).windsurf/skills/**' \
    ':(exclude).windsurf/workflows/**' ':(exclude).windsurf/worktrees/**')
}

check_workflow_indexes() {
  local expected actual actual_readme index_file f
  expected="$(find workflows -maxdepth 1 -type f -name '*.md' ! -name 'README.md' -exec basename {} \; | LC_ALL=C sort)"

  for index_file in AGENTS.md README.md; do
    actual="$(grep -hEo '`workflows/[^`]+\.md`' "$index_file" 2>/dev/null | sed 's#`workflows/##; s#`##' | grep -v '^README\.md$' | LC_ALL=C sort -u || true)"
    while IFS= read -r f; do
      [ -n "$f" ] || continue
      if ! list_contains "$f" "$actual"; then
        fail "workflow missing from $index_file index: workflows/$f"
      fi
    done <<< "$expected"

    while IFS= read -r f; do
      [ -n "$f" ] || continue
      if ! list_contains "$f" "$expected"; then
        fail "$index_file references non-existent workflow: workflows/$f"
      fi
    done <<< "$actual"
  done

  actual_readme="$(awk '/^## Available workflows$/,/^Many workflows/' workflows/README.md | grep -Eo '`[a-z0-9-]+\.md`' | tr -d '`' | LC_ALL=C sort -u || true)"
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    if ! list_contains "$f" "$actual_readme"; then
      fail "workflow missing from workflows/README.md index: $f"
    fi
  done <<< "$expected"

  while IFS= read -r f; do
    [ -n "$f" ] || continue
    if ! list_contains "$f" "$expected"; then
      fail "workflows/README.md references non-existent workflow: $f"
    fi
  done <<< "$actual_readme"
}

check_rule_indexes() {
  local expected actual f
  expected="$(find rules -maxdepth 1 -type f -name '*.md' ! -name 'README.md' -exec basename {} \; | LC_ALL=C sort)"
  actual="$(awk '/^## Rules$/,/^---$/' AGENTS.md | grep -Eo '`rules/[a-z0-9-]+\.md`' | sed 's#`rules/##; s#`##' | LC_ALL=C sort -u || true)"

  while IFS= read -r f; do
    [ -n "$f" ] || continue
    if ! list_contains "$f" "$actual"; then
      fail "rule missing from AGENTS.md Rules table: rules/$f"
    fi
  done <<< "$expected"

  while IFS= read -r f; do
    [ -n "$f" ] || continue
    if ! list_contains "$f" "$expected"; then
      fail "AGENTS.md Rules table references non-existent rule: rules/$f"
    fi
  done <<< "$actual"
}

check_subagent_index() {
  local expected actual f
  [ -d tool-subagents ] || return 0
  if [ ! -f tool-subagents/README.md ]; then
    fail "tool-subagents/README.md missing"
    return
  fi
  expected="$(find tool-subagents -maxdepth 1 -type f -name '*.md' ! -name 'README.md' -exec basename {} .md \; | LC_ALL=C sort)"
  actual="$(grep -Eo '^\| `[a-z0-9-]+` \|' tool-subagents/README.md | sed 's/^| `//; s/` |$//' | LC_ALL=C sort -u || true)"

  while IFS= read -r f; do
    [ -n "$f" ] || continue
    if ! list_contains "$f" "$actual"; then
      fail "subagent missing from tool-subagents/README.md catalog: tool-subagents/$f.md"
    fi
  done <<< "$expected"

  while IFS= read -r f; do
    [ -n "$f" ] || continue
    if ! list_contains "$f" "$expected"; then
      fail "tool-subagents/README.md catalog references non-existent subagent: tool-subagents/$f.md"
    fi
  done <<< "$actual"
}

check_intents_workflow_coverage() {
  local expected f
  [ -f INTENTS.md ] || return 0
  expected="$(find workflows -maxdepth 1 -type f -name '*.md' ! -name 'README.md' -exec basename {} .md \; | LC_ALL=C sort)"
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    if ! grep -qF "\`$f\`" INTENTS.md; then
      fail "workflow missing from INTENTS.md intent map: \`$f\`"
    fi
  done <<< "$expected"
}

check_workflow_size_limits() {
  local limit=12000 file chars python_cmd_text
  local -a python_cmd
  if ! python_cmd_text="$(find_python_cmd)"; then
    fail "python3 or python is required to validate workflow character counts"
    return
  fi
  read -r -a python_cmd <<< "$python_cmd_text"
  while IFS= read -r -d '' file; do
    chars="$("${python_cmd[@]}" - "$file" <<'PY'
from pathlib import Path
import sys
print(len(Path(sys.argv[1]).read_text(encoding="utf-8")))
PY
)"
    if [ "$chars" -gt "$limit" ]; then
      fail "$file is ${chars} characters; split reusable phases into separate workflows so each file stays <= ${limit}"
    fi
  done < <(find workflows -maxdepth 1 -type f -name '*.md' ! -name 'README.md' -print0 | LC_ALL=C sort -z)
}

check_skill_names() {
  local skill_dir skill_name folder_name
  while IFS= read -r -d '' skill_file; do
    skill_dir="$(dirname "$skill_file")"
    folder_name="$(basename "$skill_dir")"
    skill_name="$(read_metadata_value "$skill_file" "name")"
    if [ -z "$skill_name" ]; then
      fail "$skill_file missing frontmatter name"
    elif [ "$skill_name" != "$folder_name" ]; then
      fail "$skill_file name '$skill_name' does not match folder '$folder_name'"
    fi
  done < <(find skills -mindepth 2 -maxdepth 2 -name SKILL.md -print0 | LC_ALL=C sort -z)
}

check_skill_indexes() {
  local expected actual skill_file skill_dir
  expected="$(
    while IFS= read -r -d '' skill_file; do
      skill_dir="$(dirname "$skill_file")"
      basename "$skill_dir"
    done < <(find skills -mindepth 2 -maxdepth 2 -name SKILL.md -print0) | LC_ALL=C sort
  )"
  actual="$(
    {
      awk '/^## Skills$/,/^---$/' AGENTS.md
      awk '/^## Skills at a Glance$/,/^---$/' README.md
    } | grep -Eo '^\| \*\*[a-z0-9][a-z0-9-]+\*\* \|' | sed 's/^| \*\*//; s/\*\* |$//' | LC_ALL=C sort -u
  )"

  while IFS= read -r skill; do
    [ -n "$skill" ] || continue
    if ! list_contains "$skill" "$actual"; then
      fail "skill missing from AGENTS.md/README.md indexes: skills/$skill/SKILL.md"
    fi
  done <<< "$expected"

  while IFS= read -r skill; do
    [ -n "$skill" ] || continue
    if ! list_contains "$skill" "$expected"; then
      fail "AGENTS.md/README.md reference non-existent skill: skills/$skill/SKILL.md"
    fi
  done <<< "$actual"
}

check_project_specific_leaks() {
  local allowed=(
    "learnings/"
    ".github/copilot-instructions.md"
  )
  local pattern="${FORBIDDEN_PROJECT_PATTERNS:-}"
  if [ -z "$pattern" ]; then
    return 0
  fi
  local file allowed_file
  while IFS= read -r -d '' file; do
    allowed_file=0
    for prefix in "${allowed[@]}"; do
      if [[ "$file" == "$prefix"* || "$file" == "$prefix" ]]; then
        allowed_file=1
        break
      fi
    done
    if [ "$allowed_file" -eq 0 ]; then
      if grep -Eq "$pattern" "$file"; then
        fail "project-specific reference outside allowed project evidence paths: $file"
      fi
    fi
  done < <(iter_scoped_markdown_files)
}

check_scripts_executable() {
  local mode _object _stage script
  while read -r mode _object _stage script; do
    [ -f "$script" ] || continue
    if grep -q '^#!/' "$script" && [ "$mode" != "100755" ]; then
      fail "$script has a shebang but git index mode is $mode; run git update-index --chmod=+x $script"
    fi
  done < <(git ls-files -s -- 'scripts/*.sh')
}

check_learning_categories() {
  local allowed_line allowed_categories file category token
  allowed_line="$(read_metadata_value learnings/README.md "category")"
  if [ -z "$allowed_line" ]; then
    fail "learnings/README.md missing category template line"
    return
  fi

  allowed_categories="$(tr '|' '\n' <<< "$allowed_line" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//' | grep -v '^$' | LC_ALL=C sort -u)"
  while IFS= read -r -d '' file; do
    [ "$(basename "$file")" = "README.md" ] && continue
    [ "$(basename "$file")" = "INDEX.md" ] && continue
    category="$(read_metadata_value "$file" "category")"
    if [ -z "$category" ]; then
      fail "$file missing category frontmatter"
      continue
    fi
    while IFS= read -r token; do
      [ -n "$token" ] || continue
      if ! list_contains "$token" "$allowed_categories"; then
        fail "$file uses category not listed in learnings/README.md template: $token"
      fi
    done < <(tr '|' '\n' <<< "$category" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
  done < <(find learnings -maxdepth 1 -type f -name '*.md' -print0 | LC_ALL=C sort -z)
}

check_learning_index() {
  # learnings/INDEX.md is the canonical one-line-per-learning index; fall back to README.md
  local file name referenced index_file
  index_file="learnings/INDEX.md"
  [ -f "$index_file" ] || index_file="learnings/README.md"
  while IFS= read -r -d '' file; do
    name="$(basename "$file")"
    [ "$name" = "README.md" ] && continue
    [ "$name" = "INDEX.md" ] && continue
    if ! grep -qF "\`$name\`" "$index_file"; then
      fail "learning missing from $index_file: learnings/$name"
    fi
  done < <(find learnings -maxdepth 1 -type f -name '*.md' -print0 | LC_ALL=C sort -z)

  while IFS= read -r referenced; do
    [ -n "$referenced" ] || continue
    if [ ! -f "learnings/$referenced" ]; then
      fail "$index_file references non-existent learning: learnings/$referenced"
    fi
  done < <(grep -Eo '`[a-z0-9][a-z0-9-]+\.md`' "$index_file" | tr -d '`' | LC_ALL=C sort -u || true)
}

check_markdown_encoding_artifacts() {
  local file matches bom_files

  bom_files="$(iter_scoped_markdown_files | xargs -0 -r awk 'FNR == 1 && substr($0, 1, 1) == "\357\273\277" { print FILENAME }' 2>/dev/null || true)"
  if [ -n "$bom_files" ]; then
    while IFS= read -r file; do
      [ -n "$file" ] || continue
      fail "$file starts with UTF-8 BOM; rewrite as UTF-8 without BOM"
    done <<< "$bom_files"
  fi

  # Classic UTF-8-read-as-CP1252 sequences only; "Ã" before an uppercase letter is valid Portuguese (e.g. "AÇÃO").
  matches="$(iter_scoped_markdown_files | xargs -0 -r grep -nE 'â€|Ã[©£§¡³ªºµ¢­¨]|Â[[:space:]]' 2>/dev/null || true)"
  if [ -n "$matches" ]; then
    fail "possible UTF-8/CP1252 mojibake markers:"
    printf '%s\n' "$matches" >&2
  fi
}

check_rule_example_index() {
  local file name referenced
  [ -d rules/examples ] || return 0
  [ -f rules/examples/README.md ] || return 0
  while IFS= read -r -d '' file; do
    name="$(basename "$file")"
    [ "$name" = "README.md" ] && continue
    if ! grep -qF "\`$name\`" rules/examples/README.md; then
      fail "rule example missing from rules/examples/README.md index: rules/examples/$name"
    fi
  done < <(find rules/examples -maxdepth 1 -type f -name '*.md' -print0 | LC_ALL=C sort -z)

  while IFS= read -r referenced; do
    [ -n "$referenced" ] || continue
    if [ ! -f "rules/examples/$referenced" ]; then
      fail "rules/examples/README.md references non-existent example: rules/examples/$referenced"
    fi
  done < <(grep -Eo '`[a-z0-9][a-z0-9-]+\.md`' rules/examples/README.md | tr -d '`' | LC_ALL=C sort -u || true)
}

check_mandatory_headings_in_toml() {
  local md toml base name heading
  while IFS= read -r -d '' md; do
    base="${md%.md}"
    toml="${base}.toml"
    [ -f "$toml" ] || continue
    name="$(basename "$base")"
    while IFS= read -r heading; do
      [ -n "$heading" ] || continue
      if ! grep -qF "$heading" "$toml"; then
        fail "$name: MANDATORY heading missing from tool-subagents/$name.toml: $heading"
      fi
    done < <(grep -E '^## .* \(MANDATORY\)[[:space:]]*$' "$md" || true)
  done < <(find tool-subagents -maxdepth 1 -type f -name '*.md' ! -name 'README.md' -print0 | LC_ALL=C sort -z)
}

check_skill_local_references() {
  local skill_file skill_dir line rel
  while IFS= read -r -d '' skill_file; do
    skill_dir="$(dirname "$skill_file")"
    while IFS= read -r line; do
      rel="${line#*\`}"
      rel="${rel%\`*}"
      if [ ! -e "$skill_dir/$rel" ]; then
        fail "$skill_file references missing skill-local path: $rel"
      fi
    done < <(grep -Eo '`references/[^`[:space:]]+\.md`' "$skill_file" 2>/dev/null || true)
  done < <(find skills -mindepth 2 -maxdepth 2 -name SKILL.md -print0 | LC_ALL=C sort -z)
}

reference_files=(AGENTS.md README.md INTENTS.md workflows/README.md rules/*.md workflows/*.md skills/*/SKILL.md tool-subagents/*.md)
check_referenced_paths_exist "${reference_files[@]}"
check_workflow_indexes
check_intents_workflow_coverage
check_workflow_size_limits
check_skill_names
check_skill_indexes
check_rule_indexes
check_subagent_index
check_project_specific_leaks
check_scripts_executable
check_learning_categories
check_learning_index
check_markdown_encoding_artifacts
check_rule_example_index
check_mandatory_headings_in_toml
check_skill_local_references

if [ "$status" -ne 0 ]; then
  exit "$status"
fi

echo "Toolkit indexes and genericity checks passed."
