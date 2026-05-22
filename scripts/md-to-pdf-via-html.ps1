<#
.SYNOPSIS
  Markdown → standalone HTML (Pandoc, embedded CSS) → headless Chrome (or Edge) → PDF.
  Use for wide pipe tables where Pandoc+Typst column layout overlaps.

  Chrome is preferred for --print-to-pdf (Edge headless print is unreliable on some builds).

.PARAMETER Portrait
  Use letter portrait CSS instead of landscape.

.EXAMPLE
  .\md-to-pdf-via-html.ps1 -MarkdownPath ".\docs\jira\TICKET-123\README.md" -PdfOut ".\docs\jira\TICKET-123\pdf\README.pdf" -Portrait
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $MarkdownPath,

    [Parameter(Mandatory = $true)]
    [string] $PdfOut,

    [Parameter(Mandatory = $false)]
    [string] $Title = "",

    [Parameter(Mandatory = $false)]
    [switch] $Portrait,

    [Parameter(Mandatory = $false)]
    [string] $PandocExe = ""
)

$ErrorActionPreference = "Stop"

$callerCwd = (Get-Location -PSProvider FileSystem).Path
function Resolve-FilePath([string] $Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return $Path }
    if ([System.IO.Path]::IsPathRooted($Path)) { return [System.IO.Path]::GetFullPath($Path) }
    return [System.IO.Path]::GetFullPath((Join-Path $callerCwd $Path))
}

function Get-PandocExe {
    param([string] $Override)
    if (-not [string]::IsNullOrWhiteSpace($Override) -and (Test-Path -LiteralPath $Override)) { return $Override }
    $pc = Get-Command pandoc -ErrorAction SilentlyContinue
    if ($pc) { return $pc.Source }
    $local = "$env:LOCALAPPDATA\Pandoc\pandoc.exe"
    if (Test-Path -LiteralPath $local) { return $local }
    throw "pandoc not on PATH or at $local"
}

function Get-HeadlessPrintBrowser {
    $chrome = "$env:ProgramFiles\Google\Chrome\Application\chrome.exe"
    if (Test-Path -LiteralPath $chrome) { return $chrome }
    $candidates = @(
        "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
        "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path -LiteralPath $c) { return $c }
    }
    throw "Neither Google Chrome nor Microsoft Edge found for headless PDF"
}

function Get-FreeTcpPort {
    $l = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
    try {
        $l.Start()
        return $l.LocalEndpoint.Port
    } finally {
        $l.Stop()
    }
}

$MarkdownPath = (Resolve-Path -LiteralPath (Resolve-FilePath $MarkdownPath)).Path
$mdDir = Split-Path -Parent $MarkdownPath
$PdfOut = Resolve-FilePath $PdfOut
$pdfDir = Split-Path -Parent $PdfOut
if (-not (Test-Path -LiteralPath $pdfDir)) {
    New-Item -ItemType Directory -Path $pdfDir -Force | Out-Null
}

if ([string]::IsNullOrWhiteSpace($Title)) {
    $Title = [System.IO.Path]::GetFileNameWithoutExtension($MarkdownPath)
}

$pandoc = Get-PandocExe -Override $PandocExe
$browser = Get-HeadlessPrintBrowser

$cssLand = Join-Path $PSScriptRoot "pdf-from-md.css"
$cssPort = Join-Path $PSScriptRoot "pdf-from-md-portrait.css"
if ($Portrait) {
    if (-not (Test-Path -LiteralPath $cssPort)) {
        throw "Missing $cssPort"
    }
    $cssPick = (Resolve-Path -LiteralPath $cssPort).Path
} else {
    $cssPick = (Resolve-Path -LiteralPath $cssLand).Path
}

$tmp = Join-Path $env:TEMP ("mdpdf-" + [Guid]::NewGuid().ToString("n").Substring(0, 12))
New-Item -ItemType Directory -Path $tmp -Force | Out-Null
$htmlOut = Join-Path $tmp "doc.html"
$pdfTemp = Join-Path $env:TEMP ("mdout-" + [Guid]::NewGuid().ToString("n") + ".pdf")

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    throw "Python is required on PATH for localhost HTML → PDF (http.server + headless browser)."
}

try {
    & $pandoc $MarkdownPath `
        -o $htmlOut `
        --standalone `
        --embed-resources `
        --css=$cssPick `
        -f markdown `
        --metadata title="$Title" `
        "--resource-path=$mdDir"

    if (-not (Test-Path -LiteralPath $htmlOut)) {
        throw "Pandoc did not create $htmlOut"
    }

    $port = Get-FreeTcpPort
    $job = Start-Job -ScriptBlock {
        param($workDir, $listenPort)
        Set-Location -LiteralPath $workDir
        python -m http.server $listenPort
    } -ArgumentList $tmp, $port

    Start-Sleep -Seconds 2
    try {
        $httpUrl = "http://127.0.0.1:$port/doc.html"
        Remove-Item -LiteralPath $pdfTemp -Force -ErrorAction SilentlyContinue
        & $browser `
            --headless=new `
            --disable-gpu `
            --no-pdf-header-footer `
            "--print-to-pdf=$pdfTemp" `
            $httpUrl
        Start-Sleep -Seconds 2
    } finally {
        Stop-Job -Job $job -ErrorAction SilentlyContinue
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    }

    if (-not (Test-Path -LiteralPath $pdfTemp) -or (Get-Item -LiteralPath $pdfTemp).Length -lt 500) {
        throw "Headless print did not produce a usable PDF at $pdfTemp"
    }

    Remove-Item -LiteralPath $PdfOut -Force -ErrorAction SilentlyContinue
    Copy-Item -LiteralPath $pdfTemp -Destination $PdfOut -Force
} finally {
    Remove-Item -LiteralPath $pdfTemp -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
}

if (-not (Test-Path -LiteralPath $PdfOut) -or (Get-Item -LiteralPath $PdfOut).Length -lt 500) {
    throw "PDF was not produced or is too small: $PdfOut"
}

Write-Host "OK $PdfOut ($((Get-Item -LiteralPath $PdfOut).Length) bytes)"
