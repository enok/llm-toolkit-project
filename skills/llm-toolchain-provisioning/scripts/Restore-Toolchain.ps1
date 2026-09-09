<#
.SYNOPSIS
    Diff a toolchain manifest against this workstation and plan a restore.
.DESCRIPTION
    Windows wrapper around restore_toolchain.py. Dry-run by default; -Apply
    prints a copy-paste install block rather than executing installs, because
    mutating an operator's environment needs their review.
.PARAMETER Manifest
    Manifest file to restore from.
.PARAMETER Apply
    Print the install commands as a copy-paste block. Does not execute them.
.PARAMETER AsJson
    Emit the plan as JSON.
.EXAMPLE
    .\Restore-Toolchain.ps1 -Manifest $env:TEMP\toolchain.json
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $Manifest,
    [switch] $Apply,
    [switch] $AsJson
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-Python {
    foreach ($candidate in @('python3', 'python', 'py')) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if (-not $command) { continue }
        if ($candidate -eq 'py') { return @($command.Source, '-3') }
        return @($command.Source)
    }
    throw 'Python 3 was not found on PATH. Install Python 3 or run restore_toolchain.py directly.'
}

$python = Resolve-Python
$script = Join-Path $PSScriptRoot 'restore_toolchain.py'
if (-not (Test-Path -LiteralPath $script)) {
    throw "Cannot find $script"
}

$arguments = @($python[1..($python.Count - 1)]) + @($script, '--manifest', $Manifest)
if ($Apply) { $arguments += '--apply' }
if ($AsJson) { $arguments += '--json' }

& $python[0] @arguments
exit $LASTEXITCODE
