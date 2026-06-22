#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
SKIPPED_CHECKS=0

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
  local found
  found="$(command -v "$1" 2>/dev/null || true)"
  [ -n "$found" ] && [ -x "$found" ]
}

have_psscriptanalyzer() {
  have_executable_command pwsh &&
    pwsh -NoLogo -NoProfile -Command "if (Get-Command Invoke-ScriptAnalyzer -ErrorAction SilentlyContinue) { exit 0 } exit 1" >/dev/null 2>&1
}

python_with_skillspector() {
  local py
  for py in python python3; do
    if have_executable_command "$py" &&
      "$py" -c "import skillspector" >/dev/null 2>&1; then
      printf '%s\n' "$py"
      return 0
    fi
  done
  return 1
}

docker_usable() {
  docker ps >/dev/null 2>&1
}

has_files() {
  local pattern="$1"
  find "${REPO_ROOT}" -type f -name "${pattern}" -print -quit | grep -q .
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
  .setup
  integrations
  docs
  AGENTS.md
  CLAUDE.md
  INTENTS.md
  README.md
  TOOLKIT_DOC_TITLE
)

gitleaks_sources() {
  local path
  for path in "${repo_scope_paths[@]}"; do
    if [ -e "${REPO_ROOT}/${path}" ]; then
      printf '%s\0' "${path}"
    fi
  done
}

scoped_existing_paths() {
  local path
  for path in "${repo_scope_paths[@]}"; do
    if [ -e "${REPO_ROOT}/${path}" ]; then
      printf '%s\0' "${path}"
    fi
  done
}

find_scoped_files_by_extension() {
  local extension="$1"
  local path
  while IFS= read -r -d '' path; do
    if [ -d "$path" ]; then
      find "$path" -type f -name "*.${extension}" -print0
    elif [[ "$path" == *."$extension" ]]; then
      printf '%s\0' "$path"
    fi
  done < <(scoped_existing_paths)
}

run_gitleaks() {
  local source
  while IFS= read -r -d '' source; do
    gitleaks detect --source "${source}" --no-git --redact
  done < <(gitleaks_sources)
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

  local file
  for file in "${files[@]}"; do
    local escaped_file="${file//\'/\'\'}"
    pwsh -NoLogo -NoProfile -Command "Invoke-ScriptAnalyzer -Path '${escaped_file}'"
  done
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

run_skillspector() {
  local py
  py="$(python_with_skillspector)"
  "$py" scripts/validate-skills-with-skillspector.py
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

echo "Repository: ${REPO_ROOT}"

if have_executable_command gitleaks; then
  run_check "Secrets scan with gitleaks" run_gitleaks
else
  skip_check "Secrets scan with gitleaks" "gitleaks is not installed or is not executable from this shell"
fi

if have_executable_command trufflehog && have_executable_command docker && docker_usable; then
  run_check "Secrets scan with trufflehog" run_trufflehog
elif have_executable_command trufflehog; then
  skip_check "Secrets scan with trufflehog" "docker is not usable in the current environment"
else
  skip_check "Secrets scan with trufflehog" "trufflehog is not installed"
fi

if have_executable_command osv-scanner && has_node_manifest; then
  run_check "Dependency scan with osv-scanner" osv-scanner scan source -r .
else
  skip_check "Dependency scan with osv-scanner" "no Node manifest found or osv-scanner is not installed"
fi

if have_executable_command pip-audit && has_python_manifest; then
  run_check "Python dependency audit with pip-audit" pip-audit
else
  skip_check "Python dependency audit with pip-audit" "no supported Python dependency manifest or tool missing"
fi

if have_executable_command semgrep; then
  run_check "Semgrep auto scan" run_semgrep
else
  skip_check "Semgrep auto scan" "semgrep is not installed"
fi

if have_executable_command checkov && [ -d "${REPO_ROOT}/infra" ]; then
  run_check "Infrastructure scan with checkov" checkov -d infra
else
  skip_check "Infrastructure scan with checkov" "infra directory missing or checkov is not installed"
fi

if have_executable_command tfsec && [ -d "${REPO_ROOT}/infra" ]; then
  run_check "Terraform scan with tfsec" tfsec infra
else
  skip_check "Terraform scan with tfsec" "infra directory missing or tfsec is not installed"
fi

if have_executable_command cfn-lint && [ -d "${REPO_ROOT}/infra" ]; then
  run_check "CloudFormation scan with cfn-lint" run_cfn_lint
else
  skip_check "CloudFormation scan with cfn-lint" "infra directory missing or cfn-lint is not installed"
fi

if have_executable_command yamllint; then
  run_check "YAML lint" run_yamllint
else
  skip_check "YAML lint" "yamllint is not installed"
fi

if have_executable_command shellcheck && has_files '*.sh'; then
  run_check "Shell script lint with shellcheck" run_shellcheck
else
  skip_check "Shell script lint with shellcheck" "no shell scripts found or shellcheck is not installed/executable from this shell"
fi

if have_psscriptanalyzer && has_files '*.ps1'; then
  run_check "PowerShell lint with PSScriptAnalyzer" run_psscriptanalyzer
else
  skip_check "PowerShell lint with PSScriptAnalyzer" "no PowerShell scripts found, pwsh is missing, or PSScriptAnalyzer is unavailable"
fi

if have_executable_command semgrep && { has_files '*.cmd' || has_files '*.bat'; }; then
  run_check "Batch script scan with semgrep" run_cmd_semgrep
else
  skip_check "Batch script scan with semgrep" "no .cmd/.bat files found or semgrep is not installed"
fi

if python_with_skillspector >/dev/null; then
  run_check "Agent skill scan with SkillSpector" run_skillspector
else
  skip_check "Agent skill scan with SkillSpector" "skillspector is not installed in python/python3"
fi

if have_executable_command actionlint && [ -d "${REPO_ROOT}/.github/workflows" ]; then
  run_check "GitHub Actions lint with actionlint" actionlint
else
  skip_check "GitHub Actions lint with actionlint" ".github/workflows missing or actionlint is not installed"
fi

if have_executable_command hadolint && find "${REPO_ROOT}" -type f \( -name 'Dockerfile' -o -name '*.Dockerfile' \) -print -quit | grep -q .; then
  run_check "Dockerfile lint with hadolint" run_hadolint
else
  skip_check "Dockerfile lint with hadolint" "no Dockerfiles found or hadolint is not installed"
fi

run_cloud_sync_duplicate_check() {
  local dupes
  dupes="$(git ls-files 2>/dev/null | grep -E ' \([0-9]+\)\.' || true)"
  if [ -n "$dupes" ]; then
    echo "BLOCKED: cloud-sync duplicate files detected (see rules/git-conventions.md § Duplicate-File Gate):" >&2
    echo "$dupes" >&2
    return 1
  fi
  return 0
}
run_check "Cloud-sync duplicate file check" run_cloud_sync_duplicate_check

if [ -x "${REPO_ROOT}/scripts/validate-toolkit-indexes.sh" ]; then
  run_check "Toolkit index and genericity validation" "${REPO_ROOT}/scripts/validate-toolkit-indexes.sh"
else
  skip_check "Toolkit index and genericity validation" "scripts/validate-toolkit-indexes.sh is missing or not executable"
fi

if have_executable_command syft; then
  run_check "SBOM generation with syft" syft dir:. -o table
else
  skip_check "SBOM generation with syft" "syft is not installed"
fi

if have_executable_command grype; then
  run_check "Vulnerability match with grype" grype dir:.
else
  skip_check "Vulnerability match with grype" "grype is not installed"
fi

if have_executable_command trivy; then
  run_check "Filesystem scan with trivy" trivy fs .
else
  skip_check "Filesystem scan with trivy" "trivy is not installed"
fi

echo
echo "Summary:"
echo "  total:   ${TOTAL_CHECKS}"
echo "  passed:  ${PASSED_CHECKS}"
echo "  failed:  ${FAILED_CHECKS}"
echo "  skipped: ${SKIPPED_CHECKS}"

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

echo "All checks passed."
