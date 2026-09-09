# First-time developer bootstrap for the LLM toolkit toolkit (Windows).
# Installs required binaries/CLIs via winget, optional tooling, and an agent CLI
# of choice, then wires the toolkit so any LLM agent (Claude Code, Cursor,
# Windsurf, Codex, Gemini CLI, Copilot) can use it. npm-based tools are
# exact-version pinned and installed without lifecycle scripts.
#
# POSIX/Git Bash: scripts/bootstrap-dev.sh - same behavior via brew/apt/dnf.
#
# Usage: ./scripts/bootstrap-dev.ps1 [-Minimal] [-Full] [-Agent claude|codex|gemini|all]
#                                    [-Consumer <path>] [-DryRun]
#
# Idempotent: existing tools are detected and skipped. Interactive auth steps
# (gh auth login, acli auth, aws configure) are printed, never run silently.

[CmdletBinding()]
param(
    [switch]$Minimal,
    [switch]$Full,
    [ValidateSet('claude', 'codex', 'gemini', 'all')]
    [string]$Agent,
    [string]$Consumer,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$profileName = 'default'
if ($Minimal) { $profileName = 'minimal' }
if ($Full) { $profileName = 'full' }

$installed = New-Object System.Collections.Generic.List[string]
$skipped = New-Object System.Collections.Generic.List[string]
$manual = New-Object System.Collections.Generic.List[string]

function Test-Command([string]$name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

function Install-WingetTool([string]$check, [string]$label, [string]$wingetId) {
    if (Test-Command $check) {
        $skipped.Add("$label (already installed)")
        return
    }
    if (-not (Test-Command 'winget')) {
        $manual.Add("$label — winget unavailable; install manually")
        return
    }
    if ($DryRun) {
        Write-Host "[dry-run] winget install --id $wingetId -e --silent"
        return
    }
    Write-Host "+ winget install --id $wingetId -e --silent"
    # Scope EAP per native call: winget writes progress to stderr on some hosts.
    $eap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    winget install --id $wingetId -e --silent --accept-package-agreements --accept-source-agreements
    $wingetExit = $LASTEXITCODE
    $ErrorActionPreference = $eap
    if ($wingetExit -eq 0 -or (Test-Command $check)) {
        $installed.Add($label)
    } else {
        $manual.Add("$label (winget exit $wingetExit; open a new shell or install manually)")
    }
}

function Install-NpmGlobal([string]$check, [string]$label, [string]$package) {
    if (Test-Command $check) {
        $skipped.Add("$label (already installed)")
        return
    }
    if (-not (Test-Command 'npm')) {
        $manual.Add("$label (needs npm first)")
        return
    }
    if ($DryRun) {
        Write-Host "[dry-run] npm install -g --ignore-scripts --no-audit --no-fund $package"
        return
    }
    Write-Host "+ npm install -g --ignore-scripts --no-audit --no-fund $package"
    $eap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    npm install -g --ignore-scripts --no-audit --no-fund $package
    $npmExit = $LASTEXITCODE
    $ErrorActionPreference = $eap
    if ($npmExit -eq 0) { $installed.Add($label) } else { $manual.Add("$label (npm exit $npmExit)") }
}

Write-Host "== LLM toolkit bootstrap (profile: $profileName) =="

# ---------- core tools (every profile) ----------

Install-WingetTool 'git' 'git' 'Git.Git'
Install-WingetTool 'node' 'Node.js' 'OpenJS.NodeJS.LTS'
Install-WingetTool 'python' 'Python 3' 'Python.Python.3.12'
Install-WingetTool 'jq' 'jq' 'jqlang.jq'
Install-WingetTool 'rg' 'ripgrep' 'BurntSushi.ripgrep.MSVC'
Install-WingetTool 'gh' 'GitHub CLI' 'GitHub.cli'

# ---------- recommended tools (default + full) ----------

if ($profileName -ne 'minimal') {
    Install-WingetTool 'aws' 'AWS CLI v2' 'Amazon.AWSCLI'
    Install-WingetTool 'mvn' 'Maven' 'Apache.Maven'
    # Token-efficiency tools (see skills/token-efficiency/SKILL.md)
    Install-WingetTool 'sg' 'ast-grep' 'ast-grep.ast-grep'
    Install-NpmGlobal 'repomix' 'repomix' 'repomix@1.18.0'
    if (Test-Command 'acli') {
        $skipped.Add('Atlassian CLI (already installed)')
    } else {
        $manual.Add('Atlassian CLI (acli) — install per https://developer.atlassian.com/cloud/acli/guides/install-acli/')
    }
    if (Test-Command 'slack') {
        $skipped.Add('Slack CLI (already installed)')
    } else {
        $manual.Add('Slack CLI — install manually if your workflow needs it (authentication remains interactive)')
    }
    # RTK: only the security-reviewed deployment is approved (rules/command-safety.md).
    # Never auto-install from public registries; never run 'rtk init'.
    if (Test-Command 'rtk') {
        $skipped.Add('rtk (already installed)')
    } else {
        $manual.Add('rtk — optional token optimizer; use the security-reviewed RTK deployment per rules/command-safety.md and skills/token-efficiency/SKILL.md')
    }
}

# ---------- docs/diagram extras (full only) ----------

if ($profileName -eq 'full') {
    Install-NpmGlobal 'mmdc' 'Mermaid CLI' '@mermaid-js/mermaid-cli@11.17.0'
    Install-WingetTool 'pandoc' 'Pandoc' 'JohnMacFarlane.Pandoc'
    Install-WingetTool 'typst' 'Typst' 'Typst.Typst'
    if (-not (Test-Command 'plantuml')) {
        $manual.Add('PlantUML — needs Java; download plantuml.jar from https://plantuml.com/download')
    }
}

# ---------- agent CLI (opt-in) ----------

switch ($Agent) {
    'claude' { Install-NpmGlobal 'claude' 'Claude Code' '@anthropic-ai/claude-code@2.1.261' }
    'codex' { Install-NpmGlobal 'codex' 'Codex CLI' '@openai/codex@0.153.4' }
    'gemini' { Install-NpmGlobal 'gemini' 'Gemini CLI' '@google/gemini-cli@0.58.0' }
    'all' {
        Install-NpmGlobal 'claude' 'Claude Code' '@anthropic-ai/claude-code@2.1.261'
        Install-NpmGlobal 'codex' 'Codex CLI' '@openai/codex@0.153.4'
        Install-NpmGlobal 'gemini' 'Gemini CLI' '@google/gemini-cli@0.58.0'
    }
}

# ---------- RTK privacy environment (approved Windows controls) ----------

if ((Test-Command 'rtk') -and -not $DryRun) {
    $rtkVars = @{ 'RTK_DB_PATH' = 'NUL'; 'RTK_TELEMETRY_DISABLED' = '1'; 'RTK_TEE' = '0' }
    foreach ($name in $rtkVars.Keys) {
        $current = [Environment]::GetEnvironmentVariable($name, 'User')
        if ($current -ne $rtkVars[$name]) {
            [Environment]::SetEnvironmentVariable($name, $rtkVars[$name], 'User')
            $installed.Add("RTK privacy env var $name=$($rtkVars[$name]) (User scope)")
        }
    }
}

# ---------- toolkit wiring ----------

if ($Consumer) {
    Write-Host "== Linking consumer repo: $Consumer =="
    if ($DryRun) {
        Write-Host "[dry-run] $scriptDir\setup-repo.ps1 $Consumer"
    } else {
        & "$scriptDir\setup-repo.ps1" $Consumer
    }
}

# ---------- report ----------

Write-Host ''
Write-Host '== Bootstrap summary =='
if ($installed.Count) { Write-Host 'Installed:'; $installed | ForEach-Object { Write-Host "  - $_" } }
if ($skipped.Count) { Write-Host 'Already present:'; $skipped | ForEach-Object { Write-Host "  - $_" } }
if ($manual.Count) { Write-Host 'Needs manual action:'; $manual | ForEach-Object { Write-Host "  - $_" } }

Write-Host @'

Next steps (interactive, run yourself):
  1. gh auth login                      # GitHub CLI authentication
  2. acli jira auth login               # Atlassian CLI auth (if installed)
  3. aws configure sso                  # AWS auth (if your team uses AWS)
  4. slack login                        # Slack CLI auth (if installed and needed)
  5. Pick your agent surface:
     - Claude Code:  run 'claude' in any linked repo (CLAUDE.md -> AGENTS.md)
     - Cursor/Windsurf: open the repo; rules/workflows load from .cursor/.windsurf
     - Codex CLI:    run 'codex' (AGENTS.md is the primary surface)
     - Gemini CLI:   run 'gemini' (.gemini/skills compatibility link)
     - VS Code Copilot: .github/copilot-instructions.md is generated on sync
  6. Link your project repo (if not done): ./scripts/setup-repo.ps1 C:\path\to\repo
  7. Validate the toolkit:               npm run validate; ./scripts/security-check-toolkit.ps1

Windows symlink note: directory links may require Developer Mode or an elevated
shell; setup-repo.ps1 falls back to junctions where possible.

Never run 'rtk init' or enable RTK hooks/telemetry/tee/audit logging; RTK stays
an explicit per-command proxy (see rules/command-safety.md and
skills/token-efficiency/SKILL.md).
'@
