#Requires -Version 5.1
<#
.SYNOPSIS
  Refresh directory links (mklink /J, then mklink /d fallback) for skills, provider compatibility paths, rules, and workflows in a consumer repo.
.DESCRIPTION
  Mirrors scripts/ensure-symlinks.sh. Use -Pull / --pull and a consumer path (default .). Use -Force to replace blocking paths with the expected toolkit links.
.EXAMPLE
  .\scripts\ensure-symlinks.ps1 .
  .\scripts\ensure-symlinks.ps1 . -Pull
  .\scripts\ensure-symlinks.ps1 --pull .
  .\scripts\ensure-symlinks.ps1 C:\work\my-app -Pull -Force
#>
[CmdletBinding()]
param(
    [switch]$Pull,
    [switch]$Force,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArguments
)

$ErrorActionPreference = 'Stop'

$ScriptDir = $PSScriptRoot
$ToolkitRoot = Split-Path -Parent $ScriptDir

. "$ScriptDir\lib.ps1"

function Ensure-ConsumerDirectory {
    param([Parameter(Mandatory)][string]$Path)

    if (Test-Path -LiteralPath $Path) {
        $item = Get-Item -LiteralPath $Path -Force
        if ($item.PSIsContainer -and -not $item.LinkType) {
            return
        }
        if (-not $Force) {
            throw "Blocking link/file exists at $Path. Remove it manually, or rerun with -Force to replace it with a directory for per-path toolkit links."
        }
        Remove-ToolkitPathSafely -Path $Path
    }
    New-Item -ItemType Directory -Path $Path -Force | Out-Null
}

function Ensure-SharedSkillCatalogLinks {
    param(
        [Parameter(Mandatory)][string]$SkillsRoot,
        [Parameter(Mandatory)][string]$Label
    )

    $skillsSourceRoot = Join-Path $ToolkitRoot 'skills'
    Ensure-ConsumerDirectory -Path $SkillsRoot
    Get-ChildItem -LiteralPath $skillsSourceRoot -Directory |
        Sort-Object Name |
        ForEach-Object {
            $target = Join-Path $SkillsRoot $_.Name
            $null = Ensure-ToolkitDirectoryLink -LinkPath $target -TargetPath $_.FullName -AllowRepair:$Force
        }
    Write-Host $Label
}

$ConsumerPath = '.'
foreach ($a in @($RemainingArguments | ForEach-Object { $_ })) {
    if (-not $a) { continue }
    switch -Exact ($a) {
        '--pull' { $Pull = $true }
        '--force' { $Force = $true }
        '-Pull' { $Pull = $true }
        '-Force' { $Force = $true }
        default {
            if ($a -notmatch '^-') { $ConsumerPath = $a }
        }
    }
}

if (-not (Test-Path -LiteralPath "$ToolkitRoot\skills" -PathType Container) -and -not (Test-Path -LiteralPath "$ToolkitRoot\.agents\skills" -PathType Container)) {
    Write-Error "toolkit root not found (expected skills/ at $ToolkitRoot)"
}

if (-not (Test-Path -LiteralPath $ConsumerPath -PathType Container)) {
    Write-Error "consumer path is not a directory: $ConsumerPath"
}

$Consumer = Resolve-ToolkitAbsolutePath $ConsumerPath
$ToolkitRootResolved = Resolve-ToolkitAbsolutePath $ToolkitRoot
$IsToolkitRepo = ($Consumer -eq $ToolkitRootResolved)

if ($Pull) {
    Push-Location $ToolkitRoot
    try {
        Write-ToolkitExecLine "Push-Location '$ToolkitRoot'; git pull --ff-only; Pop-Location"
        & git pull --ff-only
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "git pull --ff-only exited with code $LASTEXITCODE (continuing)."
        }
    }
    finally {
        Pop-Location
    }
}

Ensure-ToolkitWindsurfLayout -ToolkitRoot $ToolkitRoot -AllowRepair:$Force

if ($IsToolkitRepo) {
    Write-Host 'Toolkit repo: skipping per-skill provider links; sync-tool-configs.sh repairs catalog junctions.'
}
else {
    # ── 1. Shared skills and provider roots, linked by subpath ───────────────────
    $consumerAgentsRoot = Join-Path $Consumer '.agents'
    Ensure-ConsumerDirectory -Path $consumerAgentsRoot
    Ensure-SharedSkillCatalogLinks -SkillsRoot (Join-Path $consumerAgentsRoot 'skills') -Label 'Skills: .agents/skills/<name> -> toolkit/skills/<name>'

    $consumerAntigravityRoot = Join-Path $Consumer '.agent'
    Ensure-ConsumerDirectory -Path $consumerAntigravityRoot
    Ensure-SharedSkillCatalogLinks -SkillsRoot (Join-Path $consumerAntigravityRoot 'skills') -Label 'Antigravity: .agent/skills/<name> -> toolkit/skills/<name>'

    $consumerClaudeRoot = Join-Path $Consumer '.claude'
    Ensure-ConsumerDirectory -Path $consumerClaudeRoot
    Ensure-SharedSkillCatalogLinks -SkillsRoot (Join-Path $consumerClaudeRoot 'skills') -Label 'Claude Code: .claude/skills/<name> -> toolkit/skills/<name>'
    $toolkitAgents = Join-Path $ToolkitRoot 'tool-subagents'
    if (Test-Path -LiteralPath $toolkitAgents -PathType Container) {
        $null = Ensure-ToolkitDirectoryLink -LinkPath (Join-Path $consumerClaudeRoot 'agents') -TargetPath $toolkitAgents -AllowRepair:$Force
    }

    $consumerCodexRoot = Join-Path $Consumer '.codex'
    Ensure-ConsumerDirectory -Path $consumerCodexRoot
    Ensure-SharedSkillCatalogLinks -SkillsRoot (Join-Path $consumerCodexRoot 'skills') -Label 'Codex: .codex/skills/<name> -> toolkit/skills/<name>'
    if (Test-Path -LiteralPath $toolkitAgents -PathType Container) {
        $null = Ensure-ToolkitDirectoryLink -LinkPath (Join-Path $consumerCodexRoot 'agents') -TargetPath $toolkitAgents -AllowRepair:$Force
    }

    $consumerWindsurfRoot = Join-Path $Consumer '.windsurf'
    Ensure-ConsumerDirectory -Path $consumerWindsurfRoot
    $null = Ensure-ToolkitDirectoryLink -LinkPath (Join-Path $consumerWindsurfRoot 'rules') -TargetPath (Join-Path $ToolkitRoot 'rules') -AllowRepair:$Force
    $null = Ensure-ToolkitDirectoryLink -LinkPath (Join-Path $consumerWindsurfRoot 'workflows') -TargetPath (Join-Path $ToolkitRoot 'workflows') -AllowRepair:$Force
    Ensure-SharedSkillCatalogLinks -SkillsRoot (Join-Path $consumerWindsurfRoot 'skills') -Label 'Windsurf: .windsurf/skills/<name> -> toolkit/skills/<name>'

    $consumerCursorRoot = Join-Path $Consumer '.cursor'
    Ensure-ConsumerDirectory -Path $consumerCursorRoot
    Ensure-SharedSkillCatalogLinks -SkillsRoot (Join-Path $consumerCursorRoot 'skills') -Label 'Cursor: .cursor/skills/<name> -> toolkit/skills/<name>'
    if (Test-Path -LiteralPath $toolkitAgents -PathType Container) {
        $null = Ensure-ToolkitDirectoryLink -LinkPath (Join-Path $consumerCursorRoot 'agents') -TargetPath $toolkitAgents -AllowRepair:$Force
    }
    Write-Host '.cursor root ready; shared rules/workflows refresh during sync'

    $consumerGeminiRoot = Join-Path $Consumer '.gemini'
    Ensure-ConsumerDirectory -Path $consumerGeminiRoot
    Ensure-SharedSkillCatalogLinks -SkillsRoot (Join-Path $consumerGeminiRoot 'skills') -Label 'Gemini CLI: .gemini/skills/<name> -> toolkit/skills/<name>'

    $consumerOpenCodeRoot = Join-Path $Consumer '.opencode'
    Ensure-ConsumerDirectory -Path $consumerOpenCodeRoot
    Ensure-SharedSkillCatalogLinks -SkillsRoot (Join-Path $consumerOpenCodeRoot 'skills') -Label 'OpenCode: .opencode/skills/<name> -> toolkit/skills/<name>'

    $toolkitLearningsRoot = Join-Path $ToolkitRoot 'learnings'
    $consumerLearningsRoot = Join-Path $Consumer 'learnings'
    if (Test-Path -LiteralPath $toolkitLearningsRoot -PathType Container) {
        $stLearnings = Ensure-ToolkitDirectoryLink -LinkPath $consumerLearningsRoot -TargetPath $toolkitLearningsRoot -AllowRepair:$Force
        Write-Host "learnings -> toolkit/learnings ($stLearnings)"
    }
    else {
        Write-Warning 'Toolkit learnings/ not found; skipped consumer learnings link.'
    }
}

$syncOk = Invoke-ToolkitSyncToolConfigs -ConsumerPath $Consumer -ScriptDir $ScriptDir -Force:$Force -SkipAgentsMd:$IsToolkitRepo
if (-not $syncOk) {
    throw 'sync-tool-configs.sh failed. Shared tool symlinks or local exports may be stale. Fix the issue and re-run, or run sync-tool-configs.sh from Git Bash.'
}

# Mark link-surface directories skip-worktree to prevent git checkout conflicts
if (-not $IsToolkitRepo) {
    Push-Location $Consumer
    try {
        $linkPaths = @(
            '.agents/skills',
            '.claude/agents',
            '.claude/skills',
            '.codex/skills',
            '.cursor/agents',
            '.cursor/rules',
            '.cursor/workflows',
            '.windsurf/rules',
            '.windsurf/skills',
            '.windsurf/workflows'
        )
        # Only mark paths that exist in the index
        $existingPaths = @()
        foreach ($p in $linkPaths) {
            $gitLsOutput = & git ls-files $p 2>$null
            if ($LASTEXITCODE -eq 0 -and $gitLsOutput) {
                $existingPaths += $p
            }
        }
        if ($existingPaths.Count -gt 0) {
            Write-Host "Marking link surfaces skip-worktree: $($existingPaths -join ', ')"
            & git update-index --skip-worktree @existingPaths 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "git update-index --skip-worktree failed (exit $LASTEXITCODE); continuing."
            }
        }
    }
    finally {
        Pop-Location
    }
}

Write-Host 'Integration refresh complete.'
