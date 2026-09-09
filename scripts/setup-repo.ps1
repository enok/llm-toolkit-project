#Requires -Version 5.1
<#
.SYNOPSIS
  Symlink skills, rules, workflows, provider compatibility paths, and repo-local LLM scaffolding into a consumer repo (Windows PowerShell).
.DESCRIPTION
  Mirrors scripts/setup-repo.sh. Shared content is linked by subpath so repo-specific skills and local tool files can coexist with toolkit-managed links.
  Toolkit .windsurf layout is ensured first. Sync runs after the local scaffold exists.
.PARAMETER ConsumerPath
  Path to the consumer repo (default: current directory).
.EXAMPLE
  .\scripts\setup-repo.ps1 .
  ..\path-to-llm-toolkit\scripts\setup-repo.ps1 C:\work\my-app
#>
param(
    [Parameter(Position = 0)]
    [string]$ConsumerPath = '.',
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$ScriptDir = $PSScriptRoot
$ToolkitRoot = Split-Path -Parent $ScriptDir

. "$ScriptDir\lib.ps1"

if (-not (Test-Path -LiteralPath "$ToolkitRoot\skills" -PathType Container) -and -not (Test-Path -LiteralPath "$ToolkitRoot\.agents\skills" -PathType Container)) {
    Write-Error "toolkit root not found (expected skills/ at $ToolkitRoot)"
}

if (-not (Test-Path -LiteralPath $ConsumerPath -PathType Container)) {
    Write-Error "consumer path is not a directory: $ConsumerPath"
}

$Consumer = Resolve-ToolkitAbsolutePath $ConsumerPath

# ── Interactive tool selection ────────────────────────────────────────────────
$USE_WINDSURF = $false; $USE_CURSOR = $false; $USE_CLAUDE = $false; $USE_CODEX = $false; $USE_ANTIGRAVITY = $false; $USE_GEMINI = $false; $USE_OPENCODE = $false

Write-Host ''
Write-Host 'Which LLM tools does this project use? (enter numbers separated by spaces)'
Write-Host '  1) Windsurf'
Write-Host '  2) Cursor'
Write-Host '  3) Claude Code'
Write-Host '  4) Codex compatibility surface'
Write-Host '  5) Antigravity'
Write-Host '  6) Gemini CLI'
Write-Host '  7) OpenCode'
Write-Host '  a) All of the above'
Write-Host ''
$toolSelection = Read-Host 'Selection [default: a]'
if ([string]::IsNullOrWhiteSpace($toolSelection)) { $toolSelection = 'a' }

if ($toolSelection -ieq 'a') {
    $USE_WINDSURF = $true; $USE_CURSOR = $true; $USE_CLAUDE = $true; $USE_CODEX = $true; $USE_ANTIGRAVITY = $true; $USE_GEMINI = $true; $USE_OPENCODE = $true
} else {
    foreach ($choice in ($toolSelection -split '\s+')) {
        switch ($choice) {
            '1' { $USE_WINDSURF = $true }
            '2' { $USE_CURSOR = $true }
            '3' { $USE_CLAUDE = $true }
            '4' { $USE_CODEX = $true }
            '5' { $USE_ANTIGRAVITY = $true }
            '6' { $USE_GEMINI = $true }
            '7' { $USE_OPENCODE = $true }
            default { Write-Warning "Unknown selection '$choice', ignored." }
        }
    }
}

$selectedTools = @()
if ($USE_WINDSURF) { $selectedTools += 'Windsurf' }
if ($USE_CURSOR) { $selectedTools += 'Cursor' }
if ($USE_CLAUDE) { $selectedTools += 'Claude Code' }
if ($USE_CODEX) { $selectedTools += 'Codex compatibility surface' }
if ($USE_ANTIGRAVITY) { $selectedTools += 'Antigravity' }
if ($USE_GEMINI) { $selectedTools += 'Gemini CLI' }
if ($USE_OPENCODE) { $selectedTools += 'OpenCode' }
Write-Host ''
Write-Host "Setting up: $($selectedTools -join ', ')"
Write-Host ''

function Ensure-ConsumerTextFile {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Content,
        [Parameter(Mandatory)][string]$Label
    )

    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        Write-Host "${Label}: already exists, unchanged."
        return
    }

    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content + [Environment]::NewLine, $encoding)
    Write-Host "${Label}: created."
}

function Get-SharedSkillIgnoreLines {
    param([Parameter(Mandatory)][string]$Prefix)

    $skillsRoot = Join-Path $ToolkitRoot 'skills'
    if (-not (Test-Path -LiteralPath $skillsRoot -PathType Container)) {
        return @()
    }

    Get-ChildItem -LiteralPath $skillsRoot -Directory |
        Sort-Object Name |
        ForEach-Object { "$Prefix/skills/$($_.Name)" }
}

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

# 1. Shared skills.
$consumerAgentsRoot = Join-Path $Consumer '.agents'
Ensure-ConsumerDirectory -Path $consumerAgentsRoot
Ensure-SharedSkillCatalogLinks -SkillsRoot (Join-Path $consumerAgentsRoot 'skills') -Label 'Skills: .agents/skills/<name> -> toolkit/skills/<name>'

if ($USE_ANTIGRAVITY) {
    $consumerAntigravityRoot = Join-Path $Consumer '.agent'
    Ensure-ConsumerDirectory -Path $consumerAntigravityRoot
    Ensure-SharedSkillCatalogLinks -SkillsRoot (Join-Path $consumerAntigravityRoot 'skills') -Label 'Antigravity: .agent/skills/<name> -> toolkit/skills/<name>'
}

# 2. Ensure toolkit layouts and link shared directories by subpath.
Ensure-ToolkitWindsurfLayout -ToolkitRoot $ToolkitRoot -AllowRepair:$Force
$toolkitAgents = Join-Path $ToolkitRoot 'tool-subagents'

$consumerWindsurfRoot = Join-Path $Consumer '.windsurf'
Ensure-ConsumerDirectory -Path $consumerWindsurfRoot
$null = Ensure-ToolkitDirectoryLink -LinkPath (Join-Path $consumerWindsurfRoot 'rules') -TargetPath (Join-Path $ToolkitRoot 'rules') -AllowRepair:$Force
$null = Ensure-ToolkitDirectoryLink -LinkPath (Join-Path $consumerWindsurfRoot 'workflows') -TargetPath (Join-Path $ToolkitRoot 'workflows') -AllowRepair:$Force

if ($USE_WINDSURF) {
    Ensure-SharedSkillCatalogLinks -SkillsRoot (Join-Path $consumerWindsurfRoot 'skills') -Label 'Windsurf: .windsurf/skills/<name> -> toolkit/skills/<name>'
    Write-Host '.windsurf/rules and .windsurf/workflows linked to toolkit'
}

if ($USE_CURSOR) {
    $consumerCursorRoot = Join-Path $Consumer '.cursor'
    Ensure-ConsumerDirectory -Path $consumerCursorRoot
    Ensure-SharedSkillCatalogLinks -SkillsRoot (Join-Path $consumerCursorRoot 'skills') -Label 'Cursor: .cursor/skills/<name> -> toolkit/skills/<name>'
    if (Test-Path -LiteralPath $toolkitAgents -PathType Container) {
        $null = Ensure-ToolkitDirectoryLink -LinkPath (Join-Path $consumerCursorRoot 'agents') -TargetPath $toolkitAgents -AllowRepair:$Force
    }
    Write-Host '.cursor root ready; shared rules/workflows refresh during sync'
}

if ($USE_GEMINI) {
    $consumerGeminiRoot = Join-Path $Consumer '.gemini'
    Ensure-ConsumerDirectory -Path $consumerGeminiRoot
    Ensure-SharedSkillCatalogLinks -SkillsRoot (Join-Path $consumerGeminiRoot 'skills') -Label 'Gemini CLI: .gemini/skills/<name> -> toolkit/skills/<name>'
}

if ($USE_OPENCODE) {
    $consumerOpenCodeRoot = Join-Path $Consumer '.opencode'
    Ensure-ConsumerDirectory -Path $consumerOpenCodeRoot
    Ensure-SharedSkillCatalogLinks -SkillsRoot (Join-Path $consumerOpenCodeRoot 'skills') -Label 'OpenCode: .opencode/skills/<name> -> toolkit/skills/<name>'
}

if ($USE_CLAUDE) {
    $consumerClaudeRoot = Join-Path $Consumer '.claude'
    Ensure-ConsumerDirectory -Path $consumerClaudeRoot
    Ensure-SharedSkillCatalogLinks -SkillsRoot (Join-Path $consumerClaudeRoot 'skills') -Label 'Claude Code: .claude/skills/<name> -> toolkit/skills/<name>'
    if (Test-Path -LiteralPath $toolkitAgents -PathType Container) {
        $null = Ensure-ToolkitDirectoryLink -LinkPath (Join-Path $consumerClaudeRoot 'agents') -TargetPath $toolkitAgents -AllowRepair:$Force
    }
}

if ($USE_CODEX) {
    $consumerCodexRoot = Join-Path $Consumer '.codex'
    Ensure-ConsumerDirectory -Path $consumerCodexRoot
    Ensure-SharedSkillCatalogLinks -SkillsRoot (Join-Path $consumerCodexRoot 'skills') -Label 'Codex: .codex/skills/<name> -> toolkit/skills/<name>'
    if (Test-Path -LiteralPath $toolkitAgents -PathType Container) {
        $null = Ensure-ToolkitDirectoryLink -LinkPath (Join-Path $consumerCodexRoot 'agents') -TargetPath $toolkitAgents -AllowRepair:$Force
    }
}

# 3. Scaffold repo-local LLM configuration outside linked toolkit directories.
$llmDir = Join-Path $Consumer 'docs\llm'
New-Item -ItemType Directory -Path (Join-Path $llmDir 'rules') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $llmDir 'workflows') -Force | Out-Null

$llmReadme = (Get-Content -Path "$ScriptDir\templates\docs-llm-README.md" -Raw).TrimEnd()
Ensure-ConsumerTextFile -Path (Join-Path $llmDir 'README.md') -Content $llmReadme -Label 'docs/llm/README.md'
Ensure-ConsumerTextFile -Path (Join-Path $llmDir 'rules\README.md') -Content "# Repo-Local Rules`n`nAdd repository-only rules here. Keep reusable generic rules in the shared toolkit." -Label 'docs/llm/rules/README.md'
Ensure-ConsumerTextFile -Path (Join-Path $llmDir 'workflows\README.md') -Content "# Repo-Local Workflows`n`nAdd repository-only workflows here. Keep reusable generic workflows in the shared toolkit." -Label 'docs/llm/workflows/README.md'

$selectionTemplate = (Get-Content -Path "$ScriptDir\templates\toolkit-selection.txt" -Raw).TrimEnd()
Ensure-ConsumerTextFile -Path (Join-Path $llmDir 'toolkit-selection.txt') -Content $selectionTemplate -Label 'docs/llm/toolkit-selection.txt'

if ($USE_CURSOR) {
    $cursorIgnoreStub = @'
# Repo-local Cursor visibility overrides.
# `sync-tool-configs.sh` manages a selection block here when `docs/llm/toolkit-selection.txt` contains entries.
# Common local hides after initial setup:
# rules/examples/
# integrations/jira.md
# integrations/confluence.md
'@
    Ensure-ConsumerTextFile -Path (Join-Path $Consumer '.cursorignore') -Content $cursorIgnoreStub -Label '.cursorignore'

    $cursorIndexingIgnoreStub = @'
# Repo-local Cursor indexing overrides.
# `sync-tool-configs.sh` manages a selection block here when `docs/llm/toolkit-selection.txt` contains entries.
# Common local hides after initial setup:
# rules/examples/
# integrations/jira.md
# integrations/confluence.md
'@
    Ensure-ConsumerTextFile -Path (Join-Path $Consumer '.cursorindexingignore') -Content $cursorIndexingIgnoreStub -Label '.cursorindexingignore'
}

$syncWrapperPs1 = (Get-Content -Path "$ScriptDir\templates\sync-llm-configs.ps1" -Raw).TrimEnd()
Ensure-ConsumerTextFile -Path (Join-Path $Consumer 'scripts\sync-llm-configs.ps1') -Content $syncWrapperPs1 -Label 'scripts/sync-llm-configs.ps1'

$syncWrapperSh = (Get-Content -Path "$ScriptDir\templates\sync-llm-configs.sh" -Raw).TrimEnd()
Ensure-ConsumerTextFile -Path (Join-Path $Consumer 'scripts\sync-llm-configs.sh') -Content $syncWrapperSh -Label 'scripts/sync-llm-configs.sh'

# 4. Sync generated tool surfaces after the local scaffold exists.
$syncOk = Invoke-ToolkitSyncToolConfigs -ConsumerPath $Consumer -ScriptDir $ScriptDir -SkipCursorRules:(-not $USE_CURSOR) -Force:$Force
if (-not $syncOk) {
    throw 'sync-tool-configs.sh failed. Shared tool symlinks or local exports may be stale. Fix the issue and re-run setup, or run sync-tool-configs.sh from Git Bash.'
}

# 5. Generate AGENTS.md.
$referenceAgentsRaw = Get-Content -Path "$ScriptDir\templates\consumer-AGENTS.md" -Raw
$referenceAgents = $referenceAgentsRaw.TrimEnd()

$orchestrationHeading = '## Mandatory agent orchestration (all LLM assistants)'
# Single source of truth: the section lives at the end of the template
# (from the heading line to end-of-template); extract it instead of
# duplicating the text here.
$headingIndex = $referenceAgentsRaw.IndexOf($orchestrationHeading)
if ($headingIndex -lt 0) {
    throw "Mandatory agent-orchestration heading not found in templates\consumer-AGENTS.md"
}
$orchestrationSection = $referenceAgentsRaw.Substring($headingIndex).TrimEnd()

$consumerAgents = Join-Path $Consumer 'AGENTS.md'
if (Test-Path -LiteralPath $consumerAgents -PathType Leaf) {
    $existing = Get-Content -LiteralPath $consumerAgents -Raw
    if ($existing -match 'LLM Dev Tools|LLM-assisted development') {
        Write-Host 'AGENTS.md: already configured, unchanged.'
    }
    else {
        Add-Content -LiteralPath $consumerAgents -Value "`n---`n$referenceAgents"
        Write-Host 'AGENTS.md: appended LLM tools reference.'
    }
}
else {
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($consumerAgents, $referenceAgents + [Environment]::NewLine, $encoding)
    Write-Host 'AGENTS.md: created.'
}

# 5b. Idempotently ensure the mandatory agent-orchestration section is present.
# The template-append/create paths above already carry it as part of
# $referenceAgents; this only fires when an already-configured AGENTS.md
# (marker present) predates the section being added to the template.
$existingAgents = Get-Content -LiteralPath $consumerAgents -Raw
if ($existingAgents -and $existingAgents.Contains($orchestrationHeading)) {
    Write-Host 'AGENTS.md: agent-orchestration section already present, unchanged.'
}
else {
    Add-Content -LiteralPath $consumerAgents -Value "`n$orchestrationSection"
    Write-Host 'AGENTS.md: appended mandatory agent-orchestration section.'
}

# 6. Update .gitignore.
$gitignoreLines = @(
    '# LLM integration — local output and symlinked/generated toolkit paths'
    'docs/jira/'
    'node_modules/'
    '.DS_Store'
) + (Get-SharedSkillIgnoreLines -Prefix '.agents') + @(
    '.agents/skills/AGENTS.md'
    '.windsurf/rules/'
    '.windsurf/workflows/'
)
if ($USE_WINDSURF) {
    $gitignoreLines += Get-SharedSkillIgnoreLines -Prefix '.windsurf'
}
if ($USE_ANTIGRAVITY) {
    $gitignoreLines += Get-SharedSkillIgnoreLines -Prefix '.agent'
    $gitignoreLines += '.agent/skills/AGENTS.md'
}
if ($USE_CURSOR) {
    $gitignoreLines += Get-SharedSkillIgnoreLines -Prefix '.cursor'
    $gitignoreLines += '.cursor/skills/AGENTS.md'
    $gitignoreLines += '.cursor/rules/'
    $gitignoreLines += '.cursor/workflows/'
    $gitignoreLines += '.cursor/agents/'
}
if ($USE_CLAUDE) {
    $gitignoreLines += Get-SharedSkillIgnoreLines -Prefix '.claude'
    $gitignoreLines += '.claude/skills/AGENTS.md'
}
if ($USE_CODEX) {
    $gitignoreLines += Get-SharedSkillIgnoreLines -Prefix '.codex'
    $gitignoreLines += '.codex/skills/AGENTS.md'
    $gitignoreLines += '.codex/agents/'
}
if ($USE_GEMINI) {
    $gitignoreLines += Get-SharedSkillIgnoreLines -Prefix '.gemini'
    $gitignoreLines += '.gemini/skills/AGENTS.md'
}
if ($USE_OPENCODE) {
    $gitignoreLines += Get-SharedSkillIgnoreLines -Prefix '.opencode'
    $gitignoreLines += '.opencode/skills/AGENTS.md'
}
$gitignoreBlock = $gitignoreLines -join "`n"

$consumerGitignore = Join-Path $Consumer '.gitignore'
if (Test-Path -LiteralPath $consumerGitignore -PathType Leaf) {
    $gi = Get-Content -LiteralPath $consumerGitignore -Raw
    if ($gi -match 'LLM integration|LLM toolkit|\docs/jira/') {
        Write-Host '.gitignore: already configured, unchanged.'
    }
    else {
        Add-Content -LiteralPath $consumerGitignore -Value "`n$gitignoreBlock"
        Write-Host '.gitignore: appended LLM tool entries.'
    }
}
else {
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($consumerGitignore, $gitignoreBlock + [Environment]::NewLine, $encoding)
    Write-Host '.gitignore: created.'
}

if ($USE_CURSOR) {
    $keepCursorFiltersBlock = @'
# Keep repo-local Cursor visibility filters committed.
!.cursorignore
!.cursorindexingignore
'@
    $giCurrent = if (Test-Path -LiteralPath $consumerGitignore -PathType Leaf) { Get-Content -LiteralPath $consumerGitignore -Raw } else { '' }
    if ($giCurrent -notmatch '(?m)^!\.cursorignore$') {
        Add-Content -LiteralPath $consumerGitignore -Value "`n$keepCursorFiltersBlock"
        Write-Host '.gitignore: ensured repo-local Cursor visibility filters stay committed.'
    }
}

Write-Host ''
Write-Host "Done. Consumer repo configured at: $Consumer"
Write-Host ''
Write-Host '  Always:'
Write-Host '    .agents/skills/<name>      - shared skills -> toolkit skills/<name>'
Write-Host '    .windsurf/rules/           - shared rules -> toolkit rules/'
Write-Host '    .windsurf/workflows/       - shared workflows -> toolkit workflows/'
Write-Host '    docs/llm/                  - repo-local LLM guidance'
Write-Host '    scripts/sync-llm-configs.* - consumer-local LLM sync wrapper'
Write-Host '    AGENTS.md                  - repo-level instructions and context'
if ($USE_WINDSURF) { Write-Host '  Windsurf:';  Write-Host '    .windsurf/skills/<name>    - shared skills -> toolkit skills/<name>' }
if ($USE_ANTIGRAVITY) { Write-Host '  Antigravity:'; Write-Host '    .agent/skills/<name>       - shared skills -> toolkit skills/<name>' }
if ($USE_CURSOR)   { Write-Host '  Cursor:';    Write-Host '    .cursor/skills/<name>      - shared skills -> toolkit skills/<name>'; Write-Host '    .cursor/                   - provider root with shared subpath links' }
if ($USE_CLAUDE)   { Write-Host '  Claude Code:'; Write-Host '    .claude/skills/<name>      - shared skills -> toolkit skills/<name>' }
if ($USE_CODEX)    { Write-Host '  Codex:';     Write-Host '    .codex/skills/<name>       - shared skills -> toolkit skills/<name>' }
if ($USE_GEMINI)   { Write-Host '  Gemini CLI:'; Write-Host '    .gemini/skills/<name>      - shared skills -> toolkit skills/<name>' }
if ($USE_OPENCODE) { Write-Host '  OpenCode:'; Write-Host '    .opencode/skills/<name>    - shared skills -> toolkit skills/<name>' }
Write-Host ''
Write-Host 'Note: linked/generated toolkit directories are gitignored; repo-local files stay committed.'
Write-Host 'Next: review docs/llm/toolkit-selection.txt and ask the LLM to add repo-specific context in docs/llm/.'
