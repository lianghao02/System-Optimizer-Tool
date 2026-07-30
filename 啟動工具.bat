@echo off
cd /d "%~dp0"
python -c "import customtkinter" 2>nul
if errorlevel 1 (
    echo Installing required dependency: customtkinter ...
    python -m pip install customtkinter
)
python main.py
if errorlevel 1 pause
