#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
SKIPPED_CHECKS=0
SECURITY_SIGNAL_CHECKS=0

run_check() {
  local check_name="$1"
  shift

  TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
  echo
  echo "==> ${check_name}"

  if "$@"; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo "PASS: ${check_name}"
  else
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    echo "FAIL: ${check_name}"
  fi
}

run_security_check() {
  local before_passed="$PASSED_CHECKS"
  run_check "$@"
  if [ "$PASSED_CHECKS" -gt "$before_passed" ]; then
    SECURITY_SIGNAL_CHECKS=$((SECURITY_SIGNAL_CHECKS + 1))
  fi
}

skip_check() {
  local check_name="$1"
  local reason="$2"

  TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
  SKIPPED_CHECKS=$((SKIPPED_CHECKS + 1))
  echo
  echo "==> ${check_name}"
  echo "SKIP: ${reason}"
}

have_command() {
  command -v "$1" >/dev/null 2>&1
}

have_executable_command() {
  local command_name="$1"
  local found
  found="$(command -v "$command_name" 2>/dev/null || true)"
  if [ -z "$found" ] || [ ! -x "$found" ]; then
    return 1
  fi
  if "$command_name" --version >/dev/null 2>&1; then
    return 0
  fi
  echo "Warning: $command_name was found at $found but could not be executed; skipping." >&2
  return 1
}

semgrep_usable() (
  local probe_dir probe_config probe_source status
  if ! probe_dir="$(mktemp -d)" || [ -z "${probe_dir}" ] || [ ! -d "${probe_dir}" ]; then
    echo "Warning: could not create a validated temporary directory for the semgrep execution probe; skipping." >&2
    return 1
  fi
  probe_config="${probe_dir}/rule.yml"
  probe_source="${probe_dir}/source.txt"
  trap 'rm -f -- "${probe_config}" "${probe_source}"; rmdir -- "${probe_dir}"' EXIT
  if ! printf '%s\n' \
    'rules:' \
    '  - id: execution-probe' \
    '    languages: [generic]' \
    '    message: execution probe' \
    '    severity: INFO' \
    '    pattern: probe' > "${probe_config}" ||
      ! printf '%s\n' 'probe' > "${probe_source}"; then
    echo "Warning: could not write the semgrep execution probe inputs; skipping." >&2
    return 1
  fi
  if PYTHONUTF8=1 SEMGREP_SETTINGS_FILE=/tmp/semgrep-settings.yml \
      semgrep scan --config "${probe_config}" "${probe_source}" >/dev/null 2>&1; then
    status=0
  else
    echo "Warning: semgrep was found but its scan engine could not execute; skipping." >&2
    status=1
  fi
  return "${status}"
)

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

have_psscriptanalyzer() {
  have_executable_command pwsh &&
    pwsh -NoLogo -NoProfile -Command "if (Get-Command Invoke-ScriptAnalyzer -ErrorAction SilentlyContinue) { exit 0 } exit 1" >/dev/null 2>&1
}

docker_usable() {
  docker ps >/dev/null 2>&1
}

has_files() {
  local pattern="$1"
  local -a matches=()
  mapfile -d '' matches < <(git_inventory "${pattern}")
  [ "${#matches[@]}" -gt 0 ]
}

git_inventory() {
  local pattern="$1" file
  while IFS= read -r -d '' file; do
    printf './%s\0' "$file"
  done < <(git -C "${REPO_ROOT}" ls-files --cached -z -- "${pattern}")
  while IFS= read -r -d '' file; do
    printf './%s\0' "$file"
  done < <(git -C "${REPO_ROOT}" ls-files --others --exclude-standard -z -- "${pattern}" \
    ':(exclude).agents/skills/**' ':(exclude).agents/worktrees/**' \
    ':(exclude).claude/agents/**' ':(exclude).claude/skills/**' ':(exclude).claude/worktrees/**' \
    ':(exclude).codex/agents/**' ':(exclude).codex/skills/**' ':(exclude).codex/worktrees/**' \
    ':(exclude).cursor/agents/**' ':(exclude).cursor/rules/**' ':(exclude).cursor/skills/**' \
    ':(exclude).cursor/workflows/**' ':(exclude).cursor/worktrees/**' \
    ':(exclude).windsurf/rules/**' ':(exclude).windsurf/skills/**' \
    ':(exclude).windsurf/workflows/**' ':(exclude).windsurf/worktrees/**')
}

repo_scope_paths=(
  rules
  workflows
  scripts
  skills
  learnings
  rubrics
  tool-subagents
  .github
  .agents
  .claude
  .cursor
  .codex
  .windsurf
  integrations
  docs
  consumer-profiles
  AGENTS.md
  CLAUDE.md
  INTENTS.md
  README.md
  TOOLKIT_DOC_TITLE
)

# Agent tools materialize transient per-session repo checkouts under
# <tool-dir>/worktrees/<session>/ (full repo copies; on Windows git checks
# them out with CRLF endings, so linting them produces false SC1017 failures
# that the canonical main-tree files do not have). Keep the rest of each
# tool dir in scope, but never sweep those checkouts into scans.
session_worktree_parents=(
  .agents
  .claude
  .codex
  .cursor
  .windsurf
)

is_session_worktree_parent() {
  local candidate="$1" parent
  for parent in "${session_worktree_parents[@]}"; do
    if [ "$candidate" = "$parent" ]; then
      return 0
    fi
  done
  return 1
}

scoped_existing_paths() {
  local path child
  for path in "${repo_scope_paths[@]}"; do
    [ -e "${REPO_ROOT}/${path}" ] || continue
    if [ -d "${REPO_ROOT}/${path}" ] && is_session_worktree_parent "${path}"; then
      while IFS= read -r -d '' child; do
        if [ "$(basename "${child}")" = "worktrees" ] && [ -d "${child}" ]; then
          continue
        fi
        printf '%s\0' "${child#"${REPO_ROOT}"/}"
      done < <(find "${REPO_ROOT}/${path}" -mindepth 1 -maxdepth 1 -print0)
    else
      printf '%s\0' "${path}"
    fi
  done
}

gitleaks_sources() {
  scoped_existing_paths
}

is_cloud_sync_duplicate_name() {
  local name="$1"
  [[ "$name" =~ \ \([0-9]+\)\. ]]
}

find_scoped_files_by_extension() {
  local extension="$1"
  git_inventory "*.${extension}"
}

run_trivy() {
  local skip_args=() parent
  for parent in "${session_worktree_parents[@]}"; do
    skip_args+=(--skip-dirs "${parent}/worktrees")
  done
  trivy fs "${skip_args[@]}" .
}

run_gitleaks() {
  local source
  local status=0
  while IFS= read -r -d '' source; do
    gitleaks detect --source "${source}" --no-git --redact || status=1
  done < <(gitleaks_sources)
  return "$status"
}

run_trufflehog() {
  local targets=()
  local path

  while IFS= read -r -d '' path; do
    targets+=("${path}")
  done < <(scoped_existing_paths)

  trufflehog filesystem "${targets[@]}" --no-update
}

run_semgrep() {
  local targets=()
  local path

  while IFS= read -r -d '' path; do
    targets+=("${path}")
  done < <(scoped_existing_paths)

  PYTHONUTF8=1 SEMGREP_SETTINGS_FILE=/tmp/semgrep-settings.yml semgrep scan --config auto "${targets[@]}"
}

has_node_manifest() {
  [ -f "${REPO_ROOT}/package.json" ] || [ -f "${REPO_ROOT}/pnpm-lock.yaml" ] || [ -f "${REPO_ROOT}/package-lock.json" ] || [ -f "${REPO_ROOT}/yarn.lock" ]
}

has_python_manifest() {
  [ -f "${REPO_ROOT}/requirements.txt" ] || [ -f "${REPO_ROOT}/pyproject.toml" ] || [ -f "${REPO_ROOT}/setup.py" ]
}

has_dependency_manifest() {
  find "${REPO_ROOT}" -type f \( \
    -name package.json -o \
    -name package-lock.json -o \
    -name pnpm-lock.yaml -o \
    -name yarn.lock -o \
    -name requirements.txt -o \
    -name pyproject.toml -o \
    -name setup.py -o \
    -name pom.xml -o \
    -name build.gradle -o \
    -name build.gradle.kts -o \
    -name go.mod -o \
    -name Cargo.toml -o \
    -name Gemfile.lock -o \
    -name composer.lock -o \
    -name '*.csproj' \
  \) -print -quit | grep -q .
}

run_shellcheck() {
  mapfile -d '' files < <(find_scoped_files_by_extension sh)

  if [ "${#files[@]}" -eq 0 ]; then
    return 0
  fi

  shellcheck -x -S warning "${files[@]}"
}

run_psscriptanalyzer() {
  mapfile -d '' files < <(find_scoped_files_by_extension ps1)

  if [ "${#files[@]}" -eq 0 ]; then
    return 0
  fi

  local file target_list target_list_for_pwsh status
  target_list="$(mktemp)"
  for file in "${files[@]}"; do
    if have_command cygpath; then
      cygpath -w "$file" >> "$target_list"
    else
      printf '%s\n' "$file" >> "$target_list"
    fi
  done

  target_list_for_pwsh="$target_list"
  if have_command cygpath; then
    target_list_for_pwsh="$(cygpath -w "$target_list")"
  fi

  PSSCRIPTANALYZER_TARGET_LIST="$target_list_for_pwsh" pwsh -NoLogo -NoProfile -Command '
    $status = 0
    Get-Content -LiteralPath $env:PSSCRIPTANALYZER_TARGET_LIST | ForEach-Object {
      $results = Invoke-ScriptAnalyzer -Path $_ -Severity Error
      if ($results) {
        $results | Format-Table -AutoSize | Out-String | Write-Output
        $status = 1
      }
    }
    exit $status
  '
  status=$?
  rm -f "$target_list"
  return "$status"
}

run_hadolint() {
  mapfile -d '' files < <(find "${REPO_ROOT}" -type f \( -name 'Dockerfile' -o -name '*.Dockerfile' \) -print0)

  if [ "${#files[@]}" -eq 0 ]; then
    return 0
  fi

  hadolint "${files[@]}"
}

run_cmd_semgrep() {
  local files=()
  local bat_files=()
  mapfile -d '' files < <(find_scoped_files_by_extension cmd)
  mapfile -d '' bat_files < <(find_scoped_files_by_extension bat)
  files+=("${bat_files[@]}")

  if [ "${#files[@]}" -eq 0 ]; then
    return 0
  fi

  PYTHONUTF8=1 SEMGREP_SETTINGS_FILE=/tmp/semgrep-settings.yml semgrep scan --config auto "${files[@]}"
}

run_llm_surface_security_scan() {
  local python_cmd_text
  local -a python_cmd

  if [ ! -f "${REPO_ROOT}/scripts/scan-llm-surface-security.py" ]; then
    echo "scripts/scan-llm-surface-security.py is missing." >&2
    return 1
  fi

  if ! python_cmd_text="$(find_python_cmd)"; then
    echo "Python is required for the LLM surface prompt-injection scan." >&2
    return 1
  fi
  read -r -a python_cmd <<< "$python_cmd_text"

  "${python_cmd[@]}" "${REPO_ROOT}/scripts/scan-llm-surface-security.py" --root "${REPO_ROOT}"
}

run_skillspector_changed_skill_scan() {
  local python_cmd_text
  local -a python_cmd

  if [ ! -f "${REPO_ROOT}/scripts/check-skillspector-skills.py" ]; then
    echo "scripts/check-skillspector-skills.py is missing." >&2
    return 1
  fi

  if ! python_cmd_text="$(find_python_cmd)"; then
    echo "Python is required for the SkillSpector skill scan." >&2
    return 1
  fi
  read -r -a python_cmd <<< "$python_cmd_text"

  "${python_cmd[@]}" "${REPO_ROOT}/scripts/check-skillspector-skills.py" --changed
}

has_changed_skill_files() {
  local file
  while IFS= read -r file; do
    [ -f "${REPO_ROOT}/${file}" ] && return 0
  done < <(
    git diff --name-only --diff-filter=AM HEAD -- 'skills/*/SKILL.md' 2>/dev/null || true
    git diff --name-only --diff-filter=AM --cached HEAD -- 'skills/*/SKILL.md' 2>/dev/null || true
    git ls-files --others --exclude-standard -- 'skills/*/SKILL.md' 2>/dev/null || true
  )
  return 1
}

run_cfn_lint() {
  mapfile -d '' files < <(find "${REPO_ROOT}" -type f \( -name '*.yaml' -o -name '*.yml' -o -name '*.json' \) -path '*/infra/*' -print0)

  if [ "${#files[@]}" -eq 0 ]; then
    return 0
  fi

  cfn-lint "${files[@]}"
}

run_yamllint() {
  local targets=()
  local candidate

  for candidate in .github docs integrations rules workflows; do
    if [ -e "${REPO_ROOT}/${candidate}" ]; then
      targets+=("${candidate}")
    fi
  done

  if [ "${#targets[@]}" -eq 0 ]; then
    return 0
  fi

  yamllint "${targets[@]}"
}

cd "${REPO_ROOT}"

SEMGREP_AVAILABLE=0
SEMGREP_SKIP_REASON="semgrep is not installed or is not executable from this shell"
if have_executable_command semgrep; then
  if semgrep_usable; then
    SEMGREP_AVAILABLE=1
  else
    SEMGREP_SKIP_REASON="semgrep is installed but its scan engine execution probe failed"
  fi
fi

echo "Repository: ${REPO_ROOT}"

if have_executable_command gitleaks; then
  run_security_check "Secrets scan with gitleaks" run_gitleaks
else
  skip_check "Secrets scan with gitleaks" "gitleaks is not installed or is not executable from this shell"
fi

if have_executable_command trufflehog && have_executable_command docker && docker_usable; then
  run_security_check "Secrets scan with trufflehog" run_trufflehog
elif have_executable_command trufflehog; then
  skip_check "Secrets scan with trufflehog" "docker is not usable in the current environment"
else
  skip_check "Secrets scan with trufflehog" "trufflehog is not installed"
fi

if have_executable_command osv-scanner && has_node_manifest; then
  run_security_check "Dependency scan with osv-scanner" osv-scanner scan source -r .
else
  skip_check "Dependency scan with osv-scanner" "no Node manifest found or osv-scanner is not installed"
fi

if have_executable_command pip-audit && has_python_manifest; then
  run_security_check "Python dependency audit with pip-audit" pip-audit
else
  skip_check "Python dependency audit with pip-audit" "no supported Python dependency manifest or tool missing"
fi

if [ "${SEMGREP_AVAILABLE}" -eq 1 ]; then
  run_security_check "Semgrep auto scan" run_semgrep
else
  skip_check "Semgrep auto scan" "${SEMGREP_SKIP_REASON}"
fi

run_check "LLM surface prompt-injection scan" run_llm_surface_security_scan

python_has_skillspector() {
  local python_cmd_text
  local -a python_cmd
  python_cmd_text="$(find_python_cmd)" || return 1
  read -r -a python_cmd <<< "$python_cmd_text"
  "${python_cmd[@]}" -c "import skillspector" >/dev/null 2>&1
}

if [ ! -f "${REPO_ROOT}/scripts/check-skillspector-skills.py" ]; then
  skip_check "SkillSpector changed skill scan" "scripts/check-skillspector-skills.py is missing"
elif ! python_has_skillspector; then
  skip_check "SkillSpector changed skill scan" "skillspector is not installed in the selected Python (pip install skillspector)"
elif has_changed_skill_files; then
  run_security_check "SkillSpector changed skill scan" run_skillspector_changed_skill_scan
else
  skip_check "SkillSpector changed skill scan" "no new or modified skill files detected"
fi

if [ -f "${REPO_ROOT}/scripts/check-new-skill-security.sh" ]; then
  if bash "${REPO_ROOT}/scripts/check-new-skill-security.sh" --has-work >/dev/null 2>&1; then
    run_security_check "Agent skill security scan" bash "${REPO_ROOT}/scripts/check-new-skill-security.sh"
  else
    skip_check "Agent skill security scan" "no new or modified skills or Gen Agent Trust Hub URLs detected"
  fi
else
  skip_check "Agent skill security scan" "scripts/check-new-skill-security.sh is missing"
fi

if have_executable_command checkov && [ -d "${REPO_ROOT}/infra" ]; then
  run_security_check "Infrastructure scan with checkov" checkov -d infra
else
  skip_check "Infrastructure scan with checkov" "infra directory missing or checkov is not installed"
fi

if have_executable_command tfsec && [ -d "${REPO_ROOT}/infra" ]; then
  run_security_check "Terraform scan with tfsec" tfsec infra
else
  skip_check "Terraform scan with tfsec" "infra directory missing or tfsec is not installed"
fi

if have_executable_command cfn-lint && [ -d "${REPO_ROOT}/infra" ]; then
  run_security_check "CloudFormation scan with cfn-lint" run_cfn_lint
else
  skip_check "CloudFormation scan with cfn-lint" "infra directory missing or cfn-lint is not installed"
fi

if have_executable_command yamllint; then
  run_security_check "YAML lint" run_yamllint
else
  skip_check "YAML lint" "yamllint is not installed"
fi

if have_executable_command shellcheck && has_files '*.sh'; then
  run_security_check "Shell script lint with shellcheck" run_shellcheck
else
  skip_check "Shell script lint with shellcheck" "no shell scripts found or shellcheck is not installed/executable from this shell"
fi

if have_psscriptanalyzer && has_files '*.ps1'; then
  run_security_check "PowerShell lint with PSScriptAnalyzer" run_psscriptanalyzer
else
  skip_check "PowerShell lint with PSScriptAnalyzer" "no PowerShell scripts found, pwsh is missing, or PSScriptAnalyzer is unavailable"
fi

if [ "${SEMGREP_AVAILABLE}" -eq 1 ] && { has_files '*.cmd' || has_files '*.bat'; }; then
  run_security_check "Batch script scan with semgrep" run_cmd_semgrep
elif [ "${SEMGREP_AVAILABLE}" -eq 1 ]; then
  skip_check "Batch script scan with semgrep" "no .cmd/.bat files found"
else
  skip_check "Batch script scan with semgrep" "${SEMGREP_SKIP_REASON}"
fi

if have_executable_command actionlint && [ -d "${REPO_ROOT}/.github/workflows" ]; then
  run_security_check "GitHub Actions lint with actionlint" actionlint
else
  skip_check "GitHub Actions lint with actionlint" ".github/workflows missing or actionlint is not installed"
fi

if have_executable_command hadolint && find "${REPO_ROOT}" -type f \( -name 'Dockerfile' -o -name '*.Dockerfile' \) -print -quit | grep -q .; then
  run_security_check "Dockerfile lint with hadolint" run_hadolint
else
  skip_check "Dockerfile lint with hadolint" "no Dockerfiles found or hadolint is not installed"
fi

run_cloud_sync_duplicate_check() {
  local dupes candidate name
  dupes="$(
    while IFS= read -r -d '' candidate; do
      name="${candidate##*/}"
      if is_cloud_sync_duplicate_name "$name"; then
        printf '  %q\n' "$candidate"
      fi
    done < <(
      git_inventory '*'
      git -C "${REPO_ROOT}" ls-files --others --ignored --exclude-standard -z -- '* (*)*' \
        ':(exclude).agents/skills/**' ':(exclude).agents/worktrees/**' \
        ':(exclude).claude/agents/**' ':(exclude).claude/skills/**' ':(exclude).claude/worktrees/**' \
        ':(exclude).codex/agents/**' ':(exclude).codex/skills/**' ':(exclude).codex/worktrees/**' \
        ':(exclude).cursor/agents/**' ':(exclude).cursor/rules/**' ':(exclude).cursor/skills/**' \
        ':(exclude).cursor/workflows/**' ':(exclude).cursor/worktrees/**' \
        ':(exclude).windsurf/rules/**' ':(exclude).windsurf/skills/**' \
        ':(exclude).windsurf/workflows/**' ':(exclude).windsurf/worktrees/**'
    ) | LC_ALL=C sort -u
  )"
  if [ -n "$dupes" ]; then
    echo "BLOCKED: cloud-sync duplicate files detected (see rules/git-conventions.md § Duplicate-File Gate):" >&2
    echo "$dupes" >&2
    return 1
  fi
  return 0
}
run_check "Cloud-sync duplicate file check" run_cloud_sync_duplicate_check

if [ -f "${REPO_ROOT}/scripts/validate-toolkit-indexes.sh" ]; then
  run_check "Toolkit index and genericity validation" bash "${REPO_ROOT}/scripts/validate-toolkit-indexes.sh"
else
  skip_check "Toolkit index and genericity validation" "scripts/validate-toolkit-indexes.sh is missing"
fi

if [ -f "${REPO_ROOT}/scripts/test-sync-tool-configs-link-safety.sh" ]; then
  run_check "Sync tool link safety regression test" bash "${REPO_ROOT}/scripts/test-sync-tool-configs-link-safety.sh"
else
  skip_check "Sync tool link safety regression test" "scripts/test-sync-tool-configs-link-safety.sh is missing"
fi

if have_executable_command syft; then
  run_security_check "SBOM generation with syft" syft dir:. -o table
else
  skip_check "SBOM generation with syft" "syft is not installed"
fi

grype_db_available() {
  grype db status >/dev/null 2>&1 || grype db update >/dev/null 2>&1
}

trivy_db_available() {
  trivy fs --download-db-only --quiet . >/dev/null 2>&1
}

if have_executable_command grype && has_dependency_manifest && grype_db_available; then
  run_security_check "Vulnerability match with grype" grype dir:.
elif have_executable_command grype && has_dependency_manifest; then
  skip_check "Vulnerability match with grype" "grype vulnerability database is unavailable (offline or restricted egress)"
elif have_executable_command grype; then
  skip_check "Vulnerability match with grype" "no dependency manifests found"
else
  skip_check "Vulnerability match with grype" "grype is not installed"
fi

if have_executable_command trivy && trivy_db_available; then
  run_security_check "Filesystem scan with trivy" run_trivy
elif have_executable_command trivy; then
  skip_check "Filesystem scan with trivy" "trivy vulnerability database is unavailable (offline or restricted egress)"
else
  skip_check "Filesystem scan with trivy" "trivy is not installed"
fi

echo
echo "Summary:"
echo "  total:   ${TOTAL_CHECKS}"
echo "  passed:  ${PASSED_CHECKS}"
echo "  failed:  ${FAILED_CHECKS}"
echo "  skipped: ${SKIPPED_CHECKS}"
echo "  security/lint signal: ${SECURITY_SIGNAL_CHECKS}"

if [ "${FAILED_CHECKS}" -gt 0 ]; then
  echo "FAILED: ${FAILED_CHECKS} check(s) failed."
  exit 1
fi

if [ "${PASSED_CHECKS}" -eq 0 ]; then
  echo "FAILED: no checks passed (all were skipped). Install at least one secrets scanner (gitleaks) and one static analysis tool (semgrep or shellcheck)."
  echo "To override for local runs where tools are unavailable, set SECURITY_ALLOW_ALL_SKIPPED=1."
  if [ "${SECURITY_ALLOW_ALL_SKIPPED:-0}" != "1" ]; then
    exit 1
  fi
  echo "WARNING: override active — accepting all-skipped result."
fi

if [ "${SECURITY_SIGNAL_CHECKS}" -eq 0 ]; then
  echo "FAILED: no external security or lint scanner produced a passing signal; only internal hygiene checks ran."
  echo "To override for local runs where tools are unavailable, set SECURITY_ALLOW_NO_SCANNER_SIGNAL=1."
  if [ "${SECURITY_ALLOW_NO_SCANNER_SIGNAL:-0}" != "1" ]; then
    exit 1
  fi
  echo "WARNING: override active — accepting run with no external scanner signal."
fi

if [ "${SKIPPED_CHECKS}" -gt 0 ]; then
  echo "All runnable checks passed; ${SKIPPED_CHECKS} check(s) skipped."
else
  echo "All checks passed."
fi
