@echo off
:: Ensure-symlinks.cmd - Elevated wrapper for ensure-symlinks.ps1
:: Run this from an elevated Command Prompt (Run as Administrator)

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: This script requires Administrator privileges.
    echo Please right-click Command Prompt and select "Run as administrator".
    pause
    exit /b 1
)

set "SCRIPT_DIR=%~dp0"
set "CONSUMER=%~1"
if "%CONSUMER%"=="" set "CONSUMER=."

powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%ensure-symlinks.ps1" "%CONSUMER%"
