#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"

have_command() {
  command -v "$1" >/dev/null 2>&1
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

find_python_uv() {
  local python_cmd_text
  local -a python_cmd
  if python_cmd_text="$(find_python_cmd)"; then
    read -r -a python_cmd <<< "$python_cmd_text"
    if "${python_cmd[@]}" -m uv --version >/dev/null 2>&1; then
      printf '%s\n' "$python_cmd_text"
    fi
  fi
}

collect_changed_skill_files() {
  {
    git diff --name-only --diff-filter=AM HEAD -- 'skills/*/SKILL.md' 2>/dev/null || true
    git diff --name-only --diff-filter=AM --cached HEAD -- 'skills/*/SKILL.md' 2>/dev/null || true
    git ls-files --others --exclude-standard -- 'skills/*/SKILL.md' 2>/dev/null || true
    if [ -n "${SECURITY_NEW_SKILL_BASE:-}" ]; then
      if git rev-parse --verify "${SECURITY_NEW_SKILL_BASE}^{commit}" >/dev/null 2>&1; then
        git diff --name-only --diff-filter=AM "${SECURITY_NEW_SKILL_BASE}...HEAD" -- 'skills/*/SKILL.md' 2>/dev/null || true
      else
        echo "Warning: SECURITY_NEW_SKILL_BASE is not a valid commit/ref: ${SECURITY_NEW_SKILL_BASE}" >&2
      fi
    fi
  } | LC_ALL=C sort -u | while IFS= read -r file; do
    [ -f "$file" ] && printf '%s\n' "$file"
  done
}

collect_agent_trust_hub_urls() {
  {
    if [ -n "${GEN_AGENT_TRUST_HUB_SKILL_URLS:-}" ]; then
      printf '%s\n' "$GEN_AGENT_TRUST_HUB_SKILL_URLS"
    fi
    if [ -n "${GEN_AGENT_TRUST_HUB_SKILL_URLS_FILE:-}" ] && [ -f "${GEN_AGENT_TRUST_HUB_SKILL_URLS_FILE}" ]; then
      sed 's/#.*$//' "${GEN_AGENT_TRUST_HUB_SKILL_URLS_FILE}"
    fi
  } | sed 's/[[:space:],]\+/\n/g; /^$/d' | LC_ALL=C sort -u
}

run_snyk_agent_scan() {
  local skill_file="$1"
  local -a python_uv_cmd

  if [ -z "${SNYK_TOKEN:-}" ]; then
    echo "SNYK_TOKEN is required to scan new or modified skills with Snyk Agent Scan." >&2
    echo "Set SNYK_TOKEN or use SECURITY_ALLOW_AGENT_SKILL_SCAN_SKIP=1 for a documented local-only exception." >&2
    return 1
  fi

  echo "Scanning skill with Snyk Agent Scan: ${skill_file}"
  if have_command snyk-agent-scan; then
    snyk-agent-scan scan --no-bootstrap "$skill_file"
  elif have_command uvx; then
    uvx snyk-agent-scan@latest scan --no-bootstrap "$skill_file"
  elif python_uv="$(find_python_uv)" && [ -n "$python_uv" ]; then
    read -r -a python_uv_cmd <<< "$python_uv"
    "${python_uv_cmd[@]}" -m uv tool run snyk-agent-scan@latest scan --no-bootstrap "$skill_file"
  else
    echo "Install uv/uvx or snyk-agent-scan before adding or modifying skills." >&2
    return 1
  fi
}

run_agent_trust_hub_lookup() {
  local skill_url="$1"
  local python_cmd_text
  local -a python_cmd

  if ! python_cmd_text="$(find_python_cmd)"; then
    echo "Python is required for the Gen Agent Trust Hub URL lookup." >&2
    return 1
  fi
  read -r -a python_cmd <<< "$python_cmd_text"

  echo "Checking skill URL with Gen Agent Trust Hub: ${skill_url}"
  "${python_cmd[@]}" - "$skill_url" <<'PY'
import json
import sys
import urllib.request

skill_url = sys.argv[1]
payload = json.dumps({"skillUrl": skill_url}).encode("utf-8")
request = urllib.request.Request(
    "https://ai.gendigital.com/api/scan/lookup",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(request, timeout=60) as response:
    body = response.read().decode("utf-8", "replace")

print(body)
data = json.loads(body)
severity = str(data.get("severity", "")).upper()
if severity != "SAFE":
    raise SystemExit(f"Agent Trust Hub severity is {severity or 'UNKNOWN'} for {skill_url}")
PY
}

mapfile -t changed_skill_files < <(collect_changed_skill_files)
mapfile -t trust_hub_urls < <(collect_agent_trust_hub_urls)

if [ "${1:-}" = "--has-new-skills" ]; then
  [ "${#changed_skill_files[@]}" -gt 0 ]
  exit $?
fi

if [ "${1:-}" = "--has-work" ]; then
  [ "${#changed_skill_files[@]}" -gt 0 ] || [ "${#trust_hub_urls[@]}" -gt 0 ]
  exit $?
fi

if [ "${#changed_skill_files[@]}" -eq 0 ] && [ "${#trust_hub_urls[@]}" -eq 0 ]; then
  echo "No new or modified skill files or Gen Agent Trust Hub URLs detected."
  exit 0
fi

status=0

if [ "${#changed_skill_files[@]}" -eq 0 ]; then
  echo "No new or modified local skill files detected for Snyk Agent Scan."
elif [ -z "${SNYK_TOKEN:-}" ] && [ "${SECURITY_REQUIRE_AGENT_SKILL_SCAN:-0}" != "1" ]; then
  # Optional commercial scanner: without a token this gate is informational.
  # SkillSpector (scripts/validate-skills-with-skillspector.py) remains the
  # required open-source skill scan. Set SECURITY_REQUIRE_AGENT_SKILL_SCAN=1
  # (for example in CI with SNYK_TOKEN provisioned) to make it blocking.
  echo "NOTE: SNYK_TOKEN is not set; skipping Snyk Agent Scan for ${#changed_skill_files[@]} changed skill file(s)."
  echo "      Run scripts/validate-skills-with-skillspector.sh --changed for the open-source skill scan."
elif [ "${SNYK_AGENT_SCAN_ENABLED:-1}" != "0" ]; then
  for skill_file in "${changed_skill_files[@]}"; do
    if ! run_snyk_agent_scan "$skill_file"; then
      status=1
    fi
  done
else
  echo "Snyk Agent Scan disabled by SNYK_AGENT_SCAN_ENABLED=0." >&2
  status=1
fi

if [ "${#trust_hub_urls[@]}" -gt 0 ]; then
  for skill_url in "${trust_hub_urls[@]}"; do
    if ! run_agent_trust_hub_lookup "$skill_url"; then
      status=1
    fi
  done
else
  echo "No Gen Agent Trust Hub skill URLs supplied."
  echo "Set GEN_AGENT_TRUST_HUB_SKILL_URLS or GEN_AGENT_TRUST_HUB_SKILL_URLS_FILE when importing a skill from a marketplace/source URL."
fi

if [ "$status" -ne 0 ] && [ "${SECURITY_ALLOW_AGENT_SKILL_SCAN_SKIP:-0}" = "1" ]; then
  echo "WARNING: SECURITY_ALLOW_AGENT_SKILL_SCAN_SKIP=1 set; accepting missing/failed new-skill scanner signal for this local run." >&2
  exit 0
fi

exit "$status"
