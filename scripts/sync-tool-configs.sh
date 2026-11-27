#!/usr/bin/env bash
# Sync rules and workflows to all AI coding tool formats.
#
# Source of truth (first match wins):
#   1. .windsurf/rules/*.md and .windsurf/workflows/*.md (consumer layout after setup-repo)
#   2. rules/*.md and workflows/*.md at project root (toolkit canonical layout)
#
# Repairs shared compatibility surfaces:
#   .cursor/rules/*.mdc -> generated from the canonical shared rules (listed in .cursor/rules/.gitignore; never an old directory link)
#   .cursor/workflows -> no longer created (not a Cursor surface); an existing link is left alone
#   .cursor/agents -> canonical shared tool-subagents
#   .claude/agents -> canonical shared tool-subagents
#
# Generates repo-local exports:
#   CLAUDE.md                        - Claude Code import of AGENTS.md (@AGENTS.md)
#   .github/copilot-instructions.md  - GitHub Copilot (shared selection + LLM config content)
#   AGENTS.md                        - primary LLM surface (preserves existing content + refreshes sync block)
#   .cursorignore / .cursorindexingignore managed blocks (repo-local, optional)
#
# LLM config is read from the project's own docs/llm/ directory. If
# docs/llm/toolkit-selection.txt exists and contains entries, generated outputs are
# curated to that shared selection. Local rules and workflows from docs/llm/rules/ and
# docs/llm/workflows/ are appended to AGENTS.md and Copilot exports without duplicating
# shared canonical files.
#
# Usage:
#   ./scripts/sync-tool-configs.sh [path-to-project] [--skip-agents-md] [--skip-github] [--force]
#
# Use --skip-agents-md when syncing this toolkit repo itself so handcrafted AGENTS.md
# is not modified.
# Use --skip-cursor-rules to skip generating `.cursor/rules/*.mdc`.
# Use --skip-github to avoid generating `.github/copilot-instructions.md`.
# Use --force to replace blocking paths that do not point at the expected sources.

set -euo pipefail

# Avoid macOS AppleDouble sidecars when generating tool surfaces on non-HFS volumes.
export COPYFILE_DISABLE=1

if ((BASH_VERSINFO[0] < 4 || (BASH_VERSINFO[0] == 4 && BASH_VERSINFO[1] < 4))); then
  echo "Error: bash 4.4+ required (found ${BASH_VERSION})" >&2
  exit 1
fi

SKIP_AGENTS_MD=0
SKIP_CURSOR_RULES=0
SKIP_GITHUB=0
ALLOW_REPAIR=0
POSITIONAL=()
for arg in "$@"; do
  case "$arg" in
    --skip-agents-md)    SKIP_AGENTS_MD=1 ;;
    --skip-cursor-rules) SKIP_CURSOR_RULES=1 ;;
    --skip-github|--skip-github-copilot) SKIP_GITHUB=1 ;;
    --force|--force-repair) ALLOW_REPAIR=1 ;;
    *)                   POSITIONAL+=("$arg") ;;
  esac
done

PROJECT="${POSITIONAL[0]:-.}"
if [[ "$PROJECT" != /* ]] && [[ ! "$PROJECT" =~ ^[A-Za-z]: ]]; then
  if [[ ! -d "$PROJECT" ]]; then
    echo "Error: project directory not found: $PROJECT" >&2
    exit 1
  fi
  PROJECT="$(cd "$PROJECT" && pwd)"
fi

is_windows_shell() {
  case "${OSTYPE:-}" in
    msys*|cygwin*|win32*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

to_native_path() {
  local path="$1"

  if command -v cygpath >/dev/null 2>&1; then
    cygpath -w "$path"
  else
    printf '%s\n' "$path"
  fi
}

resolve_symlink_source() {
  # Resolve a (possibly relative) symlink source against the destination's parent.
  # Echoes an absolute path suitable for existence checks; does NOT alter the
  # path stored in the symlink itself (which should remain relative for portability).
  local source="$1"
  local destination="$2"

  if [[ "$source" = /* ]] || [[ "$source" =~ ^[A-Za-z]: ]]; then
    printf '%s\n' "$source"
    return
  fi

  local dest_dir
  dest_dir="$(dirname "$destination")"
  printf '%s/%s\n' "$dest_dir" "$source"
}

create_symlink() {
  local source="$1"
  local destination="$2"

  # Resolve source against destination parent so `-d` works for relative paths.
  local source_resolved source_resolved_canon
  source_resolved="$(resolve_symlink_source "$source" "$destination")"
  if [[ -d "$source_resolved" ]]; then
    source_resolved_canon="$(cd "$source_resolved" && pwd -P)"
  elif [[ -e "$source_resolved" ]]; then
    source_resolved_canon="$(cd "$(dirname "$source_resolved")" && pwd -P)/$(basename "$source_resolved")"
  else
    source_resolved_canon="$source_resolved"
  fi

  if is_windows_shell; then
    local destination_native
    destination_native="$(to_native_path "$destination")"

    # Build the source path mklink should store: keep relative when possible for
    # portability; convert forward slashes to backslashes for Windows.
    local source_for_mklink="$source"
    if [[ "$source_for_mklink" = /* ]] || [[ "$source_for_mklink" =~ ^[A-Za-z]: ]]; then
      source_for_mklink="$(to_native_path "$source_for_mklink")"
    fi
    source_for_mklink="${source_for_mklink//\//\\}"

    if [[ -d "$source_resolved_canon" ]]; then
      local source_native
      source_native="$(to_native_path "$source_resolved_canon")"
      # Prefer junctions with absolute targets on Windows. Relative directory symlinks
      # often become invalid reparse points when created from Git Bash/MSYS.
      if ! cmd.exe //D //C mklink //J "$destination_native" "$source_native" >/dev/null 2>&1; then
        if ! cmd.exe //D //C mklink //D "$destination_native" "$source_for_mklink" >/dev/null 2>&1; then
          echo "Error: failed to create directory symlink '$destination' -> '$source'." >&2
          echo "  Enable Windows Developer Mode (Settings > Privacy & security > For developers)," >&2
          echo "  or run this script from an elevated shell." >&2
          return 1
        fi
      fi
    else
      if ! cmd.exe //D //C mklink "$destination_native" "$source_for_mklink" >/dev/null 2>&1; then
        echo "Error: failed to create file symlink '$destination' -> '$source'." >&2
        echo "  Enable Windows Developer Mode or run from an elevated shell." >&2
        return 1
      fi
    fi
  else
    ln -sfn "$source" "$destination"
  fi
}

reset_path() {
  local path="$1"

  if is_windows_shell && [[ -e "$path" || -L "$path" ]]; then
    local path_native
    path_native="$(to_native_path "$path")"
    cmd.exe //D //C rmdir "$path_native" >/dev/null 2>&1 || true
    cmd.exe //D //C del //F //Q "$path_native" >/dev/null 2>&1 || true
  fi

  if [[ -L "$path" ]]; then
    rm -f "$path"
    return 0
  fi

  if [[ -d "$path" ]]; then
    rm -rf "$path"
    return 0
  fi

  rm -f "$path"
}

ensure_symlink() {
  local target="$1"
  local source="$2"

  mkdir -p "$(dirname "$target")"

  # Validate the source exists before destroying the existing target, so a
  # failed symlink creation does not leave the path empty.
  local source_resolved
  source_resolved="$(resolve_symlink_source "$source" "$target")"
  if [[ ! -e "$source_resolved" ]] && [[ ! -L "$source_resolved" ]]; then
    echo "Warning: symlink source missing, skipping: $source_resolved (target: $target)" >&2
    return 1
  fi

  if [[ -e "$target" || -L "$target" ]]; then
    local target_resolved expected_source
    target_resolved="$(cd "$target" 2>/dev/null && pwd -P)" || target_resolved=""
    expected_source="$(cd "$source_resolved" 2>/dev/null && pwd -P)" || expected_source=""
    if [[ -n "$target_resolved" && "$target_resolved" == "$expected_source" ]]; then
      return 0
    fi
    if [[ "$ALLOW_REPAIR" -ne 1 ]]; then
      echo "Error: blocking path exists at $target and does not point at the expected source." >&2
      echo "  Expected source: $source_resolved" >&2
      echo "  Re-run with --force to replace it after a replacement link is created." >&2
      return 1
    fi
  fi

  local tmp_target
  tmp_target="${target}.tmp-link-$$"
  reset_path "$tmp_target"
  if ! create_symlink "$source" "$tmp_target"; then
    reset_path "$tmp_target" 2>/dev/null || true
    return 1
  fi

  reset_path "$target"
  if ! mv "$tmp_target" "$target"; then
    reset_path "$tmp_target" 2>/dev/null || true
    return 1
  fi
}

WINDSURF_RULES=""
WINDSURF_WORKFLOWS=""

if [[ -d "$PROJECT/.windsurf/rules" ]]; then
  WINDSURF_RULES="$PROJECT/.windsurf/rules"
  WINDSURF_WORKFLOWS="$PROJECT/.windsurf/workflows"
elif [[ -d "$PROJECT/rules" ]]; then
  WINDSURF_RULES="$PROJECT/rules"
  WINDSURF_WORKFLOWS="$PROJECT/workflows"
elif [[ -L "$PROJECT/.agents" || -d "$PROJECT/.agents" ]]; then
  # Fallback for consumer repos where .windsurf/rules is a broken nested symlink
  # (common on Windows synced folders). Resolve the toolkit root via .agents.
  _AGENTS_RESOLVED="$(cd "$PROJECT/.agents" 2>/dev/null && pwd -P)" || _AGENTS_RESOLVED=""
  if [[ -n "$_AGENTS_RESOLVED" ]]; then
    _TOOLKIT_ROOT="$(cd "$_AGENTS_RESOLVED/.." && pwd -P)"
    if [[ -d "$_TOOLKIT_ROOT/rules" ]]; then
      WINDSURF_RULES="$_TOOLKIT_ROOT/rules"
      WINDSURF_WORKFLOWS="$_TOOLKIT_ROOT/workflows"
      echo "Note: resolved rules via .agents -> toolkit ($WINDSURF_RULES)" >&2
    fi
  fi
  if [[ -z "$WINDSURF_RULES" ]]; then
    echo "Error: no rules directory found in $PROJECT (expected .windsurf/rules/, rules/, or .agents link to toolkit)" >&2
    exit 1
  fi
else
  echo "Error: no rules directory found in $PROJECT (expected .windsurf/rules/ or rules/)" >&2
  exit 1
fi

if [[ ! -d "$WINDSURF_WORKFLOWS" ]]; then
  echo "Warning: no workflows directory next to rules ($WINDSURF_WORKFLOWS); workflow sync skipped for missing dir" >&2
fi

if [[ -d "$PROJECT/.windsurf/rules" ]]; then
  DISPLAY_RULES_PREFIX=".windsurf/rules/"
  DISPLAY_WORKFLOWS_PREFIX=".windsurf/workflows/"
else
  DISPLAY_RULES_PREFIX="rules/"
  DISPLAY_WORKFLOWS_PREFIX="workflows/"
fi

PROJECT_NAME="$(basename "$PROJECT")"
DOC_TITLE="$PROJECT_NAME"
if [[ -n "${TOOLKIT_DOC_TITLE:-}" ]]; then
  DOC_TITLE="$TOOLKIT_DOC_TITLE"
elif [[ -f "$PROJECT/TOOLKIT_DOC_TITLE" ]]; then
  DOC_TITLE="$(head -n1 "$PROJECT/TOOLKIT_DOC_TITLE" | tr -d '\r')"
fi

LLM_CONFIG_ROOT="$PROJECT/docs/llm"
LLM_CONFIG_ROOT_LABEL="docs/llm"
SELECTION_FILE="$LLM_CONFIG_ROOT/toolkit-selection.txt"
SELECTION_FILE_LABEL="$LLM_CONFIG_ROOT_LABEL/toolkit-selection.txt"

append_unique() {
  local -n ref="$1"
  local candidate="$2"
  if [[ ${#ref[@]} -gt 0 ]]; then
    local existing
    for existing in "${ref[@]}"; do
      if [[ "$existing" == "$candidate" ]]; then
        return 0
      fi
    done
  fi
  ref+=("$candidate")
}

array_contains() {
  local needle="$1"
  shift
  local item
  for item in "$@"; do
    [[ "$item" == "$needle" ]] && return 0
  done
  return 1
}

copy_markdown_file() {
  local src="$1"
  local dest="$2"

  if cp -X "$src" "$dest" 2>/dev/null; then
    return 0
  fi

  cp "$src" "$dest"
}

strip_frontmatter() {
  local file="$1"
  awk '
    BEGIN { in_front=0; fm_count=0 }
    NR == 1 { sub(/^\xef\xbb\xbf/, "") }
    /^---$/ {
      fm_count++
      if (fm_count == 1) { in_front=1; next }
      if (fm_count == 2) { in_front=0; next }
    }
    !in_front { print }
  ' "$file"
}

file_has_frontmatter() {
  local file="$1"
  awk '
    NR == 1 {
      sub(/^\xef\xbb\xbf/, "")
      sub(/\r$/, "")
      if ($0 == "---") { print "1" }
      exit
    }
  ' "$file"
}

first_heading_or_basename() {
  local file="$1"
  local heading
  heading="$(awk '
    NR == 1 { sub(/^\xef\xbb\xbf/, "") }
    /^[[:space:]]*#/ {
      line = $0
      sub(/^[[:space:]]*#+[[:space:]]*/, "", line)
      if (line != "") {
        print line
        exit
      }
    }
  ' "$file")"

  if [[ -n "$heading" ]]; then
    printf '%s\n' "$heading"
  else
    basename "$file" .md | tr '-' ' '
  fi
}

escape_frontmatter_value() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

# Prints the frontmatter trigger value of a rule (empty when there is none).
rule_trigger() {
  awk '
    NR == 1 { sub(/^\xef\xbb\xbf/, ""); if ($0 != "---") exit; next }
    /^---[ \t\r]*$/ { exit }
    /^trigger:/ {
      sub(/^trigger:[ \t]*/, "")
      sub(/[ \t\r]+$/, "")
      print
      exit
    }
  ' "$1"
}

rule_is_on_demand() {
  [[ "$(rule_trigger "$1")" == "model_decision" ]]
}

cursor_convert_rule() {
  local src="$1"
  local dest="$2"
  if [[ "$(file_has_frontmatter "$src")" == "1" ]]; then
    awk '
      function emit_front(   i, l, manual, printed_apply, v) {
        manual = 0
        printed_apply = 0
        for (i = 1; i <= n; i++) if (buf[i] ~ /^trigger:[ \t]*manual/) manual = 1
        for (i = 1; i <= n; i++) {
          l = buf[i]
          if (l ~ /^trigger:[ \t]*always_on/) { print "alwaysApply: true"; printed_apply = 1; continue }
          if (l ~ /^trigger:[ \t]*glob/) { print "alwaysApply: false"; printed_apply = 1; continue }
          if (l ~ /^trigger:[ \t]*model_decision/) { print "alwaysApply: false"; printed_apply = 1; continue }
          if (l ~ /^trigger:[ \t]*manual/) { printed_apply = 1; continue }
          if (l ~ /^trigger:/) { print "alwaysApply: true"; printed_apply = 1; continue }
          if (manual && l ~ /^description:/) continue
          if (l ~ /^globs:/) {
            v = l
            sub(/^globs:[ \t]*/, "", v)
            gsub(/^["\047]|["\047]$/, "", v)
            l = "globs: " v
          }
          print l
        }
        if (!printed_apply) print "alwaysApply: true"
      }
      BEGIN { state = 0; n = 0 }
      NR == 1 { sub(/^\xef\xbb\xbf/, "") }
      state == 0 { state = 1; print "---"; next }
      state == 1 {
        line = $0
        sub(/\r$/, "", line)
        if (line == "---") { emit_front(); print "---"; state = 2; next }
        buf[++n] = line
        next
      }
      { print }
      END { if (state == 1) for (i = 1; i <= n; i++) print buf[i] }
    ' "$src" > "$dest"
  else
    local desc
    desc="$(escape_frontmatter_value "$(first_heading_or_basename "$src")")"
    {
      echo "---"
      echo "description: \"$desc\""
      echo "alwaysApply: true"
      echo "---"
      echo ""
      strip_frontmatter "$src"
    } > "$dest"
  fi
}

CURSOR_GENERATED_MARKER="generated-by: sync-tool-configs"

cursor_is_generated() {
  [[ -f "$1" ]] || return 1
  awk -v marker="<!-- $CURSOR_GENERATED_MARKER " '
    { sub(/\r$/, "") }
    NR == 1 { if ($0 != "---") exit 1; next }
    after { exit (index($0, marker) == 1 && $0 ~ / -->$/) ? 0 : 1 }
    $0 == "---" { after = 1 }
    END { if (!after) exit 1 }
  ' "$1" 2>/dev/null
}

# Writes dest as a Cursor .mdc rule from a shared rule and tags it as generated
# (a comment right after the frontmatter) so later syncs can tell it from hand-made files.
cursor_generate_rule() {
  local src="$1"
  local dest="$2"
  local tmp="$dest.tmp-gen-$$"
  cursor_convert_rule "$src" "$tmp"
  awk -v marker="<!-- $CURSOR_GENERATED_MARKER from rules/$(basename "$src"); do not edit, rerun the sync -->" '
    /^---[ \t\r]*$/ { seen++; print; if (seen == 2) { print marker } next }
    { print }
  ' "$tmp" > "$tmp.new"
  if [[ -f "$dest" ]] && cmp -s "$tmp.new" "$dest"; then
    rm -f "$tmp.new"
  else
    mv -f "$tmp.new" "$dest"
  fi
  rm -f "$tmp"
}

# True when the path is a link or junction (anything that is not a plain directory under .cursor).
cursor_path_is_link() {
  local path="$1" parent_resolved path_resolved
  [[ -L "$path" ]] && return 0
  [[ -d "$path" ]] || return 1
  parent_resolved="$(cd "$(dirname "$path")" 2>/dev/null && pwd -P)" || return 1
  path_resolved="$(cd "$path" 2>/dev/null && pwd -P)" || return 1
  [[ "$path_resolved" != "$parent_resolved/$(basename "$path")" ]]
}

# True when the link resolves to the toolkit rules directory (the only link --force may replace).
cursor_link_is_toolkit_rules() {
  local target cand
  target="$(cd "$1" 2>/dev/null && pwd -P)" || return 1
  for cand in "$PROJECT/rules" "$PROJECT/.windsurf/rules" "${WINDSURF_RULES:-}"; do
    [[ -n "$cand" && -d "$cand" ]] || continue
    [[ "$target" == "$(cd "$cand" && pwd -P)" ]] && return 0
  done
  return 1
}

get_description() {
  local file="$1"
  local description
  description="$(awk '
    NR == 1 { sub(/^\xef\xbb\xbf/, "") }
    /^description:/ {
      sub(/^description:[ \t]*/, "")
      gsub(/^"/, "")
      gsub(/"$/, "")
      print
      exit
    }
  ' "$file")"

  if [[ -n "$description" ]]; then
    printf '%s\n' "$description"
  else
    first_heading_or_basename "$file"
  fi
}

ordered_rule_list() {
  local -n input_ref="$1"
  [[ ${#input_ref[@]} -gt 0 ]] || return 0
  local project_overview=""
  local item
  for item in "${input_ref[@]}"; do
    if [[ "$(basename "$item")" == "project-overview.md" ]]; then
      project_overview="$item"
      break
    fi
  done
  if [[ -n "$project_overview" ]]; then
    printf '%s\n' "$project_overview"
  fi
  for item in "${input_ref[@]}"; do
    [[ "$item" == "$project_overview" ]] && continue
    printf '%s\n' "$item"
  done
}

markdown_list() {
  local prefix="$1"
  shift
  if [[ "$#" -eq 0 ]]; then
    echo "- (none selected)"
    return 0
  fi
  local item
  for item in "$@"; do
    [[ -f "$item" ]] || continue
    echo "- \`${prefix}$(basename "$item")\`"
  done
}

emit_file_section() {
  local heading="$1"
  shift
  [[ $# -gt 0 ]] || return 0
  local has_files=0 f
  for f in "$@"; do
    [[ -f "$f" ]] && { has_files=1; break; }
  done
  [[ "$has_files" -eq 1 ]] || return 0
  echo "---"
  echo ""
  if [[ -n "$heading" ]]; then
    echo "# $heading"
    echo ""
  fi
  for f in "$@"; do
    [[ -f "$f" ]] || continue
    echo "---"
    echo ""
    strip_frontmatter "$f"
    echo ""
  done
}

generate_concatenated_export() {
  local title="$1"
  local dest="$2"
  {
    echo "# $title ($DOC_TITLE)"
    echo ""
    echo "> Auto-generated from \`${DISPLAY_RULES_PREFIX}\` and \`${DISPLAY_WORKFLOWS_PREFIX}\` by \`sync-tool-configs.sh\`."
    if [[ "$SELECTION_IN_EFFECT" -eq 1 ]]; then
      echo "> Curated by \`$SELECTION_FILE_LABEL\` for this repository."
    else
      echo "> Edit the source rule/workflow files and re-run the script."
    fi
    echo ""
    local on_demand_rules=()
    while IFS= read -r f; do
      [[ -f "$f" ]] || continue
      if rule_is_on_demand "$f"; then
        on_demand_rules+=("$f")
        continue
      fi
      echo "---"
      echo ""
      strip_frontmatter "$f"
      echo ""
    done < <(ordered_rule_list EXPORT_RULE_FILES)
    if [[ ${#on_demand_rules[@]} -gt 0 ]]; then
      echo "---"
      echo ""
      echo "# Rules loaded on demand"
      echo ""
      echo "Read the rule file when its topic comes up; it is not pasted here."
      echo ""
      for f in "${on_demand_rules[@]}"; do
        echo "- \`${DISPLAY_RULES_PREFIX}$(basename "$f")\`: $(get_description "$f")"
      done
      echo ""
    fi
    if [[ ${#LOCAL_RULE_FILES[@]} -gt 0 ]]; then
      emit_file_section "Repo-Local Rules" "${LOCAL_RULE_FILES[@]}"
    fi
    if [[ ${#EXPORT_WORKFLOW_FILES[@]} -gt 0 ]]; then
      emit_file_section "Workflows" "${EXPORT_WORKFLOW_FILES[@]}"
    fi
    if [[ ${#LOCAL_WORKFLOW_FILES[@]} -gt 0 ]]; then
      emit_file_section "Repo-Local Workflows" "${LOCAL_WORKFLOW_FILES[@]}"
    fi
  } > "$dest"
}

generate_claude_pointer() {
  local dest="$1"
  {
    echo "# Claude Code instructions ($DOC_TITLE)"
    echo ""
    echo "@AGENTS.md"
    echo ""
    echo "Claude Code loads \`AGENTS.md\` through the import above, so every tool reads the same guidance; edit \`AGENTS.md\`, not this file."
  } > "$dest"
}

managed_block_update() {
  local file="$1"
  local block="$2"
  local start="# BEGIN TOOLKIT SELECTION FILTERS"
  local end="# END TOOLKIT SELECTION FILTERS"

  if [[ -f "$file" ]]; then
    if grep -qF "$start" "$file" 2>/dev/null; then
      _BLOCK="$block" awk -v start="$start" -v end="$end" '
        BEGIN { block = ENVIRON["_BLOCK"] }
        { sub(/\r$/, "") }
        $0 == start { print block; skip=1; next }
        $0 == end { skip=0; next }
        !skip { print }
      ' "$file" > "$file.tmp"
      mv "$file.tmp" "$file"
    else
      cp "$file" "$file.tmp"
      if [[ -s "$file.tmp" ]]; then
        printf "\n%s\n" "$block" >> "$file.tmp"
      else
        printf "%s\n" "$block" >> "$file.tmp"
      fi
      mv "$file.tmp" "$file"
    fi
  else
    printf "%s\n" "$block" > "$file"
  fi
}

managed_block_remove() {
  local file="$1"
  local start="# BEGIN TOOLKIT SELECTION FILTERS"
  local end="# END TOOLKIT SELECTION FILTERS"

  [[ -f "$file" ]] || return 0
  grep -qF "$start" "$file" 2>/dev/null || return 0

  awk -v start="$start" -v end="$end" '
    { sub(/\r$/, "") }
    $0 == start { skip=1; next }
    $0 == end { skip=0; next }
    !skip { print }
  ' "$file" > "$file.tmp"
  mv "$file.tmp" "$file"
}

agents_block_state() {
  local file="$1"
  local start="$2"
  local end="$3"

  awk -v start="$start" -v end="$end" '
    function trim(s) {
      sub(/^[[:space:]]+/, "", s)
      sub(/[[:space:]]+$/, "", s)
      return s
    }
    {
      line = $0
      if (NR == 1) {
        sub(/^\xef\xbb\xbf/, "", line)
      }
      line = trim(line)
      if (line == start) saw_start = 1
      if (line == end) saw_end = 1
    }
    END {
      if (saw_start && saw_end) {
        print "managed"
      } else if (saw_start) {
        print "legacy_missing_end"
      } else if (saw_end) {
        print "end_only"
      } else {
        print "absent"
      }
    }
  ' "$file"
}

rewrite_agents_block() {
  local file="$1"
  local start="$2"
  local end="$3"
  local block="$4"
  local mode="$5"

  _BLOCK="$block" awk -v start="$start" -v end="$end" -v mode="$mode" '
    function trim(s) {
      sub(/^[[:space:]]+/, "", s)
      sub(/[[:space:]]+$/, "", s)
      return s
    }
    function normalize(raw,    line) {
      line = raw
      if (NR == 1) {
        sub(/^\xef\xbb\xbf/, "", line)
      }
      return trim(line)
    }
    BEGIN {
      block = ENVIRON["_BLOCK"]
      in_block = 0
      block_emitted = 0
      legacy_fence_open = 0
    }
    {
      cmp = normalize($0)

      if (!in_block) {
        if (cmp == start) {
          print block
          block_emitted = 1
          in_block = 1
          next
        }
        print $0
        next
      }

      if (cmp == end) {
        in_block = 0
        next
      }

      if (mode == "legacy_missing_end") {
        if (cmp ~ /^```/ && legacy_fence_open == 0) {
          legacy_fence_open = 1
          next
        }
        if (cmp ~ /^```/ && legacy_fence_open == 1) {
          in_block = 0
          next
        }
      }

      next
    }
    END {
      if (!block_emitted) {
        if (NR > 0) {
          print ""
        }
        print block
      }
    }
  ' "$file" > "$file.tmp"

  mv "$file.tmp" "$file"
}

mapfile -t ALL_RULE_FILES < <(find -L "$WINDSURF_RULES" -maxdepth 1 -type f -name '*.md' | LC_ALL=C sort)
ALL_WORKFLOW_FILES=()
if [[ -d "$WINDSURF_WORKFLOWS" ]]; then
  mapfile -t ALL_WORKFLOW_FILES < <(find -L "$WINDSURF_WORKFLOWS" -maxdepth 1 -type f -name '*.md' ! -name 'README.md' | LC_ALL=C sort)
fi

LOCAL_RULE_FILES=()
LOCAL_WORKFLOW_FILES=()
if [[ -d "$LLM_CONFIG_ROOT/rules" ]]; then
  mapfile -t LOCAL_RULE_FILES < <(find -L "$LLM_CONFIG_ROOT/rules" -maxdepth 1 -type f -name '*.md' ! -name 'README.md' | LC_ALL=C sort)
fi
if [[ -d "$LLM_CONFIG_ROOT/workflows" ]]; then
  mapfile -t LOCAL_WORKFLOW_FILES < <(find -L "$LLM_CONFIG_ROOT/workflows" -maxdepth 1 -type f -name '*.md' ! -name 'README.md' | LC_ALL=C sort)
fi

SELECTED_RULE_FILES=()
SELECTED_WORKFLOW_FILES=()
SELECTED_RULE_NAMES=()
SELECTED_WORKFLOW_NAMES=()
SELECTION_IN_EFFECT=0

if [[ -f "$SELECTION_FILE" ]]; then
  while IFS= read -r raw_line || [[ -n "$raw_line" ]]; do
    line="$(printf '%s\n' "$raw_line" | sed 's/\r$//' | sed 's/#.*$//' | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
    [[ -n "$line" ]] || continue

    case "$line" in
      rules/*.md)
        candidate="$WINDSURF_RULES/$(basename "$line")"
        if [[ -f "$candidate" ]]; then
          append_unique SELECTED_RULE_FILES "$candidate"
          append_unique SELECTED_RULE_NAMES "$(basename "$candidate")"
        else
          echo "Warning: selection entry not found: $line" >&2
        fi
        ;;
      workflows/*.md)
        candidate="$WINDSURF_WORKFLOWS/$(basename "$line")"
        if [[ -f "$candidate" ]]; then
          append_unique SELECTED_WORKFLOW_FILES "$candidate"
          append_unique SELECTED_WORKFLOW_NAMES "$(basename "$candidate")"
        else
          echo "Warning: selection entry not found: $line" >&2
        fi
        ;;
      *)
        echo "Warning: unsupported selection entry (expected rules/*.md or workflows/*.md): $line" >&2
        ;;
    esac
  done < "$SELECTION_FILE"

  if [[ "${#SELECTED_RULE_FILES[@]}" -gt 0 || "${#SELECTED_WORKFLOW_FILES[@]}" -gt 0 ]]; then
    SELECTION_IN_EFFECT=1
  else
    echo "Warning: $SELECTION_FILE had no valid entries; using the full shared toolkit surface." >&2
  fi
fi

if [[ "$SELECTION_IN_EFFECT" -eq 1 ]]; then
  EXPORT_RULE_FILES=("${SELECTED_RULE_FILES[@]}")
  EXPORT_WORKFLOW_FILES=("${SELECTED_WORKFLOW_FILES[@]}")
else
  EXPORT_RULE_FILES=("${ALL_RULE_FILES[@]}")
  EXPORT_WORKFLOW_FILES=("${ALL_WORKFLOW_FILES[@]}")
fi

echo "Syncing tool configs for: $DOC_TITLE (dir: $PROJECT_NAME)"
echo "Source: ${DISPLAY_RULES_PREFIX} and ${DISPLAY_WORKFLOWS_PREFIX}"
if [[ "$SELECTION_IN_EFFECT" -eq 1 ]]; then
  echo "Selection: $SELECTION_FILE_LABEL"
fi
if [[ "${#LOCAL_RULE_FILES[@]}" -gt 0 || "${#LOCAL_WORKFLOW_FILES[@]}" -gt 0 ]]; then
  echo "LLM config docs: $LLM_CONFIG_ROOT_LABEL/rules/ and $LLM_CONFIG_ROOT_LABEL/workflows/"
fi

CURSOR_RULES=""
CURSOR_RULES_SOURCE=""
CURSOR_RULES_GENERATED=0

if [[ -d "$PROJECT/rules" || -d "$PROJECT/.windsurf/rules" ]]; then
  CURSOR_RULES_SOURCE="$WINDSURF_RULES"
fi

if [[ -n "$CURSOR_RULES_SOURCE" ]]; then
  CURSOR_RULES="$PROJECT/.cursor/rules"
  if [[ "$SKIP_CURSOR_RULES" -eq 1 ]]; then
    echo "  Cursor rules: skipped (--skip-cursor-rules)"
  else
    CURSOR_RULES_OK=1
    if cursor_path_is_link "$CURSOR_RULES"; then
      if [[ "$ALLOW_REPAIR" -eq 1 ]] && cursor_link_is_toolkit_rules "$CURSOR_RULES"; then
        reset_path "$CURSOR_RULES"
      elif [[ "$ALLOW_REPAIR" -eq 1 ]]; then
        echo "Warning: $CURSOR_RULES is a link to a directory that is not the toolkit rules; leaving it and not generating .mdc rules." >&2
        CURSOR_RULES_OK=0
      else
        echo "Warning: $CURSOR_RULES is a link; leaving it and not generating .mdc rules." >&2
        echo "  Re-run with --force to replace it with generated .mdc rules (only a link to the toolkit rules is replaced)." >&2
        CURSOR_RULES_OK=0
      fi
    elif [[ -e "$CURSOR_RULES" && ! -d "$CURSOR_RULES" ]]; then
      echo "Warning: $CURSOR_RULES exists and is not a directory; leaving it and not generating .mdc rules." >&2
      CURSOR_RULES_OK=0
    fi
    if [[ "$CURSOR_RULES_OK" -eq 1 ]]; then
      mkdir -p "$CURSOR_RULES"
      CURSOR_RULES_NAMES=()
      for f in "${EXPORT_RULE_FILES[@]}"; do
        base_name="$(basename "$f")"
        [[ "$base_name" == "README.md" ]] && continue
        mdc_name="${base_name%.md}.mdc"
        if [[ -e "$CURSOR_RULES/$mdc_name" ]] && ! cursor_is_generated "$CURSOR_RULES/$mdc_name"; then
          echo "Warning: $CURSOR_RULES/$mdc_name is hand-made; not overwritten." >&2
          continue
        fi
        cursor_generate_rule "$f" "$CURSOR_RULES/$mdc_name"
        CURSOR_RULES_NAMES+=("$mdc_name")
      done
      # Remove generated files whose rule is gone; hand-made files never carry the marker.
      for existing in "$CURSOR_RULES"/*.mdc; do
        [[ -f "$existing" ]] || continue
        cursor_is_generated "$existing" || continue
        if ! array_contains "$(basename "$existing")" "${CURSOR_RULES_NAMES[@]}"; then
          rm -f "$existing"
          echo "  Removed stale generated Cursor rule: $(basename "$existing")"
        fi
      done
      # Ignore exactly the generated files (hand-made rules stay visible to git).
      CURSOR_GI="$CURSOR_RULES/.gitignore"
      if [[ -e "$CURSOR_GI" ]] && ! grep -q -- "^# $CURSOR_GENERATED_MARKER" "$CURSOR_GI" 2>/dev/null; then
        echo "Warning: $CURSOR_GI is hand-made; not overwritten, generated rules may show up in git." >&2
      else
        {
          echo "# $CURSOR_GENERATED_MARKER: lists the generated rule files only; rewritten on every sync"
          echo "/.gitignore"
          for existing in "${CURSOR_RULES_NAMES[@]}"; do echo "/$existing"; done
        } > "$CURSOR_GI.tmp-gen-$$"
        if [[ -f "$CURSOR_GI" ]] && cmp -s "$CURSOR_GI.tmp-gen-$$" "$CURSOR_GI"; then
          rm -f "$CURSOR_GI.tmp-gen-$$"
        else
          mv -f "$CURSOR_GI.tmp-gen-$$" "$CURSOR_GI"
        fi
      fi
      CURSOR_RULES_GENERATED=1
      echo "  OK Cursor rules generated (${#CURSOR_RULES_NAMES[@]} .mdc files)"
    fi
    if [[ -e "$PROJECT/.cursor/workflows" || -L "$PROJECT/.cursor/workflows" ]]; then
      echo "  Note: .cursor/workflows is no longer created or updated (not a Cursor surface); the existing one can be removed."
    fi
  fi
fi

if [[ -d "$PROJECT/tool-subagents" ]]; then
  ensure_symlink "$PROJECT/.cursor/agents" "../tool-subagents"
  ensure_symlink "$PROJECT/.claude/agents" "../tool-subagents"
  # Codex reads generated TOML (rendered from the .md sources, never committed).
  # A legacy link onto tool-subagents/ is re-pointed; nothing else is removed.
  CODEX_LINK_OK=0
  if command -v node >/dev/null 2>&1 \
    && node "$(dirname "${BASH_SOURCE[0]}")/create-specialist-agent.js" --render-codex \
      --source "$PROJECT/tool-subagents" "$PROJECT/tool-subagents/.generated/codex" >/dev/null 2>&1; then
    if [[ -L "$PROJECT/.codex/agents" ]] \
      && [[ "$(cd "$PROJECT/.codex/agents" 2>/dev/null && pwd -P)" == "$(cd "$PROJECT/tool-subagents" && pwd -P)" ]]; then
      echo "  Re-pointing legacy .codex/agents -> tool-subagents/.generated/codex"
      rm -f -- "$PROJECT/.codex/agents"
    fi
    ensure_symlink "$PROJECT/.codex/agents" "../tool-subagents/.generated/codex" && CODEX_LINK_OK=1
  else
    echo "Warning: could not render Codex agent TOML (needs node and valid tool-subagents/*.md)." >&2
  fi
  if [[ "$CODEX_LINK_OK" -eq 1 ]]; then
    CODEX_AGENTS_SYNCED=1
    echo "  OK shared subagent symlinks repaired"
  else
    CODEX_AGENTS_SYNCED=0
    echo "Warning: optional .codex/agents link could not be repaired; continuing." >&2
    echo "  OK shared Cursor/Claude subagent symlinks repaired"
  fi
fi

if [[ -d "$PROJECT/rules" ]]; then
  ensure_symlink "$PROJECT/.windsurf/rules" "../rules"
fi
if [[ -d "$PROJECT/workflows" ]]; then
  ensure_symlink "$PROJECT/.windsurf/workflows" "../workflows"
fi

if [[ -d "$PROJECT/skills" ]]; then
  SKILLS_SYNCED=1
  for link_spec in \
    "$PROJECT/.agents/skills|../skills" \
    "$PROJECT/.agent/skills|../.agents/skills" \
    "$PROJECT/.claude/skills|../.agents/skills" \
    "$PROJECT/.codex/skills|../.agents/skills" \
    "$PROJECT/.cursor/skills|../.agents/skills" \
    "$PROJECT/.gemini/skills|../.agents/skills" \
    "$PROJECT/.opencode/skills|../.agents/skills" \
    "$PROJECT/.windsurf/skills|../.agents/skills"; do
    link_target="${link_spec%%|*}"
    link_source="${link_spec#*|}"
    if ! ensure_symlink "$link_target" "$link_source"; then
      SKILLS_SYNCED=0
      echo "Warning: shared skills compatibility link could not be repaired: $link_target" >&2
    fi
  done
  if [[ "$SKILLS_SYNCED" -eq 1 ]]; then
    echo "  OK shared skills symlinks repaired"
  else
    echo "Warning: shared skills compatibility links could not be fully repaired; continuing with generated exports." >&2
    echo "  Re-run with --force if a blocking local path should be replaced." >&2
  fi
fi

if [[ "$SELECTION_IN_EFFECT" -eq 1 ]]; then
  build_ignore_block() {
    {
      echo "# BEGIN TOOLKIT SELECTION FILTERS"
      echo "# Auto-generated from $SELECTION_FILE_LABEL by sync-tool-configs.sh."
      echo "# When .cursor/ is linked to the shared toolkit, hide non-selected shared files locally."

      ignored_any=0
      for f in "${ALL_RULE_FILES[@]}"; do
        basename_f="$(basename "$f")"
        if ! array_contains "$basename_f" "${SELECTED_RULE_NAMES[@]}"; then
          echo "${DISPLAY_RULES_PREFIX}${basename_f}"
          echo ".cursor/rules/${basename_f%.md}.mdc"
          ignored_any=1
        fi
      done

      for f in "${ALL_WORKFLOW_FILES[@]}"; do
        basename_f="$(basename "$f")"
        if ! array_contains "$basename_f" "${SELECTED_WORKFLOW_NAMES[@]}"; then
          echo "${DISPLAY_WORKFLOWS_PREFIX}${basename_f}"
          echo ".cursor/workflows/${basename_f}"
          ignored_any=1
        fi
      done

      if [[ "$ignored_any" -eq 0 ]]; then
        echo "# No shared toolkit files are excluded by the current selection."
      fi

      echo "# END TOOLKIT SELECTION FILTERS"
    }
  }

  SELECTION_BLOCK="$(build_ignore_block)"
  managed_block_update "$PROJECT/.cursorignore" "$SELECTION_BLOCK"
  managed_block_update "$PROJECT/.cursorindexingignore" "$SELECTION_BLOCK"
  echo "  OK Cursor local ignore blocks refreshed from $SELECTION_FILE_LABEL"
else
  managed_block_remove "$PROJECT/.cursorignore"
  managed_block_remove "$PROJECT/.cursorindexingignore"
fi

CLAUDE_FILE="$PROJECT/CLAUDE.md"
generate_claude_pointer "$CLAUDE_FILE"
echo "  OK CLAUDE.md imports AGENTS.md"

GITHUB_DIR="$PROJECT/.github"
if [[ "$SKIP_GITHUB" -eq 1 ]]; then
  echo "  SKIP .github/copilot-instructions.md (--skip-github)"
else
  mkdir -p "$GITHUB_DIR"
  COPILOT_FILE="$GITHUB_DIR/copilot-instructions.md"
  generate_concatenated_export "Copilot Instructions" "$COPILOT_FILE"
  echo "  OK .github/copilot-instructions.md generated"
fi

RULE_LIST_MD="$(markdown_list "$DISPLAY_RULES_PREFIX" "${EXPORT_RULE_FILES[@]}")"
WORKFLOW_LIST_MD="$(markdown_list "$DISPLAY_WORKFLOWS_PREFIX" "${EXPORT_WORKFLOW_FILES[@]}")"
LOCAL_RULE_LIST_MD="$(markdown_list "$LLM_CONFIG_ROOT_LABEL/rules/" "${LOCAL_RULE_FILES[@]}")"
LOCAL_WORKFLOW_LIST_MD="$(markdown_list "$LLM_CONFIG_ROOT_LABEL/workflows/" "${LOCAL_WORKFLOW_FILES[@]}")"

if [[ "$SELECTION_IN_EFFECT" -eq 1 ]]; then
  RULES_LABEL="### Selected Rules Files"
  WORKFLOWS_LABEL="### Selected Workflow Files"
  SELECTION_NOTE="> Curated by \`$SELECTION_FILE_LABEL\` for this repository.
>
> When \`.cursor/\` is linked to the shared toolkit, keep shared \`.cursor/rules/\` generic
> (generated \`.mdc\` files) and use \`.cursorignore\` plus \`.cursorindexingignore\`
> to hide non-selected items locally."
else
  RULES_LABEL="### Rules Files"
  WORKFLOWS_LABEL="### Workflow Files"
  SELECTION_NOTE="> Edit the source rule files and re-run the script."
fi

LOCAL_RULES_SECTION=""
if [[ "${#LOCAL_RULE_FILES[@]}" -gt 0 ]]; then
  LOCAL_RULES_SECTION="### Repo-Local Rules Files
$LOCAL_RULE_LIST_MD
"
fi

LOCAL_WORKFLOWS_SECTION=""
if [[ "${#LOCAL_WORKFLOW_FILES[@]}" -gt 0 ]]; then
  LOCAL_WORKFLOWS_SECTION="### Repo-Local Workflow Files
$LOCAL_WORKFLOW_LIST_MD
"
fi

IS_TOOLKIT_PROJECT=0
if [[ -f "$PROJECT/scripts/sync-tool-configs.sh" && -d "$PROJECT/skills" && -d "$PROJECT/rules" && -d "$PROJECT/workflows" ]]; then
  IS_TOOLKIT_PROJECT=1
fi

if [[ "$IS_TOOLKIT_PROJECT" -eq 1 ]]; then
  SYNC_COMMAND_INTRO="To refresh generated provider exports from the toolkit root while preserving the curated root \`AGENTS.md\`, run:"
  SYNC_COMMAND_BASH="./scripts/sync-tool-configs.sh . --skip-agents-md --skip-github"
  SYNC_COMMAND_POWERSHELL="./scripts/sync-tool-configs.ps1 . -SkipAgentsMd -SkipGithub"
  SYNC_COMMAND_NOTE="Omit \`--skip-agents-md\` / \`-SkipAgentsMd\` only when intentionally regenerating the managed block inside root \`AGENTS.md\`. Omit \`--skip-github\` / \`-SkipGithub\` only when \`.github/copilot-instructions.md\` is intentionally in scope."
else
  SYNC_COMMAND_INTRO="To regenerate local exports after editing shared rules, \`$SELECTION_FILE_LABEL\`, or resolved LLM config docs:"
  SYNC_COMMAND_BASH="../llm-toolkit-project/scripts/sync-tool-configs.sh ."
  SYNC_COMMAND_POWERSHELL="..\\llm-toolkit-project\\scripts\\sync-tool-configs.ps1 ."
  SYNC_COMMAND_NOTE=""
fi

if [[ "$SKIP_AGENTS_MD" -eq 1 ]]; then
  echo "  SKIP AGENTS.md (--skip-agents-md)"
else
  AGENTS_FILE="$PROJECT/AGENTS.md"
  MARKER_START="<!-- BEGIN SYNC-TOOL-CONFIGS RULES -->"
  MARKER_END="<!-- END SYNC-TOOL-CONFIGS RULES -->"

  RULES_BLOCK="$MARKER_START
## Shared Toolkit Rules

> Auto-generated from \`${DISPLAY_RULES_PREFIX}\` and \`${DISPLAY_WORKFLOWS_PREFIX}\` by \`sync-tool-configs.sh\`.
$SELECTION_NOTE

$RULES_LABEL
$RULE_LIST_MD

$LOCAL_RULES_SECTION

$WORKFLOWS_LABEL
$WORKFLOW_LIST_MD

$LOCAL_WORKFLOWS_SECTION

### Tool Config Locations

Canonical shared content lives in toolkit \`skills/\`, \`rules/\`, \`workflows/\`, and \`tool-subagents/\`. Provider folders below are compatibility links or generated exports, not duplicate sources. The central path map is \`docs/tool-compatibility-paths.md\` in the toolkit.

| Tool | Location | Format |
|------|----------|--------|
| Antigravity | \`.agent/skills/\` | Thin skill compatibility link to \`.agents/skills/\` |
| Codex / generic | \`AGENTS.md\`, \`.agents/skills/\`, optional \`.codex/skills\`, optional \`.codex/agents/\` | \`AGENTS.md\` is primary; provider skill paths stay thin links to the shared skill catalog |
| Cursor | \`.cursor/skills/\`, \`.cursor/rules/\`, \`.cursor/agents/\` | Skills and agents are links to canonical shared files; \`.cursor/rules/*.mdc\` are generated from \`rules/\` (git-ignored through \`.cursor/rules/.gitignore\`; hand-made rules there stay visible to git); project filtering happens via local ignore files |
| Claude Code | \`CLAUDE.md\`, \`.claude/skills/\`, \`.claude/agents/\` | \`CLAUDE.md\` imports \`AGENTS.md\` (\`@AGENTS.md\`); shared skills and agents are links |
| Gemini CLI | \`.gemini/skills/\` | Thin skill compatibility link to \`.agents/skills/\` |
| GitHub Copilot | \`.github/copilot-instructions.md\` | Concatenated repo-local export from shared selection plus resolved LLM config docs |
| OpenCode | \`.opencode/skills/\` | Thin skill compatibility link to \`.agents/skills/\` |
| Windsurf | \`.windsurf/skills/\`, \`.windsurf/rules/\`, \`.windsurf/workflows/\` | Thin skill links plus shared rule/workflow links |

### Clone Bootstrap

After cloning this repo on a new machine, make sure \`llm-toolkit-project\` is available locally, then recreate shared-tool folders from this repo root. If the toolkit is a sibling directory, run:

- macOS/Linux/Git Bash: \`../llm-toolkit-project/scripts/ensure-symlinks.sh . --pull\`
- Windows PowerShell: \`..\llm-toolkit-project\scripts\ensure-symlinks.ps1 . -Pull\`
- Windows Command Prompt: \`..\llm-toolkit-project\scripts\ensure-symlinks.cmd . --pull\`

Adjust the toolkit path if it lives elsewhere. The ensure script repairs \`.agents/\`, \`.agent/\`, \`.claude/\`, \`.codex/\`, \`.cursor/\`, \`.gemini/\`, \`.opencode/\`, \`.windsurf/\`, and \`learnings\` links, then refreshes local generated LLM exports. It does not create or modify \`.github/skills/\` by default. If a path is blocked by an old link or file, rerun with \`--force\` / \`-Force\` only after confirming the path is toolkit-managed. On Windows, directory symlinks may require Developer Mode or an elevated shell; the \`.cmd\` wrapper requires Administrator Command Prompt.

### Default Orchestration

For every non-trivial request, the root agent should route through shared \`rules/request-orchestration.md\` and \`tool-subagents/agent-orchestrator.md\` by default. The orchestrator maps the request, splits independent read-only or disjoint-write lanes across specialist agents, scores each delegated task's complexity tier (\`light\`/\`standard\`/\`deep\`, provider-agnostic — and MUST apply it by setting the delegation tool's model/effort parameter from the client model map in \`tool-subagents/agent-orchestrator.md\` on every dispatch where the platform exposes one; on Claude Code \`light\` -> \`haiku\`, \`standard\` -> \`sonnet\`, \`deep\` -> \`opus\`; letting a child silently inherit the session default is a routing defect, and only a platform with no per-task mechanism runs at the stated platform default), presents the plan as the 15-column wave-ordered tasks table with an assets manifest (#, Wave, Task, Assets, Vector DB used, Complexity, Model/Effort, Status, Evidence, PR link(s), CI/CD run link(s), Tokens, % Complete, SLA, Remaining SLA, and three footer rows; see \`tool-subagents/agent-orchestrator.md\` Tasks table contract), reprints the full table after every task completion, checkpoints the \`TASKS_TABLE.md\`/\`CONTEXT_STATE.md\` ledger so an interrupted run resumes instead of restarting, allows only shallow agent-to-agent delegation for independently verifiable subparts, and reduces specialist findings before editing or reporting. Every delegated task runs as a bounded produce->validate->refine quality loop per \`workflows/task-quality-loop.md\`: verifiable acceptance criteria before dispatch, a read-only validator matched to the task's evidence type, targeted refinement from the defect list on \`fail\`, max 5 iterations per task (1 for deterministic \`light\` tasks), and escalation to the root agent instead of silent acceptance when the budget is exhausted. The root agent stays on the strongest model available in the session and remains responsible for user communication, final edits, validation, commits, pushes, and PR actions. Per-task progress notifications to a user-designated channel are opt-in and gated by \`rules/human-comment-reply-gate.md\`.

If any referenced shared rule, workflow, skill, or agent path is missing, run the clone bootstrap commands above before continuing.

$SYNC_COMMAND_INTRO
\`\`\`bash
$SYNC_COMMAND_BASH
\`\`\`
On Windows PowerShell:
\`\`\`powershell
$SYNC_COMMAND_POWERSHELL
\`\`\`
$SYNC_COMMAND_NOTE
$MARKER_END"

  if [[ -f "$AGENTS_FILE" ]]; then
    AGENTS_BLOCK_STATE="$(agents_block_state "$AGENTS_FILE" "$MARKER_START" "$MARKER_END")"
    case "$AGENTS_BLOCK_STATE" in
      managed)
        rewrite_agents_block "$AGENTS_FILE" "$MARKER_START" "$MARKER_END" "$RULES_BLOCK" "$AGENTS_BLOCK_STATE"
        echo "  OK AGENTS.md rules section updated"
        ;;
      legacy_missing_end)
        rewrite_agents_block "$AGENTS_FILE" "$MARKER_START" "$MARKER_END" "$RULES_BLOCK" "$AGENTS_BLOCK_STATE"
        echo "  OK AGENTS.md legacy rules section normalized"
        ;;
      end_only)
        echo "Warning: AGENTS.md has an END marker without a BEGIN marker; appending a fresh managed block." >&2
        rewrite_agents_block "$AGENTS_FILE" "$MARKER_START" "$MARKER_END" "$RULES_BLOCK" "$AGENTS_BLOCK_STATE"
        echo "  OK AGENTS.md rules section appended"
        ;;
      *)
        rewrite_agents_block "$AGENTS_FILE" "$MARKER_START" "$MARKER_END" "$RULES_BLOCK" "$AGENTS_BLOCK_STATE"
        echo "  OK AGENTS.md rules section appended"
        ;;
    esac
  else
    echo "$RULES_BLOCK" > "$AGENTS_FILE"
    echo "  OK AGENTS.md created"
  fi
fi

GITIGNORE="$PROJECT/.gitignore"
if [[ -f "$GITIGNORE" ]]; then
  if ! grep -q "sync-tool-configs" "$GITIGNORE" 2>/dev/null; then
    cat >> "$GITIGNORE" << 'IGNORE_EOF'

# AI tool configs (auto-generated by sync-tool-configs.sh)
# Source of truth: .windsurf/rules/ and .windsurf/workflows/ OR rules/ and workflows/
# Shared provider skill roots and agent surfaces are symlinked to the canonical files.
# Repair them with: ./scripts/sync-tool-configs.sh .
# CLAUDE.md
# .github/copilot-instructions.md
IGNORE_EOF
    echo "  OK .gitignore updated with tool config notes"
  fi
fi

echo ""
echo "Done. All tool configs synced for $DOC_TITLE."
echo ""
echo "Source of truth:  ${DISPLAY_RULES_PREFIX} and ${DISPLAY_WORKFLOWS_PREFIX}"
if [[ -d "$PROJECT/tool-subagents" ]]; then
  echo "Shared agents:    tool-subagents/"
fi
if [[ "$SELECTION_IN_EFFECT" -eq 1 ]]; then
  echo "Selection file:   $SELECTION_FILE_LABEL"
fi
GENERATED_LIST="CLAUDE.md import"
[[ "$SKIP_GITHUB" -eq 0 ]] && GENERATED_LIST="$GENERATED_LIST, .github/copilot-instructions.md"
[[ "$SKIP_AGENTS_MD" -eq 0 ]] && GENERATED_LIST="$GENERATED_LIST, AGENTS.md (sync section)"
if [[ "$CURSOR_RULES_GENERATED" -eq 1 ]]; then
  GENERATED_LIST="$GENERATED_LIST, .cursor/rules/*.mdc"
fi
echo "Generated:        $GENERATED_LIST"
LINKED_LIST=""
append_linked() {
  local entry="$1"
  if [[ -n "$LINKED_LIST" ]]; then
    LINKED_LIST="$LINKED_LIST, $entry"
  else
    LINKED_LIST="$entry"
  fi
}
if [[ -d "$PROJECT/tool-subagents" ]]; then
  if [[ "${CODEX_AGENTS_SYNCED:-0}" -eq 1 ]]; then
    append_linked ".cursor/agents/, .claude/agents/, .codex/agents/"
  else
    append_linked ".cursor/agents/, .claude/agents/"
  fi
fi
if [[ -d "$PROJECT/rules" ]]; then
  append_linked ".windsurf/rules/"
fi
if [[ -d "$PROJECT/workflows" ]]; then
  append_linked ".windsurf/workflows/"
fi
if [[ -d "$PROJECT/skills" ]]; then
  if [[ "${SKILLS_SYNCED:-0}" -eq 1 ]]; then
    append_linked ".agents/skills/, .agent/skills/, .claude/skills/, .codex/skills/, .cursor/skills/, .gemini/skills/, .opencode/skills/, .windsurf/skills/"
  fi
fi
if [[ -n "$LINKED_LIST" ]]; then
  echo "Linked:           $LINKED_LIST"
fi
echo ""
echo "Commit repo-local generated files when you want this repository to work out of the box for other tools."
