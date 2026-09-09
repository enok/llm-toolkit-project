#Requires -Version 5.1
<#
.SYNOPSIS
  Repair shared symlinked tool surfaces and refresh repo-local exports via sync-tool-configs.sh.
.DESCRIPTION
  Provides a stable PowerShell entrypoint for consumer wrappers and Windows users.
.EXAMPLE
  .\scripts\sync-tool-configs.ps1 .
  .\scripts\sync-tool-configs.ps1 . -SkipAgentsMd
  .\scripts\sync-tool-configs.ps1 . -SkipCursorRules
  .\scripts\sync-tool-configs.ps1 . -SkipGithub
  .\scripts\sync-tool-configs.ps1 . -Force
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$ProjectPath = '.',
    [switch]$SkipAgentsMd,
    [switch]$SkipCursorRules,
    [switch]$SkipGithub,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$ScriptDir = $PSScriptRoot

. "$ScriptDir\lib.ps1"

$project = Resolve-ToolkitAbsolutePath $ProjectPath
$ok = Invoke-ToolkitSyncToolConfigs -ConsumerPath $project -ScriptDir $ScriptDir -SkipAgentsMd:$SkipAgentsMd -SkipCursorRules:$SkipCursorRules -SkipGithub:$SkipGithub -Force:$Force
if (-not $ok) {
    throw 'sync-tool-configs failed. Install Git Bash or run the shell script manually.'
}
