@echo off
setlocal
REM =============================================================================
REM  Run this file from an Administrator Command Prompt (required for mklink /d).
REM
REM  Directory links are created exactly as:
REM    mklink /d <DESTINATION> <SOURCE>
REM  DESTINATION = path of the new symlink under the consumer repo
REM  SOURCE      = existing toolkit directory (absolute path)
REM =============================================================================
REM
REM  Usage: scripts\setup-repo.cmd [path-to-consumer-repo]
REM  Default consumer: current directory. Quote paths with spaces.

net session >nul 2>&1
if errorlevel 1 (
    echo ERROR: Run this script from an Administrator Command Prompt so mklink /d can succeed. >&2
    exit /b 1
)

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "PS1=%SCRIPT_DIR%\setup-repo.ps1"
set "POWERSHELL_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PS1%" (
    echo Error: setup-repo.ps1 not found at %PS1% >&2
    exit /b 1
)
if not exist "%POWERSHELL_EXE%" (
    echo Error: Windows PowerShell not found at %POWERSHELL_EXE% >&2
    exit /b 1
)

"%POWERSHELL_EXE%" -NoLogo -NoProfile -ExecutionPolicy RemoteSigned -File "%PS1%" %*
exit /b %ERRORLEVEL%
