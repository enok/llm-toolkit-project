# Plan-first entry point for the complete toolkit CLI set on Windows.
# The default is a read-only plan; pass -Apply only after reviewing the
# printed package plan.
#
# Usage: ./INFRA.ps1 [-Apply] [-Consumer <path>]
#
# This wraps scripts/bootstrap-dev.ps1 with a full-profile, all-agent plan.
# POSIX/Git Bash: INFRA.sh - same behavior via scripts/bootstrap-dev.sh.

[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$Consumer
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$bootstrapArgs = @{
    Full = $true
    Agent = 'all'
    DryRun = -not $Apply
}
if ($Consumer) { $bootstrapArgs.Consumer = $Consumer }

& (Join-Path $root 'scripts\bootstrap-dev.ps1') @bootstrapArgs
exit $LASTEXITCODE
