#Requires -Version 5.1
<#
.SYNOPSIS
  Repair shared symlinked tool surfaces and refresh repo-local exports via sync-tool-configs.sh.
.DESCRIPTION
  Provides a stable PowerShell entrypoint for consumer wrappers and Windows users.
.EXAMPLE
  .\scripts\sync-tool-configs.ps1 .
  .\scripts\sync-tool-configs.ps1 . -SkipAgentsMd
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$ProjectPath = '.',
    [switch]$SkipAgentsMd
)

$ErrorActionPreference = 'Stop'

$ScriptDir = $PSScriptRoot

. "$ScriptDir\lib.ps1"

$project = Resolve-ToolkitAbsolutePath $ProjectPath
$ok = Invoke-ToolkitSyncToolConfigs -ConsumerPath $project -ScriptDir $ScriptDir -SkipAgentsMd:$SkipAgentsMd
if (-not $ok) {
    throw 'sync-tool-configs failed. Install Git Bash or run the shell script manually.'
}
