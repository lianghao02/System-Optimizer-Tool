@echo off
chcp 65001 >nul
title Windows 系統優化工具 (Python 傳統版)
cd /d "%~dp0legacy-python"
set "PS_HOST=pwsh.exe"
where.exe pwsh.exe >nul 2>&1
if errorlevel 1 set "PS_HOST=powershell.exe"

if exist "run.bat" (
    call run.bat
) else (
    "%PS_HOST%" -NoProfile -ExecutionPolicy Bypass -File setup_and_run.ps1
)
