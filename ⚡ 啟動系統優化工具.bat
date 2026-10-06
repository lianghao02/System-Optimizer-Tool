@echo off
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "%~dp0scripts\run.ps1" %*
exit /b %errorlevel%
