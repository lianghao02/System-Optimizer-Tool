@echo off
chcp 65001 >nul
title Windows 系統極速優化工具 (.NET 8 原生版)
cd /d "%~dp0"

if exist "%~dp0dotnet-src\publish\standalone\SystemOptimizer.App.exe" (
    start "" "%~dp0dotnet-src\publish\standalone\SystemOptimizer.App.exe"
) else if exist "%~dp0dotnet-src\publish\slim\SystemOptimizer.App.exe" (
    start "" "%~dp0dotnet-src\publish\slim\SystemOptimizer.App.exe"
) else if exist "%~dp0dotnet-src\publish\SystemOptimizer.App.exe" (
    start "" "%~dp0dotnet-src\publish\SystemOptimizer.App.exe"
) else (
    echo [ERROR] 找不到發布檔，請先執行 dotnet-src\build_release.ps1
    pause
)
