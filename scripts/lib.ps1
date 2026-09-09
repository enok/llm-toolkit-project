# Shared helpers for PowerShell setup scripts (symbolic links on Windows).
# Dot-source: . "$PSScriptRoot\lib.ps1"
#
# Directory links: cmd.exe
#   mklink /d <DESTINATION> <SOURCE>, then mklink /J as a Windows fallback.
# DESTINATION = path of the new directory symlink (under the consumer repo).
# SOURCE      = existing toolkit directory that DESTINATION should point to.
# Symlink mode requires Administrator (or Developer Mode); junction fallback requires a local same-drive target.
# Ten Forums reference: https://www.tenforums.com/tutorials/131182-create-soft-hard-symbolic-links-windows.html
#
# Files: mklink /H, mklink (file symlink), PowerShell fallbacks.

function Resolve-ToolkitAbsolutePath {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Path not found: $Path"
    }
    return (Resolve-Path -LiteralPath $Path).Path
}

function Get-ToolkitRelativePath {
    param(
        [Parameter(Mandatory)][string]$FromDirectory,
        [Parameter(Mandatory)][string]$ToPath
    )
    $from = (Resolve-Path -LiteralPath $FromDirectory).Path.TrimEnd('\', '/')
    $to = (Resolve-Path -LiteralPath $ToPath).Path.TrimEnd('\', '/')

    if ($PSVersionTable.PSVersion.Major -ge 6) {
        return [System.IO.Path]::GetRelativePath($from, $to)
    }

    foreach ($py in @('python', 'python3')) {
        $cmd = Get-Command $py -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        $out = & $cmd.Source -c "import os,sys; os.chdir(sys.argv[1]); print(os.path.relpath(os.path.abspath(sys.argv[2])))" $from $to 2>$null
        if ($LASTEXITCODE -eq 0 -and $out) { return $out.Trim() }
    }
    throw "Could not compute relative path. Install PowerShell 7+ or Python on PATH."
}

function Convert-ToGitBashPath {
    param([Parameter(Mandatory)][string]$Path)
    $full = (Resolve-Path -LiteralPath $Path).Path
    if ($full -match '^([A-Za-z]):\\') {
        $d = $Matches[1].ToLower()
        $tail = $full.Substring(3) -replace '\\', '/'
        return "/$d/$tail"
    }
    return $full -replace '\\', '/'
}

function New-ToolkitItemLink {
    <#
    .SYNOPSIS
      New-Item Junction/HardLink/SymbolicLink with correct parameter for PS 5.1 (-Value) vs PS 6+ (-Target).
    #>
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][ValidateSet('Junction', 'HardLink', 'SymbolicLink')][string]$ItemType,
        [Parameter(Mandatory)][string]$PointsTo
    )
    if ($PSVersionTable.PSVersion.Major -ge 6) {
        return New-Item -ItemType $ItemType -Path $Path -Target $PointsTo -ErrorAction Stop
    }
    return New-Item -ItemType $ItemType -Path $Path -Value $PointsTo -ErrorAction Stop
}

function Write-ToolkitExecLine {
    param([Parameter(Mandatory)][string]$Line)
    Write-Host "[toolkit] $Line"
}

function Invoke-ToolkitCmdMklink {
    <#
    .SYNOPSIS
      Run mklink via cmd /c. Directory: mklink /d <DESTINATION> <SOURCE>. Full argument string passed in.
      Prints the exact command (and cmd output) so you can see what ran.
    #>
    param(
        [Parameter(Mandatory)][string]$MklinkArguments
    )
    $cmdExe = Join-Path $env:SystemRoot 'System32\cmd.exe'
    $argLine = '/c ' + $MklinkArguments
    Write-ToolkitExecLine "$cmdExe $argLine"
    $output = & $cmdExe /c $MklinkArguments 2>&1
    $exitCode = $LASTEXITCODE
    foreach ($entry in @($output)) {
        $line = $entry.ToString()
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        Write-Host "         $line"
    }
    return ($exitCode -eq 0)
}

function New-ToolkitLink {
    <#
    .SYNOPSIS
      Directory: cmd  mklink /J <DESTINATION> <SOURCE>  then mklink /d fallback (quoted paths). File: mklink /H then file mklink.
      Throws if link cannot be created (no copy fallback).
    #>
    param(
        [Parameter(Mandatory)][string]$LinkPath,
        [Parameter(Mandatory)][string]$TargetPath
    )
    if (Test-Path -LiteralPath $LinkPath) {
        return $false
    }

    $targetFull = (Resolve-Path -LiteralPath $TargetPath).Path.TrimEnd('\')
    $linkPathNorm = $LinkPath.TrimEnd('\')
    $linkParent = Split-Path -Parent $linkPathNorm
    if (-not (Test-Path -LiteralPath $linkParent)) {
        # Parent dirs are ordinary folders; do not log (only mklink lines should show for links).
        New-Item -ItemType Directory -Path $linkParent -Force | Out-Null
    }

    $isDir = Test-Path -LiteralPath $TargetPath -PathType Container

    # Escape embedded double-quotes for cmd (unlikely in paths)
    function Escape-CmdArg {
        param([string]$s)
        $s -replace '"', '""'
    }
    # For cmd.exe mklink: first path = DESTINATION (new link), second = SOURCE (existing target).
    $destEscaped = Escape-CmdArg $linkPathNorm
    $srcEscaped = Escape-CmdArg $targetFull

    $ok = $false

    if ($isDir) {
        # Junctions first: they need no symlink privilege and match
        # sync-tool-configs.sh behavior; mklink /d is the fallback.
        $ok = Invoke-ToolkitCmdMklink "mklink /J `"$destEscaped`" `"$srcEscaped`""
        if (-not $ok) {
            $ok = Invoke-ToolkitCmdMklink "mklink /d `"$destEscaped`" `"$srcEscaped`""
        }
    }
    else {
        # File: mklink /H DESTINATION SOURCE (hard link)
        $ok = Invoke-ToolkitCmdMklink "mklink /H `"$destEscaped`" `"$srcEscaped`""
        if (-not $ok) {
            try {
                Write-ToolkitExecLine "New-Item -ItemType HardLink -Path '$linkPathNorm' -Value '$targetFull'"
                $null = New-ToolkitItemLink -Path $linkPathNorm -ItemType HardLink -PointsTo $targetFull
                $ok = $true
            }
            catch {
                $ok = $false
            }
        }
        if (-not $ok) {
            $ok = Invoke-ToolkitCmdMklink "mklink `"$destEscaped`" `"$srcEscaped`""
        }
        if (-not $ok) {
            try {
                Write-ToolkitExecLine "New-Item -ItemType SymbolicLink -Path '$linkPathNorm' -> '$targetFull' (PS 5.1: -Value; PS 6+: -Target)"
                $null = New-ToolkitItemLink -Path $linkPathNorm -ItemType SymbolicLink -PointsTo $targetFull
                $ok = $true
            }
            catch {
                $ok = $false
            }
        }
    }

    if ($ok) { return $true }

    $kind = if ($isDir) { 'directory junction or symbolic link (mklink /J, mklink /d)' } else { 'hard link or file symbolic link' }
    $dirHelp = @(
        'Directories use mklink /J first, then mklink /d as a Windows fallback.',
        'Run Command Prompt or PowerShell as Administrator, enable Developer Mode, or keep source and destination on the same local drive for junction fallback.',
        'See: https://www.tenforums.com/tutorials/131182-create-soft-hard-symbolic-links-windows.html'
    )
    $fileHelp = @(
        'Tried: mklink /H, HardLink, mklink (file), SymbolicLink.',
        'See: https://www.tenforums.com/tutorials/131182-create-soft-hard-symbolic-links-windows.html'
    )
    $msg = @(
        "Could not create ${kind}:",
        "  DESTINATION: $linkPathNorm",
        "  SOURCE:      $targetFull",
        '',
        $(if ($isDir) { $dirHelp -join [Environment]::NewLine } else { $fileHelp -join [Environment]::NewLine }),
        '',
        'Fix: local NTFS; many cloud-sync folders block symbolic links.'
    ) -join [Environment]::NewLine
    throw $msg
}

function Normalize-ToolkitFullPath {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return $null }
    try {
        return [System.IO.Path]::GetFullPath($Path.TrimEnd('\', '/'))
    }
    catch {
        return $Path.TrimEnd('\')
    }
}

function Assert-ToolkitSafeRemovalPath {
    param([Parameter(Mandatory)][string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) {
        throw "Refusing to remove an empty path."
    }

    $trimmed = $Path.Trim()
    if ($trimmed -in @('.', '..', '\', '/')) {
        throw "Refusing to remove unsafe path: '$Path'"
    }

    try {
        $full = [System.IO.Path]::GetFullPath($trimmed)
    }
    catch {
        throw "Refusing to remove path with invalid format: '$Path'"
    }

    if ($full -match '^[A-Za-z]:\\?$') {
        throw "Refusing to remove drive root path: '$full'"
    }
}

function Remove-ToolkitPathSafely {
    <#
    .SYNOPSIS
      Safely removes a path. For reparse points (junctions/symlinks), removes only the link, never the target contents.
    .DESCRIPTION
      PowerShell 5.1 Remove-Item -Recurse on a directory junction recurses INTO the target and deletes the target's
      contents instead of just removing the link. This function detects reparse points and removes them as links only.
    #>
    param([Parameter(Mandatory)][string]$Path)
    Assert-ToolkitSafeRemovalPath -Path $Path

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop

    # Check if this is a reparse point (junction, symlink, etc.)
    $isReparsePoint = $false
    if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
        $isReparsePoint = $true
    }

    if ($isReparsePoint) {
        # Remove reparse point as a link only (no recursion into target)
        if ($item.PSIsContainer) {
            # Directory reparse point (junction or directory symlink)
            # Use [System.IO.Directory]::Delete with recurse=$false to remove only the link
            [System.IO.Directory]::Delete($Path, $false)
        }
        else {
            # File reparse point (file symlink or hardlink)
            Remove-Item -LiteralPath $Path -Force
        }
    }
    else {
        # Regular file or directory: safe to use -Recurse
        Remove-Item -LiteralPath $Path -Recurse -Force
    }
}

function Get-ToolkitDirectoryLinkTargetCanon {
    <#
    .SYNOPSIS
      If LinkPath is a directory symlink/junction, returns normalized target path; otherwise $null (plain folder/file or missing).
    #>
    param([Parameter(Mandatory)][string]$LinkPath)
    if (-not (Test-Path -LiteralPath $LinkPath)) {
        return $null
    }
    $item = Get-Item -LiteralPath $LinkPath -Force
    if (-not $item.LinkType) {
        return $null
    }
    $raw = $item.Target
    if ($raw -is [System.Array] -and $raw.Length -gt 0) {
        $raw = $raw[0]
    }
    if ([string]::IsNullOrWhiteSpace([string]$raw)) {
        return $null
    }
    $linkTarget = [string]$raw
    if (-not [System.IO.Path]::IsPathRooted($linkTarget)) {
        $linkTarget = Join-Path (Split-Path -Parent $LinkPath) $linkTarget
    }
    return Normalize-ToolkitFullPath $linkTarget
}

function Assert-ToolkitDirectoryReparseMatches {
    <#
    .SYNOPSIS
      Ensures LinkPath is a reparse point (symlink/junction), not a copied folder, and points at TargetCanon.
    #>
    param(
        [Parameter(Mandatory)][string]$LinkPath,
        [Parameter(Mandatory)][string]$TargetCanon
    )
    $linkCanon = Get-ToolkitDirectoryLinkTargetCanon -LinkPath $LinkPath
    if (-not $linkCanon) {
        $item = Get-Item -LiteralPath $LinkPath -Force -ErrorAction SilentlyContinue
        if (-not $item) {
            throw "Path missing: '$LinkPath'"
        }
        throw @(
            "'$LinkPath' is not a link (no LinkType); it may be a plain folder or copy. Remove it, then re-run:",
            "  Remove-Item -Recurse -Force '$LinkPath'"
        ) -join [Environment]::NewLine
    }
    if ($linkCanon -ine $TargetCanon) {
        throw @(
            "Link at '$LinkPath' does not point at the toolkit path.",
            "Expected: $TargetCanon",
            "Actual:   $linkCanon",
            "Remove it, then re-run: Remove-Item -Recurse -Force '$LinkPath'"
        ) -join [Environment]::NewLine
    }
}

function Ensure-ToolkitDirectoryLink {
    <#
    .SYNOPSIS
      Create a directory symlink (mklink /d) or verify an existing reparse point points at TargetPath.
      Replaces a plain directory or a link pointing elsewhere (e.g. Drive sync copy, old layout) — never keeps a duplicate tree.
    #>
    param(
        [Parameter(Mandatory)][string]$LinkPath,
        [Parameter(Mandatory)][string]$TargetPath,
        [switch]$AllowRepair
    )
    if (-not (Test-Path -LiteralPath $TargetPath -PathType Container)) {
        throw "Toolkit directory missing: $TargetPath"
    }
    $targetCanon = Normalize-ToolkitFullPath (Resolve-Path -LiteralPath $TargetPath).Path

    $hadBlockingPath = Test-Path -LiteralPath $LinkPath
    $existingCanon = Get-ToolkitDirectoryLinkTargetCanon -LinkPath $LinkPath
    if ($existingCanon -and ($existingCanon -ieq $targetCanon)) {
        return 'ok'
    }

    if ($hadBlockingPath) {
        if (-not $AllowRepair) {
            throw @(
                "Blocking path exists at '$LinkPath' and it does not point at the expected toolkit directory.",
                "Target: $TargetPath",
                '',
                'Refusing to delete it automatically.',
                "Remove it manually, or rerun the refresh command with -Force / --force if you want the toolkit to repair it."
            ) -join [Environment]::NewLine
        }
        Write-Warning "[toolkit] Repairing '$LinkPath': replacing plain folder or wrong link with directory link (junction or symlink) -> '$TargetPath' (canonical rules/workflows stay on disk; only this path is replaced)."
        Remove-ToolkitPathSafely -Path $LinkPath
    }

    New-ToolkitLink -LinkPath $LinkPath -TargetPath $TargetPath | Out-Null
    Assert-ToolkitDirectoryReparseMatches -LinkPath $LinkPath -TargetCanon $targetCanon
    if ($hadBlockingPath) {
        return 'repaired'
    }
    return 'linked'
}

function Ensure-ToolkitWindsurfLayout {
    <#
    .SYNOPSIS
      Ensures toolkit /.windsurf/rules and /.windsurf/workflows point at canonical rules/ and workflows/.
      Lets consumers use a single symlink: .windsurf -> toolkit/.windsurf (IDE shows root as a link).
    #>
    param(
        [Parameter(Mandatory)][string]$ToolkitRoot,
        [switch]$AllowRepair
    )
    $rules = Join-Path $ToolkitRoot 'rules'
    $wf = Join-Path $ToolkitRoot 'workflows'
    if (-not (Test-Path -LiteralPath $rules -PathType Container)) {
        throw "Toolkit rules/ missing at $ToolkitRoot"
    }
    if (-not (Test-Path -LiteralPath $wf -PathType Container)) {
        throw "Toolkit workflows/ missing at $ToolkitRoot"
    }
    $ws = Join-Path $ToolkitRoot '.windsurf'
    if (-not (Test-Path -LiteralPath $ws)) {
        New-Item -ItemType Directory -Path $ws -Force | Out-Null
    }
    $null = Ensure-ToolkitDirectoryLink -LinkPath (Join-Path $ws 'rules') -TargetPath $rules -AllowRepair:$AllowRepair
    $null = Ensure-ToolkitDirectoryLink -LinkPath (Join-Path $ws 'workflows') -TargetPath $wf -AllowRepair:$AllowRepair
}

function Ensure-ToolkitSetupLayout {
    <#
    .SYNOPSIS
      Toolkit-only: links .setup/integrations and .setup/examples to the canonical
      integrations/ and rules/examples/ directories so consumers get one stable entry path.
    #>
    param(
        [Parameter(Mandatory)][string]$ToolkitRoot,
        [switch]$AllowRepair
    )
    $setup = Join-Path $ToolkitRoot '.setup'
    if (-not (Test-Path -LiteralPath $setup)) {
        New-Item -ItemType Directory -Path $setup -Force | Out-Null
    }
    $integrations = Join-Path $ToolkitRoot 'integrations'
    if (Test-Path -LiteralPath $integrations -PathType Container) {
        $null = Ensure-ToolkitDirectoryLink -LinkPath (Join-Path $setup 'integrations') -TargetPath $integrations -AllowRepair:$AllowRepair
    }
    $examples = Join-Path $ToolkitRoot 'rules\examples'
    if (Test-Path -LiteralPath $examples -PathType Container) {
        $null = Ensure-ToolkitDirectoryLink -LinkPath (Join-Path $setup 'examples') -TargetPath $examples -AllowRepair:$AllowRepair
    }
}

function Get-GitBashExe {
    foreach ($p in @(
            "${env:ProgramFiles}\Git\bin\bash.exe",
            "${env:ProgramFiles(x86)}\Git\bin\bash.exe"
        )) {
        if (Test-Path -LiteralPath $p) { return $p }
    }
    return $null
}

function ConvertTo-ToolkitBashQuotedArg {
    param([Parameter(Mandatory)][string]$Value)
    return "'" + ($Value -replace "'", "'\\''") + "'"
}

function Invoke-ToolkitBashScript {
    param(
        [Parameter(Mandatory)][string]$ScriptPath,
        [string[]]$Arguments = @()
    )
    if (-not (Test-Path -LiteralPath $ScriptPath)) {
        Write-Warning "Bash script not found: $ScriptPath"
        return $false
    }
    $gitBash = Get-GitBashExe
    if (-not $gitBash) {
        Write-Warning "Git Bash not found. Install Git for Windows or run the shell script from a Bash environment."
        return $false
    }

    $scriptUnix = Convert-ToGitBashPath $ScriptPath
    $parts = @('bash', (ConvertTo-ToolkitBashQuotedArg $scriptUnix))
    foreach ($arg in $Arguments) {
        $parts += ConvertTo-ToolkitBashQuotedArg $arg
    }
    $bashCommand = $parts -join ' '
    Write-ToolkitExecLine "& '$gitBash' -lc '$bashCommand'"
    & $gitBash -lc $bashCommand | ForEach-Object { Write-Host $_ }
    $exitCode = $LASTEXITCODE
    return ($exitCode -eq 0)
}

function Invoke-ToolkitSyncToolConfigs {
    param(
        [Parameter(Mandatory)][string]$ConsumerPath,
        [Parameter(Mandatory)][string]$ScriptDir,
        [switch]$SkipAgentsMd,
        [switch]$SkipCursorRules,
        [switch]$SkipGithub,
        [switch]$Force
    )
    $sh = Join-Path $ScriptDir 'sync-tool-configs.sh'
    if (-not (Test-Path -LiteralPath $sh)) {
        Write-Warning "sync-tool-configs.sh not found; skip shared tool surface repair and local export refresh."
        return $false
    }
    $cUnix = Convert-ToGitBashPath $ConsumerPath
    $arguments = @($cUnix)
    if ($SkipAgentsMd) {
        $arguments += '--skip-agents-md'
    }
    if ($SkipCursorRules) {
        $arguments += '--skip-cursor-rules'
    }
    if ($SkipGithub) {
        $arguments += '--skip-github'
    }
    if ($Force) {
        $arguments += '--force'
    }
    if (-not (Invoke-ToolkitBashScript -ScriptPath $sh -Arguments $arguments)) {
        Write-Warning "sync-tool-configs.sh failed (exit $LASTEXITCODE). Run from Git Bash if paths contain special characters."
        return $false
    }
    else {
        Write-Host "Shared tool surfaces repaired and local exports refreshed via sync-tool-configs.sh"
        return $true
    }
}
