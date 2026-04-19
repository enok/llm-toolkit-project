#Requires -Version 5.1
<#
.SYNOPSIS
  Symlink skills, rules, workflows, and repo-local LLM scaffolding into a consumer repo (Windows PowerShell).
.DESCRIPTION
  Mirrors scripts/setup-repo.sh. Root links: .agents, .claude, .codex, .windsurf, .cursor, .setup -> toolkit.
  Toolkit .windsurf/.setup layouts are ensured first. Sync runs after the local scaffold exists.
.PARAMETER ConsumerPath
  Path to the consumer repo (default: current directory).
.EXAMPLE
  .\scripts\setup-repo.ps1 .
  ..\llm-toolkit\scripts\setup-repo.ps1 C:\work\my-app
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

if (-not (Test-Path -LiteralPath "$ToolkitRoot\.agents" -PathType Container)) {
    Write-Error "Toolkit root not found (expected .agents/ at $ToolkitRoot)"
}

if (-not (Test-Path -LiteralPath $ConsumerPath -PathType Container)) {
    Write-Error "Consumer path is not a directory: $ConsumerPath"
}

$Consumer = Resolve-ToolkitAbsolutePath $ConsumerPath

# Interactive tool selection
$USE_WINDSURF = $false; $USE_CURSOR = $false; $USE_CLAUDE = $false; $USE_CODEX = $false

Write-Host ''
Write-Host 'Which LLM tools does this project use? (enter numbers separated by spaces)'
Write-Host '  1) Windsurf'
Write-Host '  2) Cursor'
Write-Host '  3) Claude Code'
Write-Host '  4) Codex'
Write-Host '  a) All of the above'
Write-Host ''
$toolSelection = Read-Host 'Selection [default: a]'
if ([string]::IsNullOrWhiteSpace($toolSelection)) { $toolSelection = 'a' }

if ($toolSelection -ieq 'a') {
    $USE_WINDSURF = $true; $USE_CURSOR = $true; $USE_CLAUDE = $true; $USE_CODEX = $true
} else {
    foreach ($choice in ($toolSelection -split '\s+')) {
        switch ($choice) {
            '1' { $USE_WINDSURF = $true }
            '2' { $USE_CURSOR = $true }
            '3' { $USE_CLAUDE = $true }
            '4' { $USE_CODEX = $true }
            default { Write-Warning "Unknown selection '$choice', ignored." }
        }
    }
}

$selectedTools = @()
if ($USE_WINDSURF) { $selectedTools += 'Windsurf' }
if ($USE_CURSOR) { $selectedTools += 'Cursor' }
if ($USE_CLAUDE) { $selectedTools += 'Claude Code' }
if ($USE_CODEX) { $selectedTools += 'Codex' }
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

# 1. Canonical skills/ and workflows/ - always linked to toolkit's canonical source
$toolkitSkillsRoot = Join-Path $ToolkitRoot 'skills'
$consumerSkills = Join-Path $Consumer 'skills'
$stSkills = Ensure-ToolkitDirectoryLink -LinkPath $consumerSkills -TargetPath $toolkitSkillsRoot -AllowRepair:$Force
Write-Host "skills -> toolkit/skills ($stSkills)"

$toolkitWorkflowsRoot = Join-Path $ToolkitRoot 'workflows'
$consumerWorkflows = Join-Path $Consumer 'workflows'
$stWorkflows = Ensure-ToolkitDirectoryLink -LinkPath $consumerWorkflows -TargetPath $toolkitWorkflowsRoot -AllowRepair:$Force
Write-Host "workflows -> toolkit/workflows ($stWorkflows)"

# 2. .setup/ (examples, integrations)
$toolkitSetupRoot = Join-Path $ToolkitRoot '.setup'
if (Test-Path -LiteralPath $toolkitSetupRoot -PathType Container) {
    $consumerSetupRoot = Join-Path $Consumer '.setup'
    $stSetup = Ensure-ToolkitDirectoryLink -LinkPath $consumerSetupRoot -TargetPath $toolkitSetupRoot -AllowRepair:$Force
    Write-Host ".setup -> toolkit/.setup ($stSetup)"
}

# 3. Agents (generic) - always linked
$consumerAgents = Join-Path $Consumer '.agents'
if (-not (Test-Path -LiteralPath $consumerAgents)) { New-Item -ItemType Directory -Path $consumerAgents -Force | Out-Null }
$stAgentsSkills = Ensure-ToolkitDirectoryLink -LinkPath (Join-Path $consumerAgents 'skills') -TargetPath $toolkitSkillsRoot -AllowRepair:$Force
Write-Host ".agents/skills -> toolkit/skills ($stAgentsSkills)"

# 4. Tool-specific: each agent dir gets a skills/ junction to canonical
if ($USE_WINDSURF) {
    $consumerWindsurf = Join-Path $Consumer '.windsurf'
    if (-not (Test-Path -LiteralPath $consumerWindsurf)) { New-Item -ItemType Directory -Path $consumerWindsurf -Force | Out-Null }
    $stWsWf = Ensure-ToolkitDirectoryLink -LinkPath (Join-Path $consumerWindsurf 'workflows') -TargetPath $toolkitWorkflowsRoot -AllowRepair:$Force
    Write-Host ".windsurf/workflows -> toolkit/workflows ($stWsWf)"
}

if ($USE_CURSOR) {
    $consumerCursor = Join-Path $Consumer '.cursor'
    if (-not (Test-Path -LiteralPath $consumerCursor)) { New-Item -ItemType Directory -Path $consumerCursor -Force | Out-Null }
    $stCrSkills = Ensure-ToolkitDirectoryLink -LinkPath (Join-Path $consumerCursor 'skills') -TargetPath $toolkitSkillsRoot -AllowRepair:$Force
    Write-Host ".cursor/skills -> toolkit/skills ($stCrSkills)"
    $toolkitCursorAgents = Join-Path $ToolkitRoot '.cursor\agents'
    if (Test-Path -LiteralPath $toolkitCursorAgents -PathType Container) {
        $stCrAgents = Ensure-ToolkitDirectoryLink -LinkPath (Join-Path $consumerCursor 'agents') -TargetPath $toolkitCursorAgents -AllowRepair:$Force
        Write-Host ".cursor/agents -> toolkit/.cursor/agents ($stCrAgents)"
    }
}

if ($USE_CLAUDE) {
    $consumerClaude = Join-Path $Consumer '.claude'
    if (-not (Test-Path -LiteralPath $consumerClaude)) { New-Item -ItemType Directory -Path $consumerClaude -Force | Out-Null }
    $stClSkills = Ensure-ToolkitDirectoryLink -LinkPath (Join-Path $consumerClaude 'skills') -TargetPath $toolkitSkillsRoot -AllowRepair:$Force
    Write-Host ".claude/skills -> toolkit/skills ($stClSkills)"
}

if ($USE_CODEX) {
    $consumerCodex = Join-Path $Consumer '.codex'
    if (-not (Test-Path -LiteralPath $consumerCodex)) { New-Item -ItemType Directory -Path $consumerCodex -Force | Out-Null }
    $stCxSkills = Ensure-ToolkitDirectoryLink -LinkPath (Join-Path $consumerCodex 'skills') -TargetPath $toolkitSkillsRoot -AllowRepair:$Force
    Write-Host ".codex/skills -> toolkit/skills ($stCxSkills)"
}

# 3. Scaffold repo-local LLM configuration
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
# Common local hides after initial setup:
# ".setup/examples/
# ".setup/integrations/
'@
    Ensure-ConsumerTextFile -Path (Join-Path $Consumer '.cursorignore') -Content $cursorIgnoreStub -Label '.cursorignore'

    $cursorIndexingIgnoreStub = @'
# Repo-local Cursor indexing overrides.
# Common local hides after initial setup:
# ".setup/examples/
# ".setup/integrations/
'@
    Ensure-ConsumerTextFile -Path (Join-Path $Consumer '.cursorindexingignore') -Content $cursorIndexingIgnoreStub -Label '.cursorindexingignore'
}

$syncWrapperPs1 = (Get-Content -Path "$ScriptDir\templates\sync-llm-configs.ps1" -Raw).TrimEnd()
Ensure-ConsumerTextFile -Path (Join-Path $Consumer 'scripts\sync-llm-configs.ps1') -Content $syncWrapperPs1 -Label 'scripts/sync-llm-configs.ps1'

$syncWrapperSh = (Get-Content -Path "$ScriptDir\templates\sync-llm-configs.sh" -Raw).TrimEnd()
Ensure-ConsumerTextFile -Path (Join-Path $Consumer 'scripts\sync-llm-configs.sh') -Content $syncWrapperSh -Label 'scripts/sync-llm-configs.sh'

# 4. Sync generated tool surfaces after the local scaffold exists
Invoke-ToolkitSyncToolConfigs -ConsumerPath $Consumer -ScriptDir $ScriptDir | Out-Null

# 5. Generate AGENTS.md
$referenceAgents = (Get-Content -Path "$ScriptDir\templates\consumer-AGENTS.md" -Raw).TrimEnd()

$consumerAgents = Join-Path $Consumer 'AGENTS.md'
if (Test-Path -LiteralPath $consumerAgents -PathType Leaf) {
    $existing = Get-Content -LiteralPath $consumerAgents -Raw
    if ($existing -match 'LLM Dev Tools|LLM-assisted development') {
        Write-Host 'AGENTS.md: already configured, unchanged.'
    } else {
        Add-Content -LiteralPath $consumerAgents -Value "`n---`n$referenceAgents"
        Write-Host 'AGENTS.md: appended LLM tools reference.'
    }
} else {
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($consumerAgents, $referenceAgents + [Environment]::NewLine, $encoding)
    Write-Host 'AGENTS.md: created.'
}

# 6. Update .gitignore
$gitignoreLines = @(
    '# LLM integration - symlinked/generated content (do not commit)'
    '.agents/'
    '.setup/'
)
if ($USE_WINDSURF) { $gitignoreLines += '.windsurf/' }
if ($USE_CURSOR)   { $gitignoreLines += '.cursor/' }
if ($USE_CLAUDE)   { $gitignoreLines += '.claude/' }
if ($USE_CODEX)    { $gitignoreLines += '.codex/' }
$gitignoreBlock = $gitignoreLines -join "`n"

$consumerGitignore = Join-Path $Consumer '.gitignore'
if (Test-Path -LiteralPath $consumerGitignore -PathType Leaf) {
    $gi = Get-Content -LiteralPath $consumerGitignore -Raw
    if ($gi -match 'LLM integration|LLM toolkit|\.agents/') {
        Write-Host '.gitignore: already configured, unchanged.'
    } else {
        Add-Content -LiteralPath $consumerGitignore -Value "`n$gitignoreBlock"
        Write-Host '.gitignore: appended LLM tool entries.'
    }
} else {
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
        Add-Content -LiteralPath $consumerGitignore -Value $keepCursorFiltersBlock
        Write-Host '.gitignore: ensured repo-local Cursor visibility filters stay committed.'
    }
}

Write-Host ''
Write-Host "Done. Consumer repo configured at: $Consumer"
Write-Host ''
Write-Host '  Always:'
Write-Host '    .agents/                   - skills -> toolkit .agents/'
Write-Host '    .setup/                    - templates -> toolkit .setup/'
Write-Host '    docs/llm/                  - repo-local LLM guidance'
Write-Host '    scripts/sync-llm-configs.* - consumer-local LLM sync wrapper'
Write-Host '    AGENTS.md                  - repo-level instructions and context'
if ($USE_WINDSURF) { Write-Host '  Windsurf:'; Write-Host '    .windsurf/                 - -> toolkit .windsurf/ (symlink)' }
if ($USE_CURSOR)   { Write-Host '  Cursor:'; Write-Host '    .cursor/                   - -> toolkit/.cursor (symlink)' }
if ($USE_CLAUDE)   { Write-Host '  Claude Code:'; Write-Host '    .claude/                   - -> toolkit .claude/ (symlink)' }
if ($USE_CODEX)    { Write-Host '  Codex:'; Write-Host '    .codex/                    - -> toolkit .codex/ (symlink)' }
Write-Host ''
Write-Host 'Note: linked/generated toolkit directories are gitignored; repo-local files stay committed.'
Write-Host 'Next: review docs/llm/toolkit-selection.txt and ask the LLM to add repo-specific context in docs/llm/.'
