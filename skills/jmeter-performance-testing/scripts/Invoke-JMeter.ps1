<#
.SYNOPSIS
    Thin PowerShell wrapper around run_jmeter.py.
.DESCRIPTION
    Finds a Python 3 interpreter (python3, then python, then py -3) and
    forwards every parameter to run_jmeter.py, which does the real work:
    patching a copy of the .jmx, resolving the JMeter binary, and executing
    (or, with -DryRun, previewing) the run. This wrapper adds no logic of its
    own beyond argument translation, so behavior never drifts from the
    Python implementation. See run_jmeter.py --help for full flag semantics.
.EXAMPLE
    .\Invoke-JMeter.ps1 -JmxPath C:\plan.jmx -BaseUrl https://api.example.com `
        -Threads 20 -RampUp 60 -Duration 300 -DryRun
.EXAMPLE
    .\Invoke-JMeter.ps1 -JmxPath C:\plan.jmx -BaseUrl https://api.example.com `
        -Property "tenant_id=42","region=us-west-2" -AuthTokenEnv API_TOKEN
.NOTES
    -Property takes a PowerShell array, so pass more than one value with the
    comma-array syntax shown above (-Property "a=1","b=2"), not by repeating
    -Property multiple times - PowerShell's parameter binder rejects a named
    parameter passed more than once in a single call.
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$JmxPath,

    [string]$BaseUrl = "",
    [int]$Threads = 0,
    [int]$RampUp = 0,
    [int]$Duration = 0,

    [string[]]$Property = @(),

    [string]$AuthToken = "",
    [string]$AuthTokenEnv = "",

    [string]$ResultsDir = "",
    [string]$JMeterBin = "",

    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Find-PythonCommand {
    # Mirrors scripts/validate-toolkit-indexes.sh find_python_cmd: try
    # python3, then python, then py -3, skipping the Windows Store stub and
    # any candidate that cannot actually import a module.
    $candidates = @(
        [pscustomobject]@{ Name = "python3"; PreArgs = @() },
        [pscustomobject]@{ Name = "python"; PreArgs = @() },
        [pscustomobject]@{ Name = "py"; PreArgs = @("-3") }
    )

    foreach ($candidate in $candidates) {
        $resolved = Get-Command $candidate.Name -ErrorAction SilentlyContinue
        if (-not $resolved) {
            continue
        }
        if ($resolved.Source -match "WindowsApps") {
            continue
        }
        & $resolved.Source @($candidate.PreArgs) "-c" "import sys" *>$null
        if ($LASTEXITCODE -eq 0) {
            return [pscustomobject]@{ Exe = $resolved.Source; PreArgs = $candidate.PreArgs }
        }
    }

    throw "Could not find a Python 3 interpreter (tried python3, python, py -3). Install Python 3 or add it to PATH."
}

$python = Find-PythonCommand
Write-Verbose "Using Python interpreter: $($python.Exe) $($python.PreArgs -join ' ')"

$runnerPath = Join-Path $PSScriptRoot "run_jmeter.py"
if (-not (Test-Path -LiteralPath $runnerPath)) {
    throw "Could not find run_jmeter.py next to this wrapper: $runnerPath"
}

$pythonArgs = New-Object System.Collections.Generic.List[string]
$pythonArgs.Add($runnerPath)
$pythonArgs.Add("--jmx")
$pythonArgs.Add($JmxPath)

if ($BaseUrl) {
    $pythonArgs.Add("--base-url")
    $pythonArgs.Add($BaseUrl)
}
if ($Threads -gt 0) {
    $pythonArgs.Add("--threads")
    $pythonArgs.Add([string]$Threads)
}
if ($RampUp -gt 0) {
    $pythonArgs.Add("--ramp-up")
    $pythonArgs.Add([string]$RampUp)
}
if ($Duration -gt 0) {
    $pythonArgs.Add("--duration")
    $pythonArgs.Add([string]$Duration)
}
foreach ($prop in $Property) {
    $pythonArgs.Add("--property")
    $pythonArgs.Add($prop)
}
if ($AuthToken) {
    $pythonArgs.Add("--auth-token")
    $pythonArgs.Add($AuthToken)
}
if ($AuthTokenEnv) {
    $pythonArgs.Add("--auth-token-env")
    $pythonArgs.Add($AuthTokenEnv)
}
if ($ResultsDir) {
    $pythonArgs.Add("--results-dir")
    $pythonArgs.Add($ResultsDir)
}
if ($JMeterBin) {
    $pythonArgs.Add("--jmeter-bin")
    $pythonArgs.Add($JMeterBin)
}
if ($DryRun) {
    $pythonArgs.Add("--dry-run")
}

# $AuthToken never appears above except inside $pythonArgs, which is passed
# straight to the child process argv and is never printed or logged here;
# run_jmeter.py itself redacts it from every console line and from
# manifest.json.
& $python.Exe @($python.PreArgs) @pythonArgs
exit $LASTEXITCODE
