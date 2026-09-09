<#
.SYNOPSIS
  Replaces ```mermaid fenced blocks with SVG images by default, then optionally builds a PDF with Pandoc (--pdf-engine=typst).

  Diagrams are rendered via Kroki (HTTPS POST to kroki.io). Do not use for highly sensitive diagrams on locked-down networks unless you run a self-hosted Kroki and pass -KrokiUrl.

.EXAMPLE
  .\render-mermaid-in-markdown-for-pdf.ps1 `
    -MarkdownPath "docs\jira\TICKET-123\architecture.md" `
    -OutputMarkdownPath "docs\jira\TICKET-123\pdf\architecture-for-pdf.md" `
    -PdfOut "architecture.pdf" `
    -PdfTitle "Architecture"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    ### Source .md file (e.g. architecture.md).
    [string] $MarkdownPath,

    [Parameter(Mandatory = $false)]
    ### Generated .md referencing mermaid/gen-NN.<format>. Default: <source-dir>\<stem>-for-pdf.md
    [string] $OutputMarkdownPath = "",

    [Parameter(Mandatory = $false)]
    [string] $ImageSubdir = "mermaid",

    [Parameter(Mandatory = $false)]
    ### Generated diagram format. Prefer svg for crisp PDF/wiki output; use png only when required.
    [ValidateSet("svg", "png")]
    [string] $ImageFormat = "svg",

    [Parameter(Mandatory = $false)]
    ### POST endpoint for Mermaid → image (default: public Kroki for ImageFormat).
    [string] $KrokiUrl = "",

    [Parameter(Mandatory = $false)]
    [string] $PandocExe = "",

    [Parameter(Mandatory = $false)]
    ### PDF file name only or relative path; written under the same directory as OutputMarkdownPath.
    [string] $PdfOut = "",

    [Parameter(Mandatory = $false)]
    [string] $PdfTitle = ""
)

$ErrorActionPreference = "Stop"

$callerCwd = (Get-Location -PSProvider FileSystem).Path
function Resolve-FilePath([string] $Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return $Path }
    if ([System.IO.Path]::IsPathRooted($Path)) { return [System.IO.Path]::GetFullPath($Path) }
    return [System.IO.Path]::GetFullPath((Join-Path $callerCwd $Path))
}

function Resolve-ChildDirectory([string] $Parent, [string] $Child, [string] $Label) {
    if ([string]::IsNullOrWhiteSpace($Child)) {
        throw "$Label must be a non-empty relative path."
    }
    if ([System.IO.Path]::IsPathRooted($Child)) {
        throw "$Label must be relative: $Child"
    }

    $parentFull = [System.IO.Path]::GetFullPath($Parent).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    $childFull = [System.IO.Path]::GetFullPath((Join-Path $parentFull $Child)).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    $prefix = $parentFull + [System.IO.Path]::DirectorySeparatorChar
    if (-not $childFull.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label must resolve under $parentFull`: $Child"
    }
    return $childFull
}

function Save-MermaidImageViaKroki {
    param(
        [Parameter(Mandatory = $true)][string] $Diagram,
        [Parameter(Mandatory = $true)][string] $OutPath,
        [Parameter(Mandatory = $true)][string] $KrokiUrl
    )
    Invoke-WebRequest -Uri $KrokiUrl -Method Post -Body $Diagram -ContentType "text/plain; charset=utf-8" -OutFile $OutPath -UseBasicParsing
}

$MarkdownPath = (Resolve-Path -LiteralPath (Resolve-FilePath $MarkdownPath)).Path
$mdDir = Split-Path -Parent $MarkdownPath
$mdName = [System.IO.Path]::GetFileNameWithoutExtension($MarkdownPath)

if ([string]::IsNullOrWhiteSpace($OutputMarkdownPath)) {
    $OutputMarkdownPath = Join-Path $mdDir "${mdName}-for-pdf.md"
} else {
    $OutputMarkdownPath = Resolve-FilePath $OutputMarkdownPath
    $outParent = Split-Path -Parent $OutputMarkdownPath
    if (-not (Test-Path -LiteralPath $outParent)) {
        New-Item -ItemType Directory -Path $outParent -Force | Out-Null
    }
}

$outMdParent = Split-Path -Parent $OutputMarkdownPath
$imageDir = Resolve-ChildDirectory -Parent $outMdParent -Child $ImageSubdir -Label "ImageSubdir"
if (Test-Path -LiteralPath $imageDir) {
    Remove-Item -LiteralPath $imageDir -Recurse -Force
}
New-Item -ItemType Directory -Path $imageDir -Force | Out-Null

if ([string]::IsNullOrWhiteSpace($KrokiUrl)) {
    $KrokiUrl = "https://kroki.io/mermaid/$ImageFormat"
}

$raw = [System.IO.File]::ReadAllText($MarkdownPath)
$pattern = '(?s)```mermaid\s*\r?\n(.*?)```'
$mermaidMatches = [regex]::Matches($raw, $pattern)

if ($mermaidMatches.Count -eq 0) {
    Write-Host "No mermaid blocks found; copying markdown as-is."
    [System.IO.File]::Copy($MarkdownPath, $OutputMarkdownPath, $true)
    exit 0
}

$sb = New-Object System.Text.StringBuilder
$last = 0
$idx = 1
foreach ($m in $mermaidMatches) {
    $null = $sb.Append($raw.Substring($last, $m.Index - $last))
    $body = $m.Groups[1].Value.TrimEnd()
    $baseName = ("gen-{0:D2}" -f $idx)
    $imagePath = Join-Path $imageDir "$baseName.$ImageFormat"

    Write-Host "Rendering $baseName via Kroki ..."
    Save-MermaidImageViaKroki -Diagram $body -OutPath $imagePath -KrokiUrl $KrokiUrl
    if (-not (Test-Path -LiteralPath $imagePath) -or (Get-Item -LiteralPath $imagePath).Length -lt 32) {
        throw "Kroki did not produce a usable $ImageFormat file: $imagePath"
    }

    $rel = ($ImageSubdir.TrimEnd('/', '\') + '/' + $baseName + '.' + $ImageFormat).Replace('\', '/')
    $null = $sb.AppendLine("")
    $null = $sb.AppendLine("![Diagram $idx]($rel)")
    $null = $sb.AppendLine("")
    $last = $m.Index + $m.Length
    $idx++
}
$null = $sb.Append($raw.Substring($last))
[System.IO.File]::WriteAllText($OutputMarkdownPath, $sb.ToString(), [System.Text.UTF8Encoding]::new($false))
Write-Host "Wrote $OutputMarkdownPath"

if (-not [string]::IsNullOrWhiteSpace($PdfOut)) {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    if ([string]::IsNullOrWhiteSpace($PandocExe)) {
        $pc = Get-Command pandoc -ErrorAction SilentlyContinue
        if (-not $pc) {
            $local = "$env:LOCALAPPDATA\Pandoc\pandoc.exe"
            if (Test-Path -LiteralPath $local) { $PandocExe = $local } else { throw "pandoc not on PATH or at $local" }
        } else {
            $PandocExe = $pc.Source
        }
    } elseif (-not (Test-Path -LiteralPath $PandocExe)) {
        throw "Pandoc not found at $PandocExe"
    }
    if ([string]::IsNullOrWhiteSpace($PdfTitle)) {
        $PdfTitle = $mdName
    }
    $pdfFull = [System.IO.Path]::GetFullPath((Join-Path $outMdParent (Split-Path -Leaf $PdfOut)))
    Push-Location $outMdParent
    try {
        $relMd = Split-Path -Leaf $OutputMarkdownPath
        & $PandocExe $relMd -o $pdfFull --pdf-engine=typst --metadata title="$PdfTitle" "--resource-path=$outMdParent"
        Write-Host "Wrote PDF: $pdfFull"
    } finally {
        Pop-Location
    }
}
