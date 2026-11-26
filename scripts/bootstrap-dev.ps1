# First-time developer bootstrap for the LLM toolkit toolkit (Windows).
# Installs required binaries/CLIs via winget, optional tooling, and an agent CLI
# of choice, then wires the toolkit so any LLM agent (Claude Code, Cursor,
# Windsurf, Codex, Gemini CLI, Copilot) can use it. npm-based tools are
# exact-version pinned and installed without lifecycle scripts.
#
# POSIX/Git Bash: scripts/bootstrap-dev.sh - same behavior via brew/apt/dnf.
#
# Usage: ./scripts/bootstrap-dev.ps1 [-Minimal] [-Full] [-Agent claude|codex|gemini|all]
#                                    [-Consumer <path>] [-NoKb] [-KbDataDir <path>]
#                                    [-SecurityTools] [-Rtk] [-DryRun]
#
# Opt-in switches (both off by default):
#   -SecurityTools  Installs the security-check toolchain: winget shellcheck, actionlint,
#                   hadolint, syft, grype, trivy, gitleaks, osv-scanner; pip (user scope)
#                   semgrep, yamllint, pip-audit, checkov, skillspector==2.13.7;
#                   PSScriptAnalyzer via Install-Module. trufflehog has no winget package
#                   and is listed under manual actions.
#   -Rtk            Installs only the reviewed RTK 1.2.1 (winget --exact, then winget pin
#                   add). See skills/token-efficiency/references/rtk-reviewed-deployment.md.
#                   Without -Rtk, an existing rtk is only given the privacy environment.
#
# The knowledge-base step (scripts/kb.py init, up --build, index, schedule install)
# runs after the tool installs unless -Minimal or -NoKb is given; -KbDataDir sets
# the data folder. It needs Docker with compose; without it the step prints the
# command to run later and the bootstrap still succeeds. The prompt hook is never
# installed here (opt-in: kb.py hook install).
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
    [switch]$NoKb,
    [string]$KbDataDir,
    [switch]$SecurityTools,
    [switch]$Rtk,
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

function Install-PipTool([string]$check, [string]$label, [string]$spec) {
    if (Test-Command $check) {
        $skipped.Add("$label (already installed)")
        return
    }
    $pipCmd = if (Test-Command 'pip') { 'pip' } elseif (Test-Command 'pip3') { 'pip3' } else { $null }
    if (-not $pipCmd) {
        $manual.Add("$label (needs pip first: pip install --user $spec)")
        return
    }
    if ($DryRun) {
        Write-Host "[dry-run] $pipCmd install --user $spec"
        return
    }
    Write-Host "+ $pipCmd install --user $spec"
    $eap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & $pipCmd install --user $spec
    $pipExit = $LASTEXITCODE
    $ErrorActionPreference = $eap
    if ($pipExit -eq 0) { $installed.Add($label) } else { $manual.Add("$label (pip exit $pipExit)") }
}

$rtkReviewedVersion = '1.2.1'

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
    if (Test-Command 'mvn') {
        $skipped.Add('Maven (already installed)')
    } else {
        $manual.Add('Maven — no winget package; download from https://maven.apache.org/download.cgi and add bin to PATH')
    }
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
        $manual.Add('rtk — optional token optimizer; run with -Rtk or follow skills/token-efficiency/references/rtk-reviewed-deployment.md')
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

# ---------- security-check toolchain (opt-in: -SecurityTools) ----------

if ($SecurityTools) {
    Write-Host '== Security tools =='
    Install-WingetTool 'shellcheck' 'shellcheck' 'koalaman.shellcheck'
    Install-WingetTool 'actionlint' 'actionlint' 'rhysd.actionlint'
    Install-WingetTool 'hadolint' 'hadolint' 'hadolint.hadolint'
    Install-WingetTool 'syft' 'Syft' 'Anchore.Syft'
    Install-WingetTool 'grype' 'Grype' 'Anchore.Grype'
    Install-WingetTool 'trivy' 'Trivy' 'AquaSecurity.Trivy'
    Install-WingetTool 'gitleaks' 'Gitleaks' 'Gitleaks.Gitleaks'
    Install-WingetTool 'osv-scanner' 'OSV-Scanner' 'Google.OSVScanner'
    Install-PipTool 'semgrep' 'semgrep' 'semgrep'
    Install-PipTool 'yamllint' 'yamllint' 'yamllint'
    Install-PipTool 'pip-audit' 'pip-audit' 'pip-audit'
    Install-PipTool 'checkov' 'checkov' 'checkov'
    Install-PipTool 'skillspector' 'skillspector' 'skillspector==2.13.7'
    if (Get-Module -ListAvailable -Name PSScriptAnalyzer) {
        $skipped.Add('PSScriptAnalyzer (already installed)')
    } elseif ($DryRun) {
        Write-Host '[dry-run] Install-Module PSScriptAnalyzer -Scope CurrentUser'
    } else {
        Write-Host '+ Install-Module PSScriptAnalyzer -Scope CurrentUser'
        try {
            Install-Module PSScriptAnalyzer -Scope CurrentUser -Force -ErrorAction Stop
            $installed.Add('PSScriptAnalyzer')
        } catch {
            $manual.Add('PSScriptAnalyzer (Install-Module failed; install manually)')
        }
    }
    $manual.Add('trufflehog — no winget package; install from its GitHub release if needed')
}

# ---------- reviewed RTK (opt-in: -Rtk) ----------

if ($Rtk) {
    Write-Host '== RTK (reviewed version only) =='
    $rtkVersionOk = $false
    if (Test-Command 'rtk') {
        $rtkOut = (& rtk --version 2>&1 | Out-String)
        if ($rtkOut -match [regex]::Escape($rtkReviewedVersion)) {
            $rtkVersionOk = $true
            $skipped.Add("rtk $rtkReviewedVersion (already installed)")
        } else {
            $manual.Add("rtk is installed but is not the reviewed $rtkReviewedVersion ($($rtkOut.Trim())); replace it with the reviewed version before use")
        }
    }
    if (-not $rtkVersionOk -and -not (Test-Command 'rtk')) {
        if (-not (Test-Command 'winget')) {
            $manual.Add("rtk $rtkReviewedVersion — winget unavailable; install the reviewed version manually")
        } elseif ($DryRun) {
            Write-Host "[dry-run] winget install --id rtk-ai.rtk --version $rtkReviewedVersion --exact"
            Write-Host "[dry-run] winget pin add --id rtk-ai.rtk --version $rtkReviewedVersion"
        } else {
            Write-Host "+ winget install --id rtk-ai.rtk --version $rtkReviewedVersion --exact"
            $eap = $ErrorActionPreference
            $ErrorActionPreference = 'Continue'
            winget install --id rtk-ai.rtk --version $rtkReviewedVersion --exact --silent --accept-package-agreements --accept-source-agreements
            $rtkExit = $LASTEXITCODE
            if ($rtkExit -eq 0) {
                winget pin add --id rtk-ai.rtk --version $rtkReviewedVersion
                $installed.Add("rtk $rtkReviewedVersion (pinned)")
                $manual.Add('rtk: open a new shell, verify the installer SHA-256 against the release checksums.txt, then run the smoke test in skills/token-efficiency/references/rtk-reviewed-deployment.md')
            } else {
                $manual.Add("rtk $rtkReviewedVersion (winget exit $rtkExit; install manually)")
            }
            $ErrorActionPreference = $eap
        }
    }
}

# ---------- RTK privacy environment (approved Windows controls) ----------

if (((Test-Command 'rtk') -or $Rtk) -and -not $DryRun) {
    $rtkVars = [ordered]@{
        'RTK_DB_PATH' = 'NUL'; 'RTK_TELEMETRY_DISABLED' = '1'; 'RTK_TEE' = '0'
        'RTK_RECALL' = '0'; 'RTK_SUPPRESS_HOOK_WARNING' = '1'
    }
    foreach ($name in $rtkVars.Keys) {
        $current = [Environment]::GetEnvironmentVariable($name, 'User')
        if ($current -ne $rtkVars[$name]) {
            [Environment]::SetEnvironmentVariable($name, $rtkVars[$name], 'User')
            $installed.Add("RTK privacy env var $name=$($rtkVars[$name]) (User scope)")
        }
    }
}

# ---------- knowledge base (default + full; skipped by -Minimal or -NoKb) ----------

if ($profileName -ne 'minimal' -and -not $NoKb) {
    Write-Host '== Knowledge base =='
    $kbPy = Join-Path $scriptDir 'kb.py'
    $kbInit = @('init')
    if ($KbDataDir) { $kbInit += @('--data-dir', $KbDataDir) }
    $kbSteps = @(
        $kbInit,
        @('up', '--build'),
        @('index'),
        @('schedule', 'install')
    )
    # Interpreter: py -3, then python, then python3 (first one found).
    $kbPython = $null
    if (Test-Command 'py') { $kbPython = @('py', '-3') }
    elseif (Test-Command 'python') { $kbPython = @('python') }
    elseif (Test-Command 'python3') { $kbPython = @('python3') }
    function ConvertTo-QuotedArg([string]$text) { return "'" + $text.Replace("'", "''") + "'" }
    $kbPyShown = if ($kbPython) { $kbPython -join ' ' } else { 'python' }
    # One PowerShell-5.1-safe line: commands joined with '; ', paths single-quoted.
    $kbLater = ($kbSteps | ForEach-Object {
        "$kbPyShown $(ConvertTo-QuotedArg $kbPy) " + (($_ | ForEach-Object { ConvertTo-QuotedArg $_ }) -join ' ')
    }) -join '; '
    $dockerReady = $false
    if (-not $DryRun -and $kbPython -and (Test-Command 'docker')) {
        $eap = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        docker compose version *> $null
        $composeExit = $LASTEXITCODE
        docker info *> $null
        $infoExit = $LASTEXITCODE
        $ErrorActionPreference = $eap
        $dockerReady = ($composeExit -eq 0 -and $infoExit -eq 0)
    }
    if ($DryRun) {
        foreach ($step in $kbSteps) { Write-Host "[dry-run] $kbPyShown $kbPy $($step -join ' ')" }
    } elseif (-not $kbPython) {
        Write-Host "Knowledge base skipped: python3 is missing. Run later: $kbLater"
        $manual.Add('Knowledge base (needs python3 first)')
    } elseif (-not $dockerReady) {
        Write-Host "Knowledge base skipped: Docker with compose is missing or its daemon is not running. Run later: $kbLater"
        $manual.Add('Knowledge base (start Docker, then run the command printed above)')
    } else {
        $kbOk = $true
        foreach ($step in $kbSteps) {
            Write-Host "+ $kbPyShown $kbPy $($step -join ' ')"
            $eap = $ErrorActionPreference
            $ErrorActionPreference = 'Continue'
            & $kbPython[0] @($kbPython | Select-Object -Skip 1) $kbPy @step
            $stepExit = $LASTEXITCODE
            $ErrorActionPreference = $eap
            if ($stepExit -ne 0) { $kbOk = $false; break }
        }
        if ($kbOk) {
            $installed.Add('Knowledge base (indexed; scheduled sync installed)')
        } else {
            Write-Host "Knowledge base step failed. Run later: $kbLater"
            $manual.Add('Knowledge base (a kb.py step failed; see output above)')
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
  8. Knowledge base status:              python scripts/kb.py status
     Optional prompt hook (explicit opt-in, never installed by this script):
                                         python scripts/kb.py hook install

Windows symlink note: directory links may require Developer Mode or an elevated
shell; setup-repo.ps1 falls back to junctions where possible.

Never run 'rtk init' or enable RTK hooks/telemetry/tee/audit logging; RTK stays
an explicit per-command proxy (see rules/command-safety.md and
skills/token-efficiency/SKILL.md).
'@
