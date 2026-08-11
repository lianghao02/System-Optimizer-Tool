@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

set "VENV_PYTHON=%~dp0.venv\Scripts\python.exe"

rem [ 1. 優先使用專案現有 .venv 虛擬環境 ]
if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" -c "import sys" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=%VENV_PYTHON%"
        goto LAUNCH
    )
    echo [警告] 現有 .venv 已失效，準備重新建立。
)

rem [ 2. 尋找本機實體 Python (排除 WindowsApps 假別名) ]
set "PYTHON_EXE="

for /f "delims=" %%I in ('py -3 -c "import sys; p=sys.executable; print(p) if 'windowsapps' not in p.lower() else None" 2^>nul') do (
    if exist "%%I" set "PYTHON_EXE=%%I"
)

if not defined PYTHON_EXE (
    if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
    if exist "%LOCALAPPDATA%\Python\pythoncore-3.12-64\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Python\pythoncore-3.12-64\python.exe"
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
)

if not defined PYTHON_EXE (
    echo [錯誤] 找不到本機實體 Python！請確定已安裝 Python 並將其加入系統環境變數。
    pause
    exit /b 1
)

rem [ 3. 自動建立專案獨立 .venv 環境 ]
echo [資訊] 檢測到系統 Python：%PYTHON_EXE%
echo [資訊] 正在為本專案建立獨立虛擬環境 (.venv)...
"%PYTHON_EXE%" -m venv "%~dp0.venv"
if errorlevel 1 (
    echo [錯誤] 建立虛擬環境失敗，為避免污染全域 Python，已停止啟動。
    pause
    exit /b 1
)
"%VENV_PYTHON%" -c "import sys" >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 新建的虛擬環境無法執行，已停止啟動。
    pause
    exit /b 1
)
set "PYTHON_EXE=%VENV_PYTHON%"

:LAUNCH
"%PYTHON_EXE%" -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo [資訊] 正在安裝相依套件: customtkinter ...
    "%PYTHON_EXE%" -m pip install customtkinter
    if errorlevel 1 (
        echo [錯誤] customtkinter 安裝失敗，請檢查網路與 pip 設定。
        pause
        exit /b 1
    )
    "%PYTHON_EXE%" -c "import customtkinter" >nul 2>&1
    if errorlevel 1 (
        echo [錯誤] customtkinter 安裝後仍無法載入，已停止啟動。
        pause
        exit /b 1
    )
)

echo [OK] 啟動系統優化工具...
"%PYTHON_EXE%" main.py
set "APP_EXIT=%ERRORLEVEL%"
if not "%APP_EXIT%"=="0" pause
exit /b %APP_EXIT%
