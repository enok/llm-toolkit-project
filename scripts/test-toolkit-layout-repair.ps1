#Requires -Version 5.1
<#
.SYNOPSIS
  Verifies Ensure-ToolkitWindsurfLayout repairs a plain .windsurf/rules folder with real symlinks (no copies).

.DESCRIPTION
  Creates a minimal fake toolkit under %TEMP%, seeds .windsurf/rules as a plain directory (simulates Drive/copy layout),
  runs Ensure-ToolkitWindsurfLayout, then asserts rules/workflows are directory links and content matches canonical rules/.

  Requires: Administrator OR Windows Developer Mode (same as mklink /d for directory symlinks).

.EXAMPLE
  # Elevated PowerShell:
  .\scripts\test-toolkit-layout-repair.ps1
#>
param()

$ErrorActionPreference = 'Stop'

$ScriptDir = $PSScriptRoot
. "$ScriptDir\lib.ps1"

function Test-ToolkitMklinkDirectoryAllowed {
    $d = Join-Path $env:TEMP ("toolkit-mklink-precheck-{0}" -f ([guid]::NewGuid().ToString('n').Substring(0, 8)))
    New-Item -ItemType Directory -Path $d -Force | Out-Null
    $src = Join-Path $d 'src'
    $dst = Join-Path $d 'dst'
    New-Item -ItemType Directory -Path $src -Force | Out-Null
    $cmdExe = Join-Path $env:SystemRoot 'System32\cmd.exe'
    function Escape-CmdArg { param([string]$s) $s -replace '"', '""' }
    $argLine = '/c mklink /d "{0}" "{1}"' -f (Escape-CmdArg $dst), (Escape-CmdArg $src)
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $cmdExe
        $psi.Arguments = $argLine
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $p = New-Object System.Diagnostics.Process
        $p.StartInfo = $psi
        [void]$p.Start()
        $null = $p.StandardOutput.ReadToEnd()
        $null = $p.StandardError.ReadToEnd()
        $p.WaitForExit()
        return ($p.ExitCode -eq 0)
    }
    finally {
        Remove-Item -LiteralPath $d -Recurse -Force -ErrorAction SilentlyContinue
    }
}

if (-not (Test-ToolkitMklinkDirectoryAllowed)) {
    Write-Warning 'SKIP: cannot create directory symlinks (run this test in an elevated PowerShell or enable Windows Developer Mode).'
    exit 0
}

$t = Join-Path $env:TEMP ("toolkit-layout-test-{0}" -f ([guid]::NewGuid().ToString('n').Substring(0, 8)))
try {
    New-Item -ItemType Directory -Path (Join-Path $t 'rules') -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $t 'rules\marker.txt') -Value 'rules-ok'
    New-Item -ItemType Directory -Path (Join-Path $t 'workflows') -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $t 'workflows\marker.txt') -Value 'wf-ok'

    New-Item -ItemType Directory -Path (Join-Path $t '.windsurf') -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $t '.windsurf\rules') -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $t '.windsurf\rules\stale.txt') -Value 'should-not-win'

    Ensure-ToolkitWindsurfLayout -DevToolsRoot $t

    foreach ($name in @('rules', 'workflows')) {
        $linkPath = Join-Path $t ".windsurf\$name"
        $item = Get-Item -LiteralPath $linkPath -Force
        if (-not $item.LinkType) {
            throw "FAIL: '$linkPath' is not a symlink/junction (LinkType empty)."
        }
    }

    $rulesLink = Join-Path $t '.windsurf\rules'
    $canon = Get-ToolkitDirectoryLinkTargetCanon -LinkPath $rulesLink
    $expect = Normalize-ToolkitFullPath (Join-Path $t 'rules')
    if ($canon -ine $expect) {
        throw "FAIL: .windsurf/rules target mismatch. Expected: $expect  Actual: $canon"
    }

    if (-not (Test-Path -LiteralPath (Join-Path $rulesLink 'marker.txt'))) {
        throw "FAIL: marker.txt missing through rules link."
    }
    if (Test-Path -LiteralPath (Join-Path $rulesLink 'stale.txt')) {
        throw "FAIL: stale.txt still visible (plain folder was not replaced by link)."
    }

    Write-Host 'PASS: toolkit windsurf layout repair uses symlinks; plain folder replaced.'
}
finally {
    if (Test-Path -LiteralPath $t) {
        Remove-Item -LiteralPath $t -Recurse -Force -ErrorAction SilentlyContinue
    }
}
