#Requires -Version 5.1
<#
.SYNOPSIS
  Run SkillSpector static validation across all toolkit skills.
#>
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

$ErrorActionPreference = 'Stop'

$ScriptDir = $PSScriptRoot
$script = Join-Path $ScriptDir 'validate-skills-with-skillspector.py'

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $python) {
    throw 'python is required to run SkillSpector validation.'
}

& $python.Source $script @RemainingArgs
if ($LASTEXITCODE -ne 0) {
    throw "SkillSpector validation failed with exit code $LASTEXITCODE."
}
