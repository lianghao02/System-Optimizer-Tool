@echo off
chcp 65001 >nul
title Windows 系統優化工具 (Python 傳統版)
cd /d "%~dp0legacy-python"

if exist "run.bat" (
    call run.bat
) else (
    powershell -ExecutionPolicy Bypass -File setup_and_run.ps1
)
