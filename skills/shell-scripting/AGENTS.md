# Shell Scripting Best Practices

Comprehensive best practices for writing robust, portable, and secure Bash scripts. Applies to automation, deployment, CI/CD, CLI tools, and cron jobs.

## Safety & Strict Mode

### Always Use Strict Mode

```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'
```

Every script starts with these three lines. No exceptions.

| Flag | What it does | Without it |
|------|-------------|------------|
| `set -e` | Exit on any command failure | Script continues after errors, corrupting state |
| `set -u` | Exit on unset variable access | Unset vars expand to empty string silently |
| `set -o pipefail` | Pipe fails if ANY segment fails | Only last command's exit code matters |
| `IFS=$'\n\t'` | Split only on newlines and tabs | Spaces in filenames break `for` loops |

**Why `#!/usr/bin/env bash` over `#!/bin/bash`:**
- `/bin/bash` doesn't exist on NixOS, some BSDs, or some containers.
- `env bash` uses `$PATH` to find bash — portable across systems.

### What `pipefail` Catches

```bash
# WITHOUT pipefail — exit code 0 (grep succeeds, wc succeeds)
set -e
cat /nonexistent/file 2>/dev/null | grep "pattern" | wc -l
echo "This still runs!"  # cat failed but pipeline "succeeded"

# WITH pipefail — exit code 1 (cat fails, pipeline fails)
set -eo pipefail
cat /nonexistent/file 2>/dev/null | grep "pattern" | wc -l
echo "This never runs"  # script exits at the pipe
```

## Error Handling

### Trap for Cleanup

```bash
# WRONG — temp file left behind on error
TEMP_FILE=$(mktemp)
curl -o "$TEMP_FILE" https://example.com/data
process "$TEMP_FILE"
rm -f "$TEMP_FILE"  # never reached if process fails

# CORRECT — trap guarantees cleanup regardless of exit reason
TEMP_FILE=""
cleanup() {
  if [[ -n "$TEMP_FILE" && -f "$TEMP_FILE" ]]; then
    rm -- "$TEMP_FILE"
  fi
}
trap cleanup EXIT

TEMP_FILE=$(mktemp)
curl -o "$TEMP_FILE" https://example.com/data
process "$TEMP_FILE"
# cleanup runs automatically — on success, error, or signal
```

- `trap ... EXIT` fires on normal exit, errors (`set -e`), and signals (SIGINT, SIGTERM).
- Always clean up temp files, lock files, and background processes.
- Use `trap cleanup EXIT` early, before creating any resources.

### Error Reporting with Line Numbers

```bash
trap 'echo "ERROR: Failed at line $LINENO. Exit code: $?" >&2' ERR

# Or more detailed:
on_error() {
  local exit_code=$?
  local line_no=$1
  echo "ERROR: Command failed at line ${line_no} with exit code ${exit_code}" >&2
  echo "ERROR: Script: ${BASH_SOURCE[0]}" >&2
}
trap 'on_error $LINENO' ERR
```

### Check Critical Commands

```bash
# WRONG - continues silently if cd fails
cd /some/directory
delete_current_directory_contents  # affects the wrong directory if cd failed

# CORRECT - fail explicitly
cd /some/directory || { echo "Failed to cd to /some/directory" >&2; exit 1; }

# CORRECT — die helper
die() { echo "FATAL: $*" >&2; exit 1; }

cd /some/directory || die "Cannot cd to /some/directory"
command -v docker &>/dev/null || die "Docker is required but not installed"
[[ -f "$CONFIG_FILE" ]] || die "Config file not found: $CONFIG_FILE"
```

## Security

### Never `eval` Untrusted Input

```bash
# WRONG - command injection via user input
user_input="hello; <destructive shell payload>"
eval "echo $user_input"  # executes attacker-controlled shell syntax

# CORRECT - direct execution, no eval
echo "$user_input"  # prints the string literally

# WRONG - building commands with string concatenation
cmd="ls $user_provided_path"
eval "$cmd"

# CORRECT - use arrays for command building
cmd=(ls "$user_provided_path")
"${cmd[@]}"
```

### Secure Temporary Files

```bash
# WRONG — predictable name, race condition (symlink attack)
TEMP_FILE="/tmp/myscript.tmp"
echo "$data" > "$TEMP_FILE"

# CORRECT — mktemp creates unique file with secure permissions
TEMP_FILE=$(mktemp)           # /tmp/tmp.XXXXXXXXXX
TEMP_DIR=$(mktemp -d)          # /tmp/tmp.XXXXXXXXXX/

# Always clean up
cleanup() {
  if [[ -n "${TEMP_FILE:-}" && -f "$TEMP_FILE" ]]; then
    rm -- "$TEMP_FILE"
  fi
  if [[ -n "${TEMP_DIR:-}" && -d "$TEMP_DIR" ]]; then
    rm -r -- "$TEMP_DIR"
  fi
}
trap cleanup EXIT
```

### Validate Input

```bash
# Validate required arguments
[[ $# -ge 1 ]] || die "Usage: $0 <environment>"

# Validate against allowed values
environment="$1"
case "$environment" in
  dev|staging|prod) ;;
  *) die "Invalid environment: $environment. Must be dev, staging, or prod." ;;
esac

# Validate file exists and is readable
config_file="$2"
[[ -f "$config_file" ]] || die "Config file not found: $config_file"
[[ -r "$config_file" ]] || die "Config file not readable: $config_file"

# Validate numeric input
port="${3:-8080}"
[[ "$port" =~ ^[0-9]+$ ]] || die "Port must be numeric: $port"
(( port >= 1 && port <= 65535 )) || die "Port out of range: $port"
```

### Never Hardcode Secrets

```bash
# WRONG — credentials in script
DB_PASSWORD="MyS3cretP@ss!"
curl -u "admin:$DB_PASSWORD" "$SERVICE_URL"

# CORRECT — from environment variable
: "${DB_PASSWORD:?DB_PASSWORD environment variable is required}"
curl -u "admin:$DB_PASSWORD" "$SERVICE_URL"

# CORRECT — from secret manager
DB_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id /myapp/db-password \
  --query SecretString --output text) || die "Failed to fetch secret"
```

## Script Structure

### Standard Template

```bash
#!/usr/bin/env bash

# =============================================================================
# Script: deploy.sh
# Description: Deploy application to specified environment
# Usage: deploy.sh [OPTIONS] <environment>
# =============================================================================

set -euo pipefail
IFS=$'\n\t'

# --------------- Constants ---------------
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
readonly LOG_FILE="/tmp/${SCRIPT_NAME%.*}.log"

# --------------- Defaults ---------------
VERBOSE=false
DRY_RUN=false

# --------------- Functions ---------------
die()   { echo "FATAL: $*" >&2; exit 1; }
log()   { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
debug() { [[ "$VERBOSE" == true ]] && log "DEBUG: $*"; }

usage() {
  cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS] <environment>

Deploy application to the specified environment.

ARGUMENTS:
    environment         Target environment (dev, staging, prod)

OPTIONS:
    -h, --help          Show this help message
    -v, --verbose       Enable verbose output
    -n, --dry-run       Show what would be done without executing

EXAMPLES:
    $SCRIPT_NAME dev
    $SCRIPT_NAME --verbose --dry-run prod
EOF
}

cleanup() {
  # Cleanup temp files, background processes, etc.
  :
}
trap cleanup EXIT

deploy() {
  local environment="$1"
  log "Deploying to ${environment}..."
  if [[ "$DRY_RUN" == true ]]; then
    log "DRY RUN: Would deploy to ${environment}"
    return 0
  fi
  # actual deployment logic
}

# --------------- Argument Parsing ---------------
ENVIRONMENT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)    usage; exit 0 ;;
    -v|--verbose) VERBOSE=true; shift ;;
    -n|--dry-run) DRY_RUN=true; shift ;;
    -*)           die "Unknown option: $1. Use --help for usage." ;;
    *)            ENVIRONMENT="$1"; shift ;;
  esac
done

# --------------- Validation ---------------
[[ -n "$ENVIRONMENT" ]] || { usage; die "Environment argument is required."; }
case "$ENVIRONMENT" in
  dev|staging|prod) ;;
  *) die "Invalid environment: $ENVIRONMENT" ;;
esac

# --------------- Main ---------------
deploy "$ENVIRONMENT"
log "Done."
```

### Functions with `local` Variables

```bash
# WRONG — all variables are global by default
process_file() {
  filename="$1"      # global — leaks to caller
  line_count=$(wc -l < "$filename")  # global
  echo "Lines: $line_count"
}

# CORRECT — local prevents leaking
process_file() {
  local filename="$1"
  local line_count
  line_count=$(wc -l < "$filename")
  echo "Lines: $line_count"
}
```

## Quoting & Variables

### Always Double-Quote Variables

```bash
# WRONG — word splitting + glob expansion
file="my report (final).txt"
rm $file          # tries to rm "my", "report", "(final).txt"
cat $file | wc    # same problem

# CORRECT — double-quote preserves the value as one token
rm "$file"
cat "$file" | wc

# WRONG — for loop on unquoted command substitution
for f in $(find . -name "*.txt"); do  # breaks on spaces in filenames
  echo "$f"
done

# CORRECT — read with null delimiter
while IFS= read -r -d '' f; do
  echo "$f"
done < <(find . -name "*.txt" -print0)
```

### Variable Defaults and Required Values

```bash
# Default value if unset or empty
port="${PORT:-8080}"
log_level="${LOG_LEVEL:-info}"

# Default value only if unset (empty string is kept)
port="${PORT-8080}"

# Fail if unset or empty (with message)
: "${DATABASE_URL:?DATABASE_URL is required}"
: "${API_KEY:?API_KEY environment variable must be set}"
```

### Readonly Constants

```bash
# Constants — cannot be reassigned
readonly VERSION="2.1.0"
readonly MAX_RETRIES=5
readonly CONFIG_DIR="/etc/myapp"

# Computed constants
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
```

## Text Processing & I/O

### Never Parse `ls` Output

```bash
# WRONG — breaks on spaces, newlines, special chars in filenames
for file in $(ls *.txt); do
  echo "$file"
done

# CORRECT — glob expansion (handled correctly by bash)
for file in *.txt; do
  [[ -e "$file" ]] || continue  # handle case where no files match
  echo "$file"
done

# CORRECT — find with null delimiter for recursive
find . -name "*.txt" -print0 | while IFS= read -r -d '' file; do
  echo "$file"
done
```

### Safe Line-by-Line Reading

```bash
# WRONG — while in a pipe runs in subshell (variable changes lost)
count=0
cat file.txt | while IFS= read -r line; do
  ((count++))
done
echo "$count"  # always 0 — subshell!

# CORRECT — redirect into while (runs in current shell)
count=0
while IFS= read -r line; do
  ((count++))
done < file.txt
echo "$count"  # correct count
```

### Heredocs

```bash
# Multi-line string
cat <<EOF
Hello $USER,
Today is $(date '+%A').
Working directory: $PWD
EOF

# Literal (no variable expansion)
cat <<'EOF'
This $variable is NOT expanded.
Neither is $(this command).
EOF

# Indented (<<- strips leading tabs)
if true; then
	cat <<-EOF
	This is indented with tabs.
	The leading tabs are stripped.
	EOF
fi
```

### JSON Validation with jq

```bash
# WRONG — exit 4 on perfectly valid JSON (empty emits no value for -e to inspect)
jq -e empty payload.json && deploy

# CORRECT — parse validation only
jq empty payload.json

# CORRECT — parse validation plus top-level shape assertion
jq -e 'type == "object"' payload.json
```

- The `empty` filter parses input but emits no result; with `-e`, jq derives its exit status from the last emitted value and returns 4 when there is none.
- Use `-e` only with filters that emit a value (booleans, objects, counts).

## Portability & Performance

### Prefer Builtins Over External Commands

```bash
# WRONG — external command for simple string operations
filename=$(echo "$path" | sed 's/.*\///')
extension=$(echo "$file" | sed 's/.*\.//')

# CORRECT — bash parameter expansion (no subprocess)
filename="${path##*/}"       # remove everything up to last /
extension="${file##*.}"      # remove everything up to last .
basename="${file%.*}"        # remove extension
dirname="${path%/*}"         # remove filename

# WRONG — external command for uppercase
upper=$(echo "$text" | tr '[:lower:]' '[:upper:]')

# CORRECT — bash built-in (bash 4+)
upper="${text^^}"
lower="${text,,}"
```

### Avoid Unnecessary Subshells

```bash
# WRONG — subshell for grouping (forks a new process)
(
  cd /some/dir
  make
  make install
)

# CORRECT — brace grouping (same process)
{
  cd /some/dir
  make
  make install
}
```

### ShellCheck in CI

```yaml
# GitHub Actions
- name: ShellCheck
  uses: ludeeus/action-shellcheck@2.0.0
  with:
    scandir: ./scripts
    severity: warning
```

```bash
# Local
shellcheck scripts/*.sh
shellcheck -x scripts/*.sh  # follow sourced files
```

- ShellCheck catches quoting errors, useless cats, parsing ls, and hundreds of common bugs.
- Run it on every PR — treat warnings as errors in CI.
- Use `# shellcheck disable=SC2034` for intentional suppressions (with comment explaining why).

## PowerShell / Windows Interop

### Scope ErrorActionPreference Per Native Call and Decide by Exit Code

Under Windows PowerShell 5.1, `$ErrorActionPreference = "Stop"` plus `2>&1` on a native command wraps the first stderr line in an `ErrorRecord` and promotes it to a terminating `NativeCommandError` — the script dies even when the command exits 0 (many CLIs write progress/warnings to stderr) and `$LASTEXITCODE` is never inspected. Removing `2>&1` leaks stderr and loses diagnostics; setting `Continue` globally loses fail-fast; `try/catch` loses the remaining output and breaks exit-code flow control.

```powershell
# CORRECT — scope EAP to the invocation, restore in finally, return the exit code
function Invoke-NativeCommand {
    param([Parameter(Mandatory)][string[]]$CommandArguments)
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & aws @CommandArguments 2>&1
        return [pscustomobject]@{ Output = $output; ExitCode = $LASTEXITCODE }
    } finally {
        $ErrorActionPreference = $previousPreference
    }
}

# Callers decide success from ExitCode. When parsing JSON from Output,
# filter stderr records first — they arrive as ErrorRecord objects:
$json = ($result.Output | Where-Object { $_ -isnot [System.Management.Automation.ErrorRecord] }) -join "`n"
```

PowerShell 7 changed this behavior, so scripts that must run on 5.1 (default on Windows Server and enterprise desktops) need the wrapper even if they appear fine in pwsh.

### Write Tool-Consumed Files as BOM-less UTF-8

In Windows PowerShell 5.1, both `Set-Content -Encoding UTF8` and `Out-File -Encoding utf8` emit a UTF-8 BOM (`EF BB BF`). Strict consumers such as the AWS CLI's `file://` JSON loader do not strip it and fail with parse errors even though the content looks valid in every editor — and `ConvertFrom-Json` parses it fine because PowerShell tolerates the BOM.

```powershell
# WRONG — BOM breaks the downstream consumer
$payload | Set-Content -Encoding UTF8 batch.json

# CORRECT — explicit BOM-less encoder (WriteAllText needs an absolute path)
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($outputFile, $payload, $utf8NoBom)
```

Verify by dumping the first bytes: the file must start at `7B` (`{`), not `EF BB BF`. PowerShell 7's `utf8` encoding is BOM-less by default; use the explicit encoder anyway when the script must run on both.

### Use -Command for Array Parameters — -File Binds Literal Strings

`powershell -File` performs no expression parsing on script arguments — every token is bound as a literal string, so a `[string[]]` parameter invoked as `-Only a.png,b.svg` receives one element `"a.png,b.svg"`. Array literals, `@()`, and comma constructors are language syntax and only take effect under `-Command`.

```bash
# WRONG — one comma-joined literal string reaches the [string[]] parameter
powershell -File script.ps1 -Only a.png,b.svg

# CORRECT — a real PowerShell parser builds the array
powershell -NoProfile -Command "& 'script.ps1' -Only @('a.png','b.svg')"
```

Alternatively, keep `-File` invocation but accept a single delimited string and split inside the script (`$Only -split ','`).

## Common Patterns

### Retry with Backoff

```bash
retry() {
  local max_attempts="${1:-3}"
  local delay="${2:-5}"
  shift 2
  local attempt=1

  until "$@"; do
    if (( attempt >= max_attempts )); then
      die "Command failed after $max_attempts attempts: $*"
    fi
    log "Attempt $attempt failed. Retrying in ${delay}s..."
    sleep "$delay"
    (( attempt++ ))
    (( delay *= 2 ))  # exponential backoff
  done
}

# Usage
retry 3 5 curl -sf "$HEALTH_CHECK_URL"
```

### Logging

```bash
readonly LOG_FILE="/var/log/myapp/deploy.log"

log()   { local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"; echo "$msg" | tee -a "$LOG_FILE"; }
warn()  { log "WARN: $*" >&2; }
error() { log "ERROR: $*" >&2; }
die()   { error "$*"; exit 1; }
debug() { [[ "${VERBOSE:-false}" == true ]] && log "DEBUG: $*"; }
```

### Check if Command Exists

```bash
require_command() {
  command -v "$1" &>/dev/null || die "$1 is required but not installed"
}

require_command docker
require_command aws
require_command jq
```

### Colored Output

```bash
if [[ -t 1 ]]; then  # only colorize if stdout is a terminal
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[0;33m'
  NC='\033[0m'
else
  RED='' GREEN='' YELLOW='' NC=''
fi

success() { echo -e "${GREEN}✓ $*${NC}"; }
warning() { echo -e "${YELLOW}⚠ $*${NC}" >&2; }
failure() { echo -e "${RED}✗ $*${NC}" >&2; }
```

## Common Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| No `set -euo pipefail` | Always use strict mode |
| Unquoted variables `$var` | Always `"$var"` |
| Parsing `ls` output | Use globs or `find -print0` |
| Destructive cleanup after unchecked `cd` | `cd dir \|\| die "..."` before cleanup |
| `eval "$user_input"` | Use arrays: `cmd=(...); "${cmd[@]}"` |
| Temp files in `/tmp/myscript.tmp` | `mktemp` + `trap cleanup EXIT` |
| Global variables in functions | `local` for all function variables |
| `cat file \| grep pattern` | `grep pattern file` (useless use of cat) |
| Secrets hardcoded in script | Environment variables or secret managers |
| No ShellCheck in CI | `shellcheck scripts/*.sh` on every PR |

## Related Skills

- **security** — Input validation, injection prevention, secrets management (applies to all scripts handling user input or credentials)
- **js-ts-best-practices** — CI/CD shell steps and Docker deployment scripts often accompany Node.js builds
- **terraform-change-safety** — Change-safety patterns for the Terraform/OpenTofu stacks that deployment scripts wrap
- **best-practices** — Defensive programming and fail-fast patterns that apply to script design
