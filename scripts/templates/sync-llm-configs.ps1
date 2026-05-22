# Consumer-local wrapper: refresh shared tool surfaces and local exports.
# Run from the consumer repo root: .\scripts\sync-llm-configs.ps1

$ErrorActionPreference = 'Stop'

$ScriptDir = $PSScriptRoot
$Consumer = Split-Path -Parent $ScriptDir

# Find the toolkit by resolving .agents/skills. This works whether .agents is
# a root link to the toolkit or a real directory with a nested skills link.
$Toolkit = $null
$AgentsSkillsLink = Join-Path $Consumer '.agents\skills'
if (Test-Path -LiteralPath $AgentsSkillsLink) {
    try {
        $item = Get-Item -LiteralPath $AgentsSkillsLink
        $Resolved = if ($item.Target) { $item.Target } else { $item.FullName }
        if ($Resolved) {
            $Toolkit = Split-Path -Parent $Resolved
        }
    }
    catch {
        # Not a link or can't resolve
    }
}

if (-not $Toolkit) {
    $AgentsLink = Join-Path $Consumer '.agents'
    if (Test-Path -LiteralPath $AgentsLink) {
        try {
            $item = Get-Item -LiteralPath $AgentsLink
            $Resolved = if ($item.Target) { $item.Target } else { $item.FullName }
            if ($Resolved) {
                $Toolkit = Split-Path -Parent $Resolved
            }
        }
        catch {
            # Not a link or can't resolve
        }
    }
}

if (-not $Toolkit -or -not (Test-Path (Join-Path $Toolkit 'scripts\sync-tool-configs.sh'))) {
    Write-Error "Could not locate toolkit sync-tool-configs.sh. Ensure .agents/ is symlinked to the toolkit."
}

$ToolkitScript = Join-Path $Toolkit 'scripts\sync-tool-configs.sh'

# Convert paths for Git Bash
function Convert-ToUnixPath {
    param([string]$Path)
    $full = (Resolve-Path -LiteralPath $Path).Path
    if ($full -match '^([A-Za-z]):\\') {
        $d = $Matches[1].ToLower()
        $tail = $full.Substring(3) -replace '\\', '/'
        return "/$d/$tail"
    }
    return $full -replace '\\', '/'
}

# Find Git Bash
$GitBash = $null
foreach ($p in @(
        "${env:ProgramFiles}\Git\bin\bash.exe",
        "${env:ProgramFiles(x86)}\Git\bin\bash.exe"
    )) {
    if (Test-Path -LiteralPath $p) { $GitBash = $p; break }
}

if (-not $GitBash) {
    Write-Error "Git Bash not found. Install Git for Windows."
}

$cUnix = Convert-ToUnixPath $Consumer
$sUnix = Convert-ToUnixPath $ToolkitScript

$bashArgs = @("-lc", "'$sUnix' '$cUnix' $args")
& $GitBash @bashArgs
