# Thin wrapper: all logic lives in kb.py (cross-platform).
$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot 'kb.py'
$python = $null
foreach ($name in @('python3', 'python')) {
    if (Get-Command $name -ErrorAction SilentlyContinue) { $python = $name; break }
}
if ($python) {
    & $python $script @args
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $script @args
} else {
    Write-Error 'Python 3 was not found on PATH.'
    exit 2
}
exit $LASTEXITCODE
