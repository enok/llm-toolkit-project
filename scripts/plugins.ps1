# Thin wrapper: all logic lives in plugins.py (cross-platform).
$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot 'plugins.py'
# Order matters on Windows: the py launcher first (python3 may be a store alias stub), then python, then python3.
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $script @args
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python $script @args
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    & python3 $script @args
} else {
    Write-Error 'Python 3 was not found on PATH.'
    exit 2
}
exit $LASTEXITCODE
