#Requires -Version 5.1
<#
.SYNOPSIS
  Run security-check-toolkit.sh from PowerShell using Git Bash.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$ScriptDir = $PSScriptRoot
. "$ScriptDir\lib.ps1"

$script = Join-Path $ScriptDir 'security-check-toolkit.sh'
$ok = Invoke-ToolkitBashScript -ScriptPath $script
if (-not $ok) {
    throw 'security-check-toolkit.sh failed. Review the output above, install missing tools, or run the shell script manually.'
}
