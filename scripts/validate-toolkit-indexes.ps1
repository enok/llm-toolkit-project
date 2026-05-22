#Requires -Version 5.1
<#
.SYNOPSIS
  Run validate-toolkit-indexes.sh from PowerShell using Git Bash.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$ScriptDir = $PSScriptRoot
. "$ScriptDir\lib.ps1"

$script = Join-Path $ScriptDir 'validate-toolkit-indexes.sh'
$ok = Invoke-ToolkitBashScript -ScriptPath $script
if (-not $ok) {
    throw 'validate-toolkit-indexes.sh failed. Install Git Bash or run the shell script manually.'
}
