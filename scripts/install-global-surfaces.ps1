#Requires -Version 5.1
<#
.SYNOPSIS
  Install the shared LLM toolkit as the global (home-directory) skills,
  agents, and instruction surface for every LLM tool on this machine.
.DESCRIPTION
  Canonical sources stay in this repository (skills/, tool-subagents/);
  this script only links user-level tool directories back to them and
  writes a managed instruction block into each tool's global instruction
  file. It never copies shared content and never edits text outside the
  managed block markers.

  Default mode is a dry-run: it prints the plan and changes nothing on
  disk. Pass -Apply to create/update the links and managed blocks.

  Exit status: non-zero only when -Apply hits at least one blocked path
  (an existing non-link path with -Force not given). A dry-run always
  exits 0.
.PARAMETER Apply
  Apply changes. Default is a dry-run (plan only).
.PARAMETER Tools
  claude, codex, cursor, windsurf, gemini, opencode, antigravity, all, or
  auto (default: only tools whose home directory already exists).
  Accepts a comma-separated list.
.PARAMETER Force
  Replace a blocking non-link path after backing it up to
  <path>.bak-<yyyyMMddHHmmss>.
.PARAMETER ToolkitRoot
  Toolkit repository root. Default: the repo root containing this script.
.PARAMETER HomeDir
  Home directory to install into (alias -Home). Default: the current
  user's home directory. Use this to test against a scratch directory.
.EXAMPLE
  .\scripts\install-global-surfaces.ps1
.EXAMPLE
  .\scripts\install-global-surfaces.ps1 -Apply -Tools claude,codex
.EXAMPLE
  .\scripts\install-global-surfaces.ps1 -Apply -Force
.EXAMPLE
  .\scripts\install-global-surfaces.ps1 -Home C:\Temp\fakehome -Tools all -Apply
#>
[CmdletBinding()]
param(
    [switch]$Apply,
    [string[]]$Tools = @('auto'),
    [switch]$Force,
    [string]$ToolkitRoot,
    [Alias('Home')]
    [string]$HomeDir
)

$ErrorActionPreference = 'Stop'

$BeginMark = '<!-- BEGIN LLM-TOOLKIT GLOBAL -->'
$EndMark = '<!-- END LLM-TOOLKIT GLOBAL -->'
$AllTools = @('claude', 'codex', 'cursor', 'windsurf', 'gemini', 'opencode', 'antigravity')
$BackupTimestamp = Get-Date -Format 'yyyyMMddHHmmss'

$IsWindowsPlatform = $true
if ($PSVersionTable.PSVersion.Major -ge 6) {
    $IsWindowsPlatform = [bool]$IsWindows
}

# ---------------------------------------------------------------------------
# Resolve arguments
# ---------------------------------------------------------------------------

if (-not $ToolkitRoot) {
    $ToolkitRoot = Split-Path -Parent $PSScriptRoot
}
if (-not (Test-Path -LiteralPath $ToolkitRoot -PathType Container)) {
    throw "Toolkit root not found: $ToolkitRoot"
}
$ToolkitRoot = (Resolve-Path -LiteralPath $ToolkitRoot).Path.TrimEnd('\', '/')

if (-not $HomeDir) {
    $HomeDir = $HOME
}
if (-not $HomeDir -or -not (Test-Path -LiteralPath $HomeDir -PathType Container)) {
    throw "Home directory not found: '$HomeDir' (pass -Home <path>)"
}
$HomeDir = (Resolve-Path -LiteralPath $HomeDir).Path.TrimEnd('\', '/')

$TemplateFile = Join-Path $ToolkitRoot 'scripts/templates/global-agent-directive.md'
if (-not (Test-Path -LiteralPath $TemplateFile -PathType Leaf)) {
    throw "Missing directive template: $TemplateFile"
}

function Test-ToolNameValid {
    param([Parameter(Mandatory)][string]$Name)
    return $AllTools -contains $Name
}

function Get-SelectedTool {
    param([Parameter(Mandatory)][AllowEmptyCollection()][string[]]$Requested)

    $flat = @()
    foreach ($item in $Requested) {
        foreach ($piece in ($item -split ',')) {
            $trimmed = $piece.Trim().ToLowerInvariant()
            if ($trimmed) { $flat += $trimmed }
        }
    }
    if ($flat.Count -eq 0) { $flat = @('auto') }

    if ($flat -contains 'all') {
        return $AllTools
    }
    if ($flat -contains 'auto') {
        $result = @()
        if (Test-Path -LiteralPath (Join-Path $HomeDir '.claude') -PathType Container) { $result += 'claude' }
        if (Test-Path -LiteralPath (Join-Path $HomeDir '.codex') -PathType Container) { $result += 'codex' }
        if (Test-Path -LiteralPath (Join-Path $HomeDir '.cursor') -PathType Container) { $result += 'cursor' }
        if (Test-Path -LiteralPath (Join-Path $HomeDir '.codeium/windsurf') -PathType Container) { $result += 'windsurf' }
        if (Test-Path -LiteralPath (Join-Path $HomeDir '.gemini') -PathType Container) { $result += 'gemini' }
        if (Test-Path -LiteralPath (Join-Path $HomeDir '.config/opencode') -PathType Container) { $result += 'opencode' }
        if (Test-Path -LiteralPath (Join-Path $HomeDir '.gemini/antigravity') -PathType Container) { $result += 'antigravity' }
        return $result
    }

    $result = @()
    foreach ($name in $flat) {
        if (-not (Test-ToolNameValid $name)) {
            throw "Unknown tool '$name' (expected one of: $($AllTools -join ', '), or auto/all)"
        }
        if ($result -notcontains $name) { $result += $name }
    }
    return $result
}

$SelectedTools = @(Get-SelectedTool -Requested $Tools)

# ---------------------------------------------------------------------------
# Result tracking / summary table
# ---------------------------------------------------------------------------

$script:ResultRows = New-Object System.Collections.Generic.List[object]
$script:BlockedCount = 0
$script:CursorSelected = $false
$script:CursorRulesText = ''

function Add-ResultRow {
    param(
        [Parameter(Mandatory)][string]$Tool,
        [Parameter(Mandatory)][string]$Surface,
        [Parameter(Mandatory)][string]$Action,
        [string]$Detail = ''
    )
    $script:ResultRows.Add([pscustomobject]@{
            Tool    = $Tool
            Surface = $Surface
            Action  = $Action
            Detail  = $Detail
        })
    if ($Action -eq 'blocked') {
        $script:BlockedCount++
    }
}

function Write-ResultTable {
    if ($script:ResultRows.Count -eq 0) {
        Write-Output '(no surfaces processed)'
        return
    }
    $wTool = [Math]::Max(4, ($script:ResultRows | ForEach-Object { $_.Tool.Length } | Measure-Object -Maximum).Maximum)
    $wSurface = [Math]::Max(7, ($script:ResultRows | ForEach-Object { $_.Surface.Length } | Measure-Object -Maximum).Maximum)
    $wAction = [Math]::Max(6, ($script:ResultRows | ForEach-Object { $_.Action.Length } | Measure-Object -Maximum).Maximum)
    $wDetail = [Math]::Max(6, ($script:ResultRows | ForEach-Object { $_.Detail.Length } | Measure-Object -Maximum).Maximum)

    $fmt = "{0,-$wTool}  {1,-$wSurface}  {2,-$wAction}  {3,-$wDetail}"
    Write-Output ($fmt -f 'TOOL', 'SURFACE', 'ACTION', 'DETAIL')
    Write-Output ($fmt -f ('-' * 4), ('-' * 7), ('-' * 6), ('-' * 6))
    foreach ($row in $script:ResultRows) {
        Write-Output ($fmt -f $row.Tool, $row.Surface, $row.Action, $row.Detail)
    }
}

# ---------------------------------------------------------------------------
# Link surfaces (directory junction on Windows, symlink elsewhere)
# ---------------------------------------------------------------------------

function Get-FullPathSafe {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Path)
    if ([string]::IsNullOrEmpty($Path)) { return $Path }
    try {
        return [System.IO.Path]::GetFullPath($Path.TrimEnd('\', '/'))
    }
    catch {
        return $Path.TrimEnd('\', '/')
    }
}

function Get-LinkTargetCanonical {
    param([Parameter(Mandatory)][string]$LinkPath)
    if (-not (Test-Path -LiteralPath $LinkPath)) { return $null }
    $item = Get-Item -LiteralPath $LinkPath -Force
    if (-not $item.LinkType) { return $null }
    $raw = $item.Target
    if ($raw -is [System.Array]) {
        if ($raw.Length -eq 0) { return $null }
        $raw = $raw[0]
    }
    if ([string]::IsNullOrWhiteSpace([string]$raw)) { return $null }
    $targetPath = [string]$raw
    if (-not [System.IO.Path]::IsPathRooted($targetPath)) {
        $targetPath = Join-Path (Split-Path -Parent $LinkPath) $targetPath
    }
    return Get-FullPathSafe $targetPath
}

function Remove-LinkOrPath {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return }
    $item = Get-Item -LiteralPath $Path -Force
    $isReparse = [bool]($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)
    if ($isReparse -and $item.PSIsContainer) {
        [System.IO.Directory]::Delete($Path, $false)
    }
    elseif ($isReparse) {
        Remove-Item -LiteralPath $Path -Force
    }
    else {
        Remove-Item -LiteralPath $Path -Recurse -Force
    }
}

function New-DirectoryLink {
    param(
        [Parameter(Mandatory)][string]$LinkPath,
        [Parameter(Mandatory)][string]$TargetPath
    )
    $parent = Split-Path -Parent $LinkPath
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    # Windows: directory junction, no admin/Developer Mode required.
    # Non-Windows PowerShell (Linux/macOS pwsh): junctions do not exist;
    # use a directory symbolic link instead.
    $itemType = if ($IsWindowsPlatform) { 'Junction' } else { 'SymbolicLink' }
    if ($PSVersionTable.PSVersion.Major -ge 6) {
        New-Item -ItemType $itemType -Path $LinkPath -Target $TargetPath -ErrorAction Stop | Out-Null
    }
    else {
        New-Item -ItemType $itemType -Path $LinkPath -Value $TargetPath -ErrorAction Stop | Out-Null
    }
}

function Set-LinkSurface {
    param(
        [Parameter(Mandatory)][string]$Tool,
        [Parameter(Mandatory)][string]$SurfaceLabel,
        [Parameter(Mandatory)][string]$LinkPath,
        [Parameter(Mandatory)][string]$TargetPath
    )

    $targetCanon = Get-FullPathSafe $TargetPath
    $existingTarget = Get-LinkTargetCanonical -LinkPath $LinkPath
    if ($existingTarget) {
        if ($existingTarget -ieq $targetCanon) {
            Add-ResultRow -Tool $Tool -Surface $SurfaceLabel -Action 'unchanged' -Detail "$LinkPath -> $TargetPath"
            return
        }
        if ($Apply) {
            Remove-LinkOrPath -Path $LinkPath
            New-DirectoryLink -LinkPath $LinkPath -TargetPath $TargetPath
        }
        Add-ResultRow -Tool $Tool -Surface $SurfaceLabel -Action 'updated' -Detail "$LinkPath -> $TargetPath"
        return
    }

    if (Test-Path -LiteralPath $LinkPath) {
        if ($Force) {
            $backup = "$LinkPath.bak-$BackupTimestamp"
            if ($Apply) {
                Move-Item -LiteralPath $LinkPath -Destination $backup
                New-DirectoryLink -LinkPath $LinkPath -TargetPath $TargetPath
            }
            Add-ResultRow -Tool $Tool -Surface $SurfaceLabel -Action 'updated' -Detail "backed up to $backup, then linked"
        }
        else {
            Add-ResultRow -Tool $Tool -Surface $SurfaceLabel -Action 'blocked' -Detail "existing non-link path at $LinkPath; rerun with -Force"
        }
        return
    }

    if ($Apply) {
        New-DirectoryLink -LinkPath $LinkPath -TargetPath $TargetPath
    }
    Add-ResultRow -Tool $Tool -Surface $SurfaceLabel -Action 'created' -Detail "$LinkPath -> $TargetPath"
}

# ---------------------------------------------------------------------------
# Managed-block instruction files
# ---------------------------------------------------------------------------

function Set-Utf8NoBom {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][AllowEmptyString()][string]$Content
    )
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    $text = $Content
    if (-not $text.EndsWith("`n")) { $text += "`n" }
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $text, $encoding)
}

function Get-RenderedTemplate {
    $content = Get-Content -LiteralPath $TemplateFile -Raw -Encoding UTF8
    return ($content.Replace('{{TOOLKIT_ROOT}}', $ToolkitRoot)).TrimEnd("`r", "`n")
}

function Get-ManagedBlockText {
    param([Parameter(Mandatory)][string]$FilePath)
    if (-not (Test-Path -LiteralPath $FilePath -PathType Leaf)) { return $null }
    $lines = @(Get-Content -LiteralPath $FilePath -Encoding UTF8)
    $inBlock = $false
    $sawBegin = $false
    $sawEnd = $false
    $collected = New-Object System.Collections.Generic.List[string]
    foreach ($line in $lines) {
        $norm = $line.TrimEnd("`r")
        if (-not $inBlock -and $norm -eq $BeginMark) {
            $inBlock = $true
            $sawBegin = $true
            continue
        }
        if ($inBlock -and $norm -eq $EndMark) {
            $inBlock = $false
            $sawEnd = $true
            continue
        }
        if ($inBlock) { $collected.Add($norm) }
    }
    if (-not ($sawBegin -and $sawEnd)) { return $null }
    return ($collected -join "`n")
}

function Set-ManagedBlockInPlace {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string]$Block
    )
    $lines = @(Get-Content -LiteralPath $FilePath -Encoding UTF8)
    $output = New-Object System.Collections.Generic.List[string]
    $inBlock = $false
    foreach ($line in $lines) {
        $norm = $line.TrimEnd("`r")
        if (-not $inBlock -and $norm -eq $BeginMark) {
            $output.Add($Block)
            $inBlock = $true
            continue
        }
        if ($inBlock) {
            if ($norm -eq $EndMark) { $inBlock = $false }
            continue
        }
        $output.Add($norm)
    }
    Set-Utf8NoBom -Path $FilePath -Content ($output -join "`n")
}

function Set-ManagedBlock {
    param(
        [Parameter(Mandatory)][string]$Tool,
        [Parameter(Mandatory)][string]$SurfaceLabel,
        [Parameter(Mandatory)][string]$FilePath
    )

    $rendered = Get-RenderedTemplate
    $block = "$BeginMark`n$rendered`n$EndMark"

    $existingBlock = Get-ManagedBlockText -FilePath $FilePath
    if ($null -ne $existingBlock) {
        if ($existingBlock -eq $rendered) {
            Add-ResultRow -Tool $Tool -Surface $SurfaceLabel -Action 'unchanged' -Detail $FilePath
        }
        else {
            if ($Apply) { Set-ManagedBlockInPlace -FilePath $FilePath -Block $block }
            Add-ResultRow -Tool $Tool -Surface $SurfaceLabel -Action 'updated' -Detail $FilePath
        }
        return
    }

    $isEmpty = $true
    if (Test-Path -LiteralPath $FilePath -PathType Leaf) {
        $existingText = Get-Content -LiteralPath $FilePath -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        if ($existingText -and $existingText.Trim().Length -gt 0) { $isEmpty = $false }
    }

    if ($isEmpty) {
        if ($Apply) { Set-Utf8NoBom -Path $FilePath -Content $block }
        Add-ResultRow -Tool $Tool -Surface $SurfaceLabel -Action 'created' -Detail $FilePath
        return
    }

    # Existing non-empty file without our markers: append, preserving content.
    if ($Apply) {
        $existingText = (Get-Content -LiteralPath $FilePath -Raw -Encoding UTF8).TrimEnd("`r", "`n")
        Set-Utf8NoBom -Path $FilePath -Content "$existingText`n`n$block"
    }
    Add-ResultRow -Tool $Tool -Surface $SurfaceLabel -Action 'created' -Detail "$FilePath (appended)"
}

# ---------------------------------------------------------------------------
# Per-tool installers
# ---------------------------------------------------------------------------

function Install-ClaudeSurface {
    $base = Join-Path $HomeDir '.claude'
    Set-LinkSurface -Tool 'claude' -SurfaceLabel 'skills' -LinkPath (Join-Path $base 'skills') -TargetPath (Join-Path $ToolkitRoot 'skills')
    Set-LinkSurface -Tool 'claude' -SurfaceLabel 'agents' -LinkPath (Join-Path $base 'agents') -TargetPath (Join-Path $ToolkitRoot 'tool-subagents')
    Set-ManagedBlock -Tool 'claude' -SurfaceLabel 'CLAUDE.md' -FilePath (Join-Path $base 'CLAUDE.md')
}

function Install-CodexSurface {
    $base = Join-Path $HomeDir '.codex'
    $skillsRoot = Join-Path $ToolkitRoot 'skills'
    if (Test-Path -LiteralPath $skillsRoot -PathType Container) {
        Get-ChildItem -LiteralPath $skillsRoot -Directory | Sort-Object -Property Name | ForEach-Object {
            $skillMd = Join-Path $_.FullName 'SKILL.md'
            if (Test-Path -LiteralPath $skillMd -PathType Leaf) {
                Set-LinkSurface -Tool 'codex' -SurfaceLabel "skills/$($_.Name)" -LinkPath (Join-Path $base "skills/$($_.Name)") -TargetPath $_.FullName
            }
        }
    }
    Set-LinkSurface -Tool 'codex' -SurfaceLabel 'agents' -LinkPath (Join-Path $base 'agents') -TargetPath (Join-Path $ToolkitRoot 'tool-subagents')
    Set-ManagedBlock -Tool 'codex' -SurfaceLabel 'AGENTS.md' -FilePath (Join-Path $base 'AGENTS.md')
}

function Install-CursorSurface {
    $base = Join-Path $HomeDir '.cursor'
    Set-LinkSurface -Tool 'cursor' -SurfaceLabel 'skills' -LinkPath (Join-Path $base 'skills') -TargetPath (Join-Path $ToolkitRoot 'skills')
    Set-LinkSurface -Tool 'cursor' -SurfaceLabel 'agents' -LinkPath (Join-Path $base 'agents') -TargetPath (Join-Path $ToolkitRoot 'tool-subagents')
    Add-ResultRow -Tool 'cursor' -Surface 'user-rules (manual)' -Action 'skipped' -Detail 'no global rules file; paste text below into Cursor Settings > Rules'
    $script:CursorSelected = $true
    $script:CursorRulesText = Get-RenderedTemplate
}

function Install-WindsurfSurface {
    $base = Join-Path $HomeDir '.codeium/windsurf'
    Set-LinkSurface -Tool 'windsurf' -SurfaceLabel 'skills' -LinkPath (Join-Path $base 'skills') -TargetPath (Join-Path $ToolkitRoot 'skills')
    Set-ManagedBlock -Tool 'windsurf' -SurfaceLabel 'memories/global_rules.md' -FilePath (Join-Path $base 'memories/global_rules.md')
}

function Install-GeminiSurface {
    $base = Join-Path $HomeDir '.gemini'
    Set-LinkSurface -Tool 'gemini' -SurfaceLabel 'skills' -LinkPath (Join-Path $base 'skills') -TargetPath (Join-Path $ToolkitRoot 'skills')
    Set-ManagedBlock -Tool 'gemini' -SurfaceLabel 'GEMINI.md' -FilePath (Join-Path $base 'GEMINI.md')
}

function Install-OpenCodeSurface {
    $base = Join-Path $HomeDir '.config/opencode'
    Set-LinkSurface -Tool 'opencode' -SurfaceLabel 'skills' -LinkPath (Join-Path $base 'skills') -TargetPath (Join-Path $ToolkitRoot 'skills')
}

function Install-AntigravitySurface {
    $base = Join-Path $HomeDir '.gemini/antigravity'
    Set-LinkSurface -Tool 'antigravity' -SurfaceLabel 'skills' -LinkPath (Join-Path $base 'skills') -TargetPath (Join-Path $ToolkitRoot 'skills')
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

Write-Output 'LLM toolkit global install'
Write-Output "  Mode:         $(if ($Apply) { 'APPLY' } else { 'PLAN (dry-run, no changes)' })"
Write-Output "  Toolkit root: $ToolkitRoot"
Write-Output "  Home:         $HomeDir"
Write-Output "  Tools:        $(if ($SelectedTools.Count -gt 0) { $SelectedTools -join ' ' } else { '(none)' })"
Write-Output ''

if ($SelectedTools.Count -eq 0) {
    Write-Output "No tool home directories were found under $HomeDir."
    Write-Output 'Pass -Tools all (or a specific list) to install anyway.'
    exit 0
}

foreach ($tool in $SelectedTools) {
    switch ($tool) {
        'claude' { Install-ClaudeSurface }
        'codex' { Install-CodexSurface }
        'cursor' { Install-CursorSurface }
        'windsurf' { Install-WindsurfSurface }
        'gemini' { Install-GeminiSurface }
        'opencode' { Install-OpenCodeSurface }
        'antigravity' { Install-AntigravitySurface }
    }
}

Write-ResultTable

if ($script:CursorSelected) {
    Write-Output ''
    Write-Output 'Cursor has no global rules file; paste the following into Cursor Settings > Rules (User Rules):'
    Write-Output ('-' * 80)
    Write-Output $script:CursorRulesText
    Write-Output ('-' * 80)
}

Write-Output ''
if ($Apply) {
    if ($script:BlockedCount -gt 0) {
        Write-Output "Done with $($script:BlockedCount) blocked path(s). Re-run with -Force after checking the backups it would take."
        exit 1
    }
    Write-Output "Done. Global surfaces installed for: $($SelectedTools -join ' ')"
}
else {
    Write-Output 'This was a plan only; nothing was changed. Re-run with -Apply to make these changes.'
}
