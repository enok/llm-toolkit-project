#Requires -Version 5.1
<#
.SYNOPSIS
  Ensure directory symlinks to toolkit are correct (repair if needed).
.DESCRIPTION
  Mirrors scripts/ensure-symlinks.sh. Verifies .agents, .windsurf, .cursor, etc. point at toolkit.
.PARAMETER ConsumerPath
  Path to the consumer repo (default: current directory).
.PARAMETER Force
  Replace blocking paths (wrong symlinks or copied folders).
.PARAMETER Pull
  Run git pull in toolkit before checking.
.EXAMPLE
  .\scripts\ensure-symlinks.ps1 . -Force
#>
param(
    [Parameter(Position = 0)]
    [string]$ConsumerPath = '.',
    [switch]$Force,
    [switch]$Pull
)

$ErrorActionPreference = 'Stop'

$ScriptDir = $PSScriptRoot
$ToolkitRoot = Split-Path -Parent $ScriptDir

. "$ScriptDir\lib.ps1"

$Consumer = Resolve-ToolkitAbsolutePath $ConsumerPath

# Optional: pull latest toolkit first
if ($Pull -and (Test-Path (Join-Path $ToolkitRoot '.git') -PathType Container)) {
    Write-Host "Pulling latest toolkit changes..."
    try {
        Push-Location $ToolkitRoot
        git pull
        Pop-Location
    }
    catch {
        Write-Warning "git pull failed, continuing..."
        Pop-Location
    }
}

Write-Host "Ensuring symlinks for: $Consumer"
Write-Host "Toolkit root: $ToolkitRoot"
Write-Host ''

# Ensure toolkit layouts first
Ensure-ToolkitWindsurfLayout -DevToolsRoot $ToolkitRoot -AllowRepair:$Force
Ensure-ToolkitSetupLayout -DevToolsRoot $ToolkitRoot -AllowRepair:$Force

# Define links to verify/create
$links = @(
    @{ Name = '.agents'; Target = Join-Path $ToolkitRoot '.agents' }
    @{ Name = '.windsurf'; Target = Join-Path $ToolkitRoot '.windsurf' }
    @{ Name = '.setup'; Target = Join-Path $ToolkitRoot '.setup' }
)

if (Test-Path (Join-Path $ToolkitRoot '.cursor') -PathType Container) {
    $links += @{ Name = '.cursor'; Target = Join-Path $ToolkitRoot '.cursor' }
}
if (Test-Path (Join-Path $ToolkitRoot '.claude') -PathType Container) {
    $links += @{ Name = '.claude'; Target = Join-Path $ToolkitRoot '.claude' }
}
if (Test-Path (Join-Path $ToolkitRoot '.codex') -PathType Container) {
    $links += @{ Name = '.codex'; Target = Join-Path $ToolkitRoot '.codex' }
}

$errors = 0
foreach ($entry in $links) {
    $linkPath = Join-Path $Consumer $entry.Name
    $target = $entry.Target

    if (-not (Test-Path $target)) {
        Write-Host "Skipping $($entry.Name): target not found ($target)"
        continue
    }

    try {
        $result = Ensure-ToolkitDirectoryLink -LinkPath $linkPath -TargetPath $target -AllowRepair:$Force
        Write-Host "  OK: $($entry.Name) ($result)"
    }
    catch {
        Write-Host "  FAIL: $($entry.Name) - $_"
        $errors++
    }
}

Write-Host ''
if ($errors -eq 0) {
    Write-Host "Done. All symlinks are correct."
}
else {
    Write-Warning "$errors symlink(s) could not be verified/created. Run with -Force to replace blocking paths."
    exit 1
}
