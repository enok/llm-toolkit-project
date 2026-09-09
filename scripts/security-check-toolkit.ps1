#Requires -Version 5.1
<#
.SYNOPSIS
  Run security-check-toolkit.sh from PowerShell using Git Bash, then run Windows-specific toolkit layout checks.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$ScriptDir = $PSScriptRoot
. "$ScriptDir\lib.ps1"

$pathPrepends = @()
$uvToolBin = Join-Path $HOME '.local\bin'
if (Test-Path -LiteralPath $uvToolBin) {
    $pathPrepends += $uvToolBin
}
$pythonUserRoot = Join-Path $env:APPDATA 'Python'
if (Test-Path -LiteralPath $pythonUserRoot) {
    Get-ChildItem -LiteralPath $pythonUserRoot -Directory -Filter 'Python*' -ErrorAction SilentlyContinue |
        ForEach-Object {
            $scriptsPath = Join-Path $_.FullName 'Scripts'
            if (Test-Path -LiteralPath $scriptsPath) {
                $pathPrepends += $scriptsPath
            }
        }
}
if ($pathPrepends.Count -gt 0) {
    $existingPath = @($env:PATH -split ';' | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    $env:PATH = (@($pathPrepends) + $existingPath | Select-Object -Unique) -join ';'
}

if ([string]::IsNullOrWhiteSpace($env:SNYK_TOKEN)) {
    $userSnykToken = [Environment]::GetEnvironmentVariable('SNYK_TOKEN', 'User')
    if (-not [string]::IsNullOrWhiteSpace($userSnykToken)) {
        $env:SNYK_TOKEN = $userSnykToken
    }
}

$script = Join-Path $ScriptDir 'security-check-toolkit.sh'
$ok = Invoke-ToolkitBashScript -ScriptPath $script
if (-not $ok) {
    throw 'security-check-toolkit.sh failed. Review the output above, install missing tools, or run the shell script manually.'
}

$layoutRepairTest = Join-Path $ScriptDir 'test-toolkit-layout-repair.ps1'
if (Test-Path -LiteralPath $layoutRepairTest) {
    & $layoutRepairTest
    if ($LASTEXITCODE -ne 0) {
        throw 'test-toolkit-layout-repair.ps1 failed. Review the output above, enable Windows Developer Mode or elevation for symlink creation, then re-run.'
    }
}
