#Requires -Version 5.1
param(
    [switch]$SkipCursorRules,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $scriptDir '..')).Path
function Get-ResolvedLinkTarget {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }

    $item = Get-Item -LiteralPath $Path -Force
    $rawTarget = $item.Target
    if ($rawTarget -is [System.Array] -and $rawTarget.Length -gt 0) {
        $rawTarget = $rawTarget[0]
    }

    if (-not [string]::IsNullOrWhiteSpace([string]$rawTarget)) {
        $target = [string]$rawTarget
        if (-not [System.IO.Path]::IsPathRooted($target)) {
            $target = Join-Path (Split-Path -Parent $Path) $target
        }
        return (Resolve-Path -LiteralPath $target).Path
    }

    return (Resolve-Path -LiteralPath $Path).Path
}

function Test-ToolkitRoot {
    param([Parameter(Mandatory)][string]$Path)
    return (Test-Path -LiteralPath (Join-Path $Path 'scripts\sync-tool-configs.ps1'))
}

function Resolve-ToolkitRoot {
    $agentsTarget = Get-ResolvedLinkTarget -Path (Join-Path $repoRoot '.agents')
    if ($agentsTarget) {
        $candidate = Split-Path -Parent $agentsTarget
        if (Test-ToolkitRoot -Path $candidate) { return $candidate }
    }

    foreach ($skillsRoot in @(
            (Join-Path $repoRoot '.agents\skills'),
            (Join-Path $repoRoot '.agent\skills'),
            (Join-Path $repoRoot '.claude\skills'),
            (Join-Path $repoRoot '.codex\skills'),
            (Join-Path $repoRoot '.cursor\skills'),
            (Join-Path $repoRoot '.gemini\skills'),
            (Join-Path $repoRoot '.opencode\skills'),
            (Join-Path $repoRoot '.windsurf\skills')
        )) {
        $skillsTarget = Get-ResolvedLinkTarget -Path $skillsRoot
        if ($skillsTarget) {
            $candidate = Split-Path -Parent $skillsTarget
            if (Test-ToolkitRoot -Path $candidate) { return $candidate }
        }

        if (Test-Path -LiteralPath $skillsRoot -PathType Container) {
            $firstSkill = Get-ChildItem -LiteralPath $skillsRoot -Directory -Force | Sort-Object Name | Select-Object -First 1
            if ($firstSkill) {
                $skillTarget = Get-ResolvedLinkTarget -Path $firstSkill.FullName
                if ($skillTarget) {
                    $candidate = Split-Path -Parent (Split-Path -Parent $skillTarget)
                    if (Test-ToolkitRoot -Path $candidate) { return $candidate }
                }
            }
        }
    }

    throw 'Could not resolve toolkit root from linked shared skill paths. Re-run toolkit setup or ensure-symlinks first.'
}

$toolkitRoot = Resolve-ToolkitRoot
$syncScript = Join-Path $toolkitRoot 'scripts\sync-tool-configs.ps1'

if (-not (Test-Path -LiteralPath $syncScript)) {
    throw "Toolkit sync script not found at $syncScript"
}

$syncParams = @{ ProjectPath = $repoRoot }
if ($SkipCursorRules) {
    $syncParams.SkipCursorRules = $true
}
if ($Force) {
    $syncParams.Force = $true
}

& $syncScript @syncParams
