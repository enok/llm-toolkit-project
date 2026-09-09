<#
.SYNOPSIS
    Export installed LLM assistant extensions to a portable manifest.
.DESCRIPTION
    Windows wrapper around export_toolchain.py. The Python entrypoint holds all
    logic; this only resolves an interpreter and forwards arguments, per
    rules/cross-platform-scripts.md.
.PARAMETER Out
    Path to write the manifest to. Use a git-ignored path — the manifest
    records one workstation's state and must not be committed.
.PARAMETER Provider
    Limit to specific providers (e.g. claude-code, cursor). Default: all detected.
.PARAMETER AsJson
    Print the manifest to stdout instead of a summary.
.EXAMPLE
    .\Export-Toolchain.ps1 -Out $env:TEMP\toolchain.json
#>
[CmdletBinding()]
param(
    [string] $Out,
    [string[]] $Provider,
    [switch] $AsJson
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-Python {
    foreach ($candidate in @('python3', 'python', 'py')) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if (-not $command) { continue }
        # `py` needs a version selector; the others are used directly.
        if ($candidate -eq 'py') { return @($command.Source, '-3') }
        return @($command.Source)
    }
    throw 'Python 3 was not found on PATH. Install Python 3 or run export_toolchain.py directly.'
}

$python = Resolve-Python
$script = Join-Path $PSScriptRoot 'export_toolchain.py'
if (-not (Test-Path -LiteralPath $script)) {
    throw "Cannot find $script"
}

$arguments = @($python[1..($python.Count - 1)]) + @($script)
if ($Out) { $arguments += @('--out', $Out) }
foreach ($item in $Provider) { $arguments += @('--provider', $item) }
if ($AsJson) { $arguments += '--json' }

& $python[0] @arguments
exit $LASTEXITCODE
